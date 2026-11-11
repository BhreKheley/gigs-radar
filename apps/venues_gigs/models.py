from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.services import evaluasi_status_live, hitung_crowd_heat


class Venue(models.Model):
    nama = models.CharField(max_length=150, verbose_name="Nama Tempat / Kafe")
    alamat = models.TextField(verbose_name="Alamat Lengkap")
    latitude = models.FloatField(db_index=True, verbose_name="Lintang (Latitude)")
    longitude = models.FloatField(db_index=True, verbose_name="Bujur (Longitude)")
    kontak = models.CharField(max_length=100, blank=True, verbose_name="Kontak Pengelola")
    dibuat_oleh = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='venues_dibuat')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Venue Panggung"
        verbose_name_plural = "Daftar Venue"
        ordering = ['nama']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return self.nama


class Gig(models.Model):
    STATUS_CHOICES = [
        ('TERJADWAL', 'Terjadwal'),
        ('LIVE', 'Sedang Live'),
        ('SELESAI', 'Selesai'),
        ('BATAL', 'Dibatalkan'),
    ]

    band = models.ForeignKey('accounts.BandProfile', on_delete=models.CASCADE, related_name='gigs', verbose_name="Band Musisi")
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name='gigs', verbose_name="Lokasi Venue")
    judul_acara = models.CharField(max_length=200, verbose_name="Judul Penampilan")
    mulai = models.DateTimeField(db_index=True, verbose_name="Waktu Mulai")
    selesai = models.DateTimeField(db_index=True, verbose_name="Waktu Selesai")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TERJADWAL', db_index=True)
    live_sejak = models.DateTimeField(null=True, blank=True, verbose_name="Waktu Go Live Aktif")
    sudah_diperpanjang = models.BooleanField(default=False, verbose_name="Pernah Diperpanjang +30 Menit")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Jadwal Gig"
        verbose_name_plural = "Daftar Jadwal Gig"
        ordering = ['mulai']
        indexes = [
            models.Index(fields=['status', 'mulai']),
            models.Index(fields=['mulai', 'selesai']),
        ]

    def __str__(self):
        return f"{self.judul_acara} — {self.band.nama_band} @ {self.venue.nama}"

    @property
    def status_efektif(self) -> str:
        """
        Evaluasi status dinamis tanpa cronjob (Lazy State Evaluation).
        Jika waktu sekarang melebihi jam selesai + 30m, otomatis berstatus SELESAI.
        """
        if self.status in ('SELESAI', 'BATAL'):
            return self.status

        status_terhitung = evaluasi_status_live(
            mulai=self.mulai,
            selesai=self.selesai,
            live_mulai_pada=self.live_sejak,
            live_selesai_pada=None if self.status == 'LIVE' else timezone.now() if self.status == 'SELESAI' else None
        )

        # Jika basis data masih TERJADWAL/LIVE tapi waktu sudah kedaluwarsa, perbarui lazy
        if status_terhitung == 'SELESAI' and self.status != 'SELESAI':
            Gig.objects.filter(pk=self.pk).update(status='SELESAI')
            self.status = 'SELESAI'

        return self.status

    @property
    def sedang_live(self) -> bool:
        return self.status_efektif == 'LIVE'

    @property
    def sisa_menit(self) -> int:
        now = timezone.now()
        if now < self.selesai:
            delta = self.selesai - now
            return max(0, int(delta.total_seconds() // 60))
        return 0

    @property
    def crowd_heat(self) -> dict:
        total_checkin = self.checkins.count()
        return hitung_crowd_heat(total_checkin)

