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
        menu = []
        menu.append({"href": "/", "title": _("Overview")})
        if request.user.has_perm("hwdebug.demo"):
            menu.append({"href": "/hwdebug/demo/", "title": _("Demo")})
        if request.user.has_perm("is_staff"):
            menu.append({"href": "/admin/", "title": _("Admin")})
        menu.append({"href": "/homeauto/logout/", "title": _("Logout")})
        return menu
    if request.user.is_authenticated():
        return {
            "topmenu": SimpleLazyList(topmenu)
        }
    else:
        return {}
