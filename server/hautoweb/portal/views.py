from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

@login_required
def overview(request):
    return render_to_response(
        "homeauto/overview.html", {
    }, context_instance=RequestContext(request))
