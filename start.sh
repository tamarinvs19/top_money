#!/bin/bash

set -e

export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export DJANGO_SECRET_KEY=$(grep DJANGO_SECRET_KEY .env | cut -d'=' -f2-)

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
