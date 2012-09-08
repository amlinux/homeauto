import os
from concurrence.io import Socket

class FileSocket(object):
    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.family = None

    def __getattr__(self, attr):
        return getattr(self.fileobj, attr)

    def setblocking(self, mode):
        pass

class FDStream(Socket):
    def __init__(self, fd):
        Socket.__init__(self, FileSocket(os.fdopen(fd, "r+")), Socket.STATE_CONNECTED)


