
from django.contrib import admin
from django import forms
from .models import Admin

class AdminChangeForm(forms.ModelForm):
    password = forms.fields.CharField(
        label="Password",
        widget=forms.PasswordInput(render_value=False),
        help_text="Raw password will be hashed upon saving. Leave blank if you don't want to change it.",
        required=False
    )

    class Meta:
        model = Admin
        fields = ('name', 'password') 

    def save(self, commit=True):
        admin_instance = super().save(commit=False)
        if self.cleaned_data['password']:
            admin_instance.set_password(self.cleaned_data['password'])
        
        if commit:
            admin_instance.save()
        return admin_instance

class AdminUserAdmin(admin.ModelAdmin):
    form = AdminChangeForm 
    
    list_display = ('name',)
    
    fields = ('name', 'password')

    def save_model(self, request, obj, form, change):

        obj.save()


admin.site.register(Admin, AdminUserAdmin)