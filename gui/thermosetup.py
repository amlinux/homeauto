#!/usr/bin/python2.6

import hwgui
from hwserver.config import conf, confInt
from Tkinter import *
import hwserver.hwclient
import concurrence
import logging
import time
import os
import tkFont

class Application(hwgui.Application):
    def __init__(self, master=None):
        self.sensors = {}
        self.lastSensorN = 0
        hwgui.Application.__init__(self, master)
        self.master.title("Thermometers setup")

    def loadSensors(self):
        try:
            with open("sensors.txt", "r") as f:
                for line in f:
                    tokens = line.strip().split("\t")
                    self.addSensor(tokens[0], int(tokens[1]), tokens[2])
        except IOError:
            pass

    def addSensor(self, sensorId, line, name):
        listBox = self.listBox[line]
        name = StringVar(listBox, value=name)
        temperature = StringVar(listBox)
        self.lastSensorN += 1
        self.sensors[sensorId] = {
            "n": self.lastSensorN,
            "id": sensorId,
            "line": line,
            "name": name,
            "temperature": temperature
        }
        listBox.configure(state=NORMAL)
        startIndex = listBox.index(CURRENT)
        listBox.insert(END, "%s " % sensorId)
        el = Entry(listBox, textvariable=name, font=self.font, width=30)
        listBox.window_create(END, window=el)
        listBox.insert(END, " ")
        def delSensor():
            self.delSensor(sensorId)
        el = Button(listBox, text="X", command=delSensor, font=self.font, takefocus=0)
        listBox.window_create(END, window=el)
        listBox.insert(END, " ")
        el = Label(listBox, textvariable=temperature, font=self.font)
        listBox.window_create(END, window=el)
        listBox.insert(END, "\n")
        endIndex = listBox.index(CURRENT)
        listBox.tag_add("%s.%s" % (sensorId, self.lastSensorN), startIndex, endIndex)
        listBox.configure(state=DISABLED)

    def delSensor(self, sensorId):
        if sensorId in self.sensors:
            sensorInfo = self.sensors[sensorId]
            del self.sensors[sensorId]
            self.listBox[sensorInfo["line"]].tag_config("%s.%s" % (sensorId, sensorInfo["n"]), background="red")

    def saveSensors(self):
        sensors = self.sensors.items()
        sensors.sort(cmp=lambda x, y: cmp(x[1]["n"], y[1]["n"]))
        with open("sensors.txt", "w") as f:
            for sensorId, sensorInfo in sensors:
                name = sensorInfo["name"].get()
                if type(name) == unicode:
                    name = name.encode("utf-8")
                f.write("%s\t%d\t%s\n" % (sensorId, sensorInfo["line"], name))

    def createWidgets(self):
        self.font = tkFont.Font(self, family="courier", size=8)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.listsFrame = Frame(self, takefocus=0)
        self.listsFrame.grid(row=0, column=0, sticky=N+S+E+W)
        self.listsFrame.rowconfigure(0, weight=1)

        self.listBox = []
        for i in xrange(0, 3):
            fr = Frame(self.listsFrame,
                padx=10,
                pady=10,
                takefocus=0
            )
            self.listsFrame.rowconfigure(i, weight=1)
            fr.grid(row=i, column=0, sticky=N+S+E+W)
            scroll = Scrollbar(fr, orient=VERTICAL, takefocus=0)
            scroll.grid(row=0, column=1, sticky=N+S)
            box = Text(fr,
                width=80,
                height=8,
                yscrollcommand=scroll.set,
                padx=10,
                pady=10,
                font=self.font,
                spacing1=2,
                spacing3=2,
                state=DISABLED,
                takefocus=0
            )
            scroll["command"] = box.yview
            box.grid(row=0, column=0, sticky=N+S+E+W)
            fr.rowconfigure(0, weight=1)
            fr.columnconfigure(0, weight=1)
            self.listBox.append(box)

        self.bottomFrame = Frame(self,
            padx=10,
            pady=10
        )
        self.bottomFrame.grid(row=1, column=0, sticky=N+S+E+W)

        self.quitButton = Button(self.bottomFrame, text="Quit", command=self.quit, takefocus=0)
        self.quitButton.pack({"side": "right"})

        self.saveButton = Button(self.bottomFrame, text="Save", command=self.saveSensors, takefocus=1)
        self.saveButton.pack({"side": "right", "padx": 10})

        self.loadSensors()

def monitorHw(app):
    while True:
        try:
            now = time.time()
            added = False
            okSensors = set()
            for sensorId, sensorInfo in hwserver.hwclient.thermometers().iteritems():
                if sensorInfo["timestamp"] < now - 15:
                    continue
                if sensorId not in app.sensors:
                    app.addSensor(sensorId, sensorInfo["line"], sensorId)
                    app.listBox[sensorInfo["line"]].yview_moveto(1)
                    added = True
                app.sensors[sensorId]["temperature"].set(u"%.1f\u2103" % sensorInfo["temp"])
                okSensors.add(sensorId)
            if added:
                app.saveSensors()
            deleted = False
            for sensorId, sensorInfo in app.sensors.iteritems():
                if sensorId not in okSensors:
                    deleted = True
            if added:
                os.system("mplayer -really-quiet newdevice.mp3 &")
            elif deleted:
                os.system("mplayer -really-quiet alarm.mp3 &")
            else:
                os.system("mplayer -really-quiet ok.ogg &")
            concurrence.Tasklet.sleep(5)
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
