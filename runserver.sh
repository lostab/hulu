#!/bin/bash
python manage.py runserver --noreload 0.0.0.0:$VCAP_APP_PORT