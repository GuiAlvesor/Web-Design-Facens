from django.urls import path

from .views import entrar, home, painel, registro, sair

urlpatterns = [
    path('', home, name='home'),
    path('registro/', registro, name='registro'),
    path('login/', entrar, name='login'),
    path('painel/', painel, name='painel'),
    path('logout/', sair, name='logout'),
]
