from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginUsuarioForm, RegistroUsuarioForm


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
@require_http_methods(["POST"])
def sair(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("home")
