from django.conf import settings


def app_context(request):
    """Context processor global untuk menyediakan variabel demo_mode dan status tema."""
    return {
        'DEMO_MODE': getattr(settings, 'DEMO_MODE', True),
        'APP_NAME': 'Gigs Radar',
    }

