from django.urls import path
from . import views

urlpatterns = [
    path('', views.radar_index, name='radar_index'),
    path('landing/', views.landing_page_view, name='landing_page'),
    path('api/live/', views.api_live, name='api_live'),
]

