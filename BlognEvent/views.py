from django.shortcuts import render,redirect, get_object_or_404
from BlognEvent.models import Event,Blogs
from BlognEvent.forms import EventForm,BlogsForm
from django.http import HttpResponse
from django.core import serializers
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import datetime

# Create your views here.
def create_event(request):
    form = EventForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        event_entry = form.save(commit = False)
        event_entry.user = request.user
        event_entry.save()
        return redirect('BlogNEvent:blogevent_page')

