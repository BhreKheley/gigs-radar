from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.accounts.models import BandProfile


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_penonton = User.objects.create_user(
            username='penonton1',
            password='password123',
            email='penonton1@test.com'
        )
        self.user_musisi = User.objects.create_user(
            username='musisi1',
            password='password123',
            email='musisi1@test.com'
        )
        self.band = BandProfile.objects.create(
            user=self.user_musisi,
            nama_band='Senja UI',
            genre='Indie Folk',
            kontak_ig='senja_ui'
        )

    def test_band_slug_otomatis(self):
        """Memastikan slug dibuat otomatis dan konsisten dari nama band."""
        self.assertEqual(self.band.slug, 'senja-ui')

    def test_registrasi_penonton_sukses(self):
        """Pendaftaran pengguna dengan peran penonton membuat akun User biasa."""
        resp = self.client.post(reverse('daftar'), {
            'username': 'audiens_baru',
            'email': 'audiens@test.com',
            'password': 'password123',
            'password_konfirmasi': 'password123',
            'role': 'pengunjung'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='audiens_baru').exists())
        self.assertFalse(BandProfile.objects.filter(user__username='audiens_baru').exists())

    def test_registrasi_musisi_sukses(self):
        """Pendaftaran musisi sekaligus menginstansiasi BandProfile."""
        resp = self.client.post(reverse('daftar'), {
            'username': 'band_baru',
            'email': 'band@test.com',
            'password': 'password123',
            'password_konfirmasi': 'password123',
            'role': 'band',
            'nama_band': 'The Depok Waves',
            'genre': 'Surf Rock',
            'kontak_ig': 'depokwaves'
        })
        self.assertEqual(resp.status_code, 302)
        user_band = User.objects.get(username='band_baru')
        self.assertTrue(hasattr(user_band, 'band_profile'))
        self.assertEqual(user_band.band_profile.nama_band, 'The Depok Waves')

    def test_login_sukses_dan_gagal(self):
        """Pengujian autentikasi kredensial valid dan salah."""
        # Gagal
        resp = self.client.post(reverse('masuk'), {
            'username': 'penonton1',
            'password': 'wrongpassword'
        })
        self.assertEqual(resp.status_code, 200)

        # Sukses
        resp = self.client.post(reverse('masuk'), {
            'username': 'penonton1',
            'password': 'password123'
        })
        self.assertEqual(resp.status_code, 302)

    def test_penonton_dapat_follow_band(self):
        """Penonton dapat mengikuti dan berhenti mengikuti musisi via toggle."""
        self.client.login(username='penonton1', password='password123')
        resp = self.client.post(reverse('toggle_follow', kwargs={'slug': self.band.slug}), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['following'], True)
        self.assertEqual(self.band.followers.count(), 1)

        # Unfollow
        resp2 = self.client.post(reverse('toggle_follow', kwargs={'slug': self.band.slug}), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()['following'], False)
        self.assertEqual(self.band.followers.count(), 0)

    def test_tipe_musisi_perintis_dan_pewaris(self):
        """Memastikan klasifikasi tipe musisi Perintis dan Pewaris berfungsi tepat."""
        # Default band setUp adalah PERINTIS
        self.assertTrue(self.band.is_perintis)
        self.assertFalse(self.band.is_pewaris)
        self.assertEqual(self.band.label_tipe, "Musisi Perintis")
        self.assertIn("cyan", self.band.badge_css)

        # Ubah menjadi PEWARIS
        self.band.tipe_musisi = 'PEWARIS'
        self.band.save()
        self.assertTrue(self.band.is_pewaris)
        self.assertFalse(self.band.is_perintis)
        self.assertEqual(self.band.label_tipe, "Musisi Pewaris")
        self.assertIn("amber", self.band.badge_css)

    def test_registrasi_musisi_dengan_tipe_pewaris(self):
        """Pendaftaran musisi dengan eksplisit memilih tipe PEWARIS."""
        resp = self.client.post(reverse('daftar'), {
            'username': 'band_pewaris',
            'email': 'pewaris@test.com',
            'password': 'password123',
            'password_konfirmasi': 'password123',
            'role': 'band',
            'nama_band': 'Margonda Heritage Ensemble',
            'tipe_musisi': 'PEWARIS',
            'genre': 'Classical/Jazz',
            'kontak_ig': 'margondaheritage'
        })
        self.assertEqual(resp.status_code, 302)
        user_band = User.objects.get(username='band_pewaris')
        self.assertEqual(user_band.band_profile.tipe_musisi, 'PEWARIS')
        self.assertTrue(user_band.band_profile.is_pewaris)

    def test_musisi_dilarang_follow_band_sendiri(self):
        """Aturan integritas: Musisi tidak boleh mem-follow profil band miliknya sendiri."""
        self.client.login(username='musisi1', password='password123')
        resp = self.client.post(reverse('toggle_follow', kwargs={'slug': self.band.slug}), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.band.followers.count(), 0)

