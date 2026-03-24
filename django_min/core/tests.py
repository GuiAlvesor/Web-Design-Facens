from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import ItemCatalogo, ItemCarrinho, TipoItemCatalogo


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

        painel = self.client.get(reverse("painel"))
        self.assertEqual(painel.status_code, 200)

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

        painel = self.client.get(reverse("painel"))
        self.assertRedirects(painel, f"{reverse('login')}?next={reverse('painel')}")


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

    def test_nao_permite_quantidade_maior_que_estoque(self):
        self.client.post(
            reverse("adicionar_ao_carrinho", kwargs={"item_id": self.item.id}),
            {"quantidade": 6},
        )

        self.assertFalse(ItemCarrinho.objects.filter(item_catalogo=self.item).exists())

    def test_staff_ajusta_estoque(self):
        staff = User.objects.create_user(username="admin", password="SenhaForte@123", is_staff=True)
        self.client.login(username="admin", password="SenhaForte@123")

        response = self.client.post(
            reverse("ajustar_estoque", kwargs={"item_id": self.item.id}),
            {"quantidade": 3},
        )

        self.assertRedirects(response, reverse("catalogo"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.estoque, 8)
