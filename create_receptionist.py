import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remedium_hms.settings')
django.setup()
from django.contrib.auth.models import User, Group  # noqa: E402
user = User.objects.create_user('adam_ahmed', 'adam@hospital.com', '123456789')
group = Group.objects.get(name='Receptionist')
user.groups.add(group)
user.save()
print("User adam_ahmed created and added to Receptionist group.")
