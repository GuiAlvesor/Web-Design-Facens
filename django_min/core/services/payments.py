import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from django.conf import settings
from django.db import transaction

from core.models import ItemCatalogo, ItemPedido, Pagamento, Pedido
from core.services.cart import CartService, CartError


@dataclass
class CheckoutSession:
    id: str
    url_pagamento: str


class PaymentGatewayError(Exception):
    pass


class PaymentGateway:
    provider_name = "stripe"

    def criar_checkout(self, pedido: Pedido) -> CheckoutSession:
        session_id = f"sess_{uuid4().hex[:18]}"
        return CheckoutSession(
            id=session_id,
            url_pagamento=f"/pagamentos/checkout/{session_id}/",
        )


class StripeGateway(PaymentGateway):
    provider_name = "stripe"

    def __init__(self):
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.api_base = settings.STRIPE_API_BASE.rstrip("/")

    def criar_checkout(self, pedido: Pedido) -> CheckoutSession:
        if not self.secret_key:
            raise PaymentGatewayError("STRIPE_SECRET_KEY não configurada.")

        success_url = f"{settings.SITE_URL}/pagamentos/checkout/sucesso?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.SITE_URL}/carrinho/"

        payload = {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata[pedido_id]": str(pedido.id),
            "client_reference_id": str(pedido.usuario_id),
        }

        for index, item in enumerate(pedido.itens.select_related("item_catalogo")):
            payload[f"line_items[{index}][quantity]"] = str(item.quantidade)
            payload[f"line_items[{index}][price_data][currency]"] = "brl"
            payload[f"line_items[{index}][price_data][unit_amount]"] = str(_decimal_to_cents(item.preco_unitario))
            payload[f"line_items[{index}][price_data][product_data][name]"] = item.nome_item

        body = urlencode(payload).encode("utf-8")
        request = Request(
            url=f"{self.api_base}/v1/checkout/sessions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=12) as response:
                content = response.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise PaymentGatewayError("Erro ao criar sessão de checkout no Stripe.") from exc

        data = json.loads(content)
        checkout_id = data.get("id")
        checkout_url = data.get("url")
        if not checkout_id or not checkout_url:
            raise PaymentGatewayError("Resposta inválida do Stripe ao criar checkout.")

        return CheckoutSession(id=checkout_id, url_pagamento=checkout_url)


class StripeWebhookVerifier:
    @staticmethod
    def verify(payload: bytes, signature_header: str) -> bool:
        secret = settings.STRIPE_WEBHOOK_SECRET
        if not secret or not signature_header:
            return False

        pairs = {}
        for part in signature_header.split(","):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            pairs.setdefault(key.strip(), []).append(value.strip())

        timestamp = pairs.get("t", [None])[0]
        signatures = pairs.get("v1", [])
        if not timestamp or not signatures:
            return False

        try:
            ts = int(timestamp)
        except ValueError:
            return False

        if abs(time.time() - ts) > settings.STRIPE_WEBHOOK_TOLERANCE_SECONDS:
            return False

        signed_payload = f"{timestamp}.".encode("utf-8") + payload
        expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected, candidate) for candidate in signatures)


class CheckoutService:
    @staticmethod
    @transaction.atomic
    def iniciar_checkout(usuario, gateway: PaymentGateway | None = None) -> Pagamento:
        gateway = gateway or StripeGateway()

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

        try:
            checkout = gateway.criar_checkout(pedido)
        except PaymentGatewayError as exc:
            raise CartError(str(exc)) from exc

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            provedor=gateway.provider_name,
            checkout_id=checkout.id,
            valor=pedido.valor_total,
            metadata={"checkout_url": checkout.url_pagamento},
        )

        carrinho.itens.all().delete()
        return pagamento

    @staticmethod
    @transaction.atomic
    def confirmar_pagamento(checkout_id: str):
        pagamento = Pagamento.objects.select_for_update().select_related("pedido").get(checkout_id=checkout_id)
        if pagamento.status == Pagamento.Status.APROVADO:
            return pagamento

        pagamento.status = Pagamento.Status.APROVADO
        pagamento.save(update_fields=["status", "atualizado_em"])

        pedido = pagamento.pedido
        pedido.status = Pedido.Status.PAGO
        pedido.save(update_fields=["status", "atualizado_em"])
        return pagamento

    @staticmethod
    @transaction.atomic
    def cancelar_pagamento(checkout_id: str):
        pagamento = Pagamento.objects.select_for_update().select_related("pedido").get(checkout_id=checkout_id)
        if pagamento.status == Pagamento.Status.RECUSADO:
            return pagamento

        pedido = pagamento.pedido

        for item_pedido in pedido.itens.select_related("item_catalogo").all():
            if item_pedido.item_catalogo_id is None:
                continue
            item_catalogo = ItemCatalogo.objects.select_for_update().get(pk=item_pedido.item_catalogo_id)
            item_catalogo.estoque += item_pedido.quantidade
            item_catalogo.save(update_fields=["estoque", "atualizado_em"])

        pagamento.status = Pagamento.Status.RECUSADO
        pagamento.save(update_fields=["status", "atualizado_em"])

        pedido.status = Pedido.Status.CANCELADO
        pedido.save(update_fields=["status", "atualizado_em"])
        return pagamento


def _decimal_to_cents(value: Decimal) -> int:
    return int((value * 100).quantize(Decimal("1")))
