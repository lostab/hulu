import os

os.system('python manage.py migrate --run-syncdb')
os.system('python manage.py makemigrations')
os.system('python manage.py migrate')

port = '80'

if 'PORT' in os.environ:
    port = os.environ['PORT']
#os.system('python cron.py &')
os.system('python manage.py runserver --insecure 0.0.0.0:' + port)
