from django.utils.functional import SimpleLazyObject
from l10n import _

class SimpleLazyList(SimpleLazyObject):
    def __len__(self):
        if self._wrapped is None: self._setup()
        return len(self._wrapped)

    def __iter__(self):
        if self._wrapped is None: self._setup()
        return iter(self._wrapped)

def menu(request):
    def topmenu():
        return [
            {
                "href": "/",
                "title": _("mainpage///Main"),
            },
            {
                "href": "/homeauto/logout/",
                "title": _("Log out")
            }
        ]
    if request.user.is_authenticated():
        return {
            "topmenu": SimpleLazyList(topmenu)
        }
    else:
        return {}
