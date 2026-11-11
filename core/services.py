"""
Core Service Layer — Gigs Radar & Xplor.in Geospasial & Algoritma Rekayasa
Sesuai Dokumen Perancangan TPA DDP1 Fasilkom UI & Xplor.in STACK 2026.
"""

import math
from datetime import timedelta
from django.utils import timezone


def hitung_jarak_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Menghitung jarak terpendek melengkung pada permukaan bola bumi (Haversine Formula)
    antara koordinat (lat1, lon1) dan (lat2, lon2).
    Dilengkapi floating-point domain guard untuk mencegah math domain error.
    Radius bumi R = 6371.0 km.
    """
    r_bumi = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(dlon / 2.0) ** 2)
    # Guard terhadap floating-point precision di luar [0, 1]
    a = min(1.0, max(0.0, a))
    return float(2.0 * r_bumi * math.asin(math.sqrt(a)))


def hitung_bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """
    Menghitung koordinat kotak pembatas (Bounding Box) untuk pra-filter kueri SQL:
    1 derajat lintang ≈ 111.0 km
    1 derajat bujur ≈ 111.0 km * cos(lat)
    Mengembalikan (min_lat, max_lat, min_lon, max_lon).
    """
    delta_lat = radius_km / 111.0
    lat_rad = math.radians(lat)
    cos_lat = math.cos(lat_rad)
    # Guard terhadap kutub (cos_lat mendekati 0)
    delta_lon = (radius_km / (111.0 * cos_lat)) if abs(cos_lat) > 1e-6 else (radius_km / 111.0)

    min_lat = max(-90.0, lat - delta_lat)
    max_lat = min(90.0, lat + delta_lat)
    min_lon = max(-180.0, lon - delta_lon)
    max_lon = min(180.0, lon + delta_lon)

    return (min_lat, max_lat, min_lon, max_lon)


def hitung_crowd_heat(jumlah_checkin: int) -> dict:
    """
    Mengklasifikasikan tingkat kepadatan pengunjung di venue panggung:
    - Sepi: 0 s.d. 4 penonton
    - Hangat: 5 s.d. 15 penonton
    - Ramai: > 15 penonton
    """
    if jumlah_checkin <= 4:
        return {
            'level': 'SEPI',
            'label': 'Sepi',
            'color': 'emerald',
            'badge_class': 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
            'desc': 'Suasana santai, tempat duduk masih banyak tersedia.'
        }
    elif jumlah_checkin <= 15:
        return {
            'level': 'HANGAT',
            'label': 'Hangat',
            'color': 'amber',
            'badge_class': 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
            'desc': 'Suasana mulai hidup dan intim.'
        }
    else:
        return {
            'level': 'RAMAI',
            'label': 'Ramai',
            'color': 'rose',
            'badge_class': 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
            'desc': 'Energi panggung membara, penuh antusiasme penonton.'
        }


def hitung_skor_popularitas(
    r_band: float,
    v_rating: int,
    c_global: float = 4.0,
    f_band: int = 0,
    f_maks: int = 0,
    m: int = 5
) -> float:
    """
    Formula Perangkingan Musisi Terbobot Gabungan (Bayesian Average + Normalisasi Logaritmik Follower):
    skor_bayesian = ((v / (v + m)) * r) + ((m / (v + m)) * c)
    komponen_follower = ln(1 + f_band) / ln(1 + f_maks)
    total_skor = ((0.7 * (skor_bayesian / 5.0)) + (0.3 * komponen_follower)) * 100
    
    Dilengkapi pengaman ZeroDivisionError jika f_maks == 0 atau v == 0.
    """
    c_aman = c_global if c_global > 0 else 3.5
    r_aman = r_band if v_rating > 0 else 0.0

    # Perataan Bayesian Average (meredam anomali band baru dengan 1 rating bintang 5)
    skor_bayesian = ((v_rating / (v_rating + m)) * r_aman) + ((m / (v_rating + m)) * c_aman)

    # Normalisasi Logaritmik Pengikut
    if f_maks > 0 and f_band > 0:
        komponen_follower = math.log(1.0 + f_band) / math.log(1.0 + f_maks)
    else:
        komponen_follower = 0.0

    total = ((0.7 * (skor_bayesian / 5.0)) + (0.3 * komponen_follower)) * 100.0
    return round(total, 2)


def evaluasi_status_live(mulai, selesai, live_mulai_pada=None, live_selesai_pada=None, sekarang=None) -> str:
    """
    Logika penentuan status Live deterministik (mengacu Xplor.in ADR-7):
    Status dihitung dari jendela waktu dan aksi nyata, bukan sekadar kolom statis:
    - Jika live_selesai_pada terisi atau sekarang > selesai + 30 menit -> SELESAI
    - Jika live_mulai_pada terisi dan sekarang <= selesai + 30 menit -> LIVE
    - Jika sekarang < mulai -> TERJADWAL
    """
    if sekarang is None:
        sekarang = timezone.now()

    if live_selesai_pada is not None:
        return 'SELESAI'

    batas_kedaluwarsa = selesai + timedelta(minutes=30)
    if sekarang > batas_kedaluwarsa:
        return 'SELESAI'

    if live_mulai_pada is not None:
        return 'LIVE'

    if sekarang >= mulai and sekarang <= selesai:
        return 'TERJADWAL'

    return 'TERJADWAL' if sekarang < mulai else 'SELESAI'

