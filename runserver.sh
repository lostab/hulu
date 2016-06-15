#!/bin/bash
python manage.py syncdb
python manage.py runserver --noreload --nostatic 0.0.0.0:$VCAP_APP_PORT
