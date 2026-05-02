import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import LoginUsuarioForm, RegistroUsuarioForm
from .models import ItemCatalogo, Pagamento
from .services import CartService, CheckoutService, catalog_tables_ready
from .services.cart import CartError, StockError
from .services.payments import StripeWebhookVerifier


# =========================
# PÁGINAS (LEGADO)
# =========================

@require_http_methods(["GET"])
def home(request):
    return render(request, "core/home.html")


@require_http_methods(["GET", "POST"])
def registro(request):
    if request.user.is_authenticated:
        return redirect("painel")

    form = RegistroUsuarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Conta criada com sucesso.")
        return redirect("painel")

    return render(request, "core/registro.html", {"form": form})


@require_http_methods(["GET", "POST"])
def entrar(request):
    if request.user.is_authenticated:
        return redirect("painel")

    form = LoginUsuarioForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Login realizado com sucesso.")
        return redirect("painel")

    return render(request, "core/login.html", {"form": form})


@login_required
@require_http_methods(["GET"])
def painel(request):
    return render(request, "core/painel.html")


# =========================
# API (USADA PELO REACT)
# =========================

@require_http_methods(["GET"])
def api_catalogo(request):
    itens = ItemCatalogo.objects.filter(ativo=True).select_related("tipo")

    data = []
    for item in itens:
        data.append({
            "id": str(item.id),
            "name": item.nome,
            "price": float(item.preco),
            "pixPrice": float(item.preco * 0.95),
            "image": "https://via.placeholder.com/300",
            "category": item.tipo.nome,
            "tag": None,
            "specs": {}
        })

    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def api_adicionar_carrinho(request):
    try:
        body = json.loads(request.body)
        item_id = body.get("item_id")
        quantidade = body.get("quantidade", 1)

        # usuário fixo temporário (evita problema de autenticação)
        user = User.objects.first()

        CartService.adicionar_item(user, item_id, quantidade)

        return JsonResponse({"message": "Item adicionado"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def api_carrinho(request):
    try:
        user = User.objects.first()

        carrinho = CartService.obter_carrinho(user)

        data = {
            "itens": [
                {
                    "id": str(item.item_catalogo.id),
                    "name": item.item_catalogo.nome,
                    "price": float(item.item_catalogo.preco),
                    "quantidade": item.quantidade,
                    "subtotal": float(item.subtotal),
                }
                for item in carrinho.itens.all()
            ],
            "total": float(carrinho.total),
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# =========================
# CHECKOUT / STRIPE
# =========================

@login_required
@require_http_methods(["POST"])
def iniciar_checkout(request):
    try:
        pagamento = CheckoutService.iniciar_checkout(request.user)
        return redirect(pagamento.metadata.get("checkout_url", "carrinho"))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    signature = request.headers.get("Stripe-Signature", "")

    if not StripeWebhookVerifier.verify(payload, signature):
        return JsonResponse({"error": "Assinatura inválida"}, status=400)

    try:
        event = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Payload inválido"}, status=400)

    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    checkout_id = obj.get("id")

    if not checkout_id:
        return HttpResponse(status=200)

    try:
        if event_type == "checkout.session.completed":
            CheckoutService.confirmar_pagamento(checkout_id)
        elif event_type in {"checkout.session.expired", "checkout.session.async_payment_failed"}:
            CheckoutService.cancelar_pagamento(checkout_id)
    except Pagamento.DoesNotExist:
        pass

    return HttpResponse(status=200)


# =========================
# OUTROS
# =========================

@require_http_methods(["POST"])
def sair(request):
    logout(request)
    return JsonResponse({"message": "Logout realizado"})


def health(request):
    return HttpResponse("ok", status=200)