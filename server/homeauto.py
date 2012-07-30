#!/usr/bin/python2.6

# Project path
import sys
import re
path = re.sub(r'\/[^\/]+$', '', sys.argv[0])
sys.path.append(path)

from concurrence import dispatch, Tasklet
from concurrence.http import WSGIServer
from homehardware import HomeAutoDispatcher
import logging
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "homeauto.settings"
#import django.core.handlers.wsgi

def main():
    try:
        dispatcher = HomeAutoDispatcher()
        Tasklet.new(dispatcher.loop)()
        dispatcher.open_ports("/dev/ttyUSB0", "/dev/ttyUSB1")

        while True:
            for j in xrange(0, 3):
                for i in xrange(0, 30):
                    dispatcher.relay_set(i + 1, True)
                    dispatcher.relay_set((i + 15) % 30 + 1, False)
                    Tasklet.sleep(0.05)
            dispatcher.relay_clear_all()
            Tasklet.sleep(1)
            for i in xrange(0, 30):
                dispatcher.relay_set(i + 1, True)
                Tasklet.sleep(0.05)
            Tasklet.sleep(1)
            for i in xrange(0, 30):
                dispatcher.relay_set(i + 1, False)
                Tasklet.sleep(0.05)
            Tasklet.sleep(1)
            for j in xrange(0, 5):
                dispatcher.relay_set_all()
                Tasklet.sleep(0.3)
                dispatcher.relay_clear_all()
                Tasklet.sleep(0.3)


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

