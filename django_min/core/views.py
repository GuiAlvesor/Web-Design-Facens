import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
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


@login_required
@require_http_methods(["GET"])
def catalogo(request):
    if not catalog_tables_ready():
        messages.error(request, "Banco não inicializado para catálogo/carrinho. Execute: python manage.py migrate")
        return render(request, "core/catalogo.html", {"itens": []})

    try:
        itens = list(ItemCatalogo.objects.filter(ativo=True).select_related("tipo"))
    except (OperationalError, ProgrammingError):
        messages.error(request, "Banco não inicializado para catálogo/carrinho. Execute: python manage.py migrate")
        itens = []

    return render(request, "core/catalogo.html", {"itens": itens})


@login_required
@require_http_methods(["GET"])
def carrinho(request):
    if not catalog_tables_ready():
        messages.error(request, "Banco não inicializado para catálogo/carrinho. Execute: python manage.py migrate")
        return render(request, "core/carrinho.html", {"carrinho": None})

    try:
        carrinho_usuario = CartService.obter_carrinho(request.user)
    except (OperationalError, ProgrammingError):
        messages.error(request, "Banco não inicializado para catálogo/carrinho. Execute: python manage.py migrate")
        carrinho_usuario = None

    return render(request, "core/carrinho.html", {"carrinho": carrinho_usuario})


@login_required
@require_http_methods(["POST"])
def adicionar_ao_carrinho(request, item_id):
    if not catalog_tables_ready():
        messages.error(request, "Banco não inicializado para catálogo/carrinho. Execute: python manage.py migrate")
        return redirect("catalogo")

    quantidade = int(request.POST.get("quantidade", 1))
    try:
        CartService.adicionar_item(request.user, item_id, quantidade)
        messages.success(request, "Item adicionado ao carrinho.")
    except (CartError, StockError, ValueError, OperationalError, ProgrammingError) as exc:
        messages.error(request, str(exc))
    return redirect("catalogo")


@login_required
@require_http_methods(["POST"])
def atualizar_quantidade_item(request, item_id):
    quantidade = int(request.POST.get("quantidade", 1))
    try:
        CartService.atualizar_quantidade(request.user, item_id, quantidade)
        messages.success(request, "Quantidade atualizada.")
    except (CartError, StockError, ValueError, OperationalError, ProgrammingError) as exc:
        messages.error(request, str(exc))
    return redirect("carrinho")


@login_required
@require_http_methods(["POST"])
def remover_do_carrinho(request, item_id):
    if not catalog_tables_ready():
        messages.error(request, "Banco não inicializado para catálogo/carrinho. Execute: python manage.py migrate")
        return redirect("carrinho")

    try:
        CartService.remover_item(request.user, item_id)
        messages.info(request, "Item removido do carrinho.")
    except (OperationalError, ProgrammingError) as exc:
        messages.error(request, str(exc))

    return redirect("carrinho")


@login_required
@require_http_methods(["POST"])
def iniciar_checkout(request):
    try:
        pagamento = CheckoutService.iniciar_checkout(request.user)
        messages.success(request, "Checkout criado com sucesso. Você será redirecionado para o Stripe.")
        return redirect(pagamento.metadata.get("checkout_url", "carrinho"))
    except (CartError, OperationalError, ProgrammingError) as exc:
        messages.error(request, str(exc))
        return redirect("carrinho")


@login_required
@require_http_methods(["GET"])
def checkout_placeholder(request, session_id):
    return render(request, "core/checkout.html", {"session_id": session_id})


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
        return HttpResponse(status=200)

    return HttpResponse(status=200)


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def ajustar_estoque(request, item_id):
    if not catalog_tables_ready():
        messages.error(request, "Banco não inicializado para catálogo/carrinho. Execute: python manage.py migrate")
        return redirect("catalogo")

    quantidade = int(request.POST.get("quantidade", 0))
    try:
        CartService.ajustar_estoque(item_id, quantidade)
        messages.success(request, "Estoque atualizado com sucesso.")
    except (StockError, ValueError, OperationalError, ProgrammingError) as exc:
        messages.error(request, str(exc))

    return redirect("catalogo")


@login_required
@require_http_methods(["POST"])
def sair(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("home")
