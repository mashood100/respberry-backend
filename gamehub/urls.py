from django.urls import path
from . import views

app_name = 'gamehub'

urlpatterns = [
    # Main views
    path('', views.PiDisplayView.as_view(), name='pi_display'),
    path('mobile/', views.MobileDisplayView.as_view(), name='mobile_display'),
    path('admin-panel/', views.ContentManagementView.as_view(), name='content_management'),
    
    # API endpoints
    path('api/content/update/', views.api_update_content, name='api_update_content'),
    path('api/content/create/', views.api_create_content, name='api_create_content'),
    path('api/content/active/', views.api_get_active_content, name='api_get_active_content'),
    path('api/stats/', views.api_device_stats, name='api_device_stats'),
] 