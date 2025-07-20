import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameContent, ConnectedDevice


class ContentUpdateConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time content updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_group_name = 'content_updates'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current active content to newly connected client
        active_content = await self.get_active_content()
        if active_content:
            await self.send(text_data=json.dumps({
                'type': 'content_update',
                'content': active_content
            }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'get_active_content':
                # Send current active content
                active_content = await self.get_active_content()
                if active_content:
                    await self.send(text_data=json.dumps({
                        'type': 'content_update',
                        'content': active_content
                    }))
            
            elif message_type == 'device_heartbeat':
                # Update device activity
                session_id = text_data_json.get('session_id')
                if session_id:
                    await self.update_device_activity(session_id)
                    
        except json.JSONDecodeError:
            pass
    
    async def content_update(self, event):
        """Handle content update events from group"""
        content = event['content']
        
        # Send content to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'content_update',
            'content': content
        }))
    
    @database_sync_to_async
    def get_active_content(self):
        """Get current active content from database"""
        active_content = GameContent.objects.filter(is_active=True).first()
        
        if active_content:
            return {
                'id': str(active_content.id),
                'title': active_content.title,
                'content_type': active_content.content_type,
                'text_content': active_content.text_content,
                'image_url': active_content.image.url if active_content.image else None,
                'background_color': active_content.background_color,
                'text_color': active_content.text_color,
                'font_size': active_content.font_size,
            }
        return None
    
    @database_sync_to_async
    def update_device_activity(self, session_id):
        """Update device last seen timestamp"""
        try:
            device = ConnectedDevice.objects.get(session_id=session_id)
            device.save()  # This will update last_seen due to auto_now=True
        except ConnectedDevice.DoesNotExist:
            pass


class DeviceStatsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for device statistics updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_group_name = 'device_stats'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current stats to newly connected client
        stats = await self.get_device_stats()
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': stats
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def stats_update(self, event):
        """Handle stats update events from group"""
        stats = event['stats']
        
        # Send stats to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': stats
        }))
    
    @database_sync_to_async
    def get_device_stats(self):
        """Get current device statistics from database"""
        from .models import GameSession
        
        connected_devices = ConnectedDevice.objects.filter(is_active=True).count()
        active_session = GameSession.objects.filter(is_active=True).first()
        
        return {
            'connected_devices': connected_devices,
            'qr_scans': active_session.qr_code_scans if active_session else 0,
            'session_name': active_session.name if active_session else 'No active session',
        } 