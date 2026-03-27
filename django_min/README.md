# Backend Django - Impressões 3D

## Como rodar o projeto

1. Instale as dependências (ex.: `pip install django`).
2. Entre na pasta do projeto Django:
   ```bash
   cd django_min
   ```
3. Configure variáveis de ambiente para pagamentos Stripe:
   ```bash
   export SITE_URL="http://localhost:8000"
   export STRIPE_SECRET_KEY="sk_test_..."
   export STRIPE_WEBHOOK_SECRET="whsec_..."
   ```
4. Aplique as migrations:
   ```bash
   python manage.py migrate
   ```
5. Popule o catálogo com blocos iniciais de itens:
   ```bash
   python manage.py seed_catalogo
   ```
6. Rode o servidor:
   ```bash
   python manage.py runserver
   ```

## Webhook Stripe
- Endpoint: `POST /webhooks/stripe/`
- Segurança: verificação de assinatura `Stripe-Signature` com tolerância de tempo.
- Eventos tratados:
  - `checkout.session.completed` → aprova pagamento e marca pedido como pago.
  - `checkout.session.expired` e `checkout.session.async_payment_failed` → recusa pagamento e restaura estoque.

## Fluxos implementados
- Autenticação de usuários (registro/login/logout).
- Catálogo com blocos de itens e adição ao carrinho com quantidade.
- Carrinho com atualização de quantidade e remoção de itens.
- Checkout com criação de sessão Stripe, persistência do pagamento, baixa de estoque e rollback transacional.
- Webhook para confirmação/cancelamento de pagamento e conciliação de pedido/estoque.

> Se você receber erro `no such table: core_itemcatalogo`, execute novamente `python manage.py migrate`.
