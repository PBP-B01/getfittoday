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
import base64
from django.core.files.base import ContentFile # <--- Import Penting
import json
import base64
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile 
from .models import Community, CommunityPost # Pastikan tidak ada CommunityCategory lagi

User = get_user_model()

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) 
        return super(DecimalEncoder, self).default(obj)

# --- BAGIAN AJAX WEB (MODUL LAMA) ---

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
                    "detail_url": reverse('community_detail', args=[community.id])
                })
            except Exception as e:
                 print(f"Error adding community: {e}")
                 return JsonResponse({"success": False, "error": "Failed to save community."}, status=500)
        else:
            return JsonResponse({"success": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

@login_required
def add_community(request):
    return ajax_add_community(request)

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


# ==========================================
# BAGIAN 2: API FLUTTER (JSON) - SUDAH DIPERBAIKI
# ==========================================

def get_fitness_spots_json(request):
    """
    Mengambil data tempat olahraga untuk Dropdown Flutter.
    PENTING: Kita pakai 'place_id' (String) karena model temanmu pakai itu sebagai Primary Key.
    """
    # Mengambil semua tempat, ambil place_id dan name
    spots = list(FitnessSpot.objects.values('place_id', 'name'))
    
    # Format ulang biar Flutter nerima field 'id' yang isinya string place_id
    data = []
    for spot in spots:
        data.append({
            'id': spot['place_id'], # Ini String ID dari Google
            'name': spot['name']
        })
        
    return JsonResponse(data, safe=False)

# --- CREATE COMMUNITY (Yang sudah diperbaiki tadi) ---
@csrf_exempt
def create_community_flutter(request):
    if request.method == 'POST':
        try:
            if "application/json" in request.content_type:
                data = json.loads(request.body)
            else:
                data = request.POST 
            
            name = data.get("name")
            # 👇 AMBIL DATA BARU 👇
            short_description = data.get("short_description", "") 
            category = data.get("category", "General") 
            # 👆 ---------------- 👆
            description = data.get("description")
            contact_info = data.get("contact_info")
            fitness_spot_id = data.get("fitness_spot_id")
            schedule = data.get("schedule")
            image_data = data.get("image")

            from home.models import FitnessSpot
            fitness_spot = FitnessSpot.objects.get(place_id=fitness_spot_id)

            image_file = None
            if image_data and isinstance(image_data, str) and ";base64," in image_data:
                format, imgstr = image_data.split(';base64,') 
                ext = format.split('/')[-1] 
                image_file = ContentFile(base64.b64decode(imgstr), name=f"{name}_image.{ext}")

            new_community = Community.objects.create(
                name=name,
                # 👇 SIMPAN KE DATABASE 👇
                short_description=short_description,
                category=category,
                # 👆 --------------------- 👆
                description=description,
                contact_info=contact_info,
                fitness_spot=fitness_spot,
                schedule=schedule,
                image=image_file
            )

            if request.user.is_authenticated:
                new_community.admins.add(request.user)
                new_community.members.add(request.user)
                new_community.save()

            return JsonResponse({"status": "success", "message": "Komunitas berhasil dibuat!"}, status=200)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=401)

# --- LIST COMMUNITY (Perbaikan Error 'str' object) ---
def communities_json(request):
    communities = Community.objects.all().order_by('-created_at')
    data = []
    for c in communities:
        data.append({
            "id": c.id,
            "name": c.name,
            
            # 👇 INI DIA PERBAIKANNYA (Hapus .name) 👇
            "category": c.category if c.category else "General", 
            # 👆 ----------------------------------- 👆
            
            # 👇 TAMBAHKAN INI BIAR MUNCUL DI LIST 👇
            "short_description": c.short_description,
            # 👆 ----------------------------------- 👆

            "description": c.description,
            "contact_info": c.contact_info,
            "members_count": c.members.count(),
            "image": c.image.url if c.image else None,
            "fitness_spot": {
                "id": str(c.fitness_spot.pk),
                "name": c.fitness_spot.name,
                "place_id": c.fitness_spot.place_id,
                "address": c.fitness_spot.address
            } if c.fitness_spot else None,
            
            "is_member": c.is_member(request.user) if request.user.is_authenticated else False,
        })
    return JsonResponse(data, safe=False)

# --- DETAIL COMMUNITY (Perbaikan Error 'str' object) ---
def community_detail_json(request, pk):
    try:
        c = Community.objects.get(pk=pk)
        
        all_participants = (c.members.all() | c.admins.all()).distinct()
        
        members_data = []
        for p in all_participants:
            members_data.append({
                "username": p.username,
                "is_admin": c.admins.filter(pk=p.pk).exists() 
            })

        data = {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            
            # 👇 TAMBAHKAN INI JUGA DI DETAIL 👇
            "short_description": c.short_description,
            # 👆 ----------------------------- 👆

            "contact_info": c.contact_info,
            
            # 👇 INI JUGA PERBAIKANNYA (Hapus .name) 👇
            "category": c.category if c.category else "General",
            # 👆 ----------------------------------- 👆

            "members_count": all_participants.count(),
            "image": c.image.url if c.image else None,
            "schedule": c.schedule if c.schedule else "",
            "members": members_data, 
            "fitness_spot": {
                "id": str(c.fitness_spot.pk),
                "name": c.fitness_spot.name,
                "place_id": c.fitness_spot.place_id,
                "address": c.fitness_spot.address
            } if c.fitness_spot else None,
            "has_joined": c.is_member(request.user) if request.user.is_authenticated else False,
            "is_admin": c.is_admin(request.user) if request.user.is_authenticated else False,
        }
        return JsonResponse(data, safe=False)
    except Community.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)
    
