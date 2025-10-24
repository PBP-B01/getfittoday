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
from .models import FitnessSpot
from .utils.spots_loader import build_index_and_bounds, load_all_spots


# --- Grid Configuration ---
GRID_ORIGIN_LAT = -6.8  # Bottom-left corner of our grid (latitude)
GRID_ORIGIN_LNG = 106.5 # Bottom-left corner of our grid (longitude)
GRID_CELL_SIZE_DEG = 0.09 # The size of each grid square in degrees (approx. 10km)

def get_grid_bounds(grid_id):
    """Calculates the geographic boundaries for a given grid ID (e.g., '3-5')."""
    try:
        row_str, col_str = grid_id.split('-')
        row, col = int(row_str), int(col_str)
    except (ValueError, IndexError):
        return None # Invalid grid ID format

    sw_lat = GRID_ORIGIN_LAT + row * GRID_CELL_SIZE_DEG
    sw_lng = GRID_ORIGIN_LNG + col * GRID_CELL_SIZE_DEG
    ne_lat = sw_lat + GRID_CELL_SIZE_DEG
    ne_lng = sw_lng + GRID_CELL_SIZE_DEG
    
    return {'sw_lat': sw_lat, 'sw_lng': sw_lng, 'ne_lat': ne_lat, 'ne_lng': ne_lng}

# --- Views ---
def home_view(request):
    """Renders the main map page."""
    context = {'google_api_key': settings.GOOGLE_MAPS_API_KEY}
    return render(request, 'main.html', context)

def get_fitness_spots_data(request):
    """
    Returns FitnessSpot data for a specific grid square, using grid-based caching.
    """
    grid_id = request.GET.get('gridId')
    if not grid_id:
        return JsonResponse({'spots': [], 'error': 'gridId parameter is required'}, status=400)

    # The grid ID is now our perfect cache key.
    cache_key = f"spots_grid_{grid_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        print(f"✅ GRID CACHE HIT! Serving grid {grid_id} from memory.")
        return JsonResponse(cached_data)

    print(f"❌ GRID CACHE MISS! Querying database for grid {grid_id}...")

    bounds = get_grid_bounds(grid_id)
    if not bounds:
        return JsonResponse({'spots': [], 'error': 'Invalid gridId format'}, status=400)

    # Query all spots within the entire grid square.
    spots_query = FitnessSpot.objects.filter(
        latitude__gte=bounds['sw_lat'], latitude__lte=bounds['ne_lat'],
        longitude__gte=bounds['sw_lng'], longitude__lte=bounds['ne_lng']
    )
    
    spots = spots_query.values(
        'name', 'latitude', 'longitude', 'address', 'rating', 
        'place_id', 'rating_count', 'website', 'phone_number', 'types__name'
    )
    
    # Process data (simplified for better performance)
    spots_data_map = {}
    for spot in spots:
        place_id = spot['place_id']
        if place_id not in spots_data_map:
            spots_data_map[place_id] = spot
            spots_data_map[place_id]['types'] = set()
        if spot['types__name']:
            spots_data_map[place_id]['types'].add(spot['types__name'])

    # Convert sets to lists for JSON serialization
    final_spots_data = list(spots_data_map.values())
    for spot in final_spots_data:
        spot['types'] = list(spot['types'])

    response_data = {'spots': final_spots_data}
    cache.set(cache_key, response_data, 60 * 60 * 24) # Cache for 1 hour

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

def api_map_boundaries(request):
    _, bounds = build_index_and_bounds()
    return JsonResponse(bounds)

def api_fitness_spots(request):
    grid_id = request.GET.get("gridId", "")
    index, _ = build_index_and_bounds()
    return JsonResponse({"gridId": grid_id, "spots": index.get(grid_id, [])})

def communities_by_place(request, place_id):
    """Mengembalikan list komunitas yang ada di FitnessSpot tertentu."""
    spot = get_object_or_404(FitnessSpot, place_id=place_id)
    communities = Community.objects.filter(fitness_spot=spot).values('id', 'name', 'description')
    return JsonResponse({'communities': list(communities)})


def communities_by_place_json(request, place_id):
    """Mengambil list komunitas dari file JSON lokal di static berdasarkan place_id."""
    json_path = Path(settings.BASE_DIR) / "static" / "home" / "data" / "community_data.json"
    try:
        with open(json_path, encoding="utf-8") as f:
            all_data = json.load(f)
    except FileNotFoundError:
        print("JSON file not found!")
        return JsonResponse({"communities": []})

    communities = [
        {
            "id": c["pk"],
            "name": c["fields"]["name"],
            "description": c["fields"]["description"],
            "contact_info": c["fields"].get("contact_info", "")
        }
        for c in all_data if c["fields"]["fitness_spot"] == place_id
    ]

    return JsonResponse({"communities": communities})
