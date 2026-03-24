from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


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
