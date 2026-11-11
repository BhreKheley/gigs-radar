from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Follow(models.Model):
    pengunjung = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following', verbose_name="Penonton")
    band = models.ForeignKey('accounts.BandProfile', on_delete=models.CASCADE, related_name='followers', verbose_name="Band")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pengikut Musisi"
        verbose_name_plural = "Daftar Pengikut Musisi"
        constraints = [
            models.UniqueConstraint(fields=['pengunjung', 'band'], name='unique_pengunjung_band_follow')
        ]

    def clean(self):
        super().clean()
        if hasattr(self, 'band') and self.band and self.band.user_id == self.pengunjung_id:
            raise ValidationError("Musisi tidak dapat mengikuti (follow) akun band milik sendiri.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pengunjung.username} -> {self.band.nama_band}"


class Checkin(models.Model):
    pengunjung = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkins', verbose_name="Penonton")
    gig = models.ForeignKey('venues_gigs.Gig', on_delete=models.CASCADE, related_name='checkins', verbose_name="Gig Panggung")
    latitude_user = models.FloatField(verbose_name="GPS Lintang Penonton")
    longitude_user = models.FloatField(verbose_name="GPS Bujur Penonton")
    jarak_m = models.FloatField(default=0.0, verbose_name="Jarak Terukur (meter)")
    akurasi_gps = models.FloatField(default=0.0, verbose_name="Akurasi Sinyal GPS (meter)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Check-in Penonton"
        verbose_name_plural = "Daftar Check-in Penonton"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['pengunjung', 'gig'], name='unique_pengunjung_gig_checkin')
        ]

    def clean(self):
        super().clean()
        if hasattr(self, 'gig') and self.gig:
            # Aturan Integritas Musisi: Anti Self-Checkin
            if self.gig.band.user_id == self.pengunjung_id:
                raise ValidationError("Musisi tidak dapat melakukan check-in pada gig milik sendiri.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Check-in: {self.pengunjung.username} @ {self.gig.judul_acara} ({self.jarak_m:.1f}m)"


class Rating(models.Model):
    pengunjung = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings', verbose_name="Penonton")
    band = models.ForeignKey('accounts.BandProfile', on_delete=models.CASCADE, related_name='ratings', verbose_name="Band")
    gig = models.ForeignKey('venues_gigs.Gig', on_delete=models.CASCADE, related_name='ratings', verbose_name="Gig Panggung")
    checkin = models.OneToOneField(Checkin, on_delete=models.CASCADE, related_name='rating', null=True, blank=True)
    nilai_bintang = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Skor Bintang (1–5)"
    )
    ulasan = models.TextField(max_length=500, blank=True, verbose_name="Ulasan Penonton")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rating & Ulasan Panggung"
        verbose_name_plural = "Daftar Rating & Ulasan"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['pengunjung', 'gig'], name='unique_pengunjung_gig_rating')
        ]

    def clean(self):
        super().clean()
        if hasattr(self, 'gig') and self.gig:
            # Aturan Integritas Musisi: Anti Self-Review
            if self.gig.band.user_id == self.pengunjung_id:
                raise ValidationError("Musisi tidak dapat memberikan ulasan atau rating pada penampilan milik sendiri.")

            # Verifikasi Kehadiran Fisik (Verified Attendance)
            if not self.checkin_id:
                ada_checkin = Checkin.objects.filter(pengunjung=self.pengunjung, gig=self.gig).first()
                if not ada_checkin:
                    raise ValidationError("Ulasan hanya diizinkan bagi penonton yang terverifikasi hadir (check-in) di lokasi gig.")
                self.checkin = ada_checkin

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nilai_bintang}★ oleh {self.pengunjung.username} untuk {self.band.nama_band}"


class SavedGig(models.Model):
    """
    Fitur Simpan Panggung / Event (sesuai Xplor.in saved_events)
    Memungkinkan penonton menandai gig favorit ke daftar tersimpan.
    """
    pengguna = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_gigs', verbose_name="Pengguna")
    gig = models.ForeignKey('venues_gigs.Gig', on_delete=models.CASCADE, related_name='saved_by', verbose_name="Gig Panggung")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gig Tersimpan"
        verbose_name_plural = "Daftar Gig Tersimpan"
        constraints = [
            models.UniqueConstraint(fields=['pengguna', 'gig'], name='unique_pengguna_gig_saved')
        ]

    def __str__(self):
        return f"{self.pengguna.username} menyimpan {self.gig.judul_acara}"

