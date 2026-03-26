from django.urls import path

from .views import (
    adicionar_ao_carrinho,
    ajustar_estoque,
    carrinho,
    catalogo,
    entrar,
    home,
    painel,
    registro,
    remover_do_carrinho,
    sair,
)

urlpatterns = [
    path('', home, name='home'),
    path('registro/', registro, name='registro'),
    path('login/', entrar, name='login'),
    path('painel/', painel, name='painel'),
    path('catalogo/', catalogo, name='catalogo'),
    path('carrinho/', carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:item_id>/', adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('carrinho/remover/<int:item_id>/', remover_do_carrinho, name='remover_do_carrinho'),
    path('estoque/ajustar/<int:item_id>/', ajustar_estoque, name='ajustar_estoque'),
    path('logout/', sair, name='logout'),
]
