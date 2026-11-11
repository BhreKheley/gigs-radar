from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from core.services import (
    hitung_jarak_km,
    hitung_bounding_box,
    hitung_crowd_heat,
    hitung_skor_popularitas,
    evaluasi_status_live,
)


class CoreServicesTestCase(TestCase):
    def test_haversine_jarak_nol(self):
        # Titik yang identik harus menghasilkan jarak 0.0 km
        jarak = hitung_jarak_km(-6.3645, 106.8242, -6.3645, 106.8242)
        self.assertAlmostEqual(jarak, 0.0, places=4)

    def test_haversine_depok_ke_jakarta(self):
        # Kampus UI Depok (-6.3645, 106.8242) ke Monas Jakarta (-6.1754, 106.8272) ≈ 21 km
        jarak = hitung_jarak_km(-6.3645, 106.8242, -6.1754, 106.8272)
        self.assertGreater(jarak, 20.0)
        self.assertLess(jarak, 23.0)

    def test_haversine_guard_antipoda(self):
        # Titik berseberangan kutub bumi tidak boleh memicu ValueError pada sqrt/asin
        jarak = hitung_jarak_km(90.0, 0.0, -90.0, 0.0)
        self.assertAlmostEqual(jarak, 20015.08, delta=10.0)

    def test_bounding_box_valid(self):
        min_lat, max_lat, min_lon, max_lon = hitung_bounding_box(-6.3645, 106.8242, 5.0)
        self.assertLess(min_lat, -6.3645)
        self.assertGreater(max_lat, -6.3645)
        self.assertLess(min_lon, 106.8242)
        self.assertGreater(max_lon, 106.8242)

    def test_crowd_heat_classification(self):
        self.assertEqual(hitung_crowd_heat(0)['level'], 'SEPI')
        self.assertEqual(hitung_crowd_heat(4)['level'], 'SEPI')
        self.assertEqual(hitung_crowd_heat(5)['level'], 'HANGAT')
        self.assertEqual(hitung_crowd_heat(15)['level'], 'HANGAT')
        self.assertEqual(hitung_crowd_heat(16)['level'], 'RAMAI')
        self.assertEqual(hitung_crowd_heat(100)['level'], 'RAMAI')

    def test_skor_popularitas_zero_division_guard(self):
        # Kasus ekstrem: belum ada rating dan belum ada pengikut sama sekali
        skor = hitung_skor_popularitas(r_band=0.0, v_rating=0, c_global=0.0, f_band=0, f_maks=0)
        self.assertIsInstance(skor, float)
        self.assertGreaterEqual(skor, 0.0)
        self.assertLessEqual(skor, 100.0)

    def test_skor_popularitas_bayesian_fairness(self):
        # Band A: 1 ulasan bintang 5.0
        skor_a = hitung_skor_popularitas(r_band=5.0, v_rating=1, c_global=4.0, f_band=10, f_maks=100)
        # Band B: 50 ulasan bintang 4.8
        skor_b = hitung_skor_popularitas(r_band=4.8, v_rating=50, c_global=4.0, f_band=50, f_maks=100)
        # Band B harus berperingkat lebih tinggi karena bukti ulasannya jauh lebih kredibel
        self.assertGreater(skor_b, skor_a)

    def test_evaluasi_status_live(self):
        now = timezone.now()
        mulai = now - timedelta(hours=1)
        selesai = now + timedelta(hours=1)
        
        # Gig dalam rentang waktu, band sudah tekan live
        status = evaluasi_status_live(mulai, selesai, live_mulai_pada=mulai)
        self.assertEqual(status, 'LIVE')

        # Gig sudah lewat 40 menit setelah selesai (melebihi toleransi 30 menit)
        selesai_lampau = now - timedelta(minutes=40)
        status_expired = evaluasi_status_live(mulai, selesai_lampau, live_mulai_pada=mulai)
        self.assertEqual(status_expired, 'SELESAI')

