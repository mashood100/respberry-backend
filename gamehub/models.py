from django.db import models
from django.utils import timezone
import uuid


class GameContent(models.Model):
    """Model to store dynamic content displayed on both Pi and mobile devices"""
    
    CONTENT_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('mixed', 'Mixed (Text + Image)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='text')
    text_content = models.TextField(blank=True)
    image = models.ImageField(upload_to='game_images/', blank=True, null=True)
    background_color = models.CharField(max_length=7, default='#ffffff')  # Hex color
    text_color = models.CharField(max_length=7, default='#000000')  # Hex color
    font_size = models.IntegerField(default=24)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Ensure only one content item is active at a time
        if self.is_active:
            GameContent.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class ConnectedDevice(models.Model):
    """Track connected devices for analytics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    connected_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-connected_at']
    
    def __str__(self):
        return f"Device {self.session_id} ({self.ip_address})"


class GameSession(models.Model):
    """Track game sessions and statistics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    max_connected_devices = models.IntegerField(default=0)
    qr_code_scans = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session: {self.name}"
    
    def end_session(self):
        self.ended_at = timezone.now()
        self.is_active = False
        self.save()
