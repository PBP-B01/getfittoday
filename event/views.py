from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
import json
from .models import Event
from community.models import Community
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Community, Event
from django.utils.dateparse import parse_datetime


def event_list(request):
    name_filter = request.GET.get('name', '').strip()
    location_filter = request.GET.get('location', '').strip()
    date_sort = request.GET.get('date_sort', 'newest')
    community_filter = request.GET.get('community', '').strip()
    status_filter = request.GET.get('status', 'all').strip()
    my_events = request.GET.get('my_events', '').strip()

    from_community_id = request.GET.get('from_community', '').strip()
    from_community_name = None
    
    if from_community_id:
        try:
            from_comm = Community.objects.get(id=from_community_id)
            from_community_name = from_comm.name
        except Community.DoesNotExist:
            from_community_id = None

    events = Event.objects.all().select_related('community', 'created_by')

    if my_events and request.user.is_authenticated:
        user_communities = Community.objects.filter(admins=request.user)
        events = events.filter(community__in=user_communities)

    if name_filter:
        events = events.filter(name__icontains=name_filter)
    
    if location_filter:
        events = events.filter(location__icontains=location_filter)
    
    if community_filter:
        events = events.filter(community__name__icontains=community_filter)

    now = timezone.now()
    if status_filter == 'upcoming':
        events = events.filter(date__gt=now)
    elif status_filter == 'past':
        events = events.filter(date__lte=now)

    if date_sort == 'newest':
        events = events.order_by('-created_at')
    elif date_sort == 'soonest':
        events = events.order_by('date')
    elif date_sort == 'latest':
        events = events.order_by('-date')
    else:
        events = events.order_by('date')

    events_data = []
    for event in events:
        local_date = timezone.localtime(event.date)
        
        events_data.append({
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'date': local_date.strftime('%Y-%m-%d %H:%M'),
            'date_input': local_date.strftime('%Y-%m-%dT%H:%M'),
            'location': event.location,
            'community_id': event.community.id,
            'community_name': event.community.name,
            'created_by': event.created_by.username,
            'can_edit': event.can_edit(request.user),
            'can_delete': event.can_delete(request.user),
            'can_join': event.can_join(request.user),
            'is_participant': event.user_is_participant(request.user),
            'participant_count': event.participants.count(),
            'registration_open': event.registration_open(),
            'is_past': event.is_past(),
        })

    all_communities = Community.objects.all().values('id', 'name').order_by('name')

    user_admin_communities = []
    if request.user.is_authenticated:
        user_admin_communities = Community.objects.filter(
            admins=request.user
        ).values('id', 'name')

    return render(request, 'event/event_list.html', {
        'events': events_data,
        'user_admin_communities': list(user_admin_communities),
        'all_communities': list(all_communities),
        'filter_name': name_filter,
        'filter_location': location_filter,
        'filter_date_sort': date_sort,
        'filter_community': community_filter,
        'filter_status': status_filter,
        'from_community_id': from_community_id,
        'from_community_name': from_community_name,
    })


