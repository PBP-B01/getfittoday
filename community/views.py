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
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) 
        return super(DecimalEncoder, self).default(obj)

@csrf_exempt
@login_required
def ajax_join_community(request, community_id):
    if request.method == "POST":
        try:
            community = Community.objects.get(id=community_id)
            if request.user in community.admins.all():
                 return JsonResponse({"success": False, "error": "Admin cannot leave via this method."}, status=403)
            community.members.add(request.user)
            member_count = community.members.count()
            return JsonResponse({"success": True, "member_count": member_count, "action": "joined"})
        except Community.DoesNotExist:
            return JsonResponse({"success": False, "error": "Community not found"}, status=404)
        except Exception as e:
            print(f"Error joining community {community_id}: {e}") 
            return JsonResponse({"success": False, "error": "An internal error occurred."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@csrf_exempt
@login_required
def ajax_leave_community(request, community_id):
    if request.method == "POST":
        try:
            community = Community.objects.get(id=community_id)
            if request.user in community.admins.all():
                 return JsonResponse({"success": False, "error": "Admin cannot leave via this method."}, status=403)
            community.members.remove(request.user)
            member_count = community.members.count()
            return JsonResponse({"success": True, "member_count": member_count, "action": "left"})
        except Community.DoesNotExist:
            return JsonResponse({"success": False, "error": "Community not found"}, status=404)
        except User.DoesNotExist:
             return JsonResponse({"success": False, "error": "User is not a member of this community."}, status=400)
        except Exception as e:
            print(f"Error leaving community {community_id}: {e}")
            return JsonResponse({"success": False, "error": "An internal error occurred."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
def ajax_add_community(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            try:
                community = form.save(commit=False)
                community.save() 
                community.admins.add(request.user) 
                community.refresh_from_db(fields=['fitness_spot'])

                return JsonResponse({
                    "success": True,
                    "id": community.id,
                    "name": community.name,
                    "description": community.description,
                    "contact_info": community.contact_info,
                    "fitness_spot_name": community.fitness_spot.name if community.fitness_spot else None,
                    "fitness_spot_id": community.fitness_spot.place_id if community.fitness_spot else None,
                    "detail_url": reverse('community:community_detail', args=[community.id])
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
    if request.user not in community.admins.all():
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
                    "detail_url": reverse('community:community_detail', args=[community.id])
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
    if request.user not in community.admins.all():
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        try:
            community.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error deleting community {community_id}: {e}")
            return JsonResponse({"success": False, "error": "Failed to delete community."}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

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
        print(f"Error adding admin to community {community_id}: {e}") 
        return JsonResponse({"success": False, "error": "Failed to add admin."}, status=500)

def community_list(request):
    communities = Community.objects.select_related('fitness_spot').prefetch_related('admins').all()
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

def community_detail(request, pk):
    community = get_object_or_404(
        Community.objects.select_related('fitness_spot').prefetch_related('members', 'admins'),
        pk=pk
    )
    return render(request, 'community/community_detail.html', {'community': community})

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
    
def featured_communities_api(request):
    try:
        communities = Community.objects.order_by('-id')[:15]

        data = []
        for community in communities:
            data.append({
                'id': community.id,
                'name': community.name,
                'description': community.description,
                'fitness_spot_name': community.fitness_spot.name if community.fitness_spot else 'Lokasi tidak diketahui',
                'detail_url': reverse('community_detail', args=[community.id]),
            })
        
        return JsonResponse({'communities': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
