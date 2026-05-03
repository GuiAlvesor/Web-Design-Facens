#!/usr/bin/env bash
set -o errexit

echo "=== [1/3] Instalando dependências Python ==="
pip install -r requirements.txt

echo "=== [2/3] Django: migrate + collectstatic + seed ==="
cd django_min
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_catalogo
cd ..

echo "=== Build concluído ==="