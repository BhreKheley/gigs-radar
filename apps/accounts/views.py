from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from .models import BandProfile
from .forms import DaftarForm, MasukForm, BandProfileForm
from apps.venues_gigs.models import Gig


def daftar_view(request):
    """Pendaftaran pengguna baru dengan pilihan peran Pengunjung atau Band."""
    if request.user.is_authenticated:
        return redirect('radar_index')

    role_awal = request.GET.get('role', 'pengunjung')
    if request.method == 'POST':
        form = DaftarForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                username = form.cleaned_data['username']
                email = form.cleaned_data.get('email', '')
                password = form.cleaned_data['password']
                role = form.cleaned_data['role']

                user = User.objects.create_user(username=username, email=email, password=password)

                if role == 'band':
                    BandProfile.objects.create(
                        user=user,
                        nama_band=form.cleaned_data['nama_band'],
                        genre=form.cleaned_data.get('genre', 'Indie') or 'Indie',
                        kontak_ig=form.cleaned_data.get('kontak_ig', '')
                    )
                    messages.success(request, f"Akun Musisi '{form.cleaned_data['nama_band']}' berhasil dibuat! Silakan masuk.")
                else:
                    messages.success(request, f"Akun Penonton '{username}' berhasil dibuat! Silakan masuk.")

                return redirect('masuk')
    else:
        form = DaftarForm(initial={'role': role_awal})

    return render(request, 'accounts/daftar.html', {'form': form})


def masuk_view(request):
    """Autentikasi login pengguna."""
    if request.user.is_authenticated:
        return redirect('radar_index')

    if request.method == 'POST':
        form = MasukForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                next_url = request.GET.get('next') or 'radar_index'
                messages.success(request, f"Selamat datang kembali, {user.username}!")
                return redirect(next_url)
            else:
                messages.error(request, "Nama pengguna atau kata sandi tidak cocok.")
    else:
        form = MasukForm()

    return render(request, 'accounts/masuk.html', {'form': form})


def keluar_view(request):
    """Logout sesi pengguna."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, "Anda telah keluar dari akun.")
    return redirect('radar_index')


@login_required
def profil_band_view(request):
    """Pengaturan profil panggung khusus musisi."""
    if not hasattr(request.user, 'band_profile'):
        messages.warning(request, "Halaman ini khusus untuk profil musisi / band.")
        return redirect('radar_index')

    profil = request.user.band_profile
    if request.method == 'POST':
        form = BandProfileForm(request.POST, request.FILES, instance=profil)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil panggung berhasil diperbarui!")
            return redirect('profil_band')
    else:
        form = BandProfileForm(instance=profil)

    return render(request, 'accounts/profil_band.html', {'form': form, 'profil': profil})


def band_detail_view(request, slug):
    """Halaman publik profil band lengkap dengan riwayat panggung dan ulasan."""
    band = get_object_or_404(BandProfile.objects.select_related('user'), slug=slug)
    
    # Ambil jadwal aktif dan riwayat panggung
    gigs_mendatang = band.gigs.filter(status__in=['TERJADWAL', 'LIVE']).select_related('venue').order_by('mulai')
    gigs_selesai = band.gigs.filter(status='SELESAI').select_related('venue').order_by('-selesai')[:5]
    
    is_following = False
    if request.user.is_authenticated:
        is_following = request.user.following.filter(band=band).exists()

    # Ambil ulasan dari penonton
    ratings = band.ratings.select_related('pengunjung', 'gig').order_by('-created_at')[:10]

    context = {
        'band': band,
        'gigs_mendatang': gigs_mendatang,
        'gigs_selesai': gigs_selesai,
        'is_following': is_following,
        'ratings': ratings,
    }
    return render(request, 'accounts/band_detail.html', context)


@login_required
def toggle_follow_view(request, slug):
    """Toggle ikuti/berhenti ikuti band oleh penonton."""
    band = get_object_or_404(BandProfile, slug=slug)

    # Validasi: Musisi dilarang follow band sendiri
    if band.user_id == request.user.id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Musisi tidak dapat mem-follow band sendiri.'}, status=403)
        messages.error(request, "Anda tidak dapat mengikuti band milik sendiri.")
        return redirect('band_detail', slug=slug)

    from apps.interactions.models import Follow
    follow_obj = Follow.objects.filter(pengunjung=request.user, band=band).first()

    if follow_obj:
        follow_obj.delete()
        following = False
        msg = f"Berhenti mengikuti {band.nama_band}."
    else:
        Follow.objects.create(pengunjung=request.user, band=band)
        following = True
        msg = f"Sekarang Anda mengikuti {band.nama_band}!"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'following': following,
            'followers_count': band.followers.count(),
            'message': msg
        })

    messages.info(request, msg)
    return redirect('band_detail', slug=slug)

