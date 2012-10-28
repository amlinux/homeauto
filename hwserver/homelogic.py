from hardware import EventReceiver

class HomeLogic(object):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.relayState = {}
        self.btnLongPress = {}
        self.relay_clear_all()
        self.dispatcher.subscribe({}, EventReceiver(self))

    def relay_set(self, relay, state):
        if self.relayState[relay] != state:
            self.relayState[relay] = state
            self.dispatcher.relay_set(relay, state)
            self.dispatcher.send_event({
                "type": "relay"
            })

    def relay_set_all(self, value=True):
        changed = False
        for relay in xrange(1, 31):
            if self.relayState.get(relay, None) != value:
                changed = True
                self.relayState[relay] = value
        if not changed:
            return
        if value:
            self.dispatcher.relay_set_all()
        else:
            self.dispatcher.relay_clear_all()
        self.dispatcher.send_event({
            "type": "relay"
        })

    def relay_clear_all(self):
        self.relay_set_all(False)

    def event_recv(self, event):
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
                if btn == 27:
                    return
                self.btnLongPress[btn] = False
                relay = btn + 1
                newState = not self.relayState.get(relay)
                self.relay_set(relay, newState)
            elif btnCmd == 2:
                btn = data.pop(0)
                duration = data.pop(0)
                print "Button %d was pressed for %d sec" % (btn, duration)
                if btn == 27:
                    return
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

