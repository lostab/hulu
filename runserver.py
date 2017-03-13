import os

os.system('python manage.py migrate --run-syncdb')
os.system('python manage.py makemigrations')
os.system('python manage.py migrate')

if 'PORT' in os.environ:
    #os.system('python cron.py &')
    os.system('python manage.py runserver --noreload --nostatic 0.0.0.0:' + os.environ['PORT'])
else:
    os.system('python manage.py runserver 0.0.0.0:8000')
