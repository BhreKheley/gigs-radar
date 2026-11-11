"""
WSGI config for livemusic_project project.
"""

import os
import logging
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'livemusic_project.settings')

application = get_wsgi_application()
app = application

# Auto-bootstrap database on Vercel Serverless cold-start
if os.environ.get('VERCEL') or os.environ.get('AUTO_BOOTSTRAP_DB'):
    try:
        from django.db import connection
        from django.core.management import call_command
        tables = connection.introspection.table_names()
        if 'auth_user' not in tables or 'venues_gigs_venue' not in tables:
            call_command('migrate', interactive=False)
            call_command('seed_demo')
    except Exception as exc:
        logging.getLogger('django').error(f"Auto-bootstrap database error: {exc}", exc_info=True)
