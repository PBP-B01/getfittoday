from django.shortcuts import render, redirect, get_object_or_404
from BlognEvent.models import Event, Blogs
from BlognEvent.forms import EventForm, BlogsForm
from home.models import FitnessSpot
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import json

def blogevent_page(request):
    is_admin = request.session.get("is_admin", False)

    events = Event.objects.all().order_by('-starting_date')
    blogs = Blogs.objects.all().order_by('-id')

    context = {
        'events': events,
        'blogs': blogs,
        'is_admin': is_admin,
    }
    return render(request, 'blogevent/blogevent_page.html', context)

@login_required
def event_form_page(request):
    form = EventForm()
    fitness_spots = FitnessSpot.objects.all()

    locations_for_map = [
        {
            'id': str(spot.place_id),
            'name': spot.name,
            'address': spot.address,
            'latitude': str(spot.latitude),
            'longitude': str(spot.longitude)
        } for spot in fitness_spots
    ]

    context = {
        'form': form,
        'locations': fitness_spots,
        'locations_json': json.dumps(locations_for_map),
        'selected_locations': json.dumps([]),
    }
    return render(request, 'blogevent/event_form.html', context)

@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event_entry = form.save(commit=False)
            event_entry.user = request.user
            event_entry.save()

            location_ids = request.POST.getlist('locations')
            if location_ids:
                event_entry.locations.set(location_ids)
            return redirect('BlognEvent:blogevent_page')
    return redirect('BlognEvent:event_form_page')

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_admin = request.session.get("is_admin", False)

    if not (is_admin or event.user == request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    fitness_spots = FitnessSpot.objects.all()

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event_entry = form.save()
            location_ids = request.POST.getlist('locations')
            if location_ids:
                event_entry.locations.set(location_ids)
            return redirect('BlognEvent:blogevent_page')
    else:
        form = EventForm(instance=event)

    locations_for_map = [
        {
            'id': str(spot.place_id),
            'name': spot.name,
            'address': spot.address,
            'latitude': str(spot.latitude),
            'longitude': str(spot.longitude)
        } for spot in fitness_spots
    ]

    selected_place_ids = [str(pid) for pid in event.locations.values_list('place_id', flat=True)]

    context = {
        'form': form,
        'event': event,
        'locations': fitness_spots,
        'locations_json': json.dumps(locations_for_map),
        'selected_locations': json.dumps(selected_place_ids),
    }
    return render(request, 'blogevent/event_form.html', context)

@login_required
@require_POST
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_admin = request.session.get("is_admin", False)

    if not (is_admin or event.user == request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    event.delete()
    return JsonResponse({'success': True})

@login_required
def blog_form_page(request):
    form = BlogsForm()
    return render(request, 'blogevent/blog_form.html', {'form': form})

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

@login_required
def edit_blog(request, blog_id):
    blog = get_object_or_404(Blogs, id=blog_id)
    is_admin = request.session.get("is_admin", False)

    if not (is_admin or blog.author == request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == "POST":
        form = BlogsForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            return redirect('BlognEvent:blogevent_page')
    else:
        form = BlogsForm(instance=blog)

    return render(request, 'blogevent/blog_form.html', {'form': form, 'blog': blog})

@login_required
@require_POST
def delete_blog(request, blog_id):
    blog = get_object_or_404(Blogs, id=blog_id)
    is_admin = request.session.get("is_admin", False)

    if not (is_admin or blog.author == request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    blog.delete()
    return JsonResponse({'success': True})

def event_detail_api(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    locations = [loc.name for loc in event.locations.all()]

    is_admin = request.session.get("is_admin", False)
    is_owner = request.user.is_authenticated and event.user == request.user

    return JsonResponse({
        'name': event.name,
        'image': event.image,
        'description': event.description,
        'starting_date': event.starting_date.strftime('%B %d, %Y'),
        'ending_date': event.ending_date.strftime('%B %d, %Y'),
        'user': event.user.username,
        'locations': locations,
        'is_owner': is_owner or is_admin,
    })

def blog_detail_api(request, blog_id):
    blog = get_object_or_404(Blogs, id=blog_id)

    is_admin = request.session.get("is_admin", False)
    is_owner = request.user.is_authenticated and blog.author == request.user

    return JsonResponse({
        'title': blog.title,
        'image': blog.image,
        'body': blog.body,
        'author': blog.author.username,
        'is_owner': is_owner or is_admin,
    })

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])  # Allow OPTIONS for CORS preflight
def api_events(request):
    events = Event.objects.all().order_by('-starting_date')
    events_data = []
    
    for event in events:
        is_owner = False
        is_admin = False
        
        if request.user.is_authenticated:
            is_owner = event.user == request.user
            is_admin = request.session.get("is_admin", False)
        
        events_data.append({
            'id': str(event.id),
            'name': event.name,
            'image': event.image or '',
            'description': event.description,
            'starting_date': event.starting_date.isoformat(),
            'ending_date': event.ending_date.isoformat(),
            'user': event.user.username,
            'locations': [loc.name for loc in event.locations.all()],
            'is_owner': is_owner or is_admin,
        })
    
    response = JsonResponse(events_data, safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "*"
    return response

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_blogs(request):
    blogs = Blogs.objects.all().order_by('-id')
    blogs_data = []
    
    for blog in blogs:
        is_owner = False
        is_admin = False
        
        if request.user.is_authenticated:
            is_owner = blog.author == request.user
            is_admin = request.session.get("is_admin", False)
        
        blogs_data.append({
            'id': str(blog.id),
            'title': blog.title,
            'image': blog.image or '',
            'body': blog.body,
            'author': blog.author.username,
            'is_owner': is_owner or is_admin,
        })
    
    response = JsonResponse(blogs_data, safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "*"
    return response