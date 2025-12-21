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

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def event_detail_api(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    locations = [loc.name for loc in event.locations.all()]

    is_owner = False
    is_admin = False

    if request.user.is_authenticated:
        is_owner = event.user == request.user
        is_admin = request.session.get("is_admin", False)

    data = {
        'id': str(event.id),
        'name': event.name,
        'image': event.image or '',
        'description': event.description,
        'starting_date': event.starting_date.isoformat(),
        'ending_date': event.ending_date.isoformat(),
        'user': event.user.username,
        'locations': locations,
        'is_owner': is_owner or is_admin,
    }

    response = JsonResponse(data)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "*"
    return response


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def blog_detail_api(request, blog_id):
    blog = get_object_or_404(Blogs, id=blog_id)

    is_owner = False
    is_admin = False

    if request.user.is_authenticated:
        is_owner = blog.author == request.user
        is_admin = request.session.get("is_admin", False)

    data = {
        'id': str(blog.id),
        'title': blog.title,
        'image': blog.image or '',
        'body': blog.body,
        'author': blog.author.username,
        'is_owner': is_owner or is_admin,
    }

    response = JsonResponse(data)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "*"
    return response


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])  
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

@csrf_exempt
def create_blog_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    data = request.POST

    title = data.get("title")
    body = data.get("body")
    image = data.get("image", "")

    if not title or not body:
        return JsonResponse({"error": "Missing fields"}, status=400)

    blog = Blogs.objects.create(
        title=title,
        body=body,
        image=image,
        author=request.user,
    )

    return JsonResponse(
        {
            "success": True,
            "blog_id": str(blog.id),
        },
        status=201,
    )

@csrf_exempt
def create_event_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    
    print("===== EVENT CREATE AUTH DEBUG =====")
    print("request.user:", request.user)
    print("is_authenticated:", request.user.is_authenticated)
    print("session items:", dict(request.session.items()))
    print("===================================")

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Authentication required"},
            status=401
        )

    data = request.POST

    name = data.get("name")
    image = data.get("image", "")
    description = data.get("description")
    starting_date = data.get("starting_date")
    ending_date = data.get("ending_date")

    locations_raw = data.get("locations", "[]")
    try:
        location_ids = json.loads(locations_raw)
    except json.JSONDecodeError:
        location_ids = []

    if not name or not description or not starting_date or not ending_date:
        return JsonResponse({"error": "Missing fields"}, status=400)

    event = Event.objects.create(
        name=name,
        image=image,
        description=description,
        starting_date=starting_date,
        ending_date=ending_date,
        user=request.user,  
    )

    if location_ids:
        spots = FitnessSpot.objects.filter(place_id__in=location_ids)
        event.locations.set(spots)

    return JsonResponse(
        {
            "success": True,
            "event_id": str(event.id),
            "locations_count": len(location_ids),
        },
        status=201,
    )

@csrf_exempt
@require_http_methods(["GET"])
def api_fitness_spots_flutter(request):
    spots = FitnessSpot.objects.all()

    data = [
        {
            "place_id": str(spot.place_id),      
            "name": spot.name,
            "address": spot.address,
            "latitude": float(spot.latitude),    
            "longitude": float(spot.longitude),  #
        }
        for spot in spots
    ]

    return JsonResponse(data, safe=False)

def api_me(request):
    return JsonResponse({
        "username": request.user.username,
    })

@csrf_exempt
@require_POST
def delete_event_api(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    is_admin = request.session.get("is_admin", False)
    if not (is_admin or event.user == request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    event.delete()
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
def delete_blog_api(request, blog_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    blog = get_object_or_404(Blogs, id=blog_id)

    is_admin = request.session.get("is_admin", False)
    if not (is_admin or blog.author == request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    blog.delete()
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
def edit_event_api(request, event_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    event = get_object_or_404(Event, id=event_id)

    is_admin = request.session.get("is_admin", False)
    if not (is_admin or event.user == request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    data = request.POST

    event.name = data.get("name", event.name)
    event.image = data.get("image", event.image)
    event.description = data.get("description", event.description)
    event.starting_date = data.get("starting_date", event.starting_date)
    event.ending_date = data.get("ending_date", event.ending_date)

    # locations (same format as create_event_api)
    locations_raw = data.get("locations", "[]")
    try:
        location_ids = json.loads(locations_raw)
    except json.JSONDecodeError:
        location_ids = []

    event.save()

    if location_ids:
        spots = FitnessSpot.objects.filter(place_id__in=location_ids)
        event.locations.set(spots)

    return JsonResponse(
        {
            "success": True,
            "event_id": str(event.id),
        }
    )

@csrf_exempt
@require_POST
def edit_blog_api(request, blog_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    blog = get_object_or_404(Blogs, id=blog_id)

    is_admin = request.session.get("is_admin", False)
    if not (is_admin or blog.author == request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    data = request.POST

    blog.title = data.get("title", blog.title)
    blog.body = data.get("body", blog.body)
    blog.image = data.get("image", blog.image)

    blog.save()

    return JsonResponse(
        {
            "success": True,
            "blog_id": str(blog.id),
        }
    )
