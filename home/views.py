import datetime
import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.cache import cache
from django.db.models import Min, Max
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from community.models import Community 
from .forms import StyledUserCreationForm, StyledAuthenticationForm
from .models import FitnessSpot, PlaceType
from django.views.decorators.csrf import csrf_exempt
import uuid

GRID_ORIGIN_LAT = -6.8
GRID_ORIGIN_LNG = 106.5
GRID_CELL_SIZE_DEG = 0.09

def get_grid_bounds(grid_id):
    """Calculates the geographic boundaries for a given grid ID (e.g., '3-5')."""
    try:
        row_str, col_str = grid_id.split('-')
        row, col = int(row_str), int(col_str)
    except (ValueError, IndexError):
        return None 

    sw_lat = GRID_ORIGIN_LAT + row * GRID_CELL_SIZE_DEG
    sw_lng = GRID_ORIGIN_LNG + col * GRID_CELL_SIZE_DEG
    ne_lat = sw_lat + GRID_CELL_SIZE_DEG
    ne_lng = sw_lng + GRID_CELL_SIZE_DEG
    
    return {'sw_lat': sw_lat, 'sw_lng': sw_lng, 'ne_lat': ne_lat, 'ne_lng': ne_lng}

def home_view(request):
    """Renders the main map page."""
    context = {'google_api_key': settings.GOOGLE_MAPS_API_KEY}
    return render(request, 'main.html', context)

@csrf_exempt
def get_fitness_spots_data(request):
    """
    Returns FitnessSpot data. If gridId is provided, it will return spots inside that grid.
    Otherwise it falls back to returning all spots (cached) so the endpoint does not 400.
    
    Handles POST requests to create new FitnessSpots.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            place_id = data.get('place_id')
            if not place_id:
                place_id = str(uuid.uuid4())
            
            spot = FitnessSpot.objects.create(
                place_id=place_id,
                name=data.get('name', ''),
                address=data.get('address', ''),
                latitude=data.get('latitude', 0.0),
                longitude=data.get('longitude', 0.0),
                website=data.get('website') or None,
                phone_number=data.get('phone_number') or None,
            )
            
            types_list = data.get('types', [])
            if isinstance(types_list, list):
                for type_name in types_list:
                    place_type, _ = PlaceType.objects.get_or_create(name=type_name)
                    spot.types.add(place_type)
            
            # Invalidate cache
            cache.delete("spots_all")
            cache.delete("map_boundaries")
            
            # Calculate and invalidate specific grid cache
            try:
                row = int((float(spot.latitude) - GRID_ORIGIN_LAT) / GRID_CELL_SIZE_DEG)
                col = int((float(spot.longitude) - GRID_ORIGIN_LNG) / GRID_CELL_SIZE_DEG)
                grid_id = f"{row}-{col}"
                cache.delete(f"spots_grid_{grid_id}")
                print(f"Invalidated cache for grid {grid_id}")
            except Exception as e:
                print(f"Error invalidating grid cache: {e}")

            return JsonResponse({'status': 'success', 'place_id': place_id}, status=201)
        except Exception as e:
            print(f"Error creating spot: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    grid_id = request.GET.get('gridId')

    if grid_id:
        cache_key = f"spots_grid_{grid_id}"
    else:
        cache_key = "spots_all"

    cached_data = cache.get(cache_key)
    if cached_data:
        source = f"grid {grid_id}" if grid_id else "all"
        print(f"[CACHE HIT] Serving spots for {source} from memory.")
        return JsonResponse(cached_data)

    if grid_id:
        bounds = get_grid_bounds(grid_id)
        if not bounds:
            return JsonResponse({'spots': [], 'error': 'Invalid gridId format'}, status=400)
        spots_query = FitnessSpot.objects.filter(
            latitude__gte=bounds['sw_lat'], latitude__lte=bounds['ne_lat'],
            longitude__gte=bounds['sw_lng'], longitude__lte=bounds['ne_lng']
        )
        print(f"[CACHE MISS] Querying database for grid {grid_id}...")
    else:
        # Fallback path for clients that forgot to send gridId.
        spots_query = FitnessSpot.objects.all()
        print("[CACHE MISS] Querying database for all spots (no gridId provided)...")
    
    spots = spots_query.values(
        'name', 'latitude', 'longitude', 'address', 'rating', 
        'place_id', 'rating_count', 'website', 'phone_number', 'types__name'
    )
    spots_data_map = {}
    for spot in spots:
        place_id = spot['place_id']
        if place_id not in spots_data_map:
            spots_data_map[place_id] = spot
            spots_data_map[place_id]['types'] = set()
        if spot['types__name']:
            spots_data_map[place_id]['types'].add(spot['types__name'])

    final_spots_data = list(spots_data_map.values())
    for spot in final_spots_data:
        spot['types'] = list(spot['types'])

    response_data = {'spots': final_spots_data}
    cache.set(cache_key, response_data, 60 * 60 * 24)

    return JsonResponse(response_data)


def get_map_boundaries(request):
    """Calculates and returns the bounding box for all fitness spots."""
    cache_key = 'map_boundaries'
    cached_boundaries = cache.get(cache_key)
    if cached_boundaries:
        return JsonResponse(cached_boundaries)

    bounds = FitnessSpot.objects.aggregate(
        min_lat=Min('latitude'), max_lat=Max('latitude'),
        min_lng=Min('longitude'), max_lng=Max('longitude')
    )

    if not all(bounds.values()):
        return JsonResponse({'error': 'No spots found'}, status=404)

    boundaries = {
        'north': float(bounds['max_lat']), 'south': float(bounds['min_lat']),
        'east': float(bounds['max_lng']), 'west': float(bounds['min_lng'])
    }
    cache.set(cache_key, boundaries, 60 * 60 * 24 * 7)
    return JsonResponse(boundaries)

def communities_by_place(request, place_id):
    """Mengembalikan list komunitas yang ada di FitnessSpot tertentu."""
    spot = get_object_or_404(FitnessSpot, place_id=place_id)
    communities = Community.objects.filter(fitness_spot=spot).values('id', 'name', 'description')
    return JsonResponse({'communities': list(communities)})
