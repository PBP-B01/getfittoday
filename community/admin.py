from django.contrib import admin
from .models import CommunityCategory, Community, CommunityPost

class CommunityPostInline(admin.TabularInline):
    model = CommunityPost
    extra = 0
    fields = ('title', 'content')
    readonly_fields = ('created_at',)
    show_change_link = True 

@admin.register(CommunityCategory)
class CommunityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)} 


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'fitness_spot', 'category', 'admin_list', 'member_count', 'created_at')
    list_filter = ('category', 'fitness_spot')
    search_fields = ('name', 'description', 'fitness_spot__name')
    date_hierarchy = 'created_at'
    filter_horizontal = ('admins', 'members') 
    inlines = [CommunityPostInline]
    
    def admin_list(self, obj):
        return ", ".join([admin.username for admin in obj.admins.all()[:3]])
    admin_list.short_description = 'Admins'

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'community', 'created_at')
    list_filter = ('community',)
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'