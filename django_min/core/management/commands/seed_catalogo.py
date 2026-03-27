from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import ItemCatalogo, TipoItemCatalogo


class Command(BaseCommand):
    help = "Cria blocos iniciais de itens no catálogo"

    def handle(self, *args, **options):
        blocos = {
            "Miniaturas": [
                ("Dragão articulado", "Miniatura articulada para decoração", 59.9, 20),
                ("Cavaleiro medieval", "Miniatura colecionável", 39.9, 15),
            ],
            "Casa": [
                ("Suporte para celular", "Suporte de mesa para smartphone", 24.9, 30),
                ("Organizador de cabos", "Peça utilitária para mesa", 14.9, 50),
            ],
            "Protótipos": [
                ("Engrenagem técnica", "Peça para estudo e prototipagem", 19.9, 40),
            ],
        }

        for tipo_nome, itens in blocos.items():
            tipo, _ = TipoItemCatalogo.objects.get_or_create(
                nome=tipo_nome,
                defaults={"slug": slugify(tipo_nome)},
            )

            for nome, descricao, preco, estoque in itens:
                ItemCatalogo.objects.get_or_create(
                    tipo=tipo,
                    nome=nome,
                    defaults={
                        "descricao": descricao,
                        "preco": preco,
                        "estoque": estoque,
                        "ativo": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Catálogo inicial criado/atualizado com sucesso."))
