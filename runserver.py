import os

os.system('python manage.py makemigrations')
os.system('python manage.py migrate')

if 'VCAP_APP_PORT' in os.environ:
    os.system('python manage.py runserver --noreload --nostatic 0.0.0.0:' + os.environ['VCAP_APP_PORT'])
else:
    os.system('python manage.py runserver 0.0.0.0:8000')
