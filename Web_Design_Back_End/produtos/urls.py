from django.urls import path
from .views import home
from . import views

urlpatterns = [
    path('', views.lista_produtos, name='lista_produtos'),
]