@login_required
@require_POST
def create_event(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description')
        date = data.get('date')
        location = data.get('location')
        community_id = data.get('community')
        registration_deadline = data.get('registration_deadline')

        if not all([name, description, date, location, community_id]):
            return JsonResponse({
                'status': 'error', 
                'message': 'Semua field wajib diisi.'
            }, status=400)

        community = get_object_or_404(Community, pk=community_id)

        if not community.is_admin(request.user) and not request.user.is_staff:
            return JsonResponse({
                'status': 'error', 
                'message': 'Hanya admin komunitas yang bisa membuat event.'
            }, status=403)

        event_date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        event_date = timezone.make_aware(event_date, timezone.get_current_timezone())
        
        reg_deadline = None
        if registration_deadline:
            reg_deadline = datetime.strptime(registration_deadline, '%Y-%m-%dT%H:%M')
            reg_deadline = timezone.make_aware(reg_deadline, timezone.get_current_timezone())

        event = Event.objects.create(
            name=name,
            description=description,
            date=event_date,
            location=location,
            community=community,
            created_by=request.user,
            registration_deadline=reg_deadline
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Event "{event.name}" berhasil dibuat.',
            'event_id': event.id
        })
    except Community.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Komunitas tidak ditemukan.'
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Format tanggal tidak valid: {str(e)}'
        }, status=400)
    except Exception as e:
        print(f"Error creating event: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def edit_event(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)

        if not event.can_edit(request.user):
            return JsonResponse({
                'status': 'error', 
                'message': 'Kamu tidak memiliki izin untuk mengedit event ini.'
            }, status=403)

        data = json.loads(request.body)

        if 'name' in data:
            event.name = data['name']
        if 'description' in data:
            event.description = data['description']
        if 'location' in data:
            event.location = data['location']

        if 'date' in data and data['date']:
            event_date = datetime.strptime(data['date'], '%Y-%m-%dT%H:%M')
            event.date = timezone.make_aware(event_date, timezone.get_current_timezone())
        
        if 'registration_deadline' in data:
            if data['registration_deadline']:
                reg_deadline = datetime.strptime(data['registration_deadline'], '%Y-%m-%dT%H:%M')
                event.registration_deadline = timezone.make_aware(reg_deadline, timezone.get_current_timezone())
            else:
                event.registration_deadline = None
        
        event.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Event berhasil diperbarui.'
        })
    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Format tanggal tidak valid: {str(e)}'
        }, status=400)
    except Exception as e:
        print(f"Error editing event {event_id}: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_event(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)

        if not event.can_delete(request.user):
            return JsonResponse({
                'status': 'error', 
                'message': 'Kamu tidak memiliki izin untuk menghapus event ini.'
            }, status=403)

        event_name = event.name
        event.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Event "{event_name}" telah dihapus.'
        })
    except Exception as e:
        print(f"Error deleting event {event_id}: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def join_event(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)

        if not event.can_join(request.user):
            if event.user_is_participant(request.user):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Kamu sudah terdaftar di event ini.'
                }, status=400)
            elif not event.registration_open():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Pendaftaran event sudah ditutup.'
                }, status=400)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Kamu tidak bisa bergabung ke event ini.'
                }, status=400)

        event.participants.add(request.user)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Berhasil bergabung ke event "{event.name}"!',
            'participant_count': event.participants.count()
        })
    except Exception as e:
        print(f"Error joining event {event_id}: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def leave_event(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)
        if not event.user_is_participant(request.user):
            return JsonResponse({
                'status': 'error',
                'message': 'Kamu belum terdaftar di event ini.'
            }, status=400)
        if event.is_past() or event.is_ongoing():
            return JsonResponse({
                'status': 'error',
                'message': 'Event sudah dimulai, kamu tidak bisa keluar.'
            }, status=400)

        event.participants.remove(request.user)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Berhasil keluar dari event "{event.name}".',
            'participant_count': event.participants.count()
        })
    except Exception as e:
        print(f"Error leaving event {event_id}: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
def get_event_detail(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)
        local_date = timezone.localtime(event.date)
        
        return JsonResponse({
            'status': 'success',
            'event': {
                'id': event.id,
                'name': event.name,
                'description': event.description,
                'date': local_date.strftime('%Y-%m-%d %H:%M'),
                'date_input': local_date.strftime('%Y-%m-%dT%H:%M'),
                'location': event.location,
                'community_id': event.community.id,
                'community_name': event.community.name,
                'can_edit': event.can_edit(request.user),
                'can_join': event.can_join(request.user),
                'is_participant': event.user_is_participant(request.user),
                'participant_count': event.participants.count(),
                'registration_open': event.registration_open(),
                'is_past': event.is_past(),
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def community_events_api(request, community_id):
    try:
        community = get_object_or_404(Community, id=community_id)
        events = Event.objects.filter(community=community).order_by('date')
        
        now = timezone.now()
        events_data = []
        
        for event in events:
            local_date = timezone.localtime(event.date)
            events_data.append({
                'id': event.id,
                'name': event.name,
                'description': event.description,
                'date': local_date.strftime('%Y-%m-%d %H:%M'),
                'date_display': local_date.strftime('%d %B %Y, %H:%M'),
                'location': event.location,
                'participant_count': event.participants.count(),
                'is_past': event.is_past(),
                'registration_open': event.registration_open(),
                'can_join': event.can_join(request.user),
                'is_participant': event.user_is_participant(request.user),
                'can_edit': event.can_edit(request.user),
            })
        
        return JsonResponse({
            'success': True,
            'community_name': community.name,
            'events': events_data
        })
    except Exception as e:
        print(f"Error fetching community events for community_id {community_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
<<<<<<< HEAD
>>>>>>> master
        }, status=500)
=======
        }, status=500)

# 1. API untuk Dropdown Komunitas (Hanya yang dia jadi Admin)
@login_required
def get_user_admin_communities(request):
    # Ambil komunitas dimana user terdaftar sebagai admin
    # Asumsi: Ada relasi ManyToMany 'admins' di model Community
    communities = Community.objects.filter(admins=request.user).values('id', 'name')
    
    return JsonResponse({
        'status': 'success',
        'communities': list(communities)
    })

@csrf_exempt
def create_event_flutter(request):
    if request.method == 'POST':
        try:
            # 1. Pastikan User sudah Login
            # (Jika session mati/belum login, request.user akan AnonymousUser dan bakal error saat save)
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error", "message": "Anda harus login terlebih dahulu."}, status=401)

            data = json.loads(request.body)
            
            print("DATA DITERIMA:", data) # Debugging

            # 2. Ambil Data Dasar
            name = data.get("name")
            description = data.get("description")
            date_str = data.get("date")
            location = data.get("location")
            community_id = data.get("community_id")

            # 3. Validasi Data Wajib
            if not all([name, description, date_str, location, community_id]):
                return JsonResponse({"status": "error", "message": "Semua field wajib diisi!"}, status=400)

            # 4. Ambil Object Community dari ID
            try:
                community_obj = Community.objects.get(id=community_id)
            except Community.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Komunitas tidak ditemukan"}, status=404)

            # 5. Konversi Tanggal (Format dari Flutter: "2025-12-13 17:08:00")
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return JsonResponse({"status": "error", "message": "Format tanggal salah"}, status=400)

            # 6. SIMPAN KE DATABASE (Ini Bagian Kritisnya)
            new_event = Event.objects.create(
                created_by=request.user,  # <--- Sesuai model kamu: 'created_by'
                community=community_obj,  # <--- Sesuai model kamu: butuh object, bukan ID
                name=name,
                description=description,
                date=date_obj,
                location=location,
            )

            new_event.save()

            return JsonResponse({"status": "success", "message": "Event berhasil dibuat!"}, status=200)

        except Exception as e:
            print("❌ ERROR SAAT SAVE:", str(e))
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Metode harus POST"}, status=405)

def show_event_api(request):
    # Ambil semua event, urutkan dari yang terbaru
    events = Event.objects.all().order_by('-date')
    
    data = []
    for event in events:
        # Cek apakah user yang request adalah pemilik/admin
        is_creator = request.user == event.created_by
        is_community_admin = event.community.is_admin(request.user) if request.user.is_authenticated else False
        is_joined = event.user_is_participant(request.user) if request.user.is_authenticated else False
        
        data.append({
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "date": event.date.strftime("%Y-%m-%d %H:%M:%S"), # Format string
            "location": event.location,
            "community_name": event.community.name,
            "participant_count": event.participant_count(),
            "can_edit": is_creator or is_community_admin, # Logic tombol Edit
            "is_active": event.is_ongoing() or event.registration_open(), # Logic status
            "is_joined": is_joined,
        })
        
    return JsonResponse(data, safe=False)

@csrf_exempt
def join_event_flutter(request, event_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Harap login dulu."}, status=401)
            
        try:
            event = Event.objects.get(id=event_id)
            
            # Cek apakah user sudah join?
            if event.participants.filter(id=request.user.id).exists():
                return JsonResponse({"status": "error", "message": "Anda sudah join event ini!"}, status=400)
                
            # LOGIKA JOIN:
            event.participants.add(request.user)
            return JsonResponse({"status": "success", "message": "Berhasil join event!"}, status=200)
            
        except Event.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Event tidak ditemukan."}, status=404)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def leave_event_flutter(request, event_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Harap login dulu."}, status=401)
            
        try:
            event = Event.objects.get(id=event_id)
            
            # Cek apakah user memang peserta?
            if not event.participants.filter(id=request.user.id).exists():
                return JsonResponse({"status": "error", "message": "Anda belum join event ini."}, status=400)
                
            # LOGIKA LEAVE:
            event.participants.remove(request.user)
            return JsonResponse({"status": "success", "message": "Berhasil keluar dari event."}, status=200)
            
        except Event.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Event tidak ditemukan."}, status=404)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def edit_event_flutter(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(id=event_id)
            data = json.loads(request.body)
            
            # Cek apakah user berhak edit (Admin/Creator)
            # Sesuaikan logic ini dengan model kamu
            # if event.created_by != request.user: 
            #    return JsonResponse({"status": "error", "message": "Tidak ada izin"}, status=403)

            # Update Field
            event.name = data.get("name", event.name)
            event.description = data.get("description", event.description)
            event.location = data.get("location", event.location)
            
            # Update Tanggal (Perlu parsing ulang)
            if "date" in data:
                event.date = datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S")

            event.save()
            
            return JsonResponse({"status": "success", "message": "Event berhasil diupdate!"}, status=200)

        except Event.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Event tidak ditemukan"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def delete_event_flutter(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(id=event_id)
            event.delete()
            return JsonResponse({"status": "success", "message": "Event berhasil dihapus!"}, status=200)
        except Event.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Event tidak ditemukan"}, status=404)
    
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
>>>>>>> 6095427 (Integrasi community dan community event (django))
