from BlognEvent.models import Event,Blogs
from django.forms import ModelForm
from django import forms
from django.utils.html import strip_tags

class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ["name","image","description","starting_date","ending_date"]
        widgets = {
            'starting_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ending_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean_name(self):
        title = self.cleaned_data["name"]
        return strip_tags(title)

    def clean_description(self):
        content = self.cleaned_data["description"]
        return strip_tags(content)
    
class BlogsForm(ModelForm):
    class Meta:
        model =Blogs
        fields = ["title","image","body"]

    def clean_title(self):
        title = self.cleaned_data["title"]
        return strip_tags(title)

    def clean_body(self):
        content = self.cleaned_data["body"]
        return strip_tags(content)
