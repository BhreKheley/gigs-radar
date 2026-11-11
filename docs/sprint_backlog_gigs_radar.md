# Sprint Backlog — Gigs Radar
**Laporan Manajemen Proyek & Dekomposisi Siklus Pengembangan**  
*Tugas Proyek Akhir (TPA) DDP1 Fasilkom UI Gasal 2026/2027*

---

## 1. Ikhtisar Metodologi

Pengembangan **Gigs Radar** dieksekusi dengan pendekatan *Agile Scrum* berfokus pada kualitas tinggi (*high rigor*), anti-slop, dan pemenuhan seluruh kriteria tugas akhir DDP1 Fasilkom UI serta rancangan sistem **Xplor.in (STACK 2026)**. Seluruh pekerjaan dibagi menjadi 3 Sprint terstruktur:

---

## 2. Sprint 1: Fondasi Arsitektur Geospasial & Basis Data Relasional
*Periode*: Sprint Awal  
*Fokus*: Clean slate setup, Service Layer geospasial murni, 4 modul Django, 7 tabel relasional, dan seeding realistis area Margonda Depok.

| ID | User Story / Task | Modul / Berkas | Status | Bukti Verifikasi |
|---|---|---|---|---|
| SP1-01 | Inisialisasi lingkungan Python 3.14 & Django 5.2 dengan arsitektur MVT modular | `livemusic_project/`, `.venv` | **DONE** | Django 5.2.19, Pillow, WhiteNoise terinstal |
| SP1-02 | Service Layer matematika geospasial: Haversine, Bounding-Box, Bayesian, Crowd Heat, Lazy Live | `core/services.py` | **DONE** | 8 unit test di `core/tests.py` lulus 100% |
| SP1-03 | Pemodelan `BandProfile` dengan relasi OneToOne ke `auth.User` dan auto-slug | `apps/accounts/models.py` | **DONE** | Migrasi `0001_initial.py` berhasil |
| SP1-04 | Pemodelan `Venue` dengan indeks komposit lat/lng & spatial deduplication | `apps/venues_gigs/models.py` | **DONE** | Indeks geospasial terdaftar di skema SQLite |
| SP1-05 | Pemodelan `Gig` dengan properti dinamis `status_efektif`, `sedang_live`, `crowd_heat` | `apps/venues_gigs/models.py` | **DONE** | Status deterministik `[mulai-30m, selesai+30m]` |
| SP1-06 | Pemodelan `Follow`, `Checkin`, `Rating`, dan `SavedGig` dengan konstrain ketat | `apps/interactions/models.py` | **DONE** | `unique_together` dan relasi Foreign Key terikat |
| SP1-07 | Command seeding data realistis 5 venue Margonda, 5 band indie, 26 akun penonton | `apps/accounts/management/commands/seed_demo.py` | **DONE** | Berhasil dieksekusi via `python manage.py seed_demo` |
| SP1-08 | Pembuatan snapshot database cold-start `seed.sqlite3` untuk Vercel Serverless | `seed.sqlite3` | **DONE** | Berkas biner SQLite cadangan siap pakai (286 KB) |

---

## 3. Sprint 2: Logika Bisnis, Verifikasi Geofence GPS & Integritas Platform
*Periode*: Sprint Menengah  
*Fokus*: View controller, API JSON geospasial, penegakan anti self-checkin, anti self-review, sinkronisasi kalender, dan dashboard musisi.

