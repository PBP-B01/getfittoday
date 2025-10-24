# community/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Community
from .forms import CommunityForm
from home.models import FitnessSpot # Assuming this is the correct path
import json
from decimal import Decimal # Needed for JSON encoding fix

User = get_user_model()

# --- Custom JSON Encoder for Decimal ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) # Convert Decimal to float for JSON
        return super(DecimalEncoder, self).default(obj)

# --- Join/Leave AJAX ---
@login_required
def ajax_join_community(request, community_id):
    if request.method == "POST":
        try:
            community = Community.objects.get(id=community_id)
            # Prevent admin from leaving via this button (handled in template visibility)
            if request.user in community.admins.all():
                 return JsonResponse({"success": False, "error": "Admin cannot leave via this method."}, status=403)
            community.members.add(request.user)
            member_count = community.members.count()
            return JsonResponse({"success": True, "member_count": member_count, "action": "joined"})
        except Community.DoesNotExist:
            return JsonResponse({"success": False, "error": "Community not found"}, status=404)
        except Exception as e:
            print(f"Error joining community {community_id}: {e}") # Log error
            return JsonResponse({"success": False, "error": "An internal error occurred."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
def ajax_leave_community(request, community_id):
    if request.method == "POST":
        try:
            community = Community.objects.get(id=community_id)
            # Prevent admin from leaving via this button
            if request.user in community.admins.all():
                 return JsonResponse({"success": False, "error": "Admin cannot leave via this method."}, status=403)
            community.members.remove(request.user)
            member_count = community.members.count()
            return JsonResponse({"success": True, "member_count": member_count, "action": "left"})
        except Community.DoesNotExist:
            return JsonResponse({"success": False, "error": "Community not found"}, status=404)
        except User.DoesNotExist: # User might not be a member
             return JsonResponse({"success": False, "error": "User is not a member of this community."}, status=400)
        except Exception as e:
            print(f"Error leaving community {community_id}: {e}") # Log error
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
                community.save() # Save first to get an ID
                community.admins.add(request.user) # Add creator as admin
                # We need to save ManyToMany fields separately
                # form.save_m2m() # Not needed here as admins added manually

                # Ensure fitness_spot is loaded for the response
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
                 print(f"Error adding community: {e}") # Log error
                 return JsonResponse({"success": False, "error": "Failed to save community."}, status=500)
        else:
            # Return validation errors in a JSON-serializable format
            return JsonResponse({"success": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
def ajax_edit_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.user not in community.admins.all():
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        form = CommunityForm(request.POST, instance=community)
        if form.is_valid():
            try:
                community = form.save()
                 # Ensure fitness_spot is loaded for the response
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
                 print(f"Error editing community {community_id}: {e}") # Log error
                 return JsonResponse({"success": False, "error": "Failed to save changes."}, status=500)
        else:
            return JsonResponse({"success": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
def ajax_delete_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.user not in community.admins.all():
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        try:
            community.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error deleting community {community_id}: {e}") # Log error
            return JsonResponse({"success": False, "error": "Failed to delete community."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

# --- Add Admin AJAX ---
@login_required
def ajax_add_community_admin(request, community_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

    community = get_object_or_404(Community, id=community_id)
    if request.user not in community.admins.all():
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    username_to_add = request.POST.get('username')
    if not username_to_add:
        return JsonResponse({"success": False, "error": "Username not provided"}, status=400)

    try:
        user_to_add = User.objects.get(username=username_to_add)
        community.admins.add(user_to_add)
        return JsonResponse({"success": True, "message": f"User '{username_to_add}' added as admin."})
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"}, status=404)
    except Exception as e:
        print(f"Error adding admin to community {community_id}: {e}") # Log error
        return JsonResponse({"success": False, "error": "Failed to add admin."}, status=500)

# --- Page Views ---
def community_list(request):
    communities = Community.objects.select_related('fitness_spot').prefetch_related('admins').all()
    form = CommunityForm() # For the modal

    # Get Fitness Spot data, convert Decimals for JSON
    all_fitness_spots = list(FitnessSpot.objects.values('place_id', 'name', 'latitude', 'longitude'))
    # No need to manually convert here if using DecimalEncoder, but safer to do so
    for spot in all_fitness_spots:
        if 'latitude' in spot and isinstance(spot['latitude'], Decimal):
            spot['latitude'] = float(spot['latitude'])
        if 'longitude' in spot and isinstance(spot['longitude'], Decimal):
            spot['longitude'] = float(spot['longitude'])

    context = {
        'communities': communities,
        'form': form,
        # Pass the raw Python list, let json_script handle encoding
        'all_fitness_spots_data': all_fitness_spots,
    }
    return render(request, 'community/community_list.html', context)

@login_required
def add_community(request): # Non-AJAX fallback
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            try:
                community = form.save(commit=False)
                community.save()
                community.admins.add(request.user)
                # form.save_m2m() # Not needed
                return redirect('community_list')
            except Exception as e:
                 print(f"Error adding community via non-AJAX: {e}") # Log error
                 # Add error message handling if desired
    else:
        form = CommunityForm()
    return render(request, 'community/add_community.html', {'form': form})

def community_detail(request, pk):
    # Prefetch related data for efficiency
    community = get_object_or_404(
        Community.objects.select_related('fitness_spot').prefetch_related('members', 'admins'),
        pk=pk
    )
    return render(request, 'community/community_detail.html', {'community': community})

# --- API/JSON Views (for map) ---
def communities_by_place(request, place_id): # Potentially unused?
    spot = get_object_or_404(FitnessSpot, place_id=place_id)
    communities = Community.objects.filter(fitness_spot=spot).values('id', 'name')
    return JsonResponse({'communities': list(communities)})

def communities_by_spot(request, spot_id): # Potentially unused?
    spot = get_object_or_404(FitnessSpot, place_id=spot_id)
    communities_db = Community.objects.filter(fitness_spot=spot).values('name', 'description', 'contact_info')
    return JsonResponse({'communities': list(communities_db)})

def communities_by_place_json(request, place_id): # Used by map modal
    try:
        # Return data needed by the modal's JS (id, name, description, contact_info)
        communities_in_place = Community.objects.filter(fitness_spot__place_id=place_id).values(
            'id', 'name', 'description', 'contact_info'
        )
        return JsonResponse({'communities': list(communities_in_place)})
    except FitnessSpot.DoesNotExist:
         return JsonResponse({'error': 'Fitness spot not found', 'communities': []}, status=404)
    except Exception as e:
        print(f"Error in communities_by_place_json for place_id {place_id}: {e}") # Log error
        return JsonResponse({'error': 'An internal error occurred', 'communities': []}, status=500)