from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q
from django.conf import settings
from apps.venues_gigs.models import Venue, Gig
from apps.accounts.models import BandProfile
from core.services import hitung_jarak_km, hitung_bounding_box


# Preset Koordinat Demo (Margonda & Kawasan Kampus UI Depok)
PRESET_DEMO_LOKASI = [
    {
        'id': 'kukel',
        'nama': 'Kafe Kukusan (Kukel 18)',
        'lat': -6.3645,
        'lng': 106.8242,
        'desc': 'Di dalam kafe (18m dari Kopi Kukel)'
    },
    {
        'id': 'barel',
        'nama': 'Panggung Barel (Beji)',
        'lat': -6.3688,
        'lng': 106.8315,
        'desc': 'Area tongkrongan Barel (dekat stasiun)'
    },
    {
        'id': 'teras',
        'nama': 'Teras Akustik Margonda',
        'lat': -6.3732,
        'lng': 106.8348,
        'desc': 'Koridor utama Margonda Raya'
    },
    {
        'id': 'pocin',
        'nama': 'Stasiun Pondok Cina',
        'lat': -6.3612,
        'lng': 106.8331,
        'desc': 'Titik transit mahasiswa UI'
    },
    {
        'id': 'kutek',
        'nama': 'Sudut Kopi Kutek',
        'lat': -6.3589,
        'lng': 106.8194,
        'desc': 'Kukusan Teknik (Kutek UI)'
    },
]


def radar_index(request):
    """Halaman utama Peta Radar Geospasial Interaktif."""
    genres_list = Gig.objects.values_list('band__genre', flat=True).distinct()
    context = {
        'presets_demo': PRESET_DEMO_LOKASI,
        'genres_list': set(filter(None, genres_list)),
    }
    return render(request, 'radar_map/index.html', context)


def landing_page_view(request):
    """
    Landing Page resmi Gigs Radar (sesuai spesifikasi Xplor.in & DDP1):
    Menampilkan Value Proposition, Live Stats, 3 Pilar Keunggulan, Trending Bands, dan CTA.
    """
    total_venues = Venue.objects.count()
    total_bands = BandProfile.objects.count()
    live_gigs_count = Gig.objects.filter(status='LIVE').count()

    trending_bands = BandProfile.objects.annotate(
        follower_count=Count('followers')
    ).order_by('-follower_count')[:4]

    featured_gigs = Gig.objects.filter(
        status__in=['LIVE', 'TERJADWAL']
    ).select_related('band', 'venue').order_by('mulai')[:3]

    context = {
        'total_venues': total_venues,
        'total_bands': total_bands,
        'live_gigs_count': live_gigs_count,
        'trending_bands': trending_bands,
        'featured_gigs': featured_gigs,
    }
    return render(request, 'radar_map/landing.html', context)


def api_live(request):
    """
    Endpoint JSON untuk mendapatkan gig-gig LIVE dalam radius km dari posisi pengguna.
    Menggunakan pra-filter Bounding-Box SQL lalu kalkulasi Haversine presisi.
    """
    lat_str = request.GET.get('lat')
    lng_str = request.GET.get('lng')

    if not lat_str or not lng_str:
        return JsonResponse({'gigs': []})

    try:
        user_lat = float(lat_str)
        user_lng = float(lng_str)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Parameter lat dan lng harus berupa angka desimal.'}, status=400)

    try:
        radius_km = float(request.GET.get('radius', '5.0'))
        radius_km = min(max(0.05, radius_km), 50.0)
    except (ValueError, TypeError):
        radius_km = 5.0

    genre_filter = request.GET.get('genre', '').strip()
    q_filter = request.GET.get('q', '').strip()

    # 1. Bounding-Box SQL Pre-filter
    min_lat, max_lat, min_lon, max_lon = hitung_bounding_box(user_lat, user_lng, radius_km)

    # 2. Query gig LIVE yang venuenya berada dalam bounding box
    gigs_qs = Gig.objects.select_related('band', 'venue').filter(
        status='LIVE',
        venue__latitude__gte=min_lat,
        venue__latitude__lte=max_lat,
        venue__longitude__gte=min_lon,
        venue__longitude__lte=max_lon
    )

    if genre_filter:
        gigs_qs = gigs_qs.filter(band__genre__icontains=genre_filter)

    if q_filter:
        gigs_qs = gigs_qs.filter(
            Q(judul_acara__icontains=q_filter) |
            Q(band__nama_band__icontains=q_filter) |
            Q(venue__nama__icontains=q_filter)
        )

    # 3. Filter Haversine dan susun respons JSON
    hasil_gigs = []
    for gig in gigs_qs:
        # Cek evaluasi lazy jika gig sudah lewat jam selesai
        if gig.status_efektif != 'LIVE':
            continue

        jarak_km = hitung_jarak_km(user_lat, user_lng, gig.venue.latitude, gig.venue.longitude)
        if jarak_km <= radius_km:
            jarak_m = int(jarak_km * 1000)
            heat = gig.crowd_heat

            hasil_gigs.append({
                'id': gig.id,
                'gig_id': gig.id,
                'judul': gig.judul_acara,
                'band_nama': gig.band.nama_band,
                'band_slug': gig.band.slug,
                'genre': gig.band.genre,
                'venue_nama': gig.venue.nama,
                'venue_alamat': gig.venue.alamat,
                'lat': gig.venue.latitude,
                'lng': gig.venue.longitude,
                'jarak_m': jarak_m,
                'jarak_km': round(jarak_km, 2),
                'sisa_menit': gig.sisa_menit,
                'crowd_heat': heat['level'],
                'crowd_label': heat['label'],
                'crowd_color': heat['color'],
                'total_checkin': gig.checkins.count(),
                'rating_rata': gig.band.rata_rata_rating,
                'url_detail': f"/gig/{gig.id}/"
            })

    # Urutkan berdasarkan jarak terdekat ke pengguna
    hasil_gigs.sort(key=lambda x: x['jarak_m'])

    return JsonResponse({'gigs': hasil_gigs})

