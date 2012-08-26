from django.http import HttpResponse
from concurrence import Tasklet

def index(request):
    return HttpResponse("Hello, world. You're at the poll index.")
