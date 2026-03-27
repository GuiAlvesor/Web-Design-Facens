import hashlib
import hmac
import json
import time
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.utils import OperationalError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ItemCatalogo, ItemCarrinho, Pagamento, Pedido, TipoItemCatalogo
from .services.payments import CheckoutService, CheckoutSession, PaymentGateway


class AutenticacaoTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_registro_cria_usuario_e_autentica(self):
        response = self.client.post(
            reverse("registro"),
            {
                "username": "ana",
                "email": "ana@email.com",
                "password1": "SenhaForte@123",
                "password2": "SenhaForte@123",
            },
        )

        self.assertRedirects(response, reverse("painel"))
        self.assertTrue(User.objects.filter(username="ana").exists())

    def test_login_logout(self):
        User.objects.create_user(username="joao", password="SenhaForte@123")

        response_login = self.client.post(
            reverse("login"),
            {
                "username": "joao",
                "password": "SenhaForte@123",
            },
        )

        self.assertRedirects(response_login, reverse("painel"))

        response_logout = self.client.post(reverse("logout"))
        self.assertRedirects(response_logout, reverse("home"))


class GatewayFalso(PaymentGateway):
    provider_name = "stripe"

    def criar_checkout(self, pedido):
        return CheckoutSession(
            id=f"cs_test_{pedido.id}",
            url_pagamento=f"https://checkout.stripe.test/{pedido.id}",
        )


class CarrinhoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(username="maria", password="SenhaForte@123")
        self.client.login(username="maria", password="SenhaForte@123")

        tipo = TipoItemCatalogo.objects.create(nome="Miniatura", slug="miniatura")
        self.item = ItemCatalogo.objects.create(
            tipo=tipo,
            nome="Dragão articulado",
            descricao="Modelo PLA",
            preco="59.90",
            estoque=5,
            ativo=True,
        )

    def test_adicionar_item_ao_carrinho(self):
        response = self.client.post(
            reverse("adicionar_ao_carrinho", kwargs={"item_id": self.item.id}),
            {"quantidade": 2},
        )

        self.assertRedirects(response, reverse("catalogo"))
        item_carrinho = ItemCarrinho.objects.get(item_catalogo=self.item)
        self.assertEqual(item_carrinho.quantidade, 2)

    def test_atualizar_quantidade_item_carrinho(self):
        self.client.post(
            reverse("adicionar_ao_carrinho", kwargs={"item_id": self.item.id}),
            {"quantidade": 1},
        )

        response = self.client.post(
            reverse("atualizar_quantidade_item", kwargs={"item_id": self.item.id}),
            {"quantidade": 4},
        )

        self.assertRedirects(response, reverse("carrinho"))
        item_carrinho = ItemCarrinho.objects.get(item_catalogo=self.item)
        self.assertEqual(item_carrinho.quantidade, 4)

    def test_remover_item_do_carrinho(self):
        self.client.post(
            reverse("adicionar_ao_carrinho", kwargs={"item_id": self.item.id}),
            {"quantidade": 1},
        )
        response = self.client.post(reverse("remover_do_carrinho", kwargs={"item_id": self.item.id}))

        self.assertRedirects(response, reverse("carrinho"))
        self.assertFalse(ItemCarrinho.objects.filter(item_catalogo=self.item).exists())

    @patch("core.services.payments.StripeGateway.criar_checkout")
    def test_iniciar_checkout_cria_pedido_pagamento_e_reduz_estoque(self, mock_checkout):
        mock_checkout.return_value = CheckoutSession(
            id="cs_test_123",
            url_pagamento="https://checkout.stripe.test/cs_test_123",
        )
        self.client.post(
            reverse("adicionar_ao_carrinho", kwargs={"item_id": self.item.id}),
            {"quantidade": 2},
        )

        response = self.client.post(reverse("iniciar_checkout"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Pedido.objects.exists())
        self.assertTrue(Pagamento.objects.exists())

        self.item.refresh_from_db()
        self.assertEqual(self.item.estoque, 3)
        self.assertFalse(ItemCarrinho.objects.filter(item_catalogo=self.item).exists())

    def test_checkout_falha_e_realiza_rollback_de_estoque(self):
        self.client.post(
            reverse("adicionar_ao_carrinho", kwargs={"item_id": self.item.id}),
            {"quantidade": 2},
        )

        class GatewayComFalha(PaymentGateway):
            def criar_checkout(self, pedido):
                raise RuntimeError("Falha simulada no gateway")

        with self.assertRaises(RuntimeError):
            CheckoutService.iniciar_checkout(self.usuario, gateway=GatewayComFalha())

        self.item.refresh_from_db()
        self.assertEqual(self.item.estoque, 5)
        self.assertEqual(ItemCarrinho.objects.filter(item_catalogo=self.item).count(), 1)
        self.assertFalse(Pedido.objects.exists())
        self.assertFalse(Pagamento.objects.exists())


@override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_secret", STRIPE_WEBHOOK_TOLERANCE_SECONDS=300)
class StripeWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(username="pedro", password="SenhaForte@123")
        tipo = TipoItemCatalogo.objects.create(nome="Colecionável", slug="colecionavel")
        self.item = ItemCatalogo.objects.create(
            tipo=tipo,
            nome="Nave espacial",
            descricao="Edição limitada",
            preco="100.00",
            estoque=3,
            ativo=True,
        )

        from .services.cart import CartService

        carrinho = CartService.obter_carrinho(self.usuario)
        ItemCarrinho.objects.create(carrinho=carrinho, item_catalogo=self.item, quantidade=1)

        CheckoutService.iniciar_checkout(self.usuario, gateway=GatewayFalso())
        self.pagamento = Pagamento.objects.get()

    def _signature(self, payload: bytes):
        ts = int(time.time())
        signed = f"{ts}.".encode("utf-8") + payload
        digest = hmac.new(b"whsec_test_secret", signed, hashlib.sha256).hexdigest()
        return f"t={ts},v1={digest}"

    def test_webhook_checkout_completo_aprova_pagamento(self):
        payload = json.dumps(
            {
                "type": "checkout.session.completed",
                "data": {"object": {"id": self.pagamento.checkout_id}},
            }
        ).encode("utf-8")

        response = self.client.post(
            reverse("stripe_webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=self._signature(payload),
        )

        self.assertEqual(response.status_code, 200)
        self.pagamento.refresh_from_db()
        self.assertEqual(self.pagamento.status, Pagamento.Status.APROVADO)
        self.assertEqual(self.pagamento.pedido.status, Pedido.Status.PAGO)

    def test_webhook_pagamento_falhou_reverte_estoque(self):
        payload = json.dumps(
            {
                "type": "checkout.session.expired",
                "data": {"object": {"id": self.pagamento.checkout_id}},
            }
        ).encode("utf-8")

        response = self.client.post(
            reverse("stripe_webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=self._signature(payload),
        )

        self.assertEqual(response.status_code, 200)
        self.pagamento.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.pagamento.status, Pagamento.Status.RECUSADO)
        self.assertEqual(self.pagamento.pedido.status, Pedido.Status.CANCELADO)
        self.assertEqual(self.item.estoque, 3)

    def test_webhook_rejeita_assinatura_invalida(self):
        payload = json.dumps(
            {
                "type": "checkout.session.completed",
                "data": {"object": {"id": self.pagamento.checkout_id}},
            }
        ).encode("utf-8")

        response = self.client.post(
            reverse("stripe_webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=invalid",
        )

        self.assertEqual(response.status_code, 400)


class InicializacaoBancoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(username="setup", password="SenhaForte@123")
        self.client.login(username="setup", password="SenhaForte@123")

    @patch("core.views.catalog_tables_ready", return_value=False)
    def test_catalogo_sem_migration_nao_quebra(self, _mock_ready):
        response = self.client.get(reverse("catalogo"))
        self.assertEqual(response.status_code, 200)

    @patch("core.views.catalog_tables_ready", return_value=True)
    @patch("core.views.ItemCatalogo.objects.filter", side_effect=OperationalError("no such table"))
    def test_catalogo_trata_erro_operationalerror(self, _mock_filter, _mock_ready):
        response = self.client.get(reverse("catalogo"))
        self.assertEqual(response.status_code, 200)
