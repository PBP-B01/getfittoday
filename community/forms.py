# community/forms.py
from django import forms
from .models import Community

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'contact_info', 'fitness_spot', 'category']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'border rounded p-2 w-full text-black bg-gray-50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'border rounded p-2 w-full text-black bg-gray-50'
            }),
            'contact_info': forms.TextInput(attrs={
                'class': 'border rounded p-2 w-full text-black bg-gray-50'
            }),
            'fitness_spot': forms.HiddenInput(attrs={
                'id': 'id_fitness_spot'
            }),
            'category': forms.Select(attrs={
                'class': 'border rounded p-2 w-full text-black bg-gray-50'
            }),
        }