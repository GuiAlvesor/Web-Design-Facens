from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class TipoItemCatalogo(models.Model):
    """Tipos de item para facilitar expansão futura do catálogo."""

    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        verbose_name = "Tipo de item"
        verbose_name_plural = "Tipos de item"

    def __str__(self):
        return self.nome


class ItemCatalogo(models.Model):
    tipo = models.ForeignKey(TipoItemCatalogo, on_delete=models.PROTECT, related_name="itens")
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    estoque = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de catálogo"
        verbose_name_plural = "Itens de catálogo"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.tipo.nome})"


class Carrinho(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="carrinho")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrinho de {self.usuario.username}"

    @property
    def total(self):
        return sum((item.subtotal for item in self.itens.select_related("item_catalogo")), Decimal("0.00"))


class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name="itens")
    item_catalogo = models.ForeignKey(ItemCatalogo, on_delete=models.PROTECT, related_name="itens_em_carrinho")
    quantidade = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item do carrinho"
        verbose_name_plural = "Itens do carrinho"
        constraints = [
            models.UniqueConstraint(fields=["carrinho", "item_catalogo"], name="uq_item_por_carrinho"),
        ]

    def __str__(self):
        return f"{self.item_catalogo.nome} x{self.quantidade}"

    @property
    def subtotal(self):
        return self.item_catalogo.preco * self.quantidade


class Pedido(models.Model):
    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        PAGO = "pago", "Pago"
        CANCELADO = "cancelado", "Cancelado"

    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="pedidos")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTO)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    item_catalogo = models.ForeignKey(
        ItemCatalogo,
        on_delete=models.PROTECT,
        related_name="itens_em_pedidos",
        null=True,
        blank=True,
    )
    nome_item = models.CharField(max_length=120)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade


class Pagamento(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADO = "aprovado", "Aprovado"
        RECUSADO = "recusado", "Recusado"

    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="pagamento")
    provedor = models.CharField(max_length=40, default="stripe")
    checkout_id = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    metadata = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pagamento {self.checkout_id} ({self.status})"
