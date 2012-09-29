class EventReceiver(object):
    def __init__(self, logic):
        self.logic = logic

    def __call__(self, event):
        method_name = "event_%s" % event["type"]
        method = getattr(self.logic, method_name, None)
        if method:
            method(event)

class HomeLogic(object):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.logic = EventReceiver(self)
        self.relayState = {}
        self.btnLongPress = {}
        self.relay_clear_all()
        self.dispatcher.subscribe({}, self.logic)

    def relay_set(self, relay, state):
        self.relayState[relay] = state
        self.dispatcher.relay_set(relay, state)

    def relay_set_all(self, value=True):
        for relay in xrange(1, 31):
            self.relayState[relay] = value
        if value:
            self.dispatcher.relay_set_all()
        else:
            self.dispatcher.relay_clear_all()

    def relay_clear_all(self):
        self.relay_set_all(False)

    def event_recv(self, event):
        print event
        data = event["data"]
        cmd = data.pop(0)
        if cmd == ord('B'):
            btnCmd = data.pop(0)
            if btnCmd == 0:
                btn = data.pop(0)
                print "Released button %d" % btn
            elif btnCmd == 1:
                btn = data.pop(0)
                print "Pressed button %d" % btn
                self.btnLongPress[btn] = False
                relay = btn + 1
                newState = not self.relayState.get(relay)
                self.relay_set(relay, newState)
            elif btnCmd == 2:
                btn = data.pop(0)
                duration = data.pop(0)
                print "Button %d was pressed for %d sec" % (btn, duration)
                if duration == 3:
                    self.btnLongPress[btn] = True
                    anyOn = False
                    for relay in xrange(1, 31):
                        if relay != btn + 1 and self.relayState.get(relay):
                            anyOn = True
                            break
                    self.relay_set_all(not anyOn)
            else:
                print "Unknown button event: %s %s" % (btnCmd, data)

