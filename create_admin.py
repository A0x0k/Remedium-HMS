import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remedium_hms.settings')
django.setup()
from django.contrib.auth.models import User  # noqa: E402
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@hospital.com', 'password')
