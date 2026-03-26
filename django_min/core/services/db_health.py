from django.db import connection

REQUIRED_TABLES = {
    "core_tipoitemcatalogo",
    "core_itemcatalogo",
    "core_carrinho",
    "core_itemcarrinho",
}


def catalog_tables_ready() -> bool:
    existing_tables = set(connection.introspection.table_names())
    return REQUIRED_TABLES.issubset(existing_tables)
