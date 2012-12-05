import re
import json as json_module
import cgi
import logging
import homehardware
from concurrence import Channel, TimeoutError, Tasklet
from hardware import EventReceiver

class BadRequestError(Exception):
    def __init__(self, msg):
        self.msg = msg

class MlanSearch(object):
    def __init__(self):
        self.tasklet = None

    def search(self, line):
        if self.tasklet is None:
            self.reqchannel = Channel()
            self.queued = {}
            self.tasklet = Tasklet(self._checker)
            self.tasklet()
        ch = Channel()
        if line in self.queued:
            self.queued[line].append(ch)
        else:
            self.queued[line] = [ch]
            self.reqchannel.send(line)
        return ch.recv()

    def _checker(self):
        while True:
            line = self.reqchannel.recv()
            waiters = self.reqchannel[line]
            del self.reqchannel[line]
            for waiter in waiters:
                if waiter.has_receiver():
                    waiter.send(["abc", "def", "ghi"])

class HomeLogicAPIServer(object):
    def __init__(self, dispatcher, logic):
        self.dispatcher = dispatcher
        self.logic = logic
        self.monitor_waiters = []
        self.routes = [
            (re.compile('/$'), self.index),
            (re.compile('/relay/(on|off)/(\d+)$'), self.relay_onoff),
            (re.compile('/monitor$'), self.monitor),
            (re.compile('/mlan/search/(\d+)$'), self.mlan_search),
            (re.compile('/temperature$'), self.temperature),
        ]
        self.dispatcher.subscribe({}, EventReceiver(self))
        self.mlanSearch = MlanSearch()

    def __call__(self, environ, start_response):
        try:
            uri = environ["PATH_INFO"]
            for route in self.routes:
                m = route[0].match(uri)
                if m:
                    args = list(m.groups())
                    return route[1](environ, start_response, *args)
            return self.not_found(environ, start_response)
        except BadRequestError as e:
            start_response('400 Bad Request', [('Content-Type', 'text/html')])
            return ['<html><body><h1>400 Bad Request</h1>%s</body></html>' % e.msg]
        except Exception as e:
            logging.exception(e)
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            return ['<html><body><h1>500 Internal Server Error</h1>%s</body></html>' % e.__class__.__name__]

    def index(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['Homeauto API']

    def not_found(self, environ, start_response):
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return ['<html><body><h1>404 Not Found</h1></body></html>']

    def json(self, start_response, obj):
        data = json_module.dumps(obj, indent=4).encode('utf-8')
        start_response('200 OK', [
            ('Content-type', 'application/json'),
            ('Content-length', len(data)),
            ('Cache-control', 'no-cache')
        ])
        return [data]

    def relay_onoff(self, environ, start_response, cmd, num):
        num = int(num)
        if num < 1 or num > 30:
            raise BadRequestError("Relay number must be in range 1-30")
        self.logic.relay_set(num, True if cmd == "on" else False)
        return self.json(start_response, {"relay": num, "state": cmd})

    def mlan_search(self, environ, start_response, line):
        line = int(line)
        if line < 0 or line > 2:
            raise BadRequestError("Line number must be in range 0-2")
        return self.json(start_response, {"devices": self.mlanSearch.search(line)})

    def load_params(self, environ):
        if "params" in environ:
            return
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=1)
        params = {}
        params_detail = {}
        if fs.list:
            for key in fs.keys():
                params[key] = fs.getlist(key)
            for ent in fs.list:
                try:
                    params[ent.name].append(ent.value)
                    params_detail[ent.name].append(ent)
                except KeyError:
                    params[ent.name] = [ent.value]
                    params_detail[ent.name] = [ent]
        environ["params"] = params
        environ["params_detail"] = params_detail

    def param(self, environ, key, default=u''):
        self.load_params(environ)
        val = environ["params"].get(key)
        if val is None:
            return default
        else:
            return unicode(val[0], "utf-8")

    def monitor_state(self):
        state = {}
        for relay in xrange(1, 31):
            actualState = 1 if self.logic.relayState.get(relay) else 0
            state["relay%d" % relay] = actualState
        return state

    def monitor(self, environ, start_response):
        state = self.monitor_state()
        mismatch = False
        for relay in xrange(1, 31):
            actualState = state["relay%d" % relay]
            recvState = self.param(environ, "relay%d" % relay)
            try:
                recvState = int(recvState)
            except Exception:
                recvState = None
            if recvState != actualState:
                mismatch = True
        # If any API parameter mismatches actual value
        # Send all actual data immediately. Otherwise lock
        # request in timeout.
        if not mismatch:
            ch = Channel()
            self.monitor_waiters.append(ch)
            try:
                state = ch.receive(10)
            except TimeoutError:
                pass
        return self.json(start_response, state)

    def event_relay(self, event):
        print "Event_relay triggered"
        waiters = self.monitor_waiters
        self.monitor_waiters = []
        state = self.monitor_state()
        for ch in waiters:
            if ch.has_receiver():
                ch.send(state)

    def temperature(self, environ, start_response):
        return self.json(start_response, homehardware.tempCache)
