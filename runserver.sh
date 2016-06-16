#!/bin/bash
python manage.py migrate --run-syncdb
python manage.py runserver --noreload --nostatic 0.0.0.0:$VCAP_APP_PORT
