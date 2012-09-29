import re
import json as json_module
import cgi

class BadRequestError(Exception):
    def __init__(self, msg):
        self.msg = msg

class HomeLogicAPIServer(object):
    def __init__(self, dispatcher, logic):
        self.dispatcher = dispatcher
        self.logic = logic
        self.routes = [
            (re.compile('/$'), self.index),
            (re.compile('/relay/(on|off)/(\d+)$'), self.relay_onoff),
            (re.compile('/monitor$'), self.monitor),
        ]

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
            start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
            return ['<html><body><h1>500 Internal Server Error</h1>%s</body></html>' % e.__class__.__name__]

    def index(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['Homeauto API']

    def not_found(self, environ, start_response):
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return ['<html><body><h1>404 Not Found</h1></body></html>']

    def json(self, start_response, obj):
        data = json_module.dumps(obj).encode('utf-8')
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
        self.dispatcher.relay_set(num, True if cmd == "on" else False)
        return self.json(start_response, {"relay": num, "state": cmd})

    def load_params(self, environ):
        if "params" in environ:
            return
        fs = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=1)
        params = {}
        params_detail = {}
        if fs.list:
            for key in self.fs.keys():
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

    def monitor(self, environ, start_response):
        response = {}
        for relay in xrange(1, 31):
            actualState = 1 if self.logic.relayState.get(relay) else 0
            response["relay%d" % relay] = actualState
            recvState = self.param(environ, "relay%d" % relay)
            try:
                recvState = int(recvState)
            except Exception:
                recvState = None
        return self.json(start_response, response)
