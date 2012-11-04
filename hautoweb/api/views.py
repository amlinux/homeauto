from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from hautoweb.l10n import _
from hwserver.config import conf, confInt
import json

@csrf_exempt
def loginView(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    if username is not None and password is not None:
        user = authenticate(username=username, password=password)
    else:
        user = None
    if user is not None:
        if user.is_active:
            login(request, user)
            request.session["api"] = True
            response_data = {
                "ok": "1"
            }
        else:
            response_data = {
                "err": "authfailed",
                "msg": _("Access denied")
            }
    else:
        response_data = {
            "err": "authfailed",
            "msg": _("Access denied")
        }
    return HttpResponse(json.dumps(response_data), mimetype="application/json")

@csrf_exempt
def monitor(request):
    if request.user.has_perm("api.monitor"):
        addr = conf("hwserver", "addr", "127.0.0.1")
        port = confInt("hwserver", "port", 8081)
        response_data = {
            "addr": addr,
            "port": port
        }
        # TODO: connect to backend
    else:
        response_data = {
            "err": "authfailed",
            "msg": "Not authorized"
        }
    return HttpResponse(json.dumps(response_data), mimetype="application/json")
