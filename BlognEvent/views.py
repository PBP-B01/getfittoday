from django.shortcuts import render, redirect, get_object_or_404
from BlognEvent.models import Event, Blogs
from BlognEvent.forms import EventForm, BlogsForm
from home.models import FitnessSpot
from django.http import HttpResponse
from django.core import serializers
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import datetime
import json

# Display page for both blogs and events
def blogevent_page(request):
    events = Event.objects.all().order_by('-starting_date')
    blogs = Blogs.objects.all().order_by('-id')
    
    context = {
        'events': events,
        'blogs': blogs,
    }
    return render(request, 'blogevent/blogevent_page.html', context)

# Event form page with Google Maps
@login_required
def event_form_page(request):
    form = EventForm()
    fitness_spots = FitnessSpot.objects.all()
    
    # Prepare location data for Google Maps
    locations_for_map = []
    for spot in fitness_spots:
        locations_for_map.append({
            'id': str(spot.place_id),
            'name': spot.name,
            'address': spot.address,
        })
    
    context = {
        'form': form,
        'locations': fitness_spots,
        'locations_json': json.dumps(locations_for_map),
    }
    return render(request, 'blogevent/event_form.html', context)

# Create event
@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event_entry = form.save(commit=False)
            event_entry.user = request.user
            event_entry.save()
            
            # Handle multiple location selections
            location_ids = request.POST.getlist('locations')
            if location_ids:
                event_entry.locations.set(location_ids)
            
            return redirect('BlognEvent:blogevent_page')
    
    return redirect('BlognEvent:event_form_page')

# Blog form page
@login_required
def blog_form_page(request):
    form = BlogsForm()
    context = {
        'form': form,
    }
    return render(request, 'blogevent/blog_form.html', context)

# Create blog
@login_required
def create_blog(request):
    if request.method == "POST":
        form = BlogsForm(request.POST)
        if form.is_valid():
            blog_entry = form.save(commit=False)
            blog_entry.author = request.user
            blog_entry.save()
            return redirect('BlognEvent:blogevent_page')
    
    return redirect('BlognEvent:blog_form_page')