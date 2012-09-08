import os
import termios
from concurrence.io import BufferedStream
from fdsocket import *

class SerialStream(BufferedStream):
    def __init__(self, devname):
        self.fd = fd = os.open(devname, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK | os.O_EXCL)
        attr = termios.tcgetattr(fd)
        attr[0] = attr[0] & ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK | termios.ISTRIP | termios.INLCR | termios.IGNCR | termios.ICRNL | termios.IXON);
        attr[1] = attr[1] & ~termios.OPOST;
        attr[2] = attr[2] & ~(termios.CSIZE | termios.PARENB) | termios.CS8;
        attr[3] = attr[3] & ~(termios.ECHO | termios.ECHONL | termios.ICANON | termios.ISIG | termios.IEXTEN);
        attr[4] = attr[5] = termios.B19200
        termios.tcsetattr(fd, termios.TCSANOW, attr)
        BufferedStream.__init__(self, FDStream(fd))

    def flush(self):
        termios.tcdrain(self.fd)
