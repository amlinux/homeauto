from hardware import Dispatcher, Host, Request

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

    def relay_set_all(self):
        self.relays[0] = 0xff
        self.relays[1] = 0xff
        self.relays[2] = 0xff
        self.relays[3] = 0xff
        self.request(RelaySetRequest(self.relays), timeout=1)

    def relay_clear_all(self):
        self.relays[0] = 0
        self.relays[1] = 0
        self.relays[2] = 0
        self.relays[3] = 0
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


