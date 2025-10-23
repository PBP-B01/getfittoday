from django import forms
from .models import Community

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'contact_info', 'fitness_spot']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'border rounded p-2 w-full'}),
            'description': forms.Textarea(attrs={'class': 'border rounded p-2 w-full'}),
            'contact_info': forms.TextInput(attrs={'class': 'border rounded p-2 w-full'}),
            'fitness_spot': forms.Select(attrs={'class': 'border rounded p-2 w-full'}),
        }
