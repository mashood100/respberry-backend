from django.contrib import admin
from .models import GameContent, ConnectedDevice, GameSession


@admin.register(GameContent)
class GameContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('content_type', 'is_active', 'created_at')
    search_fields = ('title', 'text_content')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content_type', 'is_active')
        }),
        ('Content', {
            'fields': ('text_content', 'image')
        }),
        ('Styling', {
            'fields': ('background_color', 'text_color', 'font_size')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_content', 'deactivate_content']
    
    def activate_content(self, request, queryset):
        # Deactivate all content first
        GameContent.objects.update(is_active=False)
        # Activate selected content (only the first one if multiple selected)
        content = queryset.first()
        if content:
            content.is_active = True
            content.save()
            self.message_user(request, f'"{content.title}" has been activated.')
        else:
            self.message_user(request, 'No content selected.')
    
    activate_content.short_description = "Activate selected content"
    
    def deactivate_content(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} content items have been deactivated.')
    
    deactivate_content.short_description = "Deactivate selected content"


@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'ip_address', 'is_active', 'connected_at', 'last_seen')
    list_filter = ('is_active', 'connected_at')
    search_fields = ('session_id', 'ip_address', 'user_agent')
    readonly_fields = ('id', 'session_id', 'ip_address', 'user_agent', 'connected_at', 'last_seen')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('session_id', 'ip_address', 'user_agent', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('connected_at', 'last_seen'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} devices marked as active.')
    
    mark_as_active.short_description = "Mark selected devices as active"
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} devices marked as inactive.')
    
    mark_as_inactive.short_description = "Mark selected devices as inactive"


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'started_at', 'ended_at', 'max_connected_devices', 'qr_code_scans')
    list_filter = ('is_active', 'started_at')
    search_fields = ('name',)
    readonly_fields = ('id', 'started_at', 'ended_at')
    
    fieldsets = (
        ('Session Information', {
            'fields': ('name', 'is_active')
        }),
        ('Statistics', {
            'fields': ('max_connected_devices', 'qr_code_scans')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'ended_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['end_session']
    
    def end_session(self, request, queryset):
        for session in queryset:
            session.end_session()
        self.message_user(request, f'{queryset.count()} sessions have been ended.')
    
    end_session.short_description = "End selected sessions"
