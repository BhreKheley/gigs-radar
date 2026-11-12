from django import forms
from django.contrib.auth.models import User
from .models import BandProfile


class DaftarForm(forms.Form):
    ROLE_CHOICES = [
        ('pengunjung', 'Penonton / Pengunjung Musik'),
        ('band', 'Musisi / Grup Band'),
    ]

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'Masukkan username unik'
    }))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'nama@contoh.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'Minimal 8 karakter'
    }))
    password_konfirmasi = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'Ulangi kata sandi'
    }))
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect(attrs={
        'class': 'text-amber-500 focus:ring-amber-500'
    }))

    # Field khusus musisi
    nama_band = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'Contoh: Senja Margonda'
    }))
    tipe_musisi = forms.ChoiceField(
        choices=BandProfile.TIPE_MUSISI_CHOICES,
        required=False,
        initial='PERINTIS',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'
        })
    )
    genre = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'Contoh: Indie Folk, Jazz Fusion'
    }))
    kontak_ig = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'username_instagram'
    }))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username ini sudah terdaftar. Pilih username lain.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_konfirmasi')
        if p1 and p2 and p1 != p2:
            self.add_error('password_konfirmasi', "Konfirmasi kata sandi tidak cocok.")

        role = cleaned_data.get('role')
        if role == 'band':
            nama_band = cleaned_data.get('nama_band')
            if not nama_band:
                self.add_error('nama_band', "Musisi wajib mengisi Nama Panggung / Band.")
        return cleaned_data


class MasukForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'Username akun Anda'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
        'placeholder': 'Kata sandi'
    }))


class BandProfileForm(forms.ModelForm):
    class Meta:
        model = BandProfile
        fields = ['nama_band', 'tipe_musisi', 'genre', 'deskripsi', 'kontak_ig', 'foto']
        widgets = {
            'nama_band': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'}),
            'tipe_musisi': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'}),
            'genre': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'}),
            'deskripsi': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'}),
            'kontak_ig': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'}),
            'foto': forms.FileInput(attrs={'class': 'w-full text-xs text-slate-500 dark:text-zinc-400'}),
        }

