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
        self.dispatcher.relay_clear_all()
        self.dispatcher.subscribe({}, self.logic)

    def event_recv(self, event):
        print event
        data = event["data"]
        cmd = data.pop(0)
        if cmd == ord('B'):
            btnCmd = data.pop(0)
            if btnCmd == 1:
                btn = data.pop(0)
                print "Pressed button %d" % btn
                relay = btn + 1
                newState = not self.relayState.get(relay)
                self.relayState[relay] = newState
                self.dispatcher.relay_set(relay, newState)
            elif btnCmd == 0:
                btn = data.pop(0)
                print "Released button %d" % btn

