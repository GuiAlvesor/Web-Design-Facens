from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_pedido_pagamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="itempedido",
            name="item_catalogo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="itens_em_pedidos",
                to="core.itemcatalogo",
            ),
        ),
    ]
