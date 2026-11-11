from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.db.models import Max, Count
from .models import Follow, Checkin, Rating, SavedGig
from apps.accounts.models import BandProfile
from apps.venues_gigs.models import Gig
from core.services import hitung_jarak_km, hitung_skor_popularitas


@login_required
def checkin_gig_view(request, id):
    """
    Check-in kehadiran penonton di lokasi panggung live.
    Menegakkan aturan integritas:
    1. Musisi dilarang check-in di panggung milik sendiri (HTTP 403)
    2. Status gig wajib LIVE
    3. Posisi GPS penonton harus berada dalam radius <= 150m
    """
    gig = get_object_or_404(Gig.objects.select_related('band', 'venue'), pk=id)

    # 1. Aturan Integritas Musisi: Anti Self-Checkin
    if gig.band.user_id == request.user.id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Musisi tidak dapat melakukan check-in pada gig milik sendiri.'}, status=403)
        return HttpResponseForbidden("Musisi tidak dapat melakukan check-in pada gig milik sendiri.")

    if request.method != 'POST':
        return redirect('gig_detail', id=gig.id)

    # 2. Cek status gig
    if gig.status_efektif != 'LIVE':
        msg = "Check-in hanya dibuka saat pertunjukan berstatus LIVE."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': msg}, status=400)
        messages.error(request, msg)
        return redirect('gig_detail', id=gig.id)

    # 3. Cek apakah sudah pernah check-in sebelumnya (Idempotensi)
    checkin_lama = Checkin.objects.filter(pengunjung=request.user, gig=gig).first()
    if checkin_lama:
        msg = "Anda sudah tercatat check-in pada panggung ini!"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg, 'crowd_heat': gig.crowd_heat})
        messages.info(request, msg)
        return redirect('gig_detail', id=gig.id)

    # 4. Validasi koordinat GPS
    import json
    body_data = {}
    if request.content_type == 'application/json' and request.body:
        try:
            body_data = json.loads(request.body)
        except Exception:
            pass

    try:
        lat = float(body_data.get('latitude') or body_data.get('lat') or request.POST.get('latitude') or request.POST.get('lat', ''))
        lng = float(body_data.get('longitude') or body_data.get('lng') or request.POST.get('longitude') or request.POST.get('lng', ''))
        akurasi = float(body_data.get('accuracy') or request.POST.get('accuracy', '0.0'))
    except (ValueError, TypeError):
        msg = "Koordinat GPS tidak valid. Pastikan izin lokasi peramban diaktifkan."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'error': msg, 'pesan': msg}, status=400)
        messages.error(request, msg)
        return redirect('gig_detail', id=gig.id)

    jarak_m = hitung_jarak_km(lat, lng, gig.venue.latitude, gig.venue.longitude) * 1000.0
    buffer = min(max(0.0, akurasi), 50.0)
    jarak_efektif = max(0.0, jarak_m - buffer)

    radius_maks = getattr(settings, 'CHECKIN_RADIUS_M', 150)
    if jarak_efektif > radius_maks:
        msg = f"Anda berada di luar jangkauan ({jarak_m:.0f}m dari panggung). Maksimal {radius_maks}m untuk check-in."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'error': msg, 'pesan': msg}, status=400)
        messages.error(request, msg)
        return redirect('gig_detail', id=gig.id)

    # Berhasil: catat check-in
    Checkin.objects.create(
        pengunjung=request.user,
        gig=gig,
        latitude_user=lat,
        longitude_user=lng,
        jarak_m=round(jarak_m, 1),
        akurasi_gps=akurasi
    )

    sukses_msg = f"Check-in Berhasil! Kehadiran Anda di {gig.venue.nama} tercatat secara resmi."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'status': 'ok',
            'success': True,
            'message': sukses_msg,
            'pesan': sukses_msg,
            'crowd_heat': gig.crowd_heat
        })

    messages.success(request, sukses_msg)
    return redirect('gig_detail', id=gig.id)


