import sys
import re
import os

path = re.sub(r'/[^/]+/[^/]+$', '', os.path.abspath(sys.argv[0]))
sys.path.append(path)

import concurrence
import logging
from Tkinter import *

class Application(Frame):
    def createWidgets(self):
        pass

    def __init__(self, master=None):
        Frame.__init__(self, master)
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky=N+S+E+W)
        self.createWidgets()
        self.bind_all("<Escape>", lambda ev: self.quit())

def idle(root, app):
    concurrence.Tasklet.yield_()
    root.after(1, lambda: idle(root, app))

def main(initapp):
    try:
        root = Tk()
        app = initapp(root)
        root.after(1, lambda: idle(root, app))
        app.mainloop()
        try:
            root.destroy()
        except TclError:
            pass
    except Exception as e:
        logging.exception(e)
    finally:
        os._exit(0)

def dispatch(initapp):
    concurrence.dispatch(lambda: main(initapp))
