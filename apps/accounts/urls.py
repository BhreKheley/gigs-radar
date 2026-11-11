from django.urls import path
from . import views

urlpatterns = [
    path('akun/daftar/', views.daftar_view, name='daftar'),
    path('akun/masuk/', views.masuk_view, name='masuk'),
    path('akun/keluar/', views.keluar_view, name='keluar'),
    path('akun/profil/', views.profil_band_view, name='akun_profil'),
    path('band/profil/', views.profil_band_view, name='profil_band'),
    path('band/<slug:slug>/follow/', views.toggle_follow_view, name='toggle_follow'),
    path('band/<slug:slug>/', views.band_detail_view, name='band_detail'),
]

