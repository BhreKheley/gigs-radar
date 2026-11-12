"""
Core Views — Gigs Radar
Endpoint diagnostik, health check, dan utilitas sistem.
"""

import sys
import django
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone


def health_check_view(request):
    """
    Health check endpoint (/healthz) untuk monitoring uptime server,
    Docker container probe, Kubernetes liveness/readiness, dan reverse proxy.
    """
    db_status = "ok"
    try:
        connection.ensure_connection()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    is_healthy = (db_status == "ok")

    payload = {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'database': db_status,
        'framework': f"Django {django.__version__}",
        'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'timestamp': timezone.now().isoformat(),
        'timezone': str(timezone.get_current_timezone_name()),
        'service': 'Gigs Radar Platform',
    }

    status_code = 200 if is_healthy else 503
    return JsonResponse(payload, status=status_code)
