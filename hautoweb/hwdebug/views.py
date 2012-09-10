from django.contrib.auth.decorators import permission_required
from django.shortcuts import render_to_response
from django.template import RequestContext

@permission_required('hwdebug.demo')
def demo(request):
    return render_to_response(
        "hwdebug/demo.html", {
    }, context_instance=RequestContext(request))
