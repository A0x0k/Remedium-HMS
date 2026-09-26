web: gunicorn remedium_hms.wsgi
release: python manage.py migrate && python manage.py create_groups && python manage.py create_demo_user --if-enabled
