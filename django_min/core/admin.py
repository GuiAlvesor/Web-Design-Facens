from django.contrib import admin

from .models import (
    Carrinho,
    ItemCarrinho,
    ItemCatalogo,
    ItemPedido,
    Pagamento,
    Pedido,
    TipoItemCatalogo,
)


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


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "status", "valor_total", "criado_em")
    list_filter = ("status",)
    inlines = [ItemPedidoInline]


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("checkout_id", "pedido", "provedor", "status", "valor", "atualizado_em")
    list_filter = ("provedor", "status")
    search_fields = ("checkout_id",)