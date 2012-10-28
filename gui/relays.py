#!/usr/bin/python2.6

import hwgui
import hwserver.hwclient
import concurrence
import logging
from Tkinter import *

class Application(hwgui.Application):
    def __init__(self, master=None):
        hwgui.Application.__init__(self, master)
        self.master.title("Relays diagnostics")

    def createWidgets(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        self.relaysBox = Text(self)
        self.relaysBox.grid(row=0, column=0, sticky=N+S+E+W)

        self.bottomFrame = Frame(self, padx=10, pady=10)
        self.bottomFrame.grid(row=1, column=0, sticky=N+S+E+W)

        self.quitButton = Button(self.bottomFrame)
        self.quitButton["text"] = "Quit"
        self.quitButton["command"] = self.quit
        self.quitButton.pack({"side": "right"})

        self.relayBtn = []
        self.relayState = []
        for i in xrange(1, 31):
            btn = Button(self.relaysBox)
            btn["text"] = "%02d" % i
            self.relaysBox.window_create(END, window=btn, padx=10, pady=10)
            if i % 10 == 0:
                self.relaysBox.insert(END, "\n")
            self.relayBtn.append(btn)
            self.relayState.append(None)
            btn["command"] = self.btnPressed(i)

    def btnPressed(self, btn):
        def handler():
            print "Button %d pressed" % btn
            val = self.relayState[btn - 1]
            if val is None:
                return
            val = 0 if val else 1
            print "Switching relay %d to state %d" % (btn, val)
            hwserver.hwclient.relay_set(btn, val)
        return handler

def fakeMonitor(state):
    import random
    for i in xrange(1, 31):
        state["relay%d" % i] = random.randrange(0, 2)
    return state

def monitorHw(app):
    state = {}
    while True:
        try:
            state = hwserver.hwclient.monitor(state)
            #state = fakeMonitor(state)
            for i in xrange(1, 31):
                val = state["relay%d" % i]
                if val:
                    bg = "#80ff80"
                else:
                    bg = "#ffc0c0"
                app.relayBtn[i - 1].configure(bg=bg)
                app.relayState[i - 1] = val
        except Exception as e:
            logging.exception(e)
        concurrence.Tasklet.sleep(1)

def initapp(root):
    app = Application(master=root)
    concurrence.Tasklet.new(monitorHw)(app)
    return app

hwgui.dispatch(initapp)
