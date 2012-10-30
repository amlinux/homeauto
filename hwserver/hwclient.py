from concurrence.http import HTTPConnection
from config import conf, confInt
import json

hwserver = conf("hwserver", "addr")
hwport = confInt("hwserver", "port")

def relay_set(relay, val):
    # query hwserver
    cnn = HTTPConnection()
    addr = (hwserver, hwport)
    cnn.connect(addr)
    req = cnn.get(str("/relay/%s/%d" % ("on" if val else "off", relay)))
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    req.add_header("Connection", "close")
    res = cnn.perform(req)
    if res.status_code != 200:
        print "Could not query relay: error %s" % res.status_code

def monitor(state):
    # prepare url
    url = '/monitor'
    first = True
    for key, val in state.iteritems():
        if first:
            url += '?'
            first = False
        else:
            url += '&'
        url += '%s=%s' % (key, val)
    # query hwserver
    cnn = HTTPConnection()
    addr = (hwserver, hwport)
    cnn.connect(addr)
    req = cnn.get(str(url))
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    req.add_header("Connection", "close")
    res = cnn.perform(req)
    if res.status_code != 200:
        raise RuntimeError("Could not query monitor: error %s" % res.status_code)
    return json.loads(res.body)

def thermometers():
    cnn = HTTPConnection()
    addr = (hwserver, hwport)
    cnn.connect(addr)
    req = cnn.get("/temperature")
    req.add_header("Connection", "close")
    res = cnn.perform(req)
    if res.status_code != 200:
        raise RuntimeError("Could not query thermometers state: error %s" % res.status_code)
    return json.loads(res.body)
