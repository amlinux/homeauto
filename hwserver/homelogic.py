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
        dispatcher.subscribe({}, self.logic)

    def event_recv(self, event):
        print "Received packet: %s" % event
