#!/usr/bin/python2.6

# Project path
import sys
import re
path = re.sub(r'\/[^\/]+$', '', sys.argv[0])
sys.path.append(path)

from concurrence import dispatch, Tasklet
from concurrence.http import WSGIServer
import logging
from hardware import Dispatcher, Host, Request
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "homeauto.settings"
#import django.core.handlers.wsgi

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
            raise HardwareError("Both devices has same version %s" % ver1)
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

def main():
    try:
        dispatcher = HomeAutoDispatcher()
        Tasklet.new(dispatcher.loop)()
        dispatcher.open_ports("/dev/ttyUSB0", "/dev/ttyUSB1")

        while True:
            for i in range(1, 26):
                dispatcher.relay_set(i, True)
                Tasklet.sleep(0.1)
            for i in range(1, 26):
                dispatcher.relay_set(i, False)
                Tasklet.sleep(0.1)

        #while True:
        #    host1.send_raw([0x5a, 0x01, 0x45, 0x2d])
        #    host2.send_raw([0x5a, 0x01, 0x45, 0x2d])

        #print "Calibration relayscontrol: %s" % dispatcher.relayscontrol.calibrate_baudrate()
        #print "Calibration maincontrol: %s" % dispatcher.maincontrol.calibrate_baudrate()

        #print "Version1: %s" % host1.version()
        #print "Version2: %s" % host2.version()

#        # Running HTTP server
#        application = django.core.handlers.wsgi.WSGIHandler()
#        def app_wrapper(*args, **kwargs):
#            try:
#                return application(*args, **kwargs)
#            except Exception as e:
#                print e
#        server = WSGIServer(application)
#        server.serve(('localhost', 8080))

        while True:
            Tasklet.sleep(1)

        os._exit(0)
    except HardwareError as e:
        print e
        os._exit(1)
    except Exception as e:
        logging.exception(e)
        os._exit(1)

dispatch(main)