@login_required
def rate_band_view(request, id):
    """
    Pemberian rating dan ulasan oleh penonton terverifikasi.
    Menegakkan aturan:
    1. Musisi dilarang rating penampilan sendiri (HTTP 403)
    2. Wajib terverifikasi check-in fisik di gig ini (HTTP 400)
    3. Maksimal 1 rating per pengguna per gig
    """
    gig = get_object_or_404(Gig.objects.select_related('band'), pk=id)

    # 1. Aturan Integritas Musisi: Anti Self-Review
    if gig.band.user_id == request.user.id:
        return HttpResponseForbidden("Musisi tidak dapat memberikan ulasan atau rating pada penampilan milik sendiri.")

    if request.method != 'POST':
        return redirect('gig_detail', id=gig.id)

    # 2. Cek apakah pengguna sudah check-in secara sah
    checkin = Checkin.objects.filter(pengunjung=request.user, gig=gig).first()
    if not checkin:
        messages.error(request, "Ulasan hanya diizinkan bagi penonton yang terverifikasi hadir di lokasi saat gig berlangsung.")
        return redirect('gig_detail', id=gig.id)

    # 3. Cek apakah sudah pernah rating
    if Rating.objects.filter(pengunjung=request.user, gig=gig).exists():
        msg = "Anda sudah memberikan ulasan untuk panggung ini."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'error': msg, 'pesan': msg}, status=400)
        messages.warning(request, msg)
        return redirect('gig_detail', id=gig.id)

    import json
    data = {}
    if request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            pass

    try:
        raw_bintang = data.get('skor') or data.get('nilai_bintang') or request.POST.get('skor') or request.POST.get('nilai_bintang', '5')
        bintang = int(raw_bintang)
        if bintang < 1 or bintang > 5:
            raise ValueError
    except (ValueError, TypeError):
        msg = "Skor bintang harus bernilai antara 1 sampai 5."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'error': msg, 'pesan': msg}, status=400)
        messages.error(request, msg)
        return redirect('gig_detail', id=gig.id)

    ulasan = (data.get('komentar') or data.get('ulasan') or request.POST.get('komentar') or request.POST.get('ulasan', '')).strip()[:500]

    Rating.objects.create(
        pengunjung=request.user,
        band=gig.band,
        gig=gig,
        checkin=checkin,
        nilai_bintang=bintang,
        ulasan=ulasan
    )

    sukses_msg = f"Terima kasih! Ulasan bintang {bintang} Anda untuk {gig.band.nama_band} berhasil dipublikasikan."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'status': 'ok', 'success': True, 'message': sukses_msg, 'pesan': sukses_msg})

    messages.success(request, sukses_msg)
    return redirect('gig_detail', id=gig.id)


@login_required
def save_gig_view(request, id):
    """Toggle simpan gig ke daftar favorit penonton (Xplor.in saved_events)."""
    gig = get_object_or_404(Gig, pk=id)
    saved = SavedGig.objects.filter(pengguna=request.user, gig=gig).first()

    if saved:
        saved.delete()
        is_saved = False
        msg = f"Gig '{gig.judul_acara}' dihapus dari daftar tersimpan."
    else:
        SavedGig.objects.create(pengguna=request.user, gig=gig)
        is_saved = True
        msg = f"Gig '{gig.judul_acara}' disimpan ke daftar acara Anda!"

    # Selalu dukung response JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json' or request.method == 'POST':
        return JsonResponse({
            'status': 'ok',
            'is_saved': is_saved,
            'tersimpan': is_saved,
            'message': msg,
            'pesan': msg
        })

    messages.info(request, msg)
    return redirect('gig_detail', id=gig.id)


@login_required
def saved_gigs_list_view(request):
    """Halaman daftar gig tersimpan milik pengguna."""
    saved_items = SavedGig.objects.filter(pengguna=request.user).select_related('gig__band', 'gig__venue').order_by('-created_at')
    return render(request, 'interactions/saved_list.html', {'saved_items': saved_items})


