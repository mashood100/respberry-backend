from django.core.management.base import BaseCommand
from gamehub.models import GameContent, GameSession


class Command(BaseCommand):
    help = 'Create sample content for demonstration'

    def handle(self, *args, **options):
        # Create sample content items
        sample_contents = [
            {
                'title': 'Welcome to Game Hub!',
                'content_type': 'text',
                'text_content': 'Welcome to the Raspberry Pi Game Hub! This is a demonstration of real-time content synchronization between your Pi and mobile devices.',
                'background_color': '#4CAF50',
                'text_color': '#ffffff',
                'font_size': 32,
                'is_active': True,
            },
            {
                'title': 'Game Instructions',
                'content_type': 'text',
                'text_content': 'Scan the QR code with your phone to connect to this game hub. Your phone will show the same content as displayed here in real-time!',
                'background_color': '#2196F3',
                'text_color': '#ffffff',
                'font_size': 28,
            },
            {
                'title': 'Fun Facts',
                'content_type': 'text',
                'text_content': '🎮 This system works entirely on your local network - no internet needed!\n\n🚀 Content updates happen in real-time using WebSockets\n\n📱 Multiple devices can connect simultaneously',
                'background_color': '#FF9800',
                'text_color': '#ffffff',
                'font_size': 24,
            },
            {
                'title': 'System Status',
                'content_type': 'text',
                'text_content': '✅ Raspberry Pi Game Hub is running\n✅ WebSocket connections active\n✅ Ready for device connections\n\nEnjoy your synchronized gaming experience!',
                'background_color': '#9C27B0',
                'text_color': '#ffffff',
                'font_size': 26,
            },
            {
                'title': 'Technical Demo',
                'content_type': 'text',
                'text_content': 'This demonstration shows how you can create a local hub for multiplayer games or interactive experiences using a Raspberry Pi.',
                'background_color': '#607D8B',
                'text_color': '#ffffff',
                'font_size': 30,
            },
        ]

        # Create or update sample content
        for content_data in sample_contents:
            content, created = GameContent.objects.get_or_create(
                title=content_data['title'],
                defaults=content_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created content: {content.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Content already exists: {content.title}')
                )

        # Create or get active session
        session, created = GameSession.objects.get_or_create(
            name='Demo Session',
            defaults={
                'is_active': True,
                'max_connected_devices': 0,
                'qr_code_scans': 0,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created session: {session.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Session already exists: {session.name}')
            )

        self.stdout.write(
            self.style.SUCCESS('Sample data creation complete!')
        )
        self.stdout.write(
            'You can now start the server with: python3 manage.py runserver 0.0.0.0:8000'
        ) 