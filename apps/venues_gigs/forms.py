from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import Venue, Gig


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['nama', 'alamat', 'latitude', 'longitude', 'kontak']
        widgets = {
            'nama': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Contoh: Kopi Kukel 18'
            }),
            'alamat': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Alamat jalan, nomor, dan patokan'
            }),
            'latitude': forms.NumberInput(attrs={
                'step': 'any',
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
                'placeholder': '-6.3645'
            }),
            'longitude': forms.NumberInput(attrs={
                'step': 'any',
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
                'placeholder': '106.8242'
            }),
            'kontak': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Nomor telepon / kontak manajer kafe'
            }),
        }


class GigForm(forms.ModelForm):
    class Meta:
        model = Gig
        fields = ['venue', 'judul_acara', 'mulai', 'selesai']
        widgets = {
            'venue': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'
            }),
            'judul_acara': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Contoh: Akustik Malam Minggu Margonda'
            }),
            'mulai': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'
            }),
            'selesai': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/[0.05] border border-slate-300 dark:border-white/[0.1] text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        mulai = cleaned_data.get('mulai')
        selesai = cleaned_data.get('selesai')

        if mulai and selesai:
            # Validasi 1: waktu selesai harus lebih lambat dari mulai
            if selesai <= mulai:
                self.add_error('selesai', "Waktu selesai harus lebih lambat daripada waktu mulai.")

            # Validasi 2: durasi pertunjukan wajar (maksimal 8 jam, misal 20:00 s.d 04:00)
            if selesai > mulai + timedelta(hours=8):
                self.add_error('selesai', "Durasi gig maksimal 8 jam.")

        return cleaned_data

