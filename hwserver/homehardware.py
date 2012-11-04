from hardware import Dispatcher, Host, Request, Lock, ResponseError
import time

tempCache = {}

class HardwareError(Exception):
    pass

class HomeAutoDispatcher(Dispatcher):
    def __init__(self):
        Dispatcher.__init__(self)
        self.relays = [0, 0, 0, 0]

    def open_ports(self, port1, port2):
        host1 = Host(self, port1)
        host2 = Host(self, port2)
        self.add_host(host1)
        self.add_host(host2)
        ver1 = host1.version()
        if ver1 is None:
            raise HardwareError("No response on %s" % port1)
        ver2 = host2.version()
        if ver2 is None:
            raise HardwareError("No response on %s" % port2)
        if ver1 != 1 and ver1 != 2:
            raise HardwareError("Unknown device version %s" % ver1)
        if ver2 != 1 and ver2 != 2:
            raise HardwareError("Unknown device version %s" % ver2)
        if ver1 == ver2:
            raise HardwareError("Both devices have the same version %s" % ver1)
        if ver1 == 1:
            self.relayscontrol = host1
            self.maincontrol = host2
        else:
            self.maincontrol = host1
            self.relayscontrol = host2

    def route(self, request):
        hint = getattr(request, "routeHint", None)
        if hint == "relays":
            return self.relayscontrol
        elif hint == "main":
            return self.maincontrol
        else:
            return Dispatcher.route(self, request)

    def relay_set(self, relay, state):
        if relay < 1 or relay > 30:
            return
        relay -= 1
        index = relay / 8
        mask = 1 << (relay & 7)
        if state:
            self.relays[index] |= mask
        else:
            self.relays[index] &= ~mask
        self.request(RelaySetRequest(self.relays), timeout=1)

    def relay_set_all(self):
        self.relays[0] = 0xff
        self.relays[1] = 0xff
        self.relays[2] = 0xff
        self.relays[3] = 0xff
        self.request(RelaySetRequest(self.relays), timeout=1)

    def relay_clear_all(self):
        self.relays[0] = 0
        self.relays[1] = 0
        self.relays[2] = 0
        self.relays[3] = 0
        self.request(RelaySetRequest(self.relays), timeout=1)

class RelaySetRequest(Request):
    "Request relay switching"
    def __init__(self, relays):
        Request.__init__(self)
        self.relays = relays
        self.routeHint = "relays"
        self.primary_key = "relayset"

    def data(self):
        return ['R'] + self.relays

    def valid_response(self, data):
        if len(data) == 1 and data[0] == ord('R'):
            return True

class MicroLANError(ResponseError):
    pass

class MicroLANInvalidCommand(MicroLANError):
    pass

class MicroLANInvalidLine(MicroLANError):
    pass

class MicroLANReadError(MicroLANError):
    pass

class MicroLANNoPresence(MicroLANError):
    pass

class MicroLANCRCError(MicroLANError):
    pass

class MicroLANSearchError(MicroLANError):
    pass

class MicroLANNoDevices(MicroLANError):
    pass

class MicroLANListError(MicroLANError):
    pass

class MicroLANTemperatureError(MicroLANError):
    pass

class MicroLANRequest(Request):
    """
    MicroLAN request is a query to one of MicroLAN lines of the 
    main controller. All such requests must be serialized
    """
    lock = Lock()

    def __init__(self, line):
        Request.__init__(self)
        self.line = line
        self.routeHint = "main"

    def valid_response(self, data):
        if len(data) >= 2 and data[0] == ord('M'):
            if data[1] == 0xff:
                raise MicroLANInvalidCommand()
            elif data[1] == 0xfe:
                raise MicroLANInvalidLine()
            elif data[1] == 0xfd:
                raise MicroLANReadError()
            elif data[1] == 0xfc:
                raise MicroLANNoPresence()
            elif data[1] == 0xfb:
                raise MicroLANCRCError()
            elif data[1] == 0xfa:
                raise MicroLANSearchError()
            elif data[1] == 0xf9:
                raise MicroLANNoDevices()
            elif data[1] == 0:
                return data[2:]
            else:
                raise MicroLANError()

class MicroLANReadROM(MicroLANRequest):
    def data(self):
        return ['M', 1, self.line]

class MicroLANSearchROM(MicroLANRequest):
    def __init__(self, line, prefixlen, prefixbuf):
        MicroLANRequest.__init__(self, line)
        self.prefixlen = prefixlen
        self.prefixbuf = prefixbuf

    def data(self):
        return ['M', 2] + [self.line, self.prefixlen] + self.prefixbuf

class MicroLANListAll(object):
    def __init__(self, dispatcher, line):
        self.dispatcher = dispatcher
        self.line = line

    def execute(self):
        try:
            return self._withprefix(0, [0, 0, 0, 0, 0, 0, 0, 0])
        except MicroLANNoPresence:
            return []

    def _withprefix(self, prefix, buf):
        try:
            buf = self.dispatcher.request(MicroLANSearchROM(self.line, prefix, buf))
        except MicroLANError as e:
            print "Microlan strange behaviour. line=%s, prefix=%s, buf=%s, response: %s" % (self.line, prefix, buf, e.__class__.__name__)
            return []
        bits = buf[0]
        buf = buf[1:]
        if bits == 64:
            return [buf]
        elif bits > 64:
            raise MicroLANListError()
        else:
            buf[bits / 8] &= ~(1 << (bits & 7))
            sublist1 = self._withprefix(bits + 1, buf)
            buf[bits / 8] |= (1 << (bits & 7))
            sublist2 = self._withprefix(bits + 1, buf)
            return sublist1 + sublist2

class MicroLANConvertTemperature(MicroLANRequest):
    def data(self):
        return ['M', 3, self.line]

class MicroLANReadTemperature(MicroLANRequest):
    def __init__(self, line, dev):
        MicroLANRequest.__init__(self, line)
        self.dev = dev

    def data(self):
        return ['M', 4, self.line] + self.dev

    def valid_response(self, data):
        res = MicroLANRequest.valid_response(self, data)
        if res is not None:
            if len(res) != 2:
                raise MicroLanTemperatureError()
            temp = res[1] * 256 + res[0]
            if temp & 0x8000:
                temp -= 0x10000
            temp = temp / 16.0
            tempCache['-'.join(["%02x" % d for d in self.dev])] = {
                "temp": temp,
                "timestamp": time.time(),
                "line": self.line,
            }
            return temp

