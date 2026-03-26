# Backend Django - Impressões 3D

## Como rodar o projeto

1. Instale as dependências (ex.: `pip install django`).
2. Entre na pasta do projeto Django:
   ```bash
   cd django_min
   ```
3. Aplique as migrations:
   ```bash
   python manage.py migrate
   ```
4. Popule o catálogo com blocos iniciais de itens:
   ```bash
   python manage.py seed_catalogo
   ```
5. Rode o servidor:
   ```bash
   python manage.py runserver
   ```

## Fluxos implementados
- Autenticação de usuários (registro/login/logout).
- Catálogo com blocos de itens e adição ao carrinho com quantidade.
- Carrinho com atualização de quantidade e remoção de itens.
- Estrutura inicial de checkout/pagamentos preparada para integração Stripe.

> Se você receber erro `no such table: core_itemcatalogo`, execute novamente `python manage.py migrate`.
