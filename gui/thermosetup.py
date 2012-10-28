#!/usr/bin/python2.6

import hwgui
from hwserver.config import conf, confInt
from Tkinter import *
import hwserver.hwclient
import concurrence
import logging
import random

class Application(hwgui.Application):
    def __init__(self, master=None):
        hwgui.Application.__init__(self, master)
        self.master.title("Thermometers setup")

    def createWidgets(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.listsFrame = Frame(self)
        self.listsFrame.grid(row=0, column=0, sticky=N+S+E+W)
        self.listsFrame.rowconfigure(0, weight=1)

        self.listBox = []
        for i in xrange(0, 3):
            fr = Frame(self.listsFrame,
                padx=10,
                pady=10
            )
            self.listsFrame.columnconfigure(i, weight=1)
            fr.grid(row=0, column=i, sticky=N+S+E+W)
            scroll = Scrollbar(fr, orient=VERTICAL)
            scroll.grid(row=0, column=1, sticky=N+S)
            box = Text(fr,
                width=30,
                height=20,
                yscrollcommand=scroll.set
            )
            scroll["command"] = box.yview
            box.grid(row=0, column=0, sticky=N+S+E+W)
            fr.rowconfigure(0, weight=1)
            fr.columnconfigure(0, weight=1)
            # Test data
            box.insert(END, "One\n")
            box.insert(END, "Two\n")
            box.insert(END, "Three ")
            el = Button(box)
            el["text"] = "test"
            win = box.window_create(END, window=el)
            self.listBox.append(box)

        self.bottomFrame = Frame(self,
            padx=10,
            pady=10
        )
        self.bottomFrame.grid(row=1, column=0, sticky=N+S+E+W)

        self.quitButton = Button(self.bottomFrame)
        self.quitButton["text"] = "Quit"
        self.quitButton["command"] =  self.quit
        self.quitButton.pack({"side": "right"})

def monitorHw(app):
    while True:
        try:
            app.listBox[0].insert(END, "%s\n" % random.randrange(1, 100))
        except Exception as e:
            logging.exception(e)
        concurrence.Tasklet.sleep(1)

def initapp(root):
    hwserver = conf("hwserver", "addr")
    hwport = confInt("hwserver", "port")
    print "Hardware server %s:%s" % (hwserver, hwport)
    app = Application(master=root)
    concurrence.Tasklet.new(monitorHw)(app)
    return app

hwgui.dispatch(initapp)