| ID | User Story / Task | Modul / Berkas | Status | Bukti Verifikasi |
|---|---|---|---|---|
| SP2-01 | API Geospasial `/api/live/` dengan filter Bounding-Box SQL dan Haversine radius | `apps/radar_map/views.py` | **DONE** | Mengembalikan JSON gig terdekat dengan jarak km |
| SP2-02 | Alur Verifikasi Geofence Check-in GPS ($\le 150\text{ m}$) di lokasi venue | `apps/interactions/views.py` | **DONE** | Toleransi buffer akurasi dalam ruangan s.d 50m |
| SP2-03 | Penegakan Aturan Integritas Musisi: Anti Self-Checkin (HTTP 403) | `apps/interactions/views.py` | **DONE** | Test `test_musisi_dilarang_checkin_gig_sendiri` LULUS |
| SP2-04 | Penegakan Aturan Integritas Musisi: Anti Self-Review (HTTP 403) | `apps/interactions/views.py` | **DONE** | Test `test_musisi_dilarang_rating_gig_sendiri` LULUS |
| SP2-05 | Verifikasi Rating Terverifikasi (Wajib check-in fisik terlebih dahulu) | `apps/interactions/views.py` | **DONE** | Test `test_penonton_belum_checkin_dilarang_rating` LULUS |
| SP2-06 | Integrasi Add to Google Calendar & Ekspor berkas standar iCalendar (`.ics`) | `apps/interactions/views.py` | **DONE** | Test `test_ekspor_kalender_ics` LULUS MIME text/calendar |
| SP2-07 | Spatial Deduplication Venue 50 meter dengan konfirmasi manual pengguna | `apps/venues_gigs/views.py` | **DONE** | Test `test_deteksi_duplikasi_venue_50_meter` LULUS |
| SP2-08 | Papan Peringkat Bayesian Leaderboard + Log normalisasi pengikut | `apps/interactions/views.py` | **DONE** | Test `test_papan_peringkat_leaderboard` LULUS |
| SP2-09 | Dashboard Musisi dengan Go-Live GPS manual, perpanjangan +30m, & grafik kehadiran | `apps/interactions/views.py` | **DONE** | Terintegrasi Chart.js kurva audiens terverifikasi |

---

## 4. Sprint 3: UI/UX Anti-Slop, Test Suite Komprehensif, & Deployment
*Periode*: Sprint Final  
*Fokus*: Desain visual konsisten tanpa emoji (100% SVG), tema ganda Obsidian/Light, skrip Windows 1-klik, 33 automated test cases, dan dokumentasi lengkap.

| ID | User Story / Task | Modul / Berkas | Status | Bukti Verifikasi |
|---|---|---|---|---|
| SP3-01 | Tata letak global `base.html` dengan tema ganda (Dark & Light) + toast kustom | `templates/base.html` | **DONE** | Tailwind CSS + Google Fonts Space Grotesk |
| SP3-02 | Landing page modern dengan KPI stats ticker, 3 pilar, dan trending bands | `templates/radar_map/landing.html` | **DONE** | Akses via `/landing/` |
| SP3-03 | Peta Radar Geospasial Leaflet interaktif dengan Demo GPS Switcher Depok | `templates/radar_map/index.html` | **DONE** | Sinkronisasi CartoDB Dark/Voyager tiles |
| SP3-04 | Halaman katalog jadwal `jadwal_list.html` dengan filter genre & ekspor kalender | `templates/venues_gigs/jadwal_list.html` | **DONE** | Mendukung pencarian teks & genre |
| SP3-05 | Halaman detail gig `gig_detail.html` dengan tombol GPS 150m & star picker | `templates/venues_gigs/gig_detail.html` | **DONE** | Mini map Leaflet + interaktif checkin & rating |
| SP3-06 | Halaman formulir pendaftaran venue & penjadwalan gig musisi | `templates/venues_gigs/` | **DONE** | Pin dropper Leaflet & validasi waktu bentrok |
| SP3-07 | Halaman autentikasi `masuk.html` dengan tombol 1-klik demo evaluasi & `daftar.html` | `templates/accounts/` | **DONE** | Role switcher otomatis penonton vs musisi |
| SP3-08 | Halaman profil band publik, edit profil panggung, & daftar tersimpan | `templates/` | **DONE** | Follow AJAX toggle & grid kartu tersimpan |
| SP3-09 | Halaman error custom anti-slop 404 & 500 dengan navigasi pemulihan | `templates/404.html`, `500.html` | **DONE** | Branded radar recovery page |
| SP3-10 | Runner skrip Windows 1-klik (`run.bat`, `run.ps1`, `seed.bat`, `seed.ps1`) | Root folder | **DONE** | Otomatis aktivasi .venv & copy snapshot database |
| SP3-11 | Automated Test Suite komprehensif: 33 Unit & Integration Tests | `apps/*/tests.py`, `core/tests.py` | **DONE** | **33 test case lulus 100% (0 errors, 0 failures)** |
| SP3-12 | Konfigurasi Vercel Serverless dengan cold-start database auto-copy | `wsgi.py`, `vercel.json` | **DONE** | Mencegah error 500 basis data kosong di `/tmp` |

