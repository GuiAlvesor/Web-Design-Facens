# Lume 3D — Backend (Django)

API REST servida pelo Django. Deploy no **Render**.

## Deploy no Render

1. Conecte este repositório no Render: **New → Web Service**
2. Configure:
   - **Runtime:** Python
   - **Build Command:** `./build.sh`
   - **Start Command:** `cd django_min && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
3. Adicione as variáveis de ambiente (veja `.env.example`)
4. Após o deploy do frontend no Vercel, volte e defina `FRONTEND_URL`

## Variáveis de ambiente obrigatórias

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | PostgreSQL — gerado pelo Render |
| `DJANGO_SECRET_KEY` | Chave secreta longa |
| `FRONTEND_URL` | URL do Vercel (ex: `https://lume3d.vercel.app`) |
| `SITE_URL` | URL deste serviço (ex: `https://lume3d-api.onrender.com`) |
| `STRIPE_SECRET_KEY` | Chave secreta do Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret do webhook do Stripe |

## Desenvolvimento local

```bash
cp .env.example .env   # preencha as variáveis
pip install -r requirements.txt
cd django_min
python manage.py migrate
python manage.py seed_catalogo
python manage.py runserver   # porta 8000
```
