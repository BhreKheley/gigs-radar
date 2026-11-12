# Entity Relationship Diagram (ERD) — Gigs Radar
**Spesifikasi Model Data Relasional & Aturan Integritas**  
*Tugas Proyek Akhir (TPA) DDP1 Fasilkom UI Gasal 2026/2027*

---

## 1. Diagram Relasi Entitas (Mermaid ERD)

```mermaid
erDiagram
    USER ||--o| BAND_PROFILE : "memiliki profil musisi (1 to 0..1)"
    USER ||--o{ CHECKIN : "melakukan check-in fisik (1 to N)"
    USER ||--o{ RATING : "menulis ulasan terverifikasi (1 to N)"
    USER ||--o{ FOLLOW : "mengikuti band (1 to N)"
    USER ||--o{ SAVED_GIG : "menyimpan jadwal favorit (1 to N)"
    USER ||--o{ VENUE : "mendaftarkan titik venue (1 to N)"

    BAND_PROFILE ||--o{ GIG : "menjadwalkan penampilan (1 to N)"
    BAND_PROFILE ||--o{ FOLLOW : "memiliki basis pengikut (1 to N)"
    BAND_PROFILE ||--o{ RATING : "menerima ulasan performa (1 to N)"

    VENUE ||--o{ GIG : "menjadi lokasi panggung (1 to N)"

    GIG ||--o{ CHECKIN : "mencatat kehadiran penonton (1 to N)"
    GIG ||--o{ RATING : "menjadi konteks acara ulasan (1 to N)"
    GIG ||--o{ SAVED_GIG : "disimpan dalam daftar pantau (1 to N)"

    CHECKIN ||--o| RATING : "menjadi bukti kehadiran fisik (1 to 0..1)"

    USER {
        int id PK
        string username UK
        string email
        string password
        boolean is_active
        datetime date_joined
    }

    BAND_PROFILE {
        int id PK
        int user_id FK,UK "OneToOne ke auth.User"
        string nama_band
        string slug UK
        string tipe_musisi "Enum: PERINTIS / PEWARIS (Rising vs Heritage)"
        string genre
        text deskripsi
        string kontak_ig
        string foto "ImageField opsional"
        datetime created_at
    }

    VENUE {
        int id PK
        string nama
        text alamat
        float latitude "Index Spasial"
        float longitude "Index Spasial"
        string kontak
        int dibuat_oleh_id FK "ForeignKey ke auth.User"
        datetime created_at
    }

    GIG {
        int id PK
        int band_id FK "ForeignKey ke BandProfile"
        int venue_id FK "ForeignKey ke Venue"
        string judul_acara
        datetime mulai "Index Waktu"
        datetime selesai "Index Waktu"
        string status "TERJADWAL, LIVE, SELESAI, BATAL"
        datetime live_sejak
        boolean sudah_diperpanjang "Flag limitasi +30m max 1x"
        datetime created_at
    }

    FOLLOW {
        int id PK
        int pengunjung_id FK "ForeignKey ke auth.User"
        int band_id FK "ForeignKey ke BandProfile"
        datetime created_at
    }

    CHECKIN {
        int id PK
        int pengunjung_id FK "ForeignKey ke auth.User"
        int gig_id FK "ForeignKey ke Gig"
        datetime waktu_checkin
        float latitude_user
        float longitude_user
        float jarak_m "Jarak aktual saat verifikasi"
        float akurasi_gps
    }

    RATING {
        int id PK
        int pengunjung_id FK "ForeignKey ke auth.User"
        int band_id FK "ForeignKey ke BandProfile"
        int gig_id FK "ForeignKey ke Gig"
        int checkin_id FK,UK "OneToOne ke Checkin"
        int nilai_bintang "Nilai 1 s.d 5"
        text ulasan
        datetime created_at
    }

    SAVED_GIG {
        int id PK
        int pengguna_id FK "ForeignKey ke auth.User"
        int gig_id FK "ForeignKey ke Gig"
        datetime created_at
    }
```

