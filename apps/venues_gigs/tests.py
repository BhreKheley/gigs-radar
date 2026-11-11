from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from apps.accounts.models import BandProfile
from apps.venues_gigs.models import Venue, Gig


class VenuesGigsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_musisi = User.objects.create_user(
            username='musisi_vg',
            password='password123'
        )
        self.band = BandProfile.objects.create(
            user=self.user_musisi,
            nama_band='Kukel Jazz Trio',
            genre='Jazz'
        )
        # Venue A: Kafe Margonda (-6.364500, 106.824200)
        self.venue_a = Venue.objects.create(
            nama='Kafe Margonda Raya',
            alamat='Jl. Margonda No. 100',
            latitude=-6.364500,
            longitude=106.824200,
            dibuat_oleh=self.user_musisi
        )

    def test_deteksi_duplikasi_venue_50_meter(self):
        """API pendeteksi duplikasi venue mengembalikan duplikat jika jarak <= 50 meter."""
        # Titik yang berjarak ~15 meter dari Venue A
        lat_dekat = -6.364510
        lng_dekat = 106.824210

        resp = self.client.get(reverse('api_cek_duplikat_venue'), {'lat': lat_dekat, 'lng': lng_dekat})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data['duplikat']) > 0)
        self.assertEqual(data['duplikat'][0]['id'], self.venue_a.id)

    def test_tidak_ada_duplikasi_jika_jarak_jauh(self):
        """Jika titik baru berjarak > 50 meter (misal 500m), tidak ada duplikasi."""
        # Titik berjarak ratusan meter
        lat_jauh = -6.370000
        lng_jauh = 106.830000

        resp = self.client.get(reverse('api_cek_duplikat_venue'), {'lat': lat_jauh, 'lng': lng_jauh})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['duplikat']), 0)

    def test_jadwal_gig_valid(self):
        """Musisi dapat menjadwalkan penampilan baru."""
        self.client.login(username='musisi_vg', password='password123')
        mulai = timezone.now() + timedelta(days=1, hours=20)
        selesai = mulai + timedelta(hours=2)

        resp = self.client.post(reverse('buat_gig'), {
            'venue': self.venue_a.id,
            'judul_acara': 'Malam Akustik Kukel',
            'mulai': mulai.strftime('%Y-%m-%dT%H:%M'),
            'selesai': selesai.strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Gig.objects.filter(judul_acara='Malam Akustik Kukel').exists())

    def test_pencegahan_jadwal_gig_bentrok(self):
        """Band dilarang membuat dua jadwal yang beririsan waktu."""
        self.client.login(username='musisi_vg', password='password123')
        t0 = timezone.localtime() + timedelta(days=2, hours=19)
        t1 = t0 + timedelta(hours=3)

        Gig.objects.create(
            band=self.band,
            venue=self.venue_a,
            judul_acara='Gig Pertama',
            mulai=t0,
            selesai=t1,
            status='TERJADWAL'
        )

        # Coba jadwalkan gig kedua yang beririsan (t0 + 1 jam s.d t1 + 1 jam)
        resp = self.client.post(reverse('buat_gig'), {
            'venue': self.venue_a.id,
            'judul_acara': 'Gig Bentrok',
            'mulai': (t0 + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'selesai': (t1 + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Gig.objects.filter(judul_acara='Gig Bentrok').exists())

    def test_go_live_gps_diluar_radius_ditolak(self):
        """Go Live ditolak jika koordinat GPS band berada > 150m dari venue."""
        self.client.login(username='musisi_vg', password='password123')
        now = timezone.now()
        gig = Gig.objects.create(
            band=self.band,
            venue=self.venue_a,
            judul_acara='Live Sekarang',
            mulai=now - timedelta(minutes=5),
            selesai=now + timedelta(hours=2),
            status='TERJADWAL'
        )

        # Koordinat di Jakarta (ratusan kilometer)
        resp = self.client.post(reverse('golive_gig', kwargs={'id': gig.id}), {
            'lat': -6.175392,
            'lng': 106.827153,
            'accuracy': 5.0
        })
        self.assertEqual(resp.status_code, 302)
        gig.refresh_from_db()
        self.assertEqual(gig.status, 'TERJADWAL')

    def test_go_live_gps_dalam_radius_diterima(self):
        """Go Live sukses jika posisi berada dalam radius 150m."""
        self.client.login(username='musisi_vg', password='password123')
        now = timezone.now()
        gig = Gig.objects.create(
            band=self.band,
            venue=self.venue_a,
            judul_acara='Live Sekarang Dekat',
            mulai=now - timedelta(minutes=5),
            selesai=now + timedelta(hours=2),
            status='TERJADWAL'
        )

        # Koordinat persis di venue
        resp = self.client.post(reverse('golive_gig', kwargs={'id': gig.id}), {
            'lat': self.venue_a.latitude,
            'lng': self.venue_a.longitude,
            'accuracy': 5.0
        })
        self.assertEqual(resp.status_code, 302)
        gig.refresh_from_db()
        self.assertEqual(gig.status, 'LIVE')

    def test_perpanjangan_gig_maksimal_satu_kali(self):
        """Perpanjangan waktu +30 menit hanya dapat dilakukan 1 kali."""
        self.client.login(username='musisi_vg', password='password123')
        now = timezone.now()
        waktu_selesai_awal = now + timedelta(hours=1)
        gig = Gig.objects.create(
            band=self.band,
            venue=self.venue_a,
            judul_acara='Gig Perpanjang',
            mulai=now - timedelta(hours=1),
            selesai=waktu_selesai_awal,
            status='LIVE'
        )

        # Perpanjangan ke-1
        self.client.post(reverse('extend_gig', kwargs={'id': gig.id}), {'aksi': 'perpanjang'})
        gig.refresh_from_db()
        self.assertTrue(gig.sudah_diperpanjang)
        self.assertAlmostEqual((gig.selesai - waktu_selesai_awal).total_seconds(), 1800, delta=2)

        # Perpanjangan ke-2 ditolak
        selesai_setelah_ext1 = gig.selesai
        self.client.post(reverse('extend_gig', kwargs={'id': gig.id}), {'aksi': 'perpanjang'})
        gig.refresh_from_db()
        self.assertEqual(gig.selesai, selesai_setelah_ext1)
