from django.db import transaction

from core.models import Carrinho, ItemCarrinho, ItemCatalogo


class CartError(Exception):
    pass


class StockError(CartError):
    pass


class CartService:
    @staticmethod
    def obter_carrinho(usuario):
        carrinho, _ = Carrinho.objects.get_or_create(usuario=usuario)
        return carrinho

    @staticmethod
    @transaction.atomic
    def adicionar_item(usuario, item_id, quantidade=1):
        if quantidade < 1:
            raise CartError("Quantidade deve ser maior que zero.")

        item_catalogo = ItemCatalogo.objects.select_for_update().get(pk=item_id, ativo=True)

        carrinho = CartService.obter_carrinho(usuario)
        item_carrinho, criado = ItemCarrinho.objects.select_for_update().get_or_create(
            carrinho=carrinho,
            item_catalogo=item_catalogo,
            defaults={"quantidade": quantidade},
        )

        quantidade_final = quantidade if criado else item_carrinho.quantidade + quantidade
        if item_catalogo.estoque < quantidade_final:
            raise StockError("Estoque insuficiente para atualizar a quantidade no carrinho.")

        if not criado:
            item_carrinho.quantidade = quantidade_final
            item_carrinho.save(update_fields=["quantidade", "atualizado_em"])

        return item_carrinho

    @staticmethod
    @transaction.atomic
    def atualizar_quantidade(usuario, item_id, quantidade):
        if quantidade < 1:
            raise CartError("Quantidade deve ser maior que zero.")

        carrinho = CartService.obter_carrinho(usuario)
        item_carrinho = ItemCarrinho.objects.select_for_update().select_related("item_catalogo").get(
            carrinho=carrinho,
            item_catalogo_id=item_id,
        )

        if item_carrinho.item_catalogo.estoque < quantidade:
            raise StockError("Estoque insuficiente para a quantidade informada.")

        item_carrinho.quantidade = quantidade
        item_carrinho.save(update_fields=["quantidade", "atualizado_em"])
        return item_carrinho

    @staticmethod
    @transaction.atomic
    def remover_item(usuario, item_id):
        carrinho = CartService.obter_carrinho(usuario)
        ItemCarrinho.objects.filter(carrinho=carrinho, item_catalogo_id=item_id).delete()

    @staticmethod
    @transaction.atomic
    def ajustar_estoque(item_id, quantidade):
        item_catalogo = ItemCatalogo.objects.select_for_update().get(pk=item_id)
        novo_estoque = item_catalogo.estoque + quantidade

        if novo_estoque < 0:
            raise StockError("Operação inválida: estoque não pode ficar negativo.")

        item_catalogo.estoque = novo_estoque
        item_catalogo.save(update_fields=["estoque", "atualizado_em"])
        return item_catalogo
