# Gigs Radar — Platform Geospasial Live Music Tracker Kota Depok

> **Tugas Proyek Akhir (TPA) DDP1 Fasilkom UI Gasal 2026/2027**  
> *Diadaptasi dari Arsitektur Sistem Xplor.in (STACK 2026 Hackathon Design) oleh Bhre Nabil Faeyza*

![Gigs Radar Banner](https://img.shields.io/badge/Status-Production%20Ready-emerald?style=for-the-badge)
![Django 5](https://img.shields.io/badge/Django-5.2.19-092E20?style=for-the-badge&logo=django)
![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python)
![Tests Passing](https://img.shields.io/badge/Tests-33%20Passed-success?style=for-the-badge)
![UI/UX Standard](https://img.shields.io/badge/Anti--Slop-100%25%20Bespoke%20Vector-amber?style=for-the-badge)

---

## 1. Tentang Gigs Radar

**Gigs Radar** adalah platform web geospasial real-time yang memetakan pertunjukan musik panggung indie di koridor Kota Depok (Margonda Raya, Kukusan Kelurahan, Kukusan Teknik, Pondok Cina, hingga Beji).

Aplikasi ini mengatasi problem *information fragmentation* yang dihadapi oleh penonton dan musisi lokal:
1. **Bagi Penonton**: Memungkinkan penemuan panggung musik terdekat secara instan menggunakan radar geospasial interaktif, filter radius cerdas (1 km s.d 50 km), sinkronisasi kalender (.ics & Google Calendar), penyimpanan gig favorit, serta pemberian rating performa yang hanya dapat dilakukan setelah terverifikasi hadir secara fisik di venue (Geofence GPS $\le 150\text{ m}$).
2. **Bagi Musisi & Band**: Pusat kendali panggung untuk mempublikasikan jadwal acara bebas bentrok, mendaftarkan titik venue dengan proteksi anti-duplikasi ($50\text{ m}$), mengaktifkan status **Go-Live** berbasis GPS saat tiba di panggung, memperpanjang durasi ($+30\text{ menit}$), dan memantau kurva kehadiran penonton via analitik visual.

---

## 2. Fitur Unggulan & Adaptasi Xplor.in (STACK 2026)

* **Deterministik Status Live (Lazy State Evaluation)**: Status LIVE dievaluasi secara cerdas pada jendela waktu `[mulai - 30 menit, selesai + 30 menit]`. Tidak bergantung pada cronjob background; basis data diperbarui secara *lazy* saat ada akses request.
* **Geofence Check-in GPS Presisi ($\le 150\text{ meter}$)**: Menggunakan formula jarak lingkaran besar Haversine dengan kompensasi akurasi sinyal dalam ruangan (*buffer* hingga 50m).
* **Aturan Integritas Musisi Ketat**:
  - **Anti Self-Checkin**: Musisi dilarang check-in di pertunjukan miliknya sendiri (HTTP 403).
  - **Anti Self-Review**: Musisi dilarang mereview band miliknya sendiri (HTTP 403). Ulasan hanya dapat dikirimkan oleh penonton yang telah diverifikasi hadir via GPS.
* **Papan Peringkat Bayesian Leaderboard**:
  $$\text{Skor} = \left(\frac{v}{v + m} \times R\right) + \left(\frac{m}{v + m} \times C\right) + \log_{10}(1 + F)$$
  Menghilangkan bias skor palsu 5.0 dari 1 ulasan tunggal dengan bobot prior minimum $m=5$, rata-rata platform $C$, serta faktor bobot logaritmik basis pengikut $F$.
* **Sinkronisasi Kalender Ganda**:
  - Tombol 1-klik **Add to Google Calendar** dengan tautan langsung terisi judul, jam, dan lokasi venue.
  - Unduh berkas standar **iCalendar (.ics)** (MIME `text/calendar`) yang kompatibel dengan Apple Calendar, Outlook, dan Google Calendar.
* **Spatial Deduplication Venue 50 Meter**:
  Pendeteksian titik kafe/panggung yang berjarak $\le 50\text{ meter}$ untuk mencegah duplikasi entitas lokasi pada basis data.
* **Indeks Keramaian (Crowd Heat)**:
  Klasifikasi dinamis berbasis jumlah check-in terverifikasi: **Sepi / Santai** ($< 10$), **Hangat** ($10 - 29$), dan **Ramai Sekali** ($\ge 30$).
* **Standar Desain Anti-Slop (Zero Emojis)**:
  - 100% ikon vektor SVG bespoke hand-crafted.
  - Dukungan Tema Ganda (*Obsidian Dark Mode* & *Studio Light Mode*) dengan sinkronisasi tile peta CartoDB secara instan.
  - Navigasi responsif desktop & mobile bottom app bar.

---

## 3. Arsitektur Proyek (Django 5 MVT)

```
TPA DDP1/
├── core/                           # Service Layer Matematika Geospasial & Algoritma
│   ├── services.py                 # Haversine, Bounding Box, Bayesian, Crowd Heat, Status Live
│   └── tests.py                    # 8 Unit Tests matematika murni
├── apps/
│   ├── accounts/                   # Modul Otentikasi & Profil Panggung Musisi
│   │   ├── models.py               # BandProfile (OneToOne ke auth.User, auto-slug)
│   │   ├── views.py                # Daftar, Masuk, Keluar, Edit Profil, Follow Toggle
│   │   ├── forms.py                # Form registrasi dengan selector peran
│   │   └── tests.py                # Unit test akun & aturan follow
│   ├── venues_gigs/                # Modul Panggung, Titik Venue & Penjadwalan Gig
│   │   ├── models.py               # Venue (Indeks Spasial Lat/Lng) & Gig (Lazy State)
│   │   ├── views.py                # Jadwal List, Detail Gig, Tambah Venue, Buat Gig, Go-Live GPS
│   │   └── tests.py                # Unit test venue dedup 50m, bentrok jadwal, perpanjang +30m
│   ├── radar_map/                  # Modul Peta Radar Geospasial & Landing Page
│   │   ├── views.py                # radar_index (Leaflet), landing_page, api_live (JSON)
│   │   └── tests.py                # Unit test geospasial radius filtering
│   └── interactions/               # Modul Interaksi Audiens, Check-in, Rating, Kalender
│       ├── models.py               # Follow, Checkin (150m), Rating (Verified), SavedGig
│       ├── views.py                # Checkin, Rate, Save, Export .ICS, Leaderboard, Dashboard Band
│       └── tests.py                # Unit test anti self-checkin, anti self-review, kalender
├── templates/                      # Antarmuka Pengguna Bespoke (Anti-Slop)
│   ├── base.html                   # Shell induk, theme switcher, toast notification, bottom bar
│   ├── 404.html & 500.html         # Custom branded error pages
│   ├── radar_map/                  # landing.html & index.html (Peta Radar)
│   ├── venues_gigs/                # jadwal_list.html, gig_detail.html, buat_gig.html, tambah_venue.html
│   ├── accounts/                   # masuk.html, daftar.html, profil_band.html, band_detail.html
│   └── interactions/               # leaderboard.html, dashboard_band.html, saved_list.html
├── docs/                           # Dokumentasi Komprehensif
│   ├── alur_flowchart_pengguna.md  # Diagram Flowchart Mermaid interaksi pengguna
│   ├── erd_gigs_radar.md           # Diagram Relasi Entitas 7 Tabel Relasional
│   └── sprint_backlog_gigs_radar.md# Manajemen Proyek Scrum 3 Sprint
├── run.bat & run.ps1               # Skrip 1-Klik Menjalankan Server di Windows
├── seed.bat & seed.ps1             # Skrip 1-Klik Reset & Seeding Data Realistis
├── seed.sqlite3                    # Snapshot Database Cold-start Vercel (286 KB)
├── vercel.json                     # Konfigurasi Deployment Serverless Vercel
└── requirements.txt                # Dependensi Python produksi
```

---

## 4. Panduan Menjalankan Aplikasi di Windows

### Cara 1: Menjalankan 1-Klik (Rekomendasi untuk Penguji)
Cukup klik dua kali berkas:
* **`run.bat`** (atau jalankan `.\run.ps1` di PowerShell).
Skrip ini otomatis mendeteksi virtualenv, menyalin database snapshot jika belum ada, dan menyalakan server lokal di `http://127.0.0.1:8000/`.

### Cara 2: Menjalankan Manual via Terminal
```powershell
# 1. Masuk ke direktori proyek
cd "C:\Users\sriha\OneDrive\Desktop\TPA DDP1"

# 2. Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Jalankan migrasi basis data (jika diperlukan)
python manage.py migrate

# 4. Muat data demo realistis Depok
python manage.py seed_demo

# 5. Jalankan server lokal
python manage.py runserver 127.0.0.1:8000
```
Buka peramban di **`http://127.0.0.1:8000/`**.

---

## 5. Kredensial Akun Uji Coba Demo

Untuk mempermudah pengujian oleh Asisten Dosen / Penguji, formulir login telah dilengkapi **Tombol 1-Klik Akses Demo**:

| Peran | Username | Password | Deskripsi Hak Akses |
|---|---|---|---|
| **Penonton / Audiens** | `budi_santoso` | `password123` | Akses penuh radar, check-in GPS venue, rating terverifikasi, simpan gig favorit. |
| **Musisi / Band** | `senjamargonda_user` | `password123` | Pemilik band *Senja Margonda*. Memiliki akses Dashboard Band, Go-Live GPS, perpanjangan waktu +30 menit, dan penjadwalan gig. |
| **Penonton 2** | `siti_rahma` | `password123` | Penonton terverifikasi dengan ulasan dan riwayat hadir. |
| **Musisi 2** | `the_margonda_project_user` | `password123` | Musisi pengelola band *The Margonda Project*. |

> **Catatan Pengujian GPS**: Pada halaman Peta Radar (`/`), disediakan **Demo GPS Location Switcher** di panel kontrol bawah peta. Anda dapat berpindah instan ke titik *Kafe Kukel 18*, *Panggung Barel*, atau *Teras Margonda* untuk menguji filter radius tanpa harus berpindah tempat fisik.

---

## 6. Hasil Eksekusi Test Suite (Automated Testing)

Seluruh 33 test case otomatis diuji dan berhasil lulus 100%:
```powershell
.venv\Scripts\python.exe manage.py test apps.accounts apps.venues_gigs apps.interactions apps.radar_map core
```
**Output**:
```text
Creating test database for alias 'default'...
.................................
----------------------------------------------------------------------
Ran 33 tests in 2.516s

OK
Destroying test database for alias 'default'...
```

---

## 7. Penanganan Vercel Serverless (Fail-Safe Cold-Start)

Di lingkungan Vercel Serverless Function, sistem berkas bersifat *ephemeral* dan hanya direktori `/tmp` yang memiliki izin tulis (*writeable*). Untuk mencegah kendala **Error 500: Database Kosong**, berkas `livemusic_project/wsgi.py` telah dilengkapi mekanisme **Auto-Bootstrap Cold-Start**:
1. Mendeteksi apakah berjalan di Vercel (`os.environ.get('VERCEL')`).
2. Jika database di `/tmp/db.sqlite3` belum ada, berkas snapshot `seed.sqlite3` otomatis disalin ke `/tmp`.
3. Menjalankan migrasi darurat jika diperlukan secara transparan sehingga endpoint tidak pernah mengembalikan galat 500.

---

## 8. Hak Cipta & Lisensi
Dikembangkan untuk Tugas Proyek Akhir (TPA) Dasar-Dasar Pemrograman 1 (DDP1), Fakultas Ilmu Komputer, Universitas Indonesia.  
*Hak Cipta © 2026 Gigs Radar. All rights reserved.*

