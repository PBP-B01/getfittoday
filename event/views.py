import json
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from .models import Event
from community.models import Community

User = get_user_model()

# --- WEB VIEWS (Django Template & AJAX) ---

def _has_admin_access(request) -> bool:
    return bool(
        request.session.get("is_admin", False)
        or (
            getattr(request, "user", None) is not None
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )
    )


def _admin_session_username(request) -> str | None:
    if not request.session.get("is_admin", False):
        return None
    name = request.session.get("admin_name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _get_or_create_admin_user(request):
    username = _admin_session_username(request)
    if not username:
        return None
    user, _created = User.objects.get_or_create(username=username)
    if _created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


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

    sort_mapping = {
        'newest': '-created_at',
        'soonest': 'date',
        'latest': '-date'
    }
    events = events.order_by(sort_mapping.get(date_sort, 'date'))

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
        user_admin_communities = Community.objects.filter(admins=request.user).values('id', 'name')

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
            return JsonResponse({'status': 'error', 'message': 'Semua field wajib diisi.'}, status=400)

        community = get_object_or_404(Community, pk=community_id)
        if not community.is_admin(request.user) and not request.user.is_staff:
            return JsonResponse({'status': 'error', 'message': 'Hanya admin komunitas yang bisa membuat event.'}, status=403)

        event_date = timezone.make_aware(datetime.strptime(date, '%Y-%m-%dT%H:%M'), timezone.get_current_timezone())
        
        reg_deadline = None
        if registration_deadline:
            reg_deadline = timezone.make_aware(datetime.strptime(registration_deadline, '%Y-%m-%dT%H:%M'), timezone.get_current_timezone())

        event = Event.objects.create(
            name=name,
            description=description,
            date=event_date,
            location=location,
            community=community,
            created_by=request.user,
            registration_deadline=reg_deadline
        )

        return JsonResponse({'status': 'success', 'message': f'Event "{event.name}" berhasil dibuat.', 'event_id': event.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def edit_event(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)
        if not event.can_edit(request.user):
            return JsonResponse({'status': 'error', 'message': 'Izin ditolak.'}, status=403)

        data = json.loads(request.body)
        event.name = data.get('name', event.name)
        event.description = data.get('description', event.description)
        event.location = data.get('location', event.location)

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
        return JsonResponse({'status': 'success', 'message': 'Event berhasil diperbarui.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not event.can_delete(request.user):
        return JsonResponse({'status': 'error', 'message': 'Izin ditolak.'}, status=403)
    event.delete()
    return JsonResponse({'status': 'success', 'message': 'Event telah dihapus.'})


@login_required
@require_POST
def join_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not event.can_join(request.user):
        if event.user_is_participant(request.user):
            message = 'Kamu sudah terdaftar di event ini.'
        elif not event.registration_open():
            message = 'Pendaftaran event sudah ditutup.'
        else:
            message = 'Kamu tidak bisa bergabung ke event ini.'
        return JsonResponse({'status': 'error', 'message': message}, status=400)

    event.participants.add(request.user)
    return JsonResponse({'status': 'success', 'message': f'Berhasil bergabung ke event "{event.name}"!', 'participant_count': event.participants.count()})


@login_required
@require_POST
def leave_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if not event.user_is_participant(request.user):
        return JsonResponse({'status': 'error', 'message': 'Kamu belum terdaftar.'}, status=400)
    if event.is_past() or event.is_ongoing():
        return JsonResponse({'status': 'error', 'message': 'Event sudah dimulai.'}, status=400)

    event.participants.remove(request.user)
    return JsonResponse({'status': 'success', 'message': 'Berhasil keluar.', 'participant_count': event.participants.count()})


@login_required
def get_event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    local_date = timezone.localtime(event.date)
    return JsonResponse({
        'status': 'success',
        'event': {
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'date': local_date.strftime('%Y-%m-%d %H:%M'),
            'location': event.location,
            'community_name': event.community.name,
            'can_edit': event.can_edit(request.user),
            'is_participant': event.user_is_participant(request.user),
            'participant_count': event.participants.count(),
        }
    })


def community_events_api(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    events = Event.objects.filter(community=community).order_by('date')
    events_data = []
    for event in events:
        local_date = timezone.localtime(event.date)
        events_data.append({
            'id': event.id,
            'name': event.name,
            'date': local_date.strftime('%Y-%m-%d %H:%M'),
            'location': event.location,
            'participant_count': event.participants.count(),
        })
    return JsonResponse({'success': True, 'community_name': community.name, 'events': events_data})


# --- FLUTTER API VIEWS ---

def get_user_admin_communities(request):
    if not (request.user.is_authenticated or _has_admin_access(request)):
        return JsonResponse({"status": "error", "message": "Harap login."}, status=401)

    if _has_admin_access(request):
        communities = Community.objects.all().values("id", "name")
    else:
        communities = Community.objects.filter(admins=request.user).values("id", "name")

    return JsonResponse({"status": "success", "communities": list(communities)})


@csrf_exempt
def create_event_flutter(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Metode harus POST"}, status=405)
    
    if not (request.user.is_authenticated or _has_admin_access(request)):
        return JsonResponse({"status": "error", "message": "Harap login."}, status=401)

    try:
        data = json.loads(request.body)
        community = get_object_or_404(Community, id=data.get("community_id"))
        
        # Timezone Aware Fix
        event_date = datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M:%S")
        aware_event_date = timezone.make_aware(event_date, timezone.get_current_timezone())

        created_by = request.user if request.user.is_authenticated else _get_or_create_admin_user(request)
        if created_by is None:
            return JsonResponse({"status": "error", "message": "Admin session invalid."}, status=401)

        new_event = Event.objects.create(
            created_by=created_by,
            community=community,
            name=data.get("name"),
            description=data.get("description"),
            date=aware_event_date,
            location=data.get("location"),
        )
        return JsonResponse({"status": "success", "message": "Event berhasil dibuat!"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def show_event_api(request):
    events = Event.objects.all().order_by('-date').select_related('community')
    data = []
    for event in events:
        is_authenticated = request.user.is_authenticated
        is_superadmin = _has_admin_access(request)
        can_manage = bool(is_superadmin or event.community.is_admin(request.user))
        admin_username = _admin_session_username(request)
        admin_user = (
            User.objects.filter(username=admin_username).first()
            if admin_username
            else None
        )
        if is_authenticated:
            is_joined = event.user_is_participant(request.user)
        elif admin_user is not None:
            is_joined = event.user_is_participant(admin_user)
        else:
            is_joined = False
        data.append({
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "date": timezone.localtime(event.date).strftime("%Y-%m-%d %H:%M:%S"),
            "location": event.location,
            "community_name": event.community.name,
            "participant_count": event.participants.count(),
            "can_edit": can_manage if (is_authenticated or is_superadmin) else False,
            "can_delete": can_manage if (is_authenticated or is_superadmin) else False,
            "is_active": not event.is_past(),
            "is_joined": is_joined,
            "is_superadmin": is_superadmin,
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
def join_event_flutter(request, event_id):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    join_user = None
    if request.user.is_authenticated:
        join_user = request.user
    elif _has_admin_access(request):
        join_user = _get_or_create_admin_user(request)
    if join_user is None:
        return JsonResponse({"status": "error", "message": "Harap login."}, status=401)
    
    event = get_object_or_404(Event, id=event_id)
    if event.participants.filter(id=join_user.id).exists():
        return JsonResponse({"status": "error", "message": "Sudah join."}, status=400)
    
    event.participants.add(join_user)
    return JsonResponse({"status": "success", "message": "Berhasil join!"}, status=200)


@csrf_exempt
def leave_event_flutter(request, event_id):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    leave_user = None
    if request.user.is_authenticated:
        leave_user = request.user
    elif _has_admin_access(request):
        admin_username = _admin_session_username(request)
        if admin_username:
            leave_user = User.objects.filter(username=admin_username).first()
    if leave_user is None:
        return JsonResponse({"status": "error", "message": "Harap login."}, status=401)
    
    event = get_object_or_404(Event, id=event_id)
    if not event.participants.filter(id=leave_user.id).exists():
        return JsonResponse({"status": "error", "message": "Belum join."}, status=400)
    event.participants.remove(leave_user)
    return JsonResponse({"status": "success", "message": "Berhasil keluar."}, status=200)


@csrf_exempt
def edit_event_flutter(request, event_id):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    
    event = get_object_or_404(Event, id=event_id)
    if not (_has_admin_access(request) or event.can_edit(request.user)):
        return JsonResponse({"status": "error", "message": "Izin ditolak."}, status=403)

    try:
        data = json.loads(request.body)
        event.name = data.get("name", event.name)
        event.description = data.get("description", event.description)
        event.location = data.get("location", event.location)
        
        if "date" in data:
            new_date = datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S")
            event.date = timezone.make_aware(new_date, timezone.get_current_timezone())

        event.save()
        return JsonResponse({"status": "success", "message": "Event berhasil diupdate!"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def delete_event_flutter(request, event_id):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    
    event = get_object_or_404(Event, id=event_id)
    if not (_has_admin_access(request) or event.can_delete(request.user)):
        return JsonResponse({"status": "error", "message": "Izin ditolak."}, status=403)
        
    event.delete()
    return JsonResponse({"status": "success", "message": "Event berhasil dihapus!"}, status=200)
