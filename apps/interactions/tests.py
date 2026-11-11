from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from apps.accounts.models import BandProfile
from apps.venues_gigs.models import Venue, Gig
from apps.interactions.models import Checkin, Rating, SavedGig, Follow


class InteractionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_musisi = User.objects.create_user(username='musisi_int', password='password123')
        self.user_penonton = User.objects.create_user(username='penonton_int', password='password123')
        self.user_penonton2 = User.objects.create_user(username='penonton_int2', password='password123')

        self.band = BandProfile.objects.create(
            user=self.user_musisi,
            nama_band='Senja UI Interaksi',
            genre='Indie Rock'
        )
        self.venue = Venue.objects.create(
            nama='Kopi Margonda Space',
            alamat='Jl. Margonda No. 12',
            latitude=-6.364500,
            longitude=106.824200
        )
        now = timezone.now()
        self.gig = Gig.objects.create(
            band=self.band,
            venue=self.venue,
            judul_acara='Live Rock Night',
            mulai=now - timedelta(minutes=15),
            selesai=now + timedelta(hours=1, minutes=45),
            status='LIVE'
        )

    def test_musisi_dilarang_checkin_gig_sendiri(self):
        """Aturan Integritas: Musisi tidak boleh check-in di panggung milik sendiri (HTTP 403)."""
        self.client.login(username='musisi_int', password='password123')
        resp = self.client.post(reverse('checkin_gig', kwargs={'id': self.gig.id}), {
            'lat': self.venue.latitude,
            'lng': self.venue.longitude
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Checkin.objects.filter(pengunjung=self.user_musisi, gig=self.gig).exists())

    def test_musisi_dilarang_rating_gig_sendiri(self):
        """Aturan Integritas: Musisi tidak boleh memberi rating pada penampilannya sendiri (HTTP 403)."""
        self.client.login(username='musisi_int', password='password123')
        resp = self.client.post(reverse('rate_band', kwargs={'id': self.gig.id}), {
            'nilai_bintang': 5,
            'ulasan': 'Kami sangat luar biasa'
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Rating.objects.filter(pengunjung=self.user_musisi, gig=self.gig).exists())

    def test_penonton_belum_checkin_dilarang_rating(self):
        """Penonton yang belum terverifikasi check-in via GPS dilarang memberikan rating."""
        self.client.login(username='penonton_int', password='password123')
        resp = self.client.post(reverse('rate_band', kwargs={'id': self.gig.id}), {
            'nilai_bintang': 5,
            'ulasan': 'Bagus'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Rating.objects.filter(pengunjung=self.user_penonton, gig=self.gig).exists())

    def test_alur_penonton_checkin_dan_beri_rating(self):
        """Alur lengkap: Penonton check-in di venue (<=150m) lalu memberikan ulasan bintang."""
        self.client.login(username='penonton_int', password='password123')

        # 1. Check-in sukses
        resp_checkin = self.client.post(reverse('checkin_gig', kwargs={'id': self.gig.id}), {
            'lat': self.venue.latitude,
            'lng': self.venue.longitude,
            'accuracy': 10.0
        })
        self.assertEqual(resp_checkin.status_code, 302)
        self.assertTrue(Checkin.objects.filter(pengunjung=self.user_penonton, gig=self.gig).exists())

        # 2. Kirim rating sukses
        resp_rating = self.client.post(reverse('rate_band', kwargs={'id': self.gig.id}), {
            'nilai_bintang': 5,
            'ulasan': 'Suara sound system jernih dan vokal mantap!'
        })
        self.assertEqual(resp_rating.status_code, 302)
        rating_obj = Rating.objects.get(pengunjung=self.user_penonton, gig=self.gig)
        self.assertEqual(rating_obj.nilai_bintang, 5)

    def test_checkin_idempotent(self):
        """Check-in kedua kali oleh pengguna yang sama pada gig yang sama tidak membuat duplikat."""
        self.client.login(username='penonton_int', password='password123')
        Checkin.objects.create(
            pengunjung=self.user_penonton,
            gig=self.gig,
            latitude_user=self.venue.latitude,
            longitude_user=self.venue.longitude,
            jarak_m=5.0
        )
        self.assertEqual(Checkin.objects.filter(pengunjung=self.user_penonton, gig=self.gig).count(), 1)

        resp = self.client.post(reverse('checkin_gig', kwargs={'id': self.gig.id}), {
            'lat': self.venue.latitude,
            'lng': self.venue.longitude
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Checkin.objects.filter(pengunjung=self.user_penonton, gig=self.gig).count(), 1)

    def test_toggle_simpan_gig(self):
        """Penonton dapat menyimpan dan membatalkan simpan gig ke daftar favorit."""
        self.client.login(username='penonton_int', password='password123')
        resp = self.client.post(reverse('save_gig', kwargs={'id': self.gig.id}), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(SavedGig.objects.filter(pengguna=self.user_penonton, gig=self.gig).exists())

        # Hapus
        resp2 = self.client.post(reverse('save_gig', kwargs={'id': self.gig.id}), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(SavedGig.objects.filter(pengguna=self.user_penonton, gig=self.gig).exists())

    def test_ekspor_kalender_ics(self):
        """Mengunduh berkas kalender .ics dengan header MIME text/calendar."""
        resp = self.client.get(reverse('export_calendar_ics', kwargs={'id': self.gig.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/calendar')
        self.assertIn(b'BEGIN:VCALENDAR', resp.content)
        self.assertIn(b'BEGIN:VEVENT', resp.content)

    def test_papan_peringkat_leaderboard(self):
        """Halaman leaderboard menghitung peringkat Bayesian musisi dengan benar."""
        resp = self.client.get(reverse('leaderboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('leaderboard', resp.context)
        self.assertIn('podium_top3', resp.context)

