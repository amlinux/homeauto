from concurrence import Tasklet, Channel, TimeoutError
from concurrence.extra import Lock
from concurrence.timer import Timeout
from serial import SerialStream
import logging
import time
import random

def crc(crc, data):
    "Accepts previous CRC byte and data byte. Returns new CRC"
    for i in xrange(0, 8):
        if (crc ^ (data >> i)) & 1:
            crc ^= 0x9d
        crc >>= 1
    return crc

class BaudRateCalibrationError(Exception):
    "Raised when host baud rate calibration failed"

class RequestNotImplemented(Exception):
    "This exception is raised by a protocol when it encounters unsupported request"

class CommunicationError(Exception):
    """
    This base class covers all exceptions due to communication problems
    (i.e. not software caused errors)
    """
    def __init__(self):
        self.args = []

class DestinationUnreachable(CommunicationError):
    "Packet routing error"

class ResponseError(CommunicationError):
    "Error during waiting for response"

class DeviceUnreachable(ResponseError):
    "Raised when requested device is unreachable"
    def __init__(self, reason):
        ResponseError.__init__(self)
        self.reason = reason
        self.args = [reason]

class Host(object):
    "Interface to the hardware"
    def __init__(self, dispatcher, devname):
        "Constructor. devname - serial port devname"
        self.dispatcher = dispatcher
        self.stream = SerialStream(devname)
        self._next_pkt_id = 0
        self._devname = devname
        self._sendlock = Lock()
        self._calibrated = False
        Tasklet.new(self.auto_calibrate_baudrate)()

    def send_raw(self, buf):
        "Send raw data without any checksuming and headers"
        with self._sendlock:
            print "%s sent: %s" % (self._devname, ", ".join(["0x%02x" % d for d in buf]))
            buf = ''.join([chr(a) for a in buf])
            with self.stream.get_writer() as writer:
                writer.write_bytes(buf)
                writer.flush()

    def flush(self):
        self.stream.flush()

    def send(self, pkt):
        "Immediately push packet to the serial port"
        buf = [0x5a]
        _crc = 0
        for data in [len(pkt)] + list(pkt):
            if type(data) == str and len(data) == 1:
                data = ord(data)
            _crc = crc(_crc, data)
            buf.append(data)
        buf.append(_crc)
        self.send_raw(buf)

    def ping(self):
        while True:
            if self._calibrated:
                pkt = [0xf2]
                for i in xrange(0, 8):
                    pkt.append(random.randint(0, 255))
                self.send(pkt)
            Tasklet.sleep(7)

    def loop(self):
        "Infinitely read serial input and parse packets"
        with self.stream.get_reader() as reader:
            while True:
                try:
                    # wait for preamble
                    while True:
                        data = ord(reader.read_bytes(1))
                        if data == 0x5a:
                            break
                    # read packet length
                    _crc = 0
                    pktlen = ord(reader.read_bytes(1))
                    _crc = crc(_crc, pktlen)
                    # read packet data
                    if pktlen > 0:
                        data = []
                        try:
                            with Timeout.push(1):
                                for d in reader.read_bytes(pktlen):
                                    d = ord(d)
                                    data.append(d)
                                    _crc = crc(_crc, d)
                                # read CRC
                                _crc = crc(_crc, ord(reader.read_bytes(1)))
                        except TimeoutError:
                            pass
                        else:
                            # check CRC
                            if _crc == 0:
                                print "%s received: %s" % (self._devname, ", ".join(["0x%02x" % d for d in data]))
                                if self._calibrated:
                                    if len(data) == 1 and (data[0] == ord('I') or data[0] == 0xf2):
                                        self._calibrated = False
                                        Tasklet.new(self.auto_calibrate_baudrate)()
                                if self._calibrated or data[0] == 0xf0 or data[0] == ord('E'):
                                    self.dispatcher.receive(data)
                except Exception as e:
                    logging.exception(e)

    def version(self):
        "Check host version (None if not available)"
        req = HostVersionRequest(self)
        try:
            return self.dispatcher.request(req, timeout=10)
        except TimeoutError:
            return None

    def calibrate_baudrate(self):
        "Perform baud rate calibration"
        req = BaudRateCalibrationRequest(self)
        try:
            res = self.dispatcher.request(req, timeout=3)
            if res:
                self._calibrated = True
                return res
            else:
                raise BaudRateCalibrationError()
        except TimeoutError:
            raise BaudRateCalibrationError()

    def auto_calibrate_baudrate(self):
        while True:
            try:
                print "%s calibrated: %s" % (self._devname, self.calibrate_baudrate())
            except BaudRateCalibrationError:
                print "%s calibration failed" % self._devname
            else:
                self._calibrated = True
                break

    def next_pkt_id(self):
        self._next_pkt_id = (self._next_pkt_id + 1) % 256
        return self._next_pkt_id

