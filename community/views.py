from django.shortcuts import render, redirect
from .models import Community
from .forms import CommunityForm
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from home.models import FitnessSpot
import os
import json
from django.conf import settings

from django.shortcuts import render
from django.contrib.staticfiles import finders
import json
from .models import Community
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Community
from .forms import CommunityForm
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required

@login_required
def ajax_join_community(request, community_id):
    if request.method == "POST":
        all_data = read_json()
        for c in all_data:
            if c['pk'] == int(community_id):
                username = request.user.username
                if username not in c['fields']['members']:
                    c['fields']['members'].append(username)
                    write_json(all_data)
                return JsonResponse({"success": True, "members": c['fields']['members']})
        return JsonResponse({"success": False, "error": "Community not found"})
    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def ajax_leave_community(request, community_id):
    if request.method == "POST":
        all_data = read_json()
        for c in all_data:
            if c['pk'] == int(community_id):
                username = request.user.username
                if username in c['fields']['members']:
                    c['fields']['members'].remove(username)
                    write_json(all_data)
                return JsonResponse({"success": True, "members": c['fields']['members']})
        return JsonResponse({"success": False, "error": "Community not found"})
    return JsonResponse({"success": False, "error": "Invalid request"})


# Helper: hanya admin
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

# Halaman komunitas admin
@admin_required
def admin_community_page(request):
    communities = Community.objects.all()
    form = CommunityForm()
    return render(request, "community/admin_community.html", {"communities": communities, "form": form})

# Tambah komunitas via AJAX
@admin_required
def ajax_add_community(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save()
            return JsonResponse({
                "success": True,
                "id": community.id,
                "name": community.name,
                "description": community.description
            })
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False, "error": "Invalid request"})

# Edit komunitas via AJAX
@admin_required
def ajax_edit_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.method == "POST":
        form = CommunityForm(request.POST, instance=community)
        if form.is_valid():
            community = form.save()
            return JsonResponse({"success": True, "id": community.id, "name": community.name, "description": community.description})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False, "error": "Invalid request"})

# Delete komunitas via AJAX
@admin_required
def ajax_delete_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.method == "POST":
        community.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})

def community_list(request):
    json_path = finders.find('home/data/community_data.json')
    
    communities_from_json = []
    if json_path:
        with open(json_path, 'r', encoding='utf-8') as f:
            communities_from_json = json.load(f)
        
        # Mapping place_id → nama tempat
        spots = FitnessSpot.objects.all()
        fitness_spots_dict = {spot.place_id: spot.name for spot in spots}

        # Tambahkan field fitness_spot_name ke setiap komunitas
        for c in communities_from_json:
            c['fields']['fitness_spot_name'] = fitness_spots_dict.get(c['fields']['fitness_spot'], "Nama tempat tidak diketahui")

    # Ambil data dari DB juga (opsional)
    communities_from_db = Community.objects.all()

    context = {
        'communities_json': communities_from_json,
        'communities_db': communities_from_db,
    }

    return render(request, 'community/community_list.html', context)

def add_community(request):
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('community_list')
    else:
        form = CommunityForm()
    return render(request, 'community/add_community.html', {'form': form})

def communities_by_place(request, place_id):
    """Mengembalikan list komunitas yang ada di FitnessSpot tertentu (JSON)."""
    spot = get_object_or_404(FitnessSpot, place_id=place_id)
    # Ambil cuma id & name supaya modal lebih ringkas
    communities = Community.objects.filter(fitness_spot=spot).values('id', 'name')
    return JsonResponse({'communities': list(communities)})

def communities_by_spot(request, spot_id):
    """Return JSON list of communities for a given fitness spot"""
    # Cek dulu di DB
    spot = get_object_or_404(FitnessSpot, place_id=spot_id)
    communities_db = Community.objects.filter(fitness_spot=spot).values(
        'name', 'description', 'contact_info'
    )

    # Ambil juga dari JSON
    json_path = os.path.join(settings.BASE_DIR, 'getfittoday', 'static', 'home', 'data', 'community_data.json')
    communities_json = []
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for c in data:
                if c['fields']['fitness_spot'] == spot.place_id:
                    communities_json.append({
                        'name': c['fields']['name'],
                        'description': c['fields']['description'],
                        'contact_info': c['fields']['contact_info']
                    })

    # Gabungkan DB + JSON
    communities_all = list(communities_db) + communities_json
    return JsonResponse({'communities': communities_all})

def communities_by_place_json(request, place_id):
    json_path = os.path.join(settings.BASE_DIR, 'static', 'home', 'data', 'community_data.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            all_communities = json.load(f)
    except Exception as e:
        return JsonResponse({'error': str(e), 'communities': []})

    # Filter komunitas berdasarkan fitness_spot
    communities_in_place = [
        {
            'id': c['pk'],
            'name': c['fields']['name']
        }
        for c in all_communities
        if c['fields']['fitness_spot'] == place_id
    ]

    return JsonResponse({'communities': communities_in_place})

def community_detail(request, pk):
    community = get_object_or_404(Community, pk=pk)
    return render(request, 'community/community_detail.html', {
        'community': community
    })