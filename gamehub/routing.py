from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/content-updates/$', consumers.ContentUpdateConsumer.as_asgi()),
    re_path(r'ws/device-stats/$', consumers.DeviceStatsConsumer.as_asgi()),
] 