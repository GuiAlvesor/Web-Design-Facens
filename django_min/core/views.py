from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginUsuarioForm, RegistroUsuarioForm
from .models import ItemCatalogo
from .services import CartService
from .services.cart import CartError, StockError


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
    itens = ItemCatalogo.objects.filter(ativo=True).select_related("tipo")
    return render(request, "core/catalogo.html", {"itens": itens})


@login_required
@require_http_methods(["GET"])
def carrinho(request):
    carrinho_usuario = CartService.obter_carrinho(request.user)
    return render(request, "core/carrinho.html", {"carrinho": carrinho_usuario})


@login_required
@require_http_methods(["POST"])
def adicionar_ao_carrinho(request, item_id):
    quantidade = int(request.POST.get("quantidade", 1))
    try:
        CartService.adicionar_item(request.user, item_id, quantidade)
        messages.success(request, "Item adicionado ao carrinho.")
    except (CartError, StockError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect("catalogo")


@login_required
@require_http_methods(["POST"])
def remover_do_carrinho(request, item_id):
    CartService.remover_item(request.user, item_id)
    messages.info(request, "Item removido do carrinho.")
    return redirect("carrinho")


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def ajustar_estoque(request, item_id):
    quantidade = int(request.POST.get("quantidade", 0))
    try:
        CartService.ajustar_estoque(item_id, quantidade)
        messages.success(request, "Estoque atualizado com sucesso.")
    except (StockError, ValueError) as exc:
        messages.error(request, str(exc))

    return redirect("catalogo")


@login_required
@require_http_methods(["POST"])
def sair(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("home")