---

## 2. Rincian Tabel Relasional & Indeks

### A. Tabel `accounts_bandprofile`
* Relasi: `OneToOneField` ke `auth.User` (cascade on delete).
* Slugification: Kolom `slug` dibuat otomatis dari `nama_band` menggunakan fungsi `slugify()` dengan penjamin keunikan numerik jika terdapat nama panggung serupa.
* Properti Terhitung:
  - `total_pengikut`: Menghitung jumlah relasi pada tabel `interactions_follow`.
  - `skor_popularitas`: Mengaplikasikan rumus Bayesian Average $\frac{v}{v+m} \cdot R + \frac{m}{v+m} \cdot C + \log_{10}(1+F)$.

### B. Tabel `venues_gigs_venue`
* Relasi: `ForeignKey` ke `auth.User` (penulis/musisi pendaftar venue, `SET_NULL`).
* Optimasi Geospasial: Kolom `latitude` dan `longitude` diberi indeks komposit `Index(fields=['latitude', 'longitude'])` untuk query cepat Bounding-Box SQL sebelum kalkulasi Haversine presisi.
* Spatial Deduplication: Pencegahan pendaftaran titik ganda dengan deteksi radius $\le 50\text{ meter}$.

### C. Tabel `venues_gigs_gig`
* Relasi:
  - `band_id` (`ForeignKey` ke `BandProfile`, `CASCADE`).
  - `venue_id` (`ForeignKey` ke `Venue`, `PROTECT`).
* Optimasi Indeks:
  - `Index(fields=['status', 'mulai'])`: Filter cepat gig berstatus LIVE dan waktu tayang.
  - `Index(fields=['mulai', 'selesai'])`: Validasi pencegahan jadwal tumpang tindih (*overlap prevention*).
* Lazy State Calculation:
  - Menghitung status deterministik tanpa cronjob via `evaluasi_status_live()`.
  - Properti `crowd_heat`: Mengelompokkan total check-in menjadi **Sepi** ($< 10$), **Hangat** ($10 - 29$), atau **Ramai** ($\ge 30$).

### D. Tabel `interactions_checkin`
* Relasi: `pengunjung_id` ke `auth.User` dan `gig_id` ke `Gig`.
* Konstrain Integritas:
  - `unique_together = ('pengunjung', 'gig')`: Mencegah duplikasi check-in oleh pengguna yang sama pada satu gig.
  - Anti Self-Checkin: Musisi dilarang check-in di gig miliknya sendiri (diverifikasi pada tingkat service layer dan model clean).
  - Geofence Verification: Koordinat GPS pengguna wajib $\le 150\text{ meter}$ dari venue panggung.

### E. Tabel `interactions_rating`
* Relasi:
  - `pengunjung_id` ke `auth.User`.
  - `band_id` ke `BandProfile`.
  - `gig_id` ke `Gig`.
  - `checkin_id` (`OneToOneField` ke `Checkin`): Menjamin bahwa ulasan hanya dapat ditulis jika terdapat rekaman check-in fisik yang sah (*verified attendee attendance*).
* Konstrain Integritas:
  - Anti Self-Review: Musisi dilarang mereview band sendiri (HTTP 403).
  - Rentang Bintang: $1 \le \text{nilai\_bintang} \le 5$.
  - `unique_together = ('pengunjung', 'gig')`: Maksimal 1 ulasan per pengguna per acara.

### F. Tabel `interactions_follow`
* Relasi: `pengunjung_id` ke `auth.User` dan `band_id` ke `BandProfile`.
* Konstrain: `unique_together = ('pengunjung', 'band')`. Musisi dilarang mem-follow profil band sendiri.

### G. Tabel `interactions_savedgig`
* Relasi: `pengguna_id` ke `auth.User` dan `gig_id` ke `Gig`.
* Konstrain: `unique_together = ('pengguna', 'gig')`. Mengakomodasi fitur simpan acara sesuai spesifikasi Xplor.in `saved_events`.

