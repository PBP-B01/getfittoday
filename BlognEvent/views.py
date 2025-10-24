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
from django.http import JsonResponse
import datetime
import json
import uuid

# blogevent page
def blogevent_page(request):
    events = Event.objects.all().order_by('-starting_date')
    blogs = Blogs.objects.all().order_by('-id')
    
    context = {
        'events': events,
        'blogs': blogs,
    }
    return render(request, 'blogevent/blogevent_page.html', context)

# event form 
@login_required
def event_form_page(request):
    form = EventForm()
    fitness_spots = FitnessSpot.objects.all()
    
    #lokasi + info
    locations_for_map = []
    for spot in fitness_spots:
        locations_for_map.append({
            'id': str(spot.place_id),
            'name': spot.name,
            'address': spot.address,
            'latitude': str(spot.latitude),   #
            'longitude': str(spot.longitude), 
        })
    
    context = {
        'form': form,
        'locations': fitness_spots,
        'locations_json': json.dumps(locations_for_map),
    }
    return render(request, 'blogevent/event_form.html', context)

# create event
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
            
            return redirect('BlogNEvent:blogevent_page')
    
    return redirect('BlogNEvent:event_form_page')

# blog form 
@login_required
def blog_form_page(request):
    form = BlogsForm()
    context = {
        'form': form,
    }
    return render(request, 'blogevent/blog_form.html', context)

# Cceate blog
@login_required
def create_blog(request):
    if request.method == "POST":
        form = BlogsForm(request.POST)
        if form.is_valid():
            blog_entry = form.save(commit=False)
            blog_entry.author = request.user
            blog_entry.save()
            return redirect('BlogNEvent:blogevent_page')
    
    return redirect('BlogNEvent:blog_form_page')


def event_detail_api(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    locations = [loc.name for loc in event.locations.all()]
    
    return JsonResponse({
        'name': event.name,
        'image': event.image,
        'description': event.description,
        'starting_date': event.starting_date.strftime('%B %d, %Y'),
        'ending_date': event.ending_date.strftime('%B %d, %Y'),
        'user': event.user.username,
        'locations': locations,
    })


def blog_detail_api(request, blog_id):
    blog = get_object_or_404(Blogs, id=blog_id)
    
    return JsonResponse({
        'title': blog.title,
        'image': blog.image,
        'body': blog.body,
        'author': blog.author.username,
    })