from django.urls import path
from . import views

urlpatterns = [
    path('jadwal/', views.jadwal_list_view, name='jadwal_list'),
    path('gig/<int:id>/', views.gig_detail_view, name='gig_detail'),
    path('venue/tambah/', views.tambah_venue_view, name='tambah_venue'),
    path('api/venue/cek-duplikat/', views.cek_duplikat_venue_api, name='api_cek_duplikat_venue'),
    path('gig/buat/', views.buat_gig_view, name='buat_gig'),
    path('gig/<int:id>/golive/', views.golive_gig_view, name='golive_gig'),
    path('gig/<int:id>/perpanjang/', views.extend_gig_view, name='extend_gig'),
]

