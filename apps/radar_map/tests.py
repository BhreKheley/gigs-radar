from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from apps.accounts.models import BandProfile
from apps.venues_gigs.models import Venue, Gig


class RadarMapTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_musisi = User.objects.create_user(username='musisi_map', password='password123')
        self.band = BandProfile.objects.create(
            user=self.user_musisi,
            nama_band='Margonda Indie Echoes',
            genre='Indie Rock'
        )
        self.venue = Venue.objects.create(
            nama='Kafe Margonda Pusat',
            alamat='Jl. Margonda No. 1',
            latitude=-6.364500,
            longitude=106.824200
        )
        now = timezone.now()
        self.gig = Gig.objects.create(
            band=self.band,
            venue=self.venue,
            judul_acara='Malam Live Margonda',
            mulai=now - timedelta(minutes=10),
            selesai=now + timedelta(hours=2),
            status='LIVE'
        )

    def test_halaman_landing_page(self):
        """Halaman landing page merender status 200 dan konteks statistik."""
        resp = self.client.get(reverse('landing_page'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('live_gigs_count', resp.context)
        self.assertIn('total_bands', resp.context)
        self.assertIn('total_venues', resp.context)

    def test_halaman_radar_map_index(self):
        """Halaman utama peta radar geospasial merender peta dan filter."""
        resp = self.client.get(reverse('radar_index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('presets_demo', resp.context)
        self.assertIn('genres_list', resp.context)

    def test_api_live_dalam_radius(self):
        """API geospasial mengembalikan gig jika user berada dalam radius pencarian."""
        # Lokasi user ~500m dari venue
        user_lat = -6.366000
        user_lng = 106.825000

        resp = self.client.get(reverse('api_live'), {
            'lat': user_lat,
            'lng': user_lng,
            'radius': 5  # 5 km
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data['gigs']) > 0)
        self.assertEqual(data['gigs'][0]['id'], self.gig.id)
        self.assertIn('jarak_km', data['gigs'][0])

    def test_api_live_diluar_radius(self):
        """API geospasial menyaring gig jika berada di luar radius (misal radius 100m, jarak 500m)."""
        user_lat = -6.375000
        user_lng = 106.835000

        resp = self.client.get(reverse('api_live'), {
            'lat': user_lat,
            'lng': user_lng,
            'radius': 0.1  # 100 meter
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['gigs']), 0)
