from django.utils.functional import SimpleLazyObject

class SimpleLazyList(SimpleLazyObject):
    def __len__(self):
        if self._wrapped is None: self._setup()
        return len(self._wrapped)

    def __iter__(self):
        if self._wrapped is None: self._setup()
        return iter(self._wrapped)

def menu(request):
    def topmenu():
        print "called topmenu"
        return [
            {
                "href": "/",
                "title": "Test",
            }
        ]

    return {
        "topmenu": SimpleLazyList(topmenu)
    }

