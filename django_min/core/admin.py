from django.contrib import admin

from .models import Carrinho, ItemCarrinho, ItemCatalogo, TipoItemCatalogo


@admin.register(TipoItemCatalogo)
class TipoItemCatalogoAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome", "slug")


@admin.register(ItemCatalogo)
class ItemCatalogoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "preco", "estoque", "ativo")
    list_filter = ("tipo", "ativo")
    search_fields = ("nome",)


class ItemCarrinhoInline(admin.TabularInline):
    model = ItemCarrinho
    extra = 0


@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "criado_em", "atualizado_em")
    inlines = [ItemCarrinhoInline]
