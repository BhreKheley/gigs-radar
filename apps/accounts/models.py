from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class BandProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='band_profile')
    nama_band = models.CharField(max_length=100, verbose_name="Nama Band")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    genre = models.CharField(max_length=50, default="Indie", verbose_name="Genre Musik")
    deskripsi = models.TextField(blank=True, verbose_name="Deskripsi / Biografi")
    kontak_ig = models.CharField(max_length=100, blank=True, verbose_name="Akun Instagram")
    foto = models.ImageField(upload_to='bands/', blank=True, null=True, verbose_name="Foto Panggung")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profil Band"
        verbose_name_plural = "Daftar Profil Band"
        ordering = ['nama_band']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nama_band) or f"band-{self.user_id or 'new'}"
            slug = base_slug
            counter = 1
            while BandProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nama_band

    @property
    def rata_rata_rating(self) -> float:
        ratings = self.ratings.all()
        if ratings.exists():
            total = sum(r.nilai_bintang for r in ratings)
            return round(total / ratings.count(), 1)
        return 0.0

    @property
    def jumlah_rating(self) -> int:
        return self.ratings.count()

    @property
    def jumlah_pengikut(self) -> int:
        return self.followers.count()

