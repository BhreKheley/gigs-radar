from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from .models import Venue, Gig
from .forms import VenueForm, GigForm
from core.services import hitung_jarak_km, hitung_bounding_box


def jadwal_list_view(request):
    """Katalog jadwal gig mendatang dan gig yang sedang berlangsung."""
    genre = request.GET.get('genre', '').strip()
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    tipe_filter = request.GET.get('tipe', '').strip().upper()

    gigs = Gig.objects.select_related('band', 'venue').filter(
        status__in=['TERJADWAL', 'LIVE']
    ).order_by('mulai')

    if genre:
        gigs = gigs.filter(band__genre__icontains=genre)

    if tipe_filter in ['PERINTIS', 'PEWARIS']:
        gigs = gigs.filter(band__tipe_musisi=tipe_filter)

    if q:
        gigs = gigs.filter(
            Q(judul_acara__icontains=q) |
            Q(band__nama_band__icontains=q) |
            Q(venue__nama__icontains=q)
        )

    if status_filter in ['TERJADWAL', 'LIVE']:
        gigs = gigs.filter(status=status_filter)

    # Ambil daftar unik genre
    genres_list = Gig.objects.values_list('band__genre', flat=True).distinct()

    context = {
        'gigs': gigs,
        'genre_aktif': genre,
        'q': q,
        'status_aktif': status_filter,
        'tipe_aktif': tipe_filter,
        'genres_list': set(filter(None, genres_list)),
    }
    return render(request, 'venues_gigs/jadwal_list.html', context)


def gig_detail_view(request, id):
    """Halaman detail gig dengan pemeriksaan kelayakan check-in dan rating."""
    gig = get_object_or_404(Gig.objects.select_related('band', 'venue'), pk=id)
    
    # Cek apakah pengguna saat ini adalah musisi pemilik gig
    is_owner = False
    if request.user.is_authenticated:
        is_owner = (gig.band.user_id == request.user.id)

    # Cek status check-in pengguna
    user_checkin = None
    if request.user.is_authenticated and not is_owner:
        user_checkin = gig.checkins.filter(pengunjung=request.user).first()

    # Cek apakah pengguna sudah memberi rating
    user_rating = None
    if request.user.is_authenticated and not is_owner:
        user_rating = gig.ratings.filter(pengunjung=request.user).first()

    # Cek apakah gig disimpan oleh pengguna
    is_saved = False
    if request.user.is_authenticated:
        is_saved = request.user.saved_gigs.filter(gig=gig).exists()

    ratings = gig.ratings.select_related('pengunjung').order_by('-created_at')

    context = {
        'gig': gig,
        'is_owner': is_owner,
        'user_checkin': user_checkin,
        'user_rating': user_rating,
        'is_saved': is_saved,
        'ratings': ratings,
        'crowd_heat': gig.crowd_heat,
    }
    return render(request, 'venues_gigs/gig_detail.html', context)


@login_required
def tambah_venue_view(request):
    """Pendaftaran titik venue baru oleh musisi."""
    if not hasattr(request.user, 'band_profile'):
        messages.warning(request, "Pendaftaran venue hanya dapat dilakukan oleh akun Musisi / Band.")
        return redirect('radar_index')

    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.dibuat_oleh = request.user

            # Pengecekan duplikasi lokasi radius 50 meter (Spatial Deduplication)
            dedup_radius = getattr(settings, 'VENUE_DEDUP_RADIUS_M', 50) / 1000.0  # konversi ke km
            min_lat, max_lat, min_lon, max_lon = hitung_bounding_box(venue.latitude, venue.longitude, dedup_radius)
            
            calon_duplikat = Venue.objects.filter(
                latitude__gte=min_lat, latitude__lte=max_lat,
                longitude__gte=min_lon, longitude__lte=max_lon
            )

            duplikat_ditemukan = None
            for v in calon_duplikat:
                jarak_m = hitung_jarak_km(venue.latitude, venue.longitude, v.latitude, v.longitude) * 1000.0
                if jarak_m <= 50.0:
                    duplikat_ditemukan = v
                    break

            # Jika force_save dicentang atau tidak ada duplikat
            if duplikat_ditemukan and not request.POST.get('konfirmasi_duplikat'):
                return render(request, 'venues_gigs/tambah_venue.html', {
                    'form': form,
                    'venue_duplikat': duplikat_ditemukan,
                    'jarak_duplikat': f"{jarak_m:.1f}"
                })

            venue.save()
            messages.success(request, f"Venue '{venue.nama}' berhasil didaftarkan!")
            return redirect('buat_gig')
    else:
        # Pre-fill lat & lng dari query param jika user klik di peta
        initial_lat = request.GET.get('lat')
        initial_lng = request.GET.get('lng')
        form = VenueForm(initial={'latitude': initial_lat, 'longitude': initial_lng})

    return render(request, 'venues_gigs/tambah_venue.html', {'form': form})


def cek_duplikat_venue_api(request):
    """API JSON pengecekan duplikasi venue dalam radius 50 meter."""
    try:
        lat = float(request.GET.get('lat', ''))
        lng = float(request.GET.get('lng', ''))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Parameter lat dan lng harus berupa angka valid.'}, status=400)

    dedup_radius = getattr(settings, 'VENUE_DEDUP_RADIUS_M', 50) / 1000.0
    min_lat, max_lat, min_lon, max_lon = hitung_bounding_box(lat, lng, dedup_radius)

    calon_duplikat = Venue.objects.filter(
        latitude__gte=min_lat, latitude__lte=max_lat,
        longitude__gte=min_lon, longitude__lte=max_lon
    )

    duplikat = []
    for v in calon_duplikat:
        jarak_m = hitung_jarak_km(lat, lng, v.latitude, v.longitude) * 1000.0
        if jarak_m <= 50.0:
            duplikat.append({
                'id': v.id,
                'nama': v.nama,
                'alamat': v.alamat,
                'jarak_m': round(jarak_m, 1)
            })

    return JsonResponse({'duplikat': duplikat})


@login_required
def buat_gig_view(request):
    """Musisi menjadwalkan penampilan (gig) baru."""
    if not hasattr(request.user, 'band_profile'):
        messages.warning(request, "Penjadwalan gig hanya dapat dilakukan oleh akun Musisi / Band.")
        return redirect('radar_index')

    band = request.user.band_profile
    if request.method == 'POST':
        form = GigForm(request.POST)
        if form.is_valid():
            gig = form.save(commit=False)
            gig.band = band

            # Validasi pencegahan jadwal bentrok untuk band yang sama
            bentrok = Gig.objects.filter(
                band=band,
                status__in=['TERJADWAL', 'LIVE'],
                mulai__lt=gig.selesai,
                selesai__gt=gig.mulai
            ).exists()

            if bentrok:
                form.add_error(None, "Anda sudah memiliki jadwal manggung lain yang beririsan dengan rentang waktu ini.")
            else:
                gig.save()
                messages.success(request, f"Gig '{gig.judul_acara}' berhasil dijadwalkan!")
                return redirect('gig_detail', id=gig.id)
    else:
        # Default waktu mulai 1 jam dari sekarang
        waktu_default = timezone.now() + timedelta(hours=1)
        form = GigForm(initial={
            'mulai': waktu_default.strftime('%Y-%m-%dT%H:%M'),
            'selesai': (waktu_default + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')
        })

    return render(request, 'venues_gigs/buat_gig.html', {'form': form, 'band': band})


@login_required
def golive_gig_view(request, id):
    """Band mengaktifkan status LIVE melalui verifikasi geofence GPS di venue."""
    gig = get_object_or_404(Gig.objects.select_related('band', 'venue'), pk=id)

    # Validasi kepemilikan: hanya musisi pemilik gig
    if gig.band.user_id != request.user.id:
        return HttpResponseForbidden("Hanya band pemilik gig yang dapat mengaktifkan status Live.")

    if request.method != 'POST':
        return redirect('gig_detail', id=gig.id)

    # Ambil koordinat GPS perangkat dari POST / JSON
    import json
    data = {}
    if request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            pass

    try:
        lat = float(data.get('latitude') or data.get('lat') or request.POST.get('latitude') or request.POST.get('lat', ''))
        lng = float(data.get('longitude') or data.get('lng') or request.POST.get('longitude') or request.POST.get('lng', ''))
        akurasi = float(data.get('accuracy') or request.POST.get('accuracy', '0.0'))
    except (ValueError, TypeError):
        msg = "Data koordinat GPS tidak valid. Pastikan GPS peramban Anda aktif."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'pesan': msg}, status=400)
        messages.error(request, msg)
        return redirect('gig_detail', id=gig.id)

    now = timezone.now()
    # Jendela waktu Live: [mulai - 30 menit, selesai]
    if now < (gig.mulai - timedelta(minutes=30)):
        msg = "Tombol Go Live hanya aktif 30 menit sebelum jadwal panggung dimulai."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'pesan': msg}, status=400)
        messages.warning(request, msg)
        return redirect('gig_detail', id=gig.id)

    if now > gig.selesai:
        msg = "Jadwal panggung ini sudah melewati batas waktu selesai."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'pesan': msg}, status=400)
        messages.error(request, msg)
        return redirect('gig_detail', id=gig.id)

    # Kalkulasi jarak geospasial Haversine
    jarak_m = hitung_jarak_km(lat, lng, gig.venue.latitude, gig.venue.longitude) * 1000.0

    # Kompensasi akurasi sinyal GPS dalam ruangan (buffer hingga 50m)
    buffer = min(max(0.0, akurasi), 50.0)
    jarak_efektif = max(0.0, jarak_m - buffer)

    radius_maks = getattr(settings, 'CHECKIN_RADIUS_M', 150)
    if jarak_efektif > radius_maks:
        msg = f"Verifikasi GPS Gagal: Anda terdeteksi berjarak {jarak_m:.0f}m dari {gig.venue.nama} (maksimal {radius_maks}m). Silakan mendekat ke lokasi venue."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'pesan': msg}, status=400)
        messages.error(request, msg)
        return redirect('gig_detail', id=gig.id)

    # Berhasil verifikasi: aktifkan status LIVE
    gig.status = 'LIVE'
    gig.live_sejak = now
    gig.save(update_fields=['status', 'live_sejak'])

    sukses_msg = f"Panggung LIVE Aktif! Penonton di sekitar {gig.venue.nama} kini dapat melihat status band Anda di peta."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'status': 'ok', 'pesan': sukses_msg})

    messages.success(request, sukses_msg)
    return redirect('gig_detail', id=gig.id)


@login_required
def extend_gig_view(request, id):
    """Band memperpanjang waktu tampil (+30 menit) atau mengakhiri panggung lebih awal."""
    gig = get_object_or_404(Gig.objects.select_related('band'), pk=id)

    if gig.band.user_id != request.user.id:
        return HttpResponseForbidden("Hanya band pemilik gig yang dapat mengelola durasi penampilan.")

    aksi = request.POST.get('aksi', '')
    if aksi == 'perpanjang':
        if gig.sudah_diperpanjang:
            messages.warning(request, "Perpanjangan waktu hanya dapat dilakukan maksimal 1 kali per gig.")
        else:
            gig.selesai = gig.selesai + timedelta(minutes=30)
            gig.sudah_diperpanjang = True
            gig.save(update_fields=['selesai', 'sudah_diperpanjang'])
            messages.success(request, "Durasi panggung berhasil diperpanjang 30 menit!")
    elif aksi == 'akhiri':
        gig.status = 'SELESAI'
        gig.selesai = timezone.now()
        gig.save(update_fields=['status', 'selesai'])
        messages.info(request, "Penampilan panggung telah ditutup. Sesi rating penonton kini terbuka.")

    return redirect('gig_detail', id=gig.id)

