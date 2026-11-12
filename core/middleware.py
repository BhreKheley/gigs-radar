"""
Enterprise Middleware Layer — Gigs Radar
Menyediakan:
1. RequestTimingMiddleware: Observabilitas latensi request server dalam milidetik.
2. EnterpriseSecurityHeadersMiddleware: Hardening header keamanan web browser.
3. RateLimitProtectionMiddleware: Mitigasi brute-force & spamming pada endpoint sensitif.
"""

import time
import logging
from collections import defaultdict
from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('gigsradar.performance')


class RequestTimingMiddleware:
    """
    Mengukur durasi eksekusi request dan menyematkan header 'X-Response-Time-ms'.
    Mencatat log warning untuk request lambat (> 500ms) untuk observabilitas backend.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response['X-Response-Time-ms'] = str(duration_ms)

        if duration_ms > 500:
            logger.warning(
                f"[SLOW REQUEST] {request.method} {request.path} took {duration_ms}ms"
            )

        return response


class EnterpriseSecurityHeadersMiddleware:
    """
    Menambahkan header keamanan enterprise standar OWASP:
    - X-Content-Type-Options: nosniff
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(self), camera=(), microphone=()
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = 'geolocation=(self), camera=(), microphone=()'
        return response


class RateLimitProtectionMiddleware:
    """
    Sliding-window in-memory rate limiter untuk mitigasi brute force pada endpoint sensitif:
    - POST /masuk/
    - POST /daftar/
    - POST /api/checkin/
    Maksimal 40 request per menit per IP address.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.ip_hits = defaultdict(list)
        self.max_requests_per_minute = 40
        self.window_seconds = 60

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip

    def __call__(self, request):
        # Hanya batasi POST pada endpoint sensitif
        sensitive_paths = ['/masuk/', '/daftar/', '/api/checkin/']
        is_sensitive = request.method == 'POST' and any(request.path.startswith(p) for p in sensitive_paths)

        if is_sensitive:
            ip = self._get_client_ip(request)
            now = time.time()
            # Hapus hit yang lebih lama dari 60 detik
            valid_hits = [t for t in self.ip_hits[ip] if now - t < self.window_seconds]
            
            if len(valid_hits) >= self.max_requests_per_minute:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'api' in request.path:
                    return JsonResponse({
                        'error': 'Terlalu banyak permintaan (Rate limit exceeded). Silakan coba lagi beberapa saat.'
                    }, status=429)
                return HttpResponse(
                    "Terlalu banyak permintaan. Demi keamanan sistem, mohon tunggu sebentar sebelum mencoba lagi.",
                    status=429,
                    content_type="text/plain; charset=utf-8"
                )

            valid_hits.append(now)
            self.ip_hits[ip] = valid_hits

        return self.get_response(request)
