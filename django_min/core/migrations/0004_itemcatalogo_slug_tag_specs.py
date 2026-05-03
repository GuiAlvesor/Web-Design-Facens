from django.db import migrations, connection
from django.utils.text import slugify


def aplicar_tudo(apps, schema_editor):
    with connection.cursor() as c:
        c.execute("""
            ALTER TABLE core_itemcatalogo
            ADD COLUMN IF NOT EXISTS slug varchar(140) NOT NULL DEFAULT '';
        """)
        c.execute("""
            ALTER TABLE core_itemcatalogo
            ADD COLUMN IF NOT EXISTS tag varchar(40) NOT NULL DEFAULT '';
        """)
        c.execute("""
            ALTER TABLE core_itemcatalogo
            ADD COLUMN IF NOT EXISTS specs jsonb NOT NULL DEFAULT '{}';
        """)

    ItemCatalogo = apps.get_model("core", "ItemCatalogo")
    seen = {}
    for item in ItemCatalogo.objects.all():
        base = slugify(item.nome)
        slug = base
        n = 1
        while slug in seen:
            slug = f"{base}-{n}"
            n += 1
        seen[slug] = True
        item.slug = slug
        item.save(update_fields=["slug"])

    with connection.cursor() as c:
        c.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'core_itemcatalogo_slug_key'
                ) THEN
                    ALTER TABLE core_itemcatalogo ADD CONSTRAINT core_itemcatalogo_slug_key UNIQUE (slug);
                END IF;
            END$$;
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS core_itemcatalogo_slug_d78b8faf_like
            ON core_itemcatalogo (slug varchar_pattern_ops);
        """)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("core", "0003_itempedido_item_catalogo"),
    ]

    operations = [
        migrations.RunPython(aplicar_tudo, migrations.RunPython.noop),
    ]