def export_calendar_ics_view(request, id):
    """
    Ekspor berkas kalender standar iCalendar (.ics) untuk satu gig
    Sesuai Xplor.in GET /events/:id/kalender.ics & ADR-10.
    """
    gig = get_object_or_404(Gig.objects.select_related('band', 'venue'), pk=id)
    
    t_format = "%Y%m%dT%H%M%SZ"
    dtstart = gig.mulai.strftime(t_format)
    dtend = gig.selesai.strftime(t_format)
    dtstamp = timezone.now().strftime(t_format)

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Gigs Radar//DDP1 Live Music Platform//ID
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:gig-{gig.id}@gigsradar.id
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{gig.judul_acara} — {gig.band.nama_band}
DESCRIPTION:Live music oleh {gig.band.nama_band} ({gig.band.genre}) di {gig.venue.nama}.
LOCATION:{gig.venue.nama}, {gig.venue.alamat}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

    response = HttpResponse(ics_content.strip(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="gig_{gig.id}.ics"'
    return response


def leaderboard_view(request):
    """
    Papan peringkat musisi Kota Depok berdasarkan algoritma Bayesian Average
    dan normalisasi logaritmik pengikut (DDP1 Hal 10).
    """
    bands = BandProfile.objects.all().select_related('user')
    
    # Hitung prior global
    semua_rating = Rating.objects.values_list('nilai_bintang', flat=True)
    c_global = (sum(semua_rating) / len(semua_rating)) if semua_rating else 4.0

    # Jumlah pengikut maksimum di platform
    max_followers_row = Follow.objects.values('band').annotate(total=models.Count('id')).order_by('-total').first()
    f_maks = max_followers_row['total'] if max_followers_row else 1

    daftar_skor = []
    for band in bands:
        ratings_band = list(band.ratings.values_list('nilai_bintang', flat=True))
        v_count = len(ratings_band)
        r_avg = (sum(ratings_band) / v_count) if v_count > 0 else 0.0
        f_count = band.followers.count()

        skor = hitung_skor_popularitas(
            r_band=r_avg,
            v_rating=v_count,
            c_global=c_global,
            f_band=f_count,
            f_maks=f_maks,
            m=5
        )

        daftar_skor.append({
            'band': band,
            'skor': skor,
            'rata_rata': round(r_avg, 1) if v_count > 0 else 5.0,
            'total_ulasan': v_count,
            'total_pengikut': f_count,
        })

    # Urutkan berdasarkan skor tertinggi
    daftar_skor.sort(key=lambda x: x['skor'], reverse=True)

    # Tambahkan peringkat
    for i, item in enumerate(daftar_skor, 1):
        item['peringkat'] = i

    context = {
        'leaderboard': daftar_skor,
        'podium_top3': daftar_skor[:3],
    }
    return render(request, 'interactions/leaderboard.html', context)


@login_required
def dashboard_band_view(request):
    """Dashboard internal musisi untuk memantau performa, riwayat gig, dan analitik penonton."""
    if not hasattr(request.user, 'band_profile'):
        messages.warning(request, "Dashboard ini khusus untuk akun Musisi / Band.")
        return redirect('radar_index')

    band = request.user.band_profile
    gigs = band.gigs.select_related('venue').order_by('-mulai')

    # Data analitik kurva penonton untuk Chart.js
    chart_labels = []
    chart_data = []
    for g in reversed(list(gigs[:7])):
        chart_labels.append(g.mulai.strftime('%d %b'))
        chart_data.append(g.checkins.count())

    total_penonton = sum(g.checkins.count() for g in gigs)

    context = {
        'band': band,
        'gigs': gigs,
        'total_penonton': total_penonton,
        'total_gigs': gigs.count(),
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'interactions/dashboard_band.html', context)

