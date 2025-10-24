from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime
import json
from .models import Event, Community

# @login_required
def event_list(request):
    # events = Event.objects.all()
    # return render(request, 'events/event_list.html', {'events': events})
    events = [
    {
        'id': 1,
        'name': 'Morning Run UI',
        'description': 'Join us for a 5K fun run around campus!',
        'date': '2025-10-28 06:30',
        'location': 'Fasilkom UI',
        'created_by': 'admin'
    },
    {
        'id': 2,
        'name': 'Yoga Session',
        'description': 'Relax and stretch your body with community yoga.',
        'date': '2025-11-01 07:00',
        'location': 'Balairung UI',
        'created_by': 'user1'
    },
]

    # Simulasi user login
    class DummyUser:
        def __init__(self, username, is_authenticated, is_staff):
            self.username = username
            self.is_authenticated = is_authenticated
            self.is_staff = is_staff

    # Ganti ini sesuai role yang mau dites:
    # Guest → DummyUser('guest', False, False)
    # User biasa → DummyUser('user1', True, False)
    # Admin komunitas → DummyUser('admin', True, False)
    # Superuser → DummyUser('superadmin', True, True)
    dummy_user = DummyUser('user1', True, False)

    return render(request, 'event/event_list.html', {
        'events': events,
        'user': dummy_user,
        'csrf_token': 'dummy_token'  # biar gak error di fetch()
    })

# @login_required
@require_POST
def create_event(request):
    data = json.loads(request.body)
    name = data.get('name')
    description = data.get('description')
    date = data.get('date')
    location = data.get('location')
    community_id = data.get('community')

    if not all([name, description, date, location, community_id]):
        return JsonResponse({'status': 'error', 'message': 'All fields are required.'})

    try:
        community = Community.objects.get(pk=community_id)
        if community.admin != request.user:
            return JsonResponse({'status': 'error', 'message': 'You are not the admin of this community.'}, status=403)

        event = Event.objects.create(
            name=name,
            description=description,
            date=datetime.strptime(date, '%Y-%m-%dT%H:%M'),
            location=location,
            community=community,
            created_by=request.user
        )

        return JsonResponse({
            'status': 'success',
            'event': {
                'id': event.id,
                'name': event.name,
                'community': community.name,
                'location': event.location,
                'date': event.date.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# @login_required
@require_POST
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.created_by != request.user:
        return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)

    data = json.loads(request.body)
    event.name = data.get('name', event.name)
    event.description = data.get('description', event.description)
    event.date = datetime.strptime(data.get('date'), '%Y-%m-%dT%H:%M')
    event.location = data.get('location', event.location)
    event.save()

    return JsonResponse({'status': 'success', 'message': 'Event updated successfully'})

# @login_required
@require_POST
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.created_by != request.user:
        return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)

    event.delete()
    return JsonResponse({'status': 'success', 'message': 'Event deleted successfully'})
