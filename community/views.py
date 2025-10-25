# community/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Community
from .forms import CommunityForm
from home.models import FitnessSpot
import json
from decimal import Decimal
from django.views.decorators.http import require_POST

User = get_user_model()

# --- Custom JSON Encoder for Decimal ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# --- Join/Leave AJAX ---
@login_required
@require_POST
def ajax_join_community(request, community_id):
    if request.method == "POST":
        try:
            community = Community.objects.get(id=community_id)
            
            # Cek apakah sudah member
            if community.is_member(request.user):
                return JsonResponse({"success": False, "error": "Kamu sudah menjadi member."}, status=400)
            
            community.members.add(request.user)
            member_count = community.members.count()
            return JsonResponse({"success": True, "member_count": member_count, "action": "joined"})
        except Community.DoesNotExist:
            return JsonResponse({"success": False, "error": "Community not found"}, status=404)
        except Exception as e:
            print(f"Error joining community {community_id}: {e}")
            return JsonResponse({"success": False, "error": "An internal error occurred."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
@require_POST
def ajax_leave_community(request, community_id):
    if request.method == "POST":
        try:
            community = Community.objects.get(id=community_id)

            if not community.can_leave(request.user):
                return JsonResponse({
                    "success": False, 
                    "error": "Founder tidak bisa keluar. Tambahkan admin lain terlebih dahulu atau hapus komunitas."
                }, status=403)

            community.members.remove(request.user)

            if community.is_admin(request.user) and not community.is_founder(request.user):
                community.admins.remove(request.user)
            
            member_count = community.members.count()
            return JsonResponse({"success": True, "member_count": member_count, "action": "left"})
        except Community.DoesNotExist:
            return JsonResponse({"success": False, "error": "Community not found"}, status=404)
        except Exception as e:
            print(f"Error leaving community {community_id}: {e}")
            return JsonResponse({"success": False, "error": "An internal error occurred."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

# --- Add/Edit/Delete AJAX ---
@login_required
def ajax_add_community(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            try:
                community = form.save(commit=False)
                community.founder = request.user
                community.save()

                community.admins.add(request.user)
                community.members.add(request.user)
                
                community.refresh_from_db(fields=['fitness_spot'])

                return JsonResponse({
                    "success": True,
                    "id": community.id,
                    "name": community.name,
                    "description": community.description,
                    "contact_info": community.contact_info,
                    "fitness_spot_name": community.fitness_spot.name if community.fitness_spot else None,
                    "fitness_spot_id": community.fitness_spot.place_id if community.fitness_spot else None,
                    "detail_url": reverse('community_detail', args=[community.id])
                })
            except Exception as e:
                print(f"Error adding community: {e}")
                return JsonResponse({"success": False, "error": "Failed to save community."}, status=500)
        else:
            return JsonResponse({"success": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
def ajax_edit_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if not community.is_admin(request.user):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        form = CommunityForm(request.POST, instance=community)
        if form.is_valid():
            try:
                community = form.save()
                community.refresh_from_db(fields=['fitness_spot'])
                return JsonResponse({
                    "success": True,
                    "id": community.id,
                    "name": community.name,
                    "description": community.description,
                    "contact_info": community.contact_info,
                    "fitness_spot_name": community.fitness_spot.name if community.fitness_spot else None,
                    "fitness_spot_id": community.fitness_spot.place_id if community.fitness_spot else None,
                    "detail_url": reverse('community_detail', args=[community.id])
                })
            except Exception as e:
                print(f"Error editing community {community_id}: {e}")
                return JsonResponse({"success": False, "error": "Failed to save changes."}, status=500)
        else:
            return JsonResponse({"success": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
def ajax_delete_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if not (community.is_founder(request.user) or request.user.is_staff):
        return JsonResponse({"success": False, "error": "Permission denied. Only founder can delete."}, status=403)

    if request.method == "POST":
        try:
            community.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error deleting community {community_id}: {e}")
            return JsonResponse({"success": False, "error": "Failed to delete community."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

# --- Admin Management AJAX ---
@login_required
def ajax_add_community_admin(request, community_id):
    """
    Menambahkan admin baru ke komunitas.
    Hanya founder atau platform admin yang bisa.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    community = get_object_or_404(Community, id=community_id)

    if not community.can_manage_admins(request.user):
        return JsonResponse({
            "success": False, 
            "error": "Hanya founder yang bisa menambah admin."
        }, status=403)

    username_to_add = request.POST.get('username')
    if not username_to_add:
        return JsonResponse({"success": False, "error": "Username tidak disediakan"}, status=400)

    try:
        user_to_add = User.objects.get(username=username_to_add)

        if not community.is_member(user_to_add):
            return JsonResponse({
                "success": False, 
                "error": "User harus menjadi member terlebih dahulu."
            }, status=400)

        if community.is_admin(user_to_add):
            return JsonResponse({
                "success": False, 
                "error": "User sudah menjadi admin."
            }, status=400)
        
        community.admins.add(user_to_add)
        
        return JsonResponse({
            "success": True, 
            "message": f"User '{username_to_add}' berhasil ditambahkan sebagai admin."
        })
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User tidak ditemukan"}, status=404)
    except Exception as e:
        print(f"Error adding admin to community {community_id}: {e}")
        return JsonResponse({"success": False, "error": "Gagal menambah admin."}, status=500)

@login_required
def ajax_remove_community_admin(request, community_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    community = get_object_or_404(Community, id=community_id)

    if not community.can_manage_admins(request.user):
        return JsonResponse({
            "success": False, 
            "error": "Hanya founder yang bisa menghapus admin."
        }, status=403)

    username_to_remove = request.POST.get('username')
    if not username_to_remove:
        return JsonResponse({"success": False, "error": "Username tidak disediakan"}, status=400)

    try:
        user_to_remove = User.objects.get(username=username_to_remove)

        if community.is_founder(user_to_remove):
            return JsonResponse({
                "success": False, 
                "error": "Founder tidak bisa dihapus sebagai admin."
            }, status=400)

        if not community.admins.filter(id=user_to_remove.id).exists():
            return JsonResponse({
                "success": False, 
                "error": "User bukan admin komunitas ini."
            }, status=400)
        
        community.admins.remove(user_to_remove)
        
        return JsonResponse({
            "success": True, 
            "message": f"User '{username_to_remove}' berhasil dihapus dari admin."
        })
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User tidak ditemukan"}, status=404)
    except Exception as e:
        print(f"Error removing admin from community {community_id}: {e}")
        return JsonResponse({"success": False, "error": "Gagal menghapus admin."}, status=500)

def community_list(request):
    communities = Community.objects.select_related('fitness_spot', 'founder').prefetch_related('admins', 'members').all()
    form = CommunityForm()

    all_fitness_spots = list(FitnessSpot.objects.values('place_id', 'name', 'latitude', 'longitude'))
    for spot in all_fitness_spots:
        if 'latitude' in spot and isinstance(spot['latitude'], Decimal):
            spot['latitude'] = float(spot['latitude'])
        if 'longitude' in spot and isinstance(spot['longitude'], Decimal):
            spot['longitude'] = float(spot['longitude'])

    context = {
        'communities': communities,
        'form': form,
        'all_fitness_spots_data': all_fitness_spots,
    }
    return render(request, 'community/community_list.html', context)

@login_required
def add_community(request):
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            try:
                community = form.save(commit=False)
                community.founder = request.user
                community.save()
                community.admins.add(request.user)
                community.members.add(request.user)
                return redirect('community_list')
            except Exception as e:
                print(f"Error adding community via non-AJAX: {e}")
    else:
        form = CommunityForm()
    return render(request, 'community/add_community.html', {'form': form})

def community_detail(request, pk):
    community = get_object_or_404(
        Community.objects.select_related('fitness_spot', 'founder').prefetch_related('members', 'admins'),
        pk=pk
    )

    context = {
        'community': community,
        'is_member': community.is_member(request.user) if request.user.is_authenticated else False,
        'is_admin': community.is_admin(request.user) if request.user.is_authenticated else False,
        'is_founder': community.is_founder(request.user) if request.user.is_authenticated else False,
        'can_leave': community.can_leave(request.user) if request.user.is_authenticated else False,
    }
    return render(request, 'community/community_detail.html', context)

# --- API/JSON Views (for map) ---
def communities_by_place_json(request, place_id):
    try:
        communities_in_place = Community.objects.filter(fitness_spot__place_id=place_id).values(
            'id', 'name', 'description', 'contact_info'
        )
        return JsonResponse({'communities': list(communities_in_place)})
    except FitnessSpot.DoesNotExist:
        return JsonResponse({'error': 'Fitness spot not found', 'communities': []}, status=404)
    except Exception as e:
        print(f"Error in communities_by_place_json for place_id {place_id}: {e}")
        return JsonResponse({'error': 'An internal error occurred', 'communities': []}, status=500)

def communities_by_spot(request, spot_id):
    spot = get_object_or_404(FitnessSpot, place_id=spot_id)
    communities_db = Community.objects.filter(fitness_spot=spot).values('name', 'description', 'contact_info')
    return JsonResponse({'communities': list(communities_db)})