from dataclasses import dataclass
from uuid import uuid4

from django.db import transaction

from core.models import ItemPedido, Pagamento, Pedido
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
        itens = list(carrinho.itens.select_related("item_catalogo"))
        if not itens:
            raise CartError("Seu carrinho está vazio.")

        pedido = Pedido.objects.create(usuario=usuario, valor_total=carrinho.total)

        for item in itens:
            ItemPedido.objects.create(
                pedido=pedido,
                nome_item=item.item_catalogo.nome,
                preco_unitario=item.item_catalogo.preco,
                quantidade=item.quantidade,
            )

        checkout = gateway.criar_checkout(pedido)
        pagamento = Pagamento.objects.create(
            pedido=pedido,
            provedor=gateway.provider_name,
            checkout_id=checkout.id,
            valor=pedido.valor_total,
            metadata={"checkout_url": checkout.url_pagamento},
        )
        return pagamento
