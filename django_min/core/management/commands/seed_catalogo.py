"""
Popula o catálogo com os mesmos produtos do frontend (products.ts).
As imagens ficam no frontend; o backend armazena apenas metadados.

Uso:
    python manage.py seed_catalogo
    python manage.py seed_catalogo --reset   # apaga tudo antes de inserir
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import ItemCatalogo, TipoItemCatalogo

PRODUTOS = [
    # ── Modelos Prontos ────────────────────────────────────────────────────
    {
        "tipo": "Modelos Prontos",
        "id_frontend": "tablet-suporte-black",
        "nome": "Suporte para Tablet - Preto",
        "descricao": (
            "Suporte para tablet pronto, estilo moderno, impresso em PLA com acabamento liso. "
            "Ideal para uso diário e suporte de dispositivos."
        ),
        "preco": 24.90,
        "estoque": 30,
        "tag": "Promoção",
        "specs": {
            "Material": "PLA (impresso)",
            "Dimensões aproximadas (C x L x A)": "13 x 23 x 4 cm",
            "Acabamento": "Liso / Pintura opcional",
        },
    },
    {
        "tipo": "Modelos Prontos",
        "id_frontend": "model-figure-kratos",
        "nome": "Boneco Kratos - Cinza",
        "descricao": (
            "Modelo boneco kratos pronto, detalhes finos e acabamento profissional. "
            "Ideal para colecionadores."
        ),
        "preco": 119.90,
        "estoque": 10,
        "tag": "",
        "specs": {
            "Material": "PETG (impresso)",
            "Dimensões aproximadas (C x L x A)": "12 x 7 x 15 cm",
            "Uso": "Decoração / Display",
        },
    },
    {
        "tipo": "Modelos Prontos",
        "id_frontend": "model-figure-spiderman",
        "nome": "Boneco Homem-Aranha - Cinza",
        "descricao": (
            "Miniatura Homem-Aranha colecionável pronta, detalhes finos e acabamento profissional. "
            "Perfeita para colecionadores."
        ),
        "preco": 109.90,
        "estoque": 8,
        "tag": "",
        "specs": {
            "Material": "PLA (impresso)",
            "Dimensões aproximadas (C x L x A)": "10 x 5 x 15 cm",
            "Acabamento": "Detalhado",
        },
    },
    {
        "tipo": "Modelos Prontos",
        "id_frontend": "vaso-black",
        "nome": "Vaso para Plantas - Preto",
        "descricao": "Peça vaso para plantas, acabamento opaco preto. Ideal para protótipos de apresentação.",
        "preco": 29.90,
        "estoque": 20,
        "tag": "Promoção",
        "specs": {
            "Material": "PLA (impresso)",
            "Dimensões aproximadas (C x L x A)": "7 x 7 x 10 cm",
            "Uso": "Exposição / Protótipo",
        },
    },
    {
        "tipo": "Modelos Prontos",
        "id_frontend": "porta-palhetas-grey",
        "nome": "Peça Porta Palhetas - Cinza",
        "descricao": (
            "Peça porta palhetas pronta, impressa em PETG para maior resistência ao impacto. "
            "Indicada para encaixes e protótipos funcionais."
        ),
        "preco": 19.90,
        "estoque": 25,
        "tag": "",
        "specs": {
            "Material": "PETG (impresso)",
            "Dimensões aproximadas (C x L x A)": "70 x 40 x 30 mm",
            "Resistência": "Alta",
        },
    },
    {
        "tipo": "Modelos Prontos",
        "id_frontend": "portacanetas",
        "nome": "Porta Canetas - Preto",
        "descricao": "Porta canetas pronto em PLA preto, visual elegante ideal para organização de mesa.",
        "preco": 29.90,
        "estoque": 15,
        "tag": "",
        "specs": {
            "Material": "PLA (impresso)",
            "Dimensões aproximadas (C x L x A)": "18,3 x 13,3 x 10 cm",
            "Acabamento": "Preto",
        },
    },
    {
        "tipo": "Modelos Prontos",
        "id_frontend": "suporte-headset-black",
        "nome": "Suporte para Headset - Preto",
        "descricao": (
            "Suporte para headset pronto, maior escala e detalhes impressos em PETG para maior durabilidade."
        ),
        "preco": 39.90,
        "estoque": 12,
        "tag": "Lançamento",
        "specs": {
            "Material": "PETG (impresso)",
            "Dimensões aproximadas": "150 x 80 x 60 mm",
            "Uso": "Colecionável / Exibição",
        },
    },
    # ── Impressão 3D ────────────────────────────────────────────────────────
    {
        "tipo": "Impressao 3d",
        "id_frontend": "impressao-3d-personalizada",
        "nome": "Impressão 3D Personalizada",
        "descricao": (
            "Serviço de impressão 3D personalizada. Envie o arquivo do modelo (STL/OBJ/ZIP) e escolha "
            "o tipo de filamento: PLA, ABS, PETG ou TPU. Há um campo de 'Observações' para informar "
            "acabamento, escala, tolerâncias ou solicitações especiais. O preço final será confirmado "
            "após análise técnica do arquivo e das opções escolhidas."
        ),
        "preco": 0.00,
        "estoque": 9999,
        "tag": "Lançamento",
        "specs": {
            "Filamentos disponíveis": "PLA, ABS, PETG, TPU",
            "Envio de arquivo": "STL/OBJ/ZIP",
            "Observações": "Campo de texto livre para requisitos adicionais",
            "Nota": "Preço final confirmado após análise técnica",
        },
    },
]


class Command(BaseCommand):
    help = "Popula o catálogo com os produtos do frontend"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove todos os itens antes de inserir",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            ItemCatalogo.objects.all().delete()
            TipoItemCatalogo.objects.all().delete()
            self.stdout.write("Catálogo resetado.")

        criados = 0
        atualizados = 0

        for p in PRODUTOS:
            tipo, _ = TipoItemCatalogo.objects.get_or_create(
                nome=p["tipo"],
                defaults={"slug": slugify(p["tipo"])},
            )

            # O slug deve ser igual ao id do frontend para compatibilidade
            slug_frontend = p["id_frontend"]

            obj, created = ItemCatalogo.objects.update_or_create(
                slug=slug_frontend,
                defaults={
                    "tipo": tipo,
                    "nome": p["nome"],
                    "descricao": p["descricao"],
                    "preco": p["preco"],
                    "estoque": p["estoque"],
                    "ativo": True,
                    "tag": p.get("tag", ""),
                    "specs": p.get("specs", {}),
                },
            )

            if created:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed concluído: {criados} criados, {atualizados} atualizados."
            )
        )
