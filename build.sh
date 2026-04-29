#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

cd django_min
python manage.py collectstatic --noinput
python manage.py migrate