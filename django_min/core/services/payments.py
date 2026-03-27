from dataclasses import dataclass
from uuid import uuid4

from django.db import transaction

from core.models import ItemCatalogo, ItemPedido, Pagamento, Pedido
from core.services.cart import CartService, CartError


@dataclass
class CheckoutSession:
    id: str
    url_pagamento: str


class PaymentGateway:
    provider_name = "stripe"

    def criar_checkout(self, pedido: Pedido) -> CheckoutSession:
        session_id = f"sess_{uuid4().hex[:18]}"
        return CheckoutSession(
            id=session_id,
            url_pagamento=f"/pagamentos/checkout/{session_id}/",
        )


class CheckoutService:
    @staticmethod
    @transaction.atomic
    def iniciar_checkout(usuario, gateway: PaymentGateway | None = None) -> Pagamento:
        gateway = gateway or PaymentGateway()

        carrinho = CartService.obter_carrinho(usuario)
        itens_carrinho = list(carrinho.itens.select_related("item_catalogo").select_for_update())
        if not itens_carrinho:
            raise CartError("Seu carrinho está vazio.")

        item_ids = [item.item_catalogo_id for item in itens_carrinho]
        itens_catalogo = {
            item.id: item
            for item in ItemCatalogo.objects.select_for_update().filter(id__in=item_ids, ativo=True)
        }

        pedido = Pedido.objects.create(usuario=usuario, valor_total=carrinho.total)

        for item_carrinho in itens_carrinho:
            item_catalogo = itens_catalogo.get(item_carrinho.item_catalogo_id)
            if not item_catalogo:
                raise CartError(f"O item '{item_carrinho.item_catalogo.nome}' não está mais disponível.")

            if item_catalogo.estoque < item_carrinho.quantidade:
                raise CartError(
                    f"Estoque insuficiente para '{item_catalogo.nome}'. Disponível: {item_catalogo.estoque}."
                )

            item_catalogo.estoque -= item_carrinho.quantidade
            item_catalogo.save(update_fields=["estoque", "atualizado_em"])

            ItemPedido.objects.create(
                pedido=pedido,
                nome_item=item_catalogo.nome,
                preco_unitario=item_catalogo.preco,
                quantidade=item_carrinho.quantidade,
            )

        checkout = gateway.criar_checkout(pedido)
        pagamento = Pagamento.objects.create(
            pedido=pedido,
            provedor=gateway.provider_name,
            checkout_id=checkout.id,
            valor=pedido.valor_total,
            metadata={"checkout_url": checkout.url_pagamento},
        )

        carrinho.itens.all().delete()
        return pagamento
