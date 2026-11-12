"""
URL configuration for livemusic_project project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import health_check_view

urlpatterns = [
    path('healthz', health_check_view, name='health_check'),
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('', include('apps.venues_gigs.urls')),
    path('', include('apps.interactions.urls')),
    path('', include('apps.radar_map.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
