#!/usr/bin/python2.6

from httplib import HTTPConnection
import json

state = {}

while True:
    url = '/monitor'
    first = True
    for key, val in state.iteritems():
        if first:
            url += '?'
            first = False
        else:
            url += '&'
        url += '%s=%s' % (key, val)
    h1 = HTTPConnection('10.90.0.245', 8081);
    req = h1.request('GET', url)
    res = h1.getresponse()
    if res.status != 200:
        print "Could not query monitor: %s %s" % (res.status, res.reason)
    else:
        state = json.loads(res.read())
        res = ''
        for i in xrange(1, 31):
            res += "%s " % (state["relay%d" % i])
        print res
