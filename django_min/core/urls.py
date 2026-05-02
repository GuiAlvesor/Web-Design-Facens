from django.urls import path
from .views import (
    home,
    registro,
    entrar,
    painel,
    api_catalogo,
    api_adicionar_carrinho,
    api_carrinho,
    iniciar_checkout,
    stripe_webhook,
    sair,
    health,
)

urlpatterns = [
    # páginas (opcional)
    path('', home),
    path('registro/', registro),
    path('login/', entrar),
    path('painel/', painel),

    # API (React usa isso)
    path('api/catalogo/', api_catalogo),
    path('api/carrinho/', api_carrinho),
    path('api/carrinho/adicionar/', api_adicionar_carrinho),

    # checkout
    path('api/checkout/', iniciar_checkout),
    path('webhooks/stripe/', stripe_webhook),

    # outros
    path('logout/', sair),
    path('health/', health),
]