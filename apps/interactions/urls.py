from django.urls import path
from . import views

urlpatterns = [
    path('gig/<int:id>/checkin/', views.checkin_gig_view, name='checkin_gig'),
    path('gig/<int:id>/rate/', views.rate_band_view, name='rate_band'),
    path('gig/<int:id>/simpan/', views.save_gig_view, name='save_gig'),
    path('gig/<int:id>/kalender.ics', views.export_calendar_ics_view, name='export_calendar_ics'),
    path('saya/tersimpan/', views.saved_gigs_list_view, name='saved_gigs_list'),
    path('peringkat/', views.leaderboard_view, name='leaderboard'),
    path('musisi/dashboard/', views.dashboard_band_view, name='dashboard_band'),
]

