from django.urls import path

from .views import (
    adicionar_ao_carrinho,
    ajustar_estoque,
    atualizar_quantidade_item,
    carrinho,
    checkout_placeholder,
    catalogo,
    entrar,
    home,
    iniciar_checkout,
    painel,
    registro,
    remover_do_carrinho,
    sair,
    stripe_webhook,
)

urlpatterns = [
    path('', home, name='home'),
    path('registro/', registro, name='registro'),
    path('login/', entrar, name='login'),
    path('painel/', painel, name='painel'),
    path('catalogo/', catalogo, name='catalogo'),
    path('carrinho/', carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:item_id>/', adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/atualizar/<int:item_id>/', atualizar_quantidade_item, name='atualizar_quantidade_item'),
    path('carrinho/remover/<int:item_id>/', remover_do_carrinho, name='remover_do_carrinho'),
    path('carrinho/checkout/', iniciar_checkout, name='iniciar_checkout'),
    path('pagamentos/checkout/<str:session_id>/', checkout_placeholder, name='checkout_placeholder'),
    path('webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
    path('estoque/ajustar/<int:item_id>/', ajustar_estoque, name='ajustar_estoque'),
    path('logout/', sair, name='logout'),
]
