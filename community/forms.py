from django import forms
from .models import Community

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = [
            'image', 
            'name', 
            'short_description', 
            'category', 
            'description', 
            'contact_info', 
            'schedule', 
            'fitness_spot'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#0E5A64] outline-none transition-all',
                'placeholder': 'Enter your community name'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#0E5A64] outline-none transition-all',
                'placeholder': 'Enter your community tagline (short description)'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#0E5A64] outline-none transition-all cursor-pointer'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#0E5A64] outline-none transition-all',
                'rows': 4,
                'placeholder': 'Tell us about your community...'
            }),
            'contact_info': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#0E5A64] outline-none transition-all',
                'placeholder': 'Enter your community Instagram or WhatsApp number'
            }),
            'schedule': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#0E5A64] outline-none transition-all',
                'rows': 3,
                'placeholder': 'Enter your community routine schedule'
            }),
            
            'fitness_spot': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:bg-white focus:border-[#0E5A64] outline-none transition-all cursor-pointer'
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'id_image'
            })
        }