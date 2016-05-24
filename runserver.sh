#!/bin/bash
pip --update pip
python manage.py runserver --noreload --nostatic 0.0.0.0:$VCAP_APP_PORT
