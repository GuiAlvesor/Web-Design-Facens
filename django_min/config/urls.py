from django.contrib import admin
from django.urls import path, include

# Deploy separado: Django serve apenas a API.
# O React está no Vercel e gerencia suas próprias rotas.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]