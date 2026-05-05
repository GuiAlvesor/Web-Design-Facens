import json

from decimal import Decimal

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import ItemCatalogo, Pagamento, Pedido, ItemPedido
from .services import CartService, CheckoutService, catalog_tables_ready
from .services.cart import CartError, StockError
from .services.payments import StripeWebhookVerifier
from .services.email import enviar_email_boas_vindas


# ─── helpers ──────────────────────────────────────────────────────────────────

def _json_body(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


def _user_required(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Autenticação necessária."}, status=401)
    return None


# ─── CSRF ─────────────────────────────────────────────────────────────────────

@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_token_view(request):
    return JsonResponse({"detail": "CSRF cookie definido."})


# ─── AUTH ─────────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def api_me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"user": None})
    u = request.user
    return JsonResponse({
        "user": {
            "id": u.id,
            "name": u.first_name or u.username,
            "email": u.email,
            "username": u.username,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    body = _json_body(request)
    identifier = body.get("username", "").strip()
    password = body.get("password", "")

    if not identifier or not password:
        return JsonResponse({"error": "Usuário e senha são obrigatórios."}, status=400)

    if "@" in identifier:
        try:
            user_obj = User.objects.get(email__iexact=identifier)
            identifier = user_obj.username
        except User.DoesNotExist:
            return JsonResponse({"error": "Credenciais inválidas."}, status=401)

    user = authenticate(request, username=identifier, password=password)
    if user is None:
        return JsonResponse({"error": "Credenciais inválidas."}, status=401)

    login(request, user)
    return JsonResponse({
        "user": {
            "id": user.id,
            "name": user.first_name or user.username,
            "email": user.email,
            "username": user.username,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_signup(request):
    body = _json_body(request)
    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not name or not email or not password:
        return JsonResponse({"error": "Nome, e-mail e senha são obrigatórios."}, status=400)

    if len(password) < 6:
        return JsonResponse({"error": "A senha deve ter pelo menos 6 caracteres."}, status=400)

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"error": "Este e-mail já está cadastrado."}, status=400)

    base = name.lower().replace(" ", "")[:20]
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=name.split()[0],
        last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "",
    )
    login(request, user)
    enviar_email_boas_vindas(
        nome=user.first_name,
        email_destino=user.email,
    )
    return JsonResponse({
        "user": {
            "id": user.id,
            "name": user.first_name or user.username,
            "email": user.email,
            "username": user.username,
        }
    }, status=201)


@require_http_methods(["POST"])
def api_logout(request):
    logout(request)
    return JsonResponse({"detail": "Logout realizado."})

@csrf_exempt
@require_http_methods(["POST"])
def api_change_password(request):
    err = _user_required(request)
    if err:
        return err

    body = _json_body(request)
    senha_atual = body.get("current_password", "")
    nova_senha = body.get("new_password", "")

    if not senha_atual or not nova_senha:
        return JsonResponse({"error": "Senha atual e nova senha são obrigatórias."}, status=400)

    if len(nova_senha) < 6:
        return JsonResponse({"error": "A nova senha deve ter pelo menos 6 caracteres."}, status=400)

    user = authenticate(request, username=request.user.username, password=senha_atual)
    if user is None:
        return JsonResponse({"error": "Senha atual incorreta."}, status=401)

    user.set_password(nova_senha)
    user.save()
    login(request, user)  # mantém a sessão ativa após trocar a senha
    return JsonResponse({"detail": "Senha alterada com sucesso."})


# ─── CATÁLOGO ─────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def api_catalogo(request):
    itens = ItemCatalogo.objects.filter(ativo=True).select_related("tipo")
    data = []
    for item in itens:
        preco = float(item.preco)
        data.append({
            "id": item.slug,
            "db_id": item.id,
            "name": item.nome,
            "price": preco,
            "pixPrice": round(preco * 0.9, 2),
            "category": item.tipo.nome,
            "tag": item.tag or None,
            "description": item.descricao,
            "specs": item.specs or {},
            "estoque": item.estoque,
        })
    return JsonResponse(data, safe=False)


# ─── CARRINHO ─────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def api_carrinho(request):
    err = _user_required(request)
    if err:
        return err

    carrinho = CartService.obter_carrinho(request.user)
    itens = carrinho.itens.select_related("item_catalogo__tipo").all()

    data = {
        "itens": [
            {
                "id": item.item_catalogo.slug,
                "db_id": item.item_catalogo.id,
                "name": item.item_catalogo.nome,
                "price": float(item.item_catalogo.preco),
                "category": item.item_catalogo.tipo.nome,
                "tag": item.item_catalogo.tag or None,
                "quantity": item.quantidade,
                "subtotal": float(item.subtotal),
            }
            for item in itens
        ],
        "total": float(carrinho.total),
    }
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["POST"])
def api_adicionar_carrinho(request):
    err = _user_required(request)
    if err:
        return err

    body = _json_body(request)
    db_id = body.get("db_id")
    quantidade = int(body.get("quantidade", 1))

    if not db_id:
        return JsonResponse({"error": "db_id é obrigatório."}, status=400)

    try:
        CartService.adicionar_item(request.user, db_id, quantidade)
        return JsonResponse({"detail": "Item adicionado ao carrinho."})
    except StockError as e:
        return JsonResponse({"error": str(e)}, status=409)
    except CartError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except ItemCatalogo.DoesNotExist:
        return JsonResponse({"error": "Produto não encontrado."}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def api_atualizar_carrinho(request):
    err = _user_required(request)
    if err:
        return err

    body = _json_body(request)
    db_id = body.get("db_id")
    quantidade = int(body.get("quantidade", 1))

    if not db_id:
        return JsonResponse({"error": "db_id é obrigatório."}, status=400)

    try:
        if quantidade <= 0:
            CartService.remover_item(request.user, db_id)
            return JsonResponse({"detail": "Item removido."})
        CartService.atualizar_quantidade(request.user, db_id, quantidade)
        return JsonResponse({"detail": "Carrinho atualizado."})
    except StockError as e:
        return JsonResponse({"error": str(e)}, status=409)
    except CartError as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_remover_carrinho(request):
    err = _user_required(request)
    if err:
        return err

    body = _json_body(request)
    db_id = body.get("db_id")
    if not db_id:
        return JsonResponse({"error": "db_id é obrigatório."}, status=400)

    CartService.remover_item(request.user, db_id)
    return JsonResponse({"detail": "Item removido."})


@csrf_exempt
@require_http_methods(["POST"])
def api_limpar_carrinho(request):
    err = _user_required(request)
    if err:
        return err

    carrinho = CartService.obter_carrinho(request.user)
    carrinho.itens.all().delete()
    return JsonResponse({"detail": "Carrinho limpo."})


# ─── PEDIDOS ──────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def api_pedidos(request):
    err = _user_required(request)
    if err:
        return err

    pedidos = (
        Pedido.objects
        .filter(usuario=request.user)
        .prefetch_related("itens__item_catalogo")
        .order_by("-criado_em")
    )

    data = []
    for pedido in pedidos:
        data.append({
            "id": pedido.id,
            "status": pedido.status,
            "valor_total": float(pedido.valor_total),
            "criado_em": pedido.criado_em.isoformat(),
            "itens": [
                {
                    "nome": it.nome_item,
                    "preco_unitario": float(it.preco_unitario),
                    "quantidade": it.quantidade,
                    "subtotal": float(it.subtotal),
                }
                for it in pedido.itens.all()
            ],
        })
    return JsonResponse(data, safe=False)


# ─── CHECKOUT ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def api_checkout(request):
    """
    POST /api/checkout/
    Cria o pedido e retorna a URL do Stripe para redirecionar o usuário.
    """
    err = _user_required(request)
    if err:
        return err

    body = _json_body(request)
    frete_nome = body.get("frete_nome", None)
    frete_valor = Decimal(str(body.get("frete_valor", 0)))
    desconto = Decimal(str(body.get("desconto", 0)))

    try:
        pagamento = CheckoutService.iniciar_checkout(
            request.user,
            frete_nome=frete_nome,
            frete_valor=frete_valor,
            desconto=desconto,
        )
        checkout_url = pagamento.metadata.get("checkout_url", "")
        return JsonResponse({
            "checkout_url": checkout_url,
            "pedido_id": pagamento.pedido_id,
            "pagamento_id": pagamento.id,
            "checkout_id": pagamento.checkout_id,
        })
    except CartError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Erro interno ao iniciar checkout."}, status=500)


@require_http_methods(["GET"])
def api_checkout_status(request):
    """
    GET /api/checkout/status/?session_id=sess_xxx
    Consultado pelo frontend após o usuário retornar do Stripe.
    Retorna status do pagamento e dados do pedido.
    """
    err = _user_required(request)
    if err:
        return err

    session_id = request.GET.get("session_id", "").strip()
    if not session_id:
        return JsonResponse({"error": "session_id é obrigatório."}, status=400)

    try:
        pagamento = (
            Pagamento.objects
            .select_related("pedido")
            .prefetch_related("pedido__itens")
            .get(checkout_id=session_id, pedido__usuario=request.user)
        )
    except Pagamento.DoesNotExist:
        return JsonResponse({"error": "Sessão não encontrada."}, status=404)

    pedido = pagamento.pedido
    return JsonResponse({
        "status": pagamento.status,          # pendente | aprovado | recusado
        "pedido_id": pedido.id,
        "valor_total": float(pedido.valor_total),
        "criado_em": pedido.criado_em.isoformat(),
        "itens": [
            {
                "nome": it.nome_item,
                "preco_unitario": float(it.preco_unitario),
                "quantidade": it.quantidade,
                "subtotal": float(it.subtotal),
            }
            for it in pedido.itens.all()
        ],
    })


# ─── STRIPE WEBHOOK ───────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    signature = request.headers.get("Stripe-Signature", "")

    if not StripeWebhookVerifier.verify(payload, signature):
        return JsonResponse({"error": "Assinatura inválida."}, status=400)

    try:
        event = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Payload inválido."}, status=400)

    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    checkout_id = obj.get("id")

    if not checkout_id:
        from django.http import HttpResponse
        return HttpResponse(status=200)

    try:
        if event_type == "checkout.session.completed":
            CheckoutService.confirmar_pagamento(checkout_id)
        elif event_type in {"checkout.session.expired", "checkout.session.async_payment_failed"}:
            CheckoutService.cancelar_pagamento(checkout_id)
    except Pagamento.DoesNotExist:
        pass

    from django.http import HttpResponse
    return HttpResponse(status=200)


# ─── HEALTH ───────────────────────────────────────────────────────────────────

def health(request):
    from django.http import HttpResponse
    return HttpResponse("ok", status=200)
