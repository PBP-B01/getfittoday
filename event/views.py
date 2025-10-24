from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.utils import timezone
import json
from .models import Event, Community


def event_list(request):
    events = Event.objects.all().order_by('date')

    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'date': event.date.strftime('%Y-%m-%d %H:%M'),
            'location': event.location,
            'community_name': event.community.name,
            'created_by': event.created_by.username,
            'can_edit': event.can_edit(request.user),
            'can_delete': event.can_delete(request.user),
        })

    return render(request, 'event/event_list.html', {
        'events': events_data,
    })


@login_required
@require_POST
def create_event(request):
    """
    Admin komunitas membuat event baru.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description')
        date = data.get('date')
        location = data.get('location')
        community_id = data.get('community')

        if not all([name, description, date, location, community_id]):
            return JsonResponse({
                'status': 'error', 
                'message': 'Semua field wajib diisi.'
            }, status=400)

        community = get_object_or_404(Community, pk=community_id)

        if not community.is_admin(request.user) and not request.user.is_staff:
            return JsonResponse({
                'status': 'error', 
                'message': 'Kamu bukan admin komunitas ini.'
            }, status=403)

        event_date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        event_date = timezone.make_aware(event_date)

        event = Event.objects.create(
            name=name,
            description=description,
            date=event_date,
            location=location,
            community=community,
            created_by=request.user
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
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def edit_event(request, event_id):
    """
    Edit event - hanya boleh admin komunitas atau platform admin.
    """
    try:
        event = get_object_or_404(Event, id=event_id)

        if not event.can_edit(request.user):
            return JsonResponse({
                'status': 'error', 
                'message': 'Kamu tidak memiliki izin untuk mengedit event ini.'
            }, status=403)

        data = json.loads(request.body)

        event.name = data.get('name', event.name)
        event.description = data.get('description', event.description)
        event.location = data.get('location', event.location)

        if data.get('date'):
            event_date = datetime.strptime(data.get('date'), '%Y-%m-%dT%H:%M')
            event.date = timezone.make_aware(event_date)
        
        event.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Event berhasil diperbarui.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_event(request, event_id):
    """
    Hapus event - hanya boleh admin komunitas atau platform admin.
    """
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
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def join_event(request, event_id):
    """
    User bisa join event kalau belum dimulai.
    """
    try:
        event = get_object_or_404(Event, id=event_id)

        now = timezone.now()
        if event.date <= now:
            return JsonResponse({
                'status': 'error',
                'message': 'Event sudah dimulai, kamu tidak bisa bergabung lagi.'
            }, status=400)

        if event.participants.filter(id=request.user.id).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Kamu sudah bergabung di event ini.'
            }, status=400)

        event.participants.add(request.user)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Berhasil bergabung ke event "{event.name}"!'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, status=500)