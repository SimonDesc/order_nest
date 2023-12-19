#!/bin/sh

cd src

pipenv run python manage.py migrate --no-input
pipenv run python manage.py collectstatic --no-input
pipenv run gunicorn order_nest.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - -w 4 --timeout 600
