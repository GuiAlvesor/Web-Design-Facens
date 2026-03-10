from django.shortcuts import render
from .models import Produto

def lista_produtos(request):
    produtos = Produto.objects.all()
    return render(request, 'checkout.html')
