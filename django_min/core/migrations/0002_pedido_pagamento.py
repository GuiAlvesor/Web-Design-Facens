from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Pedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("aberto", "Aberto"), ("pago", "Pago"), ("cancelado", "Cancelado")], default="aberto", max_length=20)),
                ("valor_total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="ItemPedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome_item", models.CharField(max_length=120)),
                ("preco_unitario", models.DecimalField(decimal_places=2, max_digits=10)),
                ("quantidade", models.PositiveIntegerField(validators=[MinValueValidator(1)])),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="core.pedido")),
            ],
        ),
        migrations.CreateModel(
            name="Pagamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provedor", models.CharField(default="stripe", max_length=40)),
                ("checkout_id", models.CharField(max_length=120, unique=True)),
                ("status", models.CharField(choices=[("pendente", "Pendente"), ("aprovado", "Aprovado"), ("recusado", "Recusado")], default="pendente", max_length=20)),
                ("valor", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("pedido", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="pagamento", to="core.pedido")),
            ],
        ),
    ]
