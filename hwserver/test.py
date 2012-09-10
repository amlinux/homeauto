#!/usr/bin/python2.6

import sys
import re
import os
path = os.path.abspath(re.sub(r'\/[^\/]+$', '', sys.argv[0]))
sys.path.append(path)

from concurrence import dispatch, Tasklet
from hardware import Dispatcher, Host

def main():
    disp = Dispatcher()
    Tasklet.new(disp.loop)()
    host = Host(disp, "/dev/ttySP1")
    disp.add_host(host)
    while True:
        host.send([0x45])

dispatch(main)
