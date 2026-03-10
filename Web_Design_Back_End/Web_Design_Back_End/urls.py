from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("SITE FUNCIONANDO")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('produtos.urls')),
]