class Request(object):
    """
    Request is the single request to the remote device. Requests can be queued and sent.
    Request can check any packet to detect whether it is a valid response.
    Request.primary_key is a unique identifier of the request. Several requests with same primary key
    may be joined by the system and requested once.
    """
    def __init__(self, host=None):
        self._waiters = []
        self.failures = 0
        self.host = host

    def data(self):
        "Returns request data to be sent"
        return []

    def valid_response(self, data):
        "Checks whether this data is a valid response for the request"
        return False

    def send(self, host):
        "Send request to the host. Some requests implement specific sending protocols"
        host.send(self.data())

    def response(self, timeout=-1):
        """
        Wait for response and return it.
        timeout: -1: retry infinitely, 0: one attempt (raise exception if any), >0: timeout in seconds
        """
        channel = Channel()
        if timeout == 0:
            self._waiters.append((channel, True))
            return channel.receive()
        else:
            self._waiters.append((channel, False))
            return channel.receive(timeout)

    def deliver_response(self, response):
        "This method sends response to all waiting channels"
        waiters = self._waiters
        self._waiters = []
        for channel, onetime in waiters:
            if channel.has_receiver():
                channel.send(response)

    def deliver_exception(self, exc, *args, **kwargs):
        "This method sends exception to all waiting channels"
        waiters = self._waiters
        self._waiters = []
        for channel, onetime in waiters:
            if channel.has_receiver():
                channel.send_exception(exc, *args, **kwargs)

    def deliver_onetime_exception(self, exc, *args, **kwargs):
        """
        This method sends exception to waiting channels created with timeout=0,
        i.e. channels waiting any response after the first request
        """
        waiters = self._waiters
        self._waiters = [(channel, onetime) for channel, onetime in self._waiters if not onetime]
        for channel, onetime in waiters:
            if onetime and channel.has_receiver():
                channel.send_exception(exc, *args, **kwargs)

    def any_waiters(self):
        "Returns True when any waiters are waiting for response. False otherwise"
        return True if self._waiters else False

class RequestQueue(object):
    """
    This class represents abstract request queue. It has two basic operations -
    adding request to the queue and retrieving request to be sent just now.
    Different implementation may perform different algorithms of determining a
    the to be sent first.
    """
    def __init__(self):
        self._wait = Channel()

    def add(self, request):
        "Add request to the queue"
        if self._wait.has_receiver():
            self._wait.send(request)
        else:
            self.queue_add(request)

    def retrieve(self):
        "Retrieve request to be sent. If no requests in the queue sleep until request arrives"
        request = self.queue_retrieve()
        if request is None:
            request = self._wait.receive()
        return request

    def find(self, primary_key):
        "Find request in the internal queue by its primary key"

    def queue_add(self, request):
        "Add request to the internal queue"

    def queue_retrieve(self, request):
        "Retrieve request from the internal queue. If no request in the internal queue return None"

class FIFORequestQueue(RequestQueue):
    "This queue retrieves requests in order of adding"
    def __init__(self):
        RequestQueue.__init__(self)
        self._fifo = []

    def queue_add(self, request):
        self._fifo.append(request)

    def queue_retrieve(self):
        if not self._fifo:
            return None
        return self._fifo.pop(0)

    def find(self, primary_key):
        for req in self._fifo:
            if getattr(req, "primary_key", None) == primary_key:
                return req

class Dispatcher(object):
    "Dispatcher implements requests machinery"
    def __init__(self, queue=None):
        self.hosts = []
        self.queue = queue or FIFORequestQueue()
        self.sent_request = None
        self.subscribers = []

    def add_host(self, host):
        "Add a host to the dispatcher. Host is a Host instance"
        self.hosts.append(host)

    def request(self, request, timeout=-1):
        """
        Performs request. Response data is returned to the caller.
        TimeoutError raised when no valid response received.
        """
        def run():
            primary_key = getattr(request, "primary_key", None)
            if primary_key:
                existing_request = self.queue.find(primary_key)
                if existing_request:
                    return existing_request.response(timeout)
            self.queue.add(request)
            return request.response(timeout)
        lock = getattr(request, "lock", None)
        if lock:
            with lock:
                return run()
        else:
            return run()

    def loop(self):
        "Infinitely reads input queue, performs requests and returns responses"
        host_tasks = []
        for host in self.hosts:
            # Run loop
            task = Tasklet.new(host.loop)
            host_tasks.append(task)
            task()
            task = Tasklet.new(host.ping)
            host_tasks.append(task)
            task()
        try:
            while True:
                try:
                    # Fetch and send requests infinitely
                    request = self.queue.retrieve()
                    # Make routing decision
                    host = self.route(request)
                    if host is None:
                        # No route to send this packet
                        request.deliver_exception(DestinationUnreachable)
                    else:
                        # Creating "callback" channel
                        channel = Channel()
                        self.sent_request = (request, channel)
                        try:
                            # Sending request
                            request.send(host)
                            try:
                                # Waiting for response
                                response = channel.receive(2)
                            except TimeoutError:
                                request.deliver_onetime_exception(TimeoutError)
                                if request.any_waiters():
                                    request.failures += 1
                                    self.queue.add(request)
                            except DeviceUnreachable as e:
                                if e.reason == 2:
                                    # reason=2 means we received unexpected packet from another host
                                    # occasionally. In this case even onetime requests are performed again
                                    self.queue.add(request)
                                else:
                                    request.failures += 1
                                    args = e.args
                                    request.deliver_onetime_exception(e.__class__, *args)
                                    if request.any_waiters():
                                        self.queue.add(request)
                            except CommunicationError as e:
                                # Dispatcher loop received unexpected exception"
                                args = e.args
                                request.deliver_exception(e.__class__, *args)
                            else:
                                # Dispatcher loop received valid response. Delivering it to all waiters
                                request.deliver_response(response)
                        finally:
                            self.sent_request = False
                except Exception as e:
                    logging.exception(e)
        finally:
            for task in host_tasks:
                task.kill()

    def route(self, request):
        """
        This method decides what host to send the request to.
        Return None if nowhere to send
        """
        if request.host:
            return request.host
        if self.hosts:
            return self.hosts[0]

    def receive(self, data):
        "This message notifies dispatcher about packet received"
        if self.sent_request:
            # If dispatcher loop is waiting for the packet.
            # Try to determine whether response is related to the request being sent recently
            request, channel = self.sent_request
            try:
                # Calling validator
                validateResult = request.valid_response(data)
            except CommunicationError as e:
                # Validator raised exception
                if channel.has_receiver():
                    # Passing it to the dispatcher loop
                    args = e.args
                    channel.send_exception(e.__class__, *args)
            else:
                # If we received valid request and dispatcher loop is still waiting
                # deliver data into the loop
                if validateResult is not None and channel.has_receiver():
                    channel.send(validateResult)
        # Notify all subscribers about new event
        self.send_event({
            "type": "recv",
            "data": data
        })

    def subscribe(self, conditions, handler):
        self.subscribers.append({
            "conditions": conditions,
            "handler": handler
        })

    def send_event(self, event):
        for sub in self.subscribers:
            match = True
            for key, val in sub["conditions"].items():
                if event.get("key") != val:
                    match = False
                    break
            if match:
                sub["handler"](event)

class HostVersionRequest(Request):
    "Request to check host availability"
    def data(self):
        return ['E']

    def valid_response(self, data):
        if len(data) == 2 and data[0] == ord('E'):
            return data[1]

class BaudRateCalibrationRequest(Request):
    "Calibrate frequency generator on the host to match server baud rate"
    def data(self):
        return [0xf0]

    def valid_response(self, data):
        if len(data) == 4 and data[0] == 0xf0:
            if data[1] == 0:
                return data[2:]
            else:
                return []

    def send(self, host):
        Request.send(self, host)
        host.flush()
        Tasklet.sleep(0.005)
        host.send_raw([0x55])

class EventReceiver(object):
    def __init__(self, recipient):
        self.recipient = recipient

    def __call__(self, event):
        method_name = "event_%s" % event["type"]
        method = getattr(self.recipient, method_name, None)
        if method:
            method(event)

