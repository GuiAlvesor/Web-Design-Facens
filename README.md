# Lume 3D — Back-end

Projeto acadêmico (e-commerce focado em impressão 3D) criado para a disciplina de Desenvolvimento Web. O back-end é responsável por autenticação de usuários, catálogo de produtos, carrinho de compras, processamento de pagamentos via Stripe e integração com banco de dados PostgreSQL.

---

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Instalação rápida](#instalação-rápida)
- [Scripts disponíveis](#scripts-disponíveis)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Rotas da API](#rotas-da-api)
- [Dependências importantes](#dependências-importantes)
- [Deploy](#deploy)
- [Padrão de branches e contribuição](#padrão-de-branches-e-contribuição)
- [Problemas comuns](#problemas-comuns)

---

## Pré-requisitos

- Python 3.12+
- pip
- Git

---

## Instalação rápida

1. Clone o repositório:

```bash
git clone https://github.com/GuiAlvesor/Web-Design-Facens.git
cd Web-Design-Facens/django_min
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente criando um arquivo `.env` na pasta `django_min/`:

```env
SECRET_KEY=sua-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=URL-gerada-pelo-render
SITE_URL=URL-deste-serviço
STRIPE_SECRET_KEY=chave-secreta-do-stripe
STRIPE_WEBHOOK_SECRET=secret-do-webhook-do-stripe
```

4. Rode as migrations:

```bash
python manage.py migrate
```

5. Popule o banco com produtos de exemplo:

```bash
python manage.py seed_catalogo
```

6. Inicie o servidor de desenvolvimento:

```bash
python manage.py runserver
```

---

## Scripts disponíveis

- `python manage.py runserver` — inicia o servidor de desenvolvimento
- `python manage.py migrate` — aplica as migrations no banco de dados
- `python manage.py makemigrations` — gera novas migrations a partir das alterações nos models
- `python manage.py seed_catalogo` — popula o banco com produtos de exemplo
- `python manage.py createsuperuser` — cria um usuário administrador

---

## Variáveis de ambiente

| Variável | Descrição | Obrigatória |
|---|---|---|
| `SECRET_KEY` | Chave secreta do Django | ✅ |
| `DEBUG` | Modo de depuração (`True` em dev, `False` em produção) | ✅ |
| `ALLOWED_HOSTS` | Domínios permitidos separados por vírgula | ✅ |
| `DATABASE_URL` | URL de conexão com o banco de dados | ✅ |
| `SITE_URL` | URL base do site (usada nos redirecionamentos do Stripe) | ✅ |
| `FRONTEND_URL` | URL do vercel | ✅ | 
| `STRIPE_SECRET_KEY` | Chave secreta da API do Stripe | ⚠️ Necessária para pagamentos |
| `STRIPE_WEBHOOK_SECRET` | Segredo do webhook do Stripe | ⚠️ Necessário para webhooks |

---

## Rotas da API

> Observação: As rotas abaixo representam a estrutura geral da API e podem sofrer alterações.

### Autenticação

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| `GET` | `/` | Página inicial | Não |
| `POST` | `/registro/` | Cadastro de novo usuário | Não |
| `POST` | `/login/` | Login de usuário | Não |
| `POST` | `/logout/` | Logout de usuário | Sim |
| `GET` | `/painel/` | Painel do usuário | Sim |

### Catálogo

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| `GET` | `/catalogo/` | Lista de produtos disponíveis | Sim |

### Carrinho

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| `GET` | `/carrinho/` | Visualizar carrinho | Sim |
| `POST` | `/carrinho/adicionar/<item_id>/` | Adicionar item ao carrinho | Sim |
| `POST` | `/carrinho/atualizar/<item_id>/` | Atualizar quantidade de item | Sim |
| `POST` | `/carrinho/remover/<item_id>/` | Remover item do carrinho | Sim |
| `POST` | `/carrinho/checkout/` | Iniciar checkout via Stripe | Sim |

### Pagamentos

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| `GET` | `/pagamentos/checkout/sucesso/` | Página de retorno após pagamento | Sim |
| `POST` | `/webhooks/stripe/` | Webhook de eventos do Stripe | Não (uso interno) |

### Admin

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| `POST` | `/estoque/ajustar/<item_id>/` | Ajustar estoque de produto | Sim (staff) |

---

## Dependências importantes

- `Django` — framework web principal
- `gunicorn` — servidor WSGI para produção
- `whitenoise` — serviço de arquivos estáticos em produção
- `psycopg2-binary` — driver de conexão com PostgreSQL
- `python-decouple` — gerenciamento de variáveis de ambiente via `.env`
- `dj-database-url` — conversão da URL do banco para configuração Django
- `stripe` — integração com a API de pagamentos do Stripe

Veja o `requirements.txt` para a lista completa de dependências.

---

## Deploy

O projeto está configurado para deploy no [Render](https://render.com).

**Variáveis de ambiente necessárias no Render:**

- Todas as listadas na seção [Variáveis de ambiente](#variáveis-de-ambiente)
- `DATABASE_URL` gerada automaticamente ao criar um banco PostgreSQL no Render

**Comando de build:**
```
./build.sh
```

**Comando de start:**
```
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

> Após o primeiro deploy ou ao aplicar novas migrations, adicione temporariamente ao start command: `python manage.py migrate && gunicorn config.wsgi`. Após o deploy, volte para `gunicorn config.wsgi`.

---

## Padrão de branches e contribuição

O projeto adota um fluxo em três etapas com as branches:

- `features` — entrada de conteúdo novo
- `develop` — homologação e consolidação
- `main` — estável e produção

### Política obrigatória

- Commits de novas funcionalidades, correções e refactors devem ser feitos em `features`.
- A `develop` deve receber mudanças validadas via merge/PR aprovado de `features`.
- A `main` deve receber código somente via merge/PR aprovado de `develop`.
- **Nunca commitar diretamente na `main`.**

### Processo de entrega

1. Crie uma branch a partir de `features`:
```bash
git checkout -b feat/minha-feature
```
2. Implemente e commite suas alterações.
3. Abra PR de `features` → `develop` com descrição técnica.
4. Após aprovação em `develop`, abra PR de `develop` → `main`.
5. Faça merge em `main` apenas após revisão e aprovação final.

### Documentação por branch

- `FEATURES.md` — entrada de conteúdo novo
- `DEVELOP.md` — validação e consolidação
- `MAIN.md` — versão estável de produção

Fluxo obrigatório: `features` → `develop` → `main`.

---

## Problemas comuns

- **Erro de `SECRET_KEY` não encontrada** — verifique se o arquivo `.env` existe na pasta `django_min/` e se a variável está preenchida.
- **Erro de `DATABASE_URL` não encontrada** — adicione a variável no `.env` com o valor `sqlite:///db.sqlite3` para desenvolvimento local.
- **Catálogo vazio** — rode `python manage.py seed_catalogo` para popular o banco com produtos de exemplo.
- **Webhook do Stripe retornando 400** — verifique se o `STRIPE_WEBHOOK_SECRET` está correto e se o endpoint está cadastrado no painel do Stripe.