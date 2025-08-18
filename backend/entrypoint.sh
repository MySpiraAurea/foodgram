#!/bin/bash

python manage.py migrate --noinput

# python manage.py load_data_ingredients

python manage.py collectstatic --noinput

# cp -r /app/collected_static/. /var/html/static/

exec "$@"