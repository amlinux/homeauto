import re
import json as json_module

class BadRequestError(Exception):
    def __init__(self, msg):
        self.msg = msg

class HardwareAPIServer(object):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.routes = [
            (re.compile('/$'), self.index),
            (re.compile('/relay/(on|off)/(\d+)$'), self.relay_onoff),
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
        return ['Homeauto API<br />%s' % environ]

    def not_found(self, environ, start_response):
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return ['<html><body><h1>404 Not Found</h1></body></html>']

    def json(self, start_response, obj):
        data = json_module.dumps(obj).encode('utf-8')
        start_response('200 OK', [
            ('Content-type', 'application/json'),
            ('Content-length', len(data))
        ])
        return [data]

    def relay_onoff(self, environ, start_response, cmd, num):
        num = int(num)
        if num < 1 or num > 30:
            raise BadRequestError("Relay number must be in range 1-30")
        self.dispatcher.relay_set(num, True if cmd == "on" else False)
        return self.json(start_response, {"relay": num, "state": cmd})
