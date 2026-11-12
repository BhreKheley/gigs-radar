"""
Perintah Management Seed Data Demo Realistis Depok & Margonda
Sesuai Dokumen Perancangan TPA DDP1 Fasilkom UI (LM-401) & Xplor.in
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from apps.accounts.models import BandProfile
from apps.venues_gigs.models import Venue, Gig
from apps.interactions.models import Follow, Checkin, Rating


class Command(BaseCommand):
    help = 'Populasi data demo realistis Depok & Margonda sesuai Dokumen Perancangan TPA DDP1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Hapus data lama sebelum mengisi data demo baru',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Memulai seeding data demo Margonda & UI Depok...'))

        with transaction.atomic():
            if options.get('flush'):
                Rating.objects.all().delete()
                Checkin.objects.all().delete()
                Follow.objects.all().delete()
                Gig.objects.all().delete()
                Venue.objects.all().delete()
                BandProfile.objects.all().delete()
                User.objects.filter(is_superuser=False).delete()

            # 1. Buat Akun Musisi & Band
            bands_data = [
                {
                    'username': 'senjamargonda_user',
                    'nama_band': 'Senja Margonda',
                    'slug': 'senja-margonda',
                    'tipe_musisi': 'PEWARIS',
                    'genre': 'Indie Folk',
                    'deskripsi': 'Kolektif musik indie folk asal Kukusan, Depok. Memadukan petikan gitar akustik dengan lirik bertema senja, kereta rel listrik, dan kehangatan Margonda.',
                    'kontak_ig': 'senjamargonda'
                },
                {
                    'username': 'distorsifasilkom_user',
                    'nama_band': 'Distorsi Fasilkom',
                    'slug': 'distorsi-fasilkom',
                    'tipe_musisi': 'PERINTIS',
                    'genre': 'Alt Rock',
                    'deskripsi': 'Grup musik alternatif rock bentukan mahasiswa Ilmu Komputer UI yang bising dan penuh distorsi melodi distopik.',
                    'kontak_ig': 'distorsifasilkom'
                },
                {
                    'username': 'kuartetjazzui_user',
                    'nama_band': 'Kuartet Jazz UI',
                    'slug': 'kuartet-jazz-ui',
                    'tipe_musisi': 'PEWARIS',
                    'genre': 'Jazz Fusion',
                    'deskripsi': 'Musisi jazz fusion kampus yang membawakan standar jazz klasik dengan improvisasi modern yang lembut dan menenangkan.',
                    'kontak_ig': 'kuartetjazzui'
                },
                {
                    'username': 'nadasore_user',
                    'nama_band': 'Nada Sore',
                    'slug': 'nada-sore',
                    'tipe_musisi': 'PERINTIS',
                    'genre': 'Pop Acoustic',
                    'deskripsi': 'Duo vokal akustik yang menyanyikan lagu-lagu pop syahdu pengiring obrolan sore hari di kedai kopi.',
                    'kontak_ig': 'nadasoremusic'
                },
                {
                    'username': 'orkesmalamjumat_user',
                    'nama_band': 'Orkes Malam Jumat',
                    'slug': 'orkes-malam-jumat',
                    'tipe_musisi': 'PEWARIS',
                    'genre': 'Ska/Indie',
                    'deskripsi': 'Band ska brass section berenergi tinggi yang selalu membuat seluruh lantai kafe berdansa ria.',
                    'kontak_ig': 'orkesmalamjumat'
                },
            ]

            band_objs = {}
            for b in bands_data:
                user, _ = User.objects.get_or_create(
                    username=b['username'],
                    defaults={'email': f"{b['username']}@gigsradar.id"}
                )
                user.set_password('demopass123')
                user.save()

                band_prof, created = BandProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'nama_band': b['nama_band'],
                        'slug': b['slug'],
                        'tipe_musisi': b['tipe_musisi'],
                        'genre': b['genre'],
                        'deskripsi': b['deskripsi'],
                        'kontak_ig': b['kontak_ig']
                    }
                )
                if not created:
                    band_prof.tipe_musisi = b['tipe_musisi']
                    band_prof.nama_band = b['nama_band']
                    band_prof.genre = b['genre']
                    band_prof.save()
                band_objs[b['slug']] = band_prof

            # 2. Buat Venue Panggung Margonda & Kampus UI Depok
            venues_data = [
                {
                    'key': 'kukel',
                    'nama': 'Kopi Kukel 18 (Kukusan)',
                    'alamat': 'Jl. Juragan Sinda No. 18, Kukusan, Beji, Depok',
                    'lat': -6.3645,
                    'lng': 106.8242,
                    'kontak': '081234567801'
                },
                {
                    'key': 'barel',
                    'nama': 'Panggung Barel (Beji)',
                    'alamat': 'Kawasan Barel UI, Jl. Margonda Raya No. 102, Beji, Depok',
                    'lat': -6.3688,
                    'lng': 106.8315,
                    'kontak': '081234567802'
                },
                {
                    'key': 'teras',
                    'nama': 'Teras Akustik Margonda',
                    'alamat': 'Jl. Margonda Raya No. 450, Kemiri Muka, Beji, Depok',
                    'lat': -6.3732,
                    'lng': 106.8348,
                    'kontak': '081234567803'
                },
                {
                    'key': 'pocin',
                    'nama': 'Ruang Seduh Pondok Cina',
                    'alamat': 'Jl. Margonda Raya No. 288 (Dekat Stasiun Pondok Cina), Beji, Depok',
                    'lat': -6.3612,
                    'lng': 106.8331,
                    'kontak': '081234567804'
                },
                {
                    'key': 'kutek',
                    'nama': 'Sudut Kopi Kutek',
                    'alamat': 'Jl. H. Asmawi No. 44, Kukusan Teknik, Beji, Depok',
                    'lat': -6.3589,
                    'lng': 106.8194,
                    'kontak': '081234567805'
                },
            ]

            venue_objs = {}
            for v in venues_data:
                venue, _ = Venue.objects.get_or_create(
                    nama=v['nama'],
                    defaults={
                        'alamat': v['alamat'],
                        'latitude': v['lat'],
                        'longitude': v['lng'],
                        'kontak': v['kontak'],
                        'dibuat_oleh': band_objs['senja-margonda'].user
                    }
                )
                venue_objs[v['key']] = venue

            # 3. Buat Akun Demo Penonton
            user_budi, _ = User.objects.get_or_create(
                username='budi_santoso',
                defaults={'email': 'budi@student.ui.ac.id'}
            )
            user_budi.set_password('demopass123')
            user_budi.save()

            penonton_users = [user_budi]
            for i in range(1, 26):
                u, _ = User.objects.get_or_create(
                    username=f'penonton_depok_{i}',
                    defaults={'email': f'penonton{i}@gigsradar.id'}
                )
                u.set_password('demopass123')
                u.save()
                penonton_users.append(u)

            # 4. Buat Jadwal Gig (3 Live, 1 Terjadwal, 1 Selesai)
            now = timezone.now()
            gigs_spec = [
                {
                    'band': band_objs['senja-margonda'],
                    'venue': venue_objs['kukel'],
                    'judul': 'Senja Akustik Kukel: Pulang Kampus Santai',
                    'mulai': now - timedelta(minutes=45),
                    'selesai': now + timedelta(hours=1, minutes=15),
                    'status': 'LIVE',
                    'checkin_count': 19  # Ramai
                },
                {
                    'band': band_objs['distorsi-fasilkom'],
                    'venue': venue_objs['barel'],
                    'judul': 'Barel Loud Night: Distorsi & Kafein',
                    'mulai': now - timedelta(minutes=20),
                    'selesai': now + timedelta(hours=1, minutes=40),
                    'status': 'LIVE',
                    'checkin_count': 11  # Hangat
                },
                {
                    'band': band_objs['kuartet-jazz-ui'],
                    'venue': venue_objs['teras'],
                    'judul': 'Margonda Midnight Jazz Session',
                    'mulai': now - timedelta(minutes=15),
                    'selesai': now + timedelta(hours=2),
                    'status': 'LIVE',
                    'checkin_count': 4  # Sepi
                },
                {
                    'band': band_objs['nada-sore'],
                    'venue': venue_objs['pocin'],
                    'judul': 'Acoustic Warmth Pondok Cina',
                    'mulai': now + timedelta(hours=3),
                    'selesai': now + timedelta(hours=6),
                    'status': 'TERJADWAL',
                    'checkin_count': 0
                },
                {
                    'band': band_objs['orkes-malam-jumat'],
                    'venue': venue_objs['kutek'],
                    'judul': 'Ska Pesta Rakyat Kutek UI',
                    'mulai': now - timedelta(days=2, hours=3),
                    'selesai': now - timedelta(days=2),
                    'status': 'SELESAI',
                    'checkin_count': 15
                },
            ]

            for g_spec in gigs_spec:
                gig, _ = Gig.objects.get_or_create(
                    band=g_spec['band'],
                    venue=g_spec['venue'],
                    judul_acara=g_spec['judul'],
                    defaults={
                        'mulai': g_spec['mulai'],
                        'selesai': g_spec['selesai'],
                        'status': g_spec['status'],
                        'live_sejak': g_spec['mulai'] if g_spec['status'] == 'LIVE' else None
                    }
                )

                # Tambahkan check-in penonton
                count = g_spec['checkin_count']
                for idx in range(min(count, len(penonton_users))):
                    u = penonton_users[idx]
                    # Pastikan penonton bukan pemilik band
                    if u.id != gig.band.user_id:
                        Checkin.objects.get_or_create(
                            pengunjung=u,
                            gig=gig,
                            defaults={
                                'latitude_user': gig.venue.latitude,
                                'longitude_user': gig.venue.longitude,
                                'jarak_m': 15.0 + (idx * 2.0),
                                'akurasi_gps': 8.0
                            }
                        )

                # Tambahkan follow dan rating contoh
                for idx in range(min(5, len(penonton_users))):
                    u = penonton_users[idx]
                    if u.id != gig.band.user_id:
                        Follow.objects.get_or_create(pengunjung=u, band=g_spec['band'])

                        # Jika gig sudah pernah dihadiri, tambahkan ulasan contoh
                        ck = Checkin.objects.filter(pengunjung=u, gig=gig).first()
                        if ck:
                            Rating.objects.get_or_create(
                                pengunjung=u,
                                gig=gig,
                                defaults={
                                    'band': gig.band,
                                    'checkin': ck,
                                    'nilai_bintang': 5 if idx % 2 == 0 else 4,
                                    'ulasan': 'Penampilan luar biasa! Vokal jernih dan suasananya sangat mendukung.'
                                }
                            )

        self.stdout.write(self.style.SUCCESS('Seeding data demo Depok & Margonda berhasil selesai 100%!'))