@csrf_exempt
def edit_community_flutter(request, community_id):
    if request.method == 'POST':
        try:
            print(f"\n🕵️‍♀️ DEBUG EDIT: Menerima request untuk ID {community_id}")
            
            # 1. Cek Komunitas
            try:
                community = Community.objects.get(pk=community_id)
            except Community.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Komunitas tidak ditemukan."}, status=404)
            
            # 2. Cek Admin
            if not community.is_admin(request.user):
                return JsonResponse({"status": "error", "message": "Anda bukan admin komunitas ini."}, status=403)

            # 👇 3. LOGIKA BACA DATA (OMNIVORA: JSON atau FORM DATA) 👇
            data = None
            try:
                # Coba baca sebagai JSON
                data = json.loads(request.body)
                print("✅ Data terbaca sebagai JSON")
            except:
                # Kalau gagal, baca sebagai Form Data (request.POST)
                data = request.POST
                print("✅ Data terbaca sebagai Form Data")
            
            if not data:
                return JsonResponse({"status": "error", "message": "Tidak ada data yang dikirim."}, status=400)
            # 👆 -------------------------------------------------- 👆

            # 4. Update Field Teks (Pakai .get biar aman)
            community.name = data.get("name", community.name)
            community.description = data.get("description", community.description)
            community.contact_info = data.get("contact_info", community.contact_info)
            community.short_description = data.get("short_description", community.short_description)
            community.category = data.get("category", community.category)
            community.schedule = data.get("schedule", community.schedule)
            
            # 5. Update Lokasi
            fitness_spot_id = data.get("fitness_spot_id")
            if fitness_spot_id:
                try:
                    from home.models import FitnessSpot
                    # Pastikan fitness_spot_id tidak kosong/null string
                    if fitness_spot_id != "null" and fitness_spot_id != "":
                        community.fitness_spot = FitnessSpot.objects.get(place_id=fitness_spot_id)
                except FitnessSpot.DoesNotExist:
                    print(f"⚠️ Lokasi {fitness_spot_id} tidak ditemukan.")
                    pass 

            # 6. Update Gambar
            image_data = data.get("image")
            # Cek apakah string Base64 valid
            if image_data and isinstance(image_data, str) and ";base64," in image_data:
                try:
                    format, imgstr = image_data.split(';base64,') 
                    ext = format.split('/')[-1] 
                    file_name = f"{community.name}_edit_{community.id}.{ext}"
                    community.image = ContentFile(base64.b64decode(imgstr), name=file_name)
                    print("📸 Gambar berhasil di-update")
                except Exception as img_error:
                    print(f"❌ Gagal update gambar: {img_error}")

            # 7. SIMPAN!
            community.save()
            print("✅ Berhasil simpan perubahan!")
            
            return JsonResponse({"status": "success", "message": "Komunitas berhasil diupdate!"}, status=200)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ ERROR FATAL DI EDIT: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=401)

# 1. API DELETE COMMUNITY
@csrf_exempt
def delete_community(request, community_id):
    if request.method == 'POST': # Pakai POST biar aman dari CSRF di mobile
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error", "message": "Belum login"}, status=401)

            community = get_object_or_404(Community, pk=community_id)

            # Cek apakah yang request adalah Admin
            if not community.is_admin(request.user):
                return JsonResponse({"status": "error", "message": "Hanya admin yang bisa menghapus"}, status=403)

            community.delete()
            return JsonResponse({"status": "success", "message": "Komunitas berhasil dihapus"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

# 2. API PROMOTE MEMBER JADI ADMIN
@csrf_exempt
def promote_admin(request, community_id):
    if request.method == 'POST':
        try:
            # 1. Cek Login
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error", "message": "Belum login"}, status=401)

            community = get_object_or_404(Community, pk=community_id)

            # 2. Cek Permission
            if not community.is_admin(request.user):
                return JsonResponse({"status": "error", "message": "Anda bukan admin"}, status=403)

            # 👇 3. LOGIKA BACA DATA (OMNIVORA) 👇
            target_username = None
            
            # Cara A: Coba baca sebagai JSON
            try:
                data = json.loads(request.body)
                target_username = data.get('username')
            except:
                pass
            
            # Cara B: Kalau JSON gagal, coba baca sebagai Form Data
            if not target_username:
                target_username = request.POST.get('username')
            
            # CCTV DEBUG
            print(f"🕵️‍♀️ DEBUG PROMOTE: Username yang diterima = '{target_username}'")
            
            if not target_username:
                return JsonResponse({"status": "error", "message": "Username tidak dikirim oleh aplikasi"}, status=400)
            # 👆 -------------------------------- 👆

            # 4. Cari User & Eksekusi
            try:
                target_user = User.objects.get(username=target_username)
                community.admins.add(target_user)
                community.save()
                
                print(f"✅ SUKSES: {target_username} jadi admin!")
                return JsonResponse({"status": "success", "message": f"{target_username} sekarang adalah Admin"}, status=200)
                
            except User.DoesNotExist:
                return JsonResponse({"status": "error", "message": f"User '{target_username}' tidak ditemukan"}, status=404)

        except Exception as e:
            print(f"❌ ERROR SYSTEM: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)