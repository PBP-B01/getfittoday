from django.shortcuts import render, redirect
from .models import Community
from .forms import CommunityForm

def community_list(request):
    communities = Community.objects.all()
    return render(request, 'community/community_list.html', {'communities': communities})

def add_community(request):
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('community_list')
    else:
        form = CommunityForm()
    return render(request, 'community/add_community.html', {'form': form})
