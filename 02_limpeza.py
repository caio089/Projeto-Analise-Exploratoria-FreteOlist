"""
Frente 1 — Limpeza e tratamento das bases Olist (Briefing 4).

Recebe DataFrames brutos, devolve cópias tratadas.
Não altera os CSVs originais em data/raw/.
Não cria atributos analíticos finais (isso é Frente 2).
"""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd

# Status em que o pedido tipicamente não conclui ciclo útil para frete entregue.
# Mantidos na tabela orders para transparência; o critério de uso fica no diário.
STATUS_SEM_ENTREGA = {
    "canceled",
    "unavailable",
    "created",
    "approved",
    "invoiced",
    "processing",
}


def _copiar(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Trabalha sempre em cópia para não mutar os brutos."""
    return (
        orders.copy(),
        items.copy(),
        products.copy(),
        customers.copy(),
        sellers.copy(),
    )


def converter_tipos_e_datas(
    orders: pd.DataFrame,
    items: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Converte colunas de data (texto → datetime) e garante monetários numéricos."""
    colunas_data_orders = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in colunas_data_orders:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors="coerce")

    if "shipping_limit_date" in items.columns:
        items["shipping_limit_date"] = pd.to_datetime(
            items["shipping_limit_date"], errors="coerce"
        )

    for col in ("price", "freight_value"):
        if col in items.columns:
            items[col] = pd.to_numeric(items[col], errors="coerce")

    return orders, items


def padronizar_textos(
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
    orders: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Padroniza UF, status e categoria sem inventar valores de negócio."""
    if "customer_state" in customers.columns:
        customers["customer_state"] = (
            customers["customer_state"].astype(str).str.strip().str.upper()
        )
    if "customer_city" in customers.columns:
        customers["customer_city"] = customers["customer_city"].astype(str).str.strip()

    if "seller_state" in sellers.columns:
        sellers["seller_state"] = (
            sellers["seller_state"].astype(str).str.strip().str.upper()
        )
    if "seller_city" in sellers.columns:
        sellers["seller_city"] = sellers["seller_city"].astype(str).str.strip()

    if "order_status" in orders.columns:
        orders["order_status"] = (
            orders["order_status"].astype(str).str.strip().str.lower()
        )

    if "product_category_name" in products.columns:
        # Categoria ausente vira rótulo explícito (não imputação estatística).
        nulos = products["product_category_name"].isna()
        products.loc[nulos, "product_category_name"] = "sem_categoria"
        products["product_category_name"] = (
            products["product_category_name"].astype(str).str.strip().str.lower()
        )

    return products, customers, sellers, orders


def remover_duplicatas_por_chave(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Garante unicidade das chaves de negócio de cada tabela."""
    orders = orders.drop_duplicates(subset=["order_id"], keep="first")
    items = items.drop_duplicates(subset=["order_id", "order_item_id"], keep="first")
    products = products.drop_duplicates(subset=["product_id"], keep="first")
    customers = customers.drop_duplicates(subset=["customer_id"], keep="first")
    sellers = sellers.drop_duplicates(subset=["seller_id"], keep="first")
    return orders, items, products, customers, sellers


def tratar_chaves_nulas(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Remove linhas sem identificador mínimo para join."""
    orders = orders.dropna(subset=["order_id", "customer_id"])
    items = items.dropna(subset=["order_id", "order_item_id", "product_id", "seller_id"])
    products = products.dropna(subset=["product_id"])
    customers = customers.dropna(subset=["customer_id"])
    sellers = sellers.dropna(subset=["seller_id"])
    return orders, items, products, customers, sellers


def tratar_inconsistencias_monetarias(items: pd.DataFrame) -> pd.DataFrame:
    """
    Remove apenas valores monetários inválidos (negativos).
    Extremos altos de frete/preço NÃO são excluídos automaticamente.
    """
    items = items[items["price"].notna() & (items["price"] >= 0)]
    items = items[items["freight_value"].notna() & (items["freight_value"] >= 0)]
    return items.reset_index(drop=True)


def tratar_dimensoes_e_peso(products: pd.DataFrame) -> pd.DataFrame:
    """
    Peso <= 0 é fisicamente inválido → NaN (mantém o produto).
    Dimensões ausentes permanecem NaN; não imputa média.
    """
    cols_dim = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    for col in cols_dim:
        if col in products.columns:
            products[col] = pd.to_numeric(products[col], errors="coerce")

    if "product_weight_g" in products.columns:
        invalidos = products["product_weight_g"].notna() & (
            products["product_weight_g"] <= 0
        )
        products.loc[invalidos, "product_weight_g"] = pd.NA

    for col in ("product_length_cm", "product_height_cm", "product_width_cm"):
        if col in products.columns:
            invalidos = products[col].notna() & (products[col] <= 0)
            products.loc[invalidos, col] = pd.NA

    return products


def filtrar_pedidos_sem_item(
    orders: pd.DataFrame,
    items: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove da tabela orders os pedidos sem nenhum item.
    Itens continuam sendo a base da análise de frete.
    """
    com_item = orders["order_id"].isin(items["order_id"])
    return orders.loc[com_item].reset_index(drop=True)


def relatorio_chaves(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> Dict[str, object]:
    """Diagnóstico pós-limpeza para o diário e para a Frente 2 (merges)."""
    return {
        "orders_unicos": int(orders["order_id"].is_unique),
        "items_chave_unica": int(
            not items.duplicated(subset=["order_id", "order_item_id"]).any()
        ),
        "products_unicos": int(products["product_id"].is_unique),
        "customers_unicos": int(customers["customer_id"].is_unique),
        "sellers_unicos": int(sellers["seller_id"].is_unique),
        "items_sem_order": int((~items["order_id"].isin(orders["order_id"])).sum()),
        "orders_sem_customer": int(
            (~orders["customer_id"].isin(customers["customer_id"])).sum()
        ),
        "items_sem_product": int(
            (~items["product_id"].isin(products["product_id"])).sum()
        ),
        "items_sem_seller": int((~items["seller_id"].isin(sellers["seller_id"])).sum()),
        "orders_status": orders["order_status"].value_counts().to_dict(),
        "produtos_sem_categoria_rotulo": int(
            (products["product_category_name"] == "sem_categoria").sum()
        ),
        "produtos_peso_ausente": int(products["product_weight_g"].isna().sum()),
    }


def limpar_bases(
    orders: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Pipeline de limpeza da Frente 1.

    Ordem: cópia → tipos/datas → textos → chaves nulas → duplicatas
    → monetários → peso/dimensões → pedidos sem item.
    """
    orders, items, products, customers, sellers = _copiar(
        orders, items, products, customers, sellers
    )

    orders, items = converter_tipos_e_datas(orders, items)
    products, customers, sellers, orders = padronizar_textos(
        products, customers, sellers, orders
    )
    orders, items, products, customers, sellers = tratar_chaves_nulas(
        orders, items, products, customers, sellers
    )
    orders, items, products, customers, sellers = remover_duplicatas_por_chave(
        orders, items, products, customers, sellers
    )
    items = tratar_inconsistencias_monetarias(items)
    products = tratar_dimensoes_e_peso(products)
    orders = filtrar_pedidos_sem_item(orders, items)

    return orders, items, products, customers, sellers


def resumir_impacto_antes_depois(
    brutos: Dict[str, pd.DataFrame],
    limpos: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Compara contagem de linhas antes/depois para o diário."""
    linhas = []
    for nome in brutos:
        antes = len(brutos[nome])
        depois = len(limpos[nome])
        linhas.append(
            {
                "tabela": nome,
                "linhas_antes": antes,
                "linhas_depois": depois,
                "removidas": antes - depois,
                "pct_removido": round(100 * (antes - depois) / antes, 4) if antes else 0.0,
            }
        )
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    from pathlib import Path

    raw = Path("data/raw")
    out = Path("data/processed")
    out.mkdir(parents=True, exist_ok=True)

    brutos = {
        "orders": pd.read_csv(raw / "olist_orders_dataset.csv"),
        "items": pd.read_csv(raw / "olist_order_items_dataset.csv"),
        "products": pd.read_csv(raw / "olist_products_dataset.csv"),
        "customers": pd.read_csv(raw / "olist_customers_dataset.csv"),
        "sellers": pd.read_csv(raw / "olist_sellers_dataset.csv"),
    }

    orders, items, products, customers, sellers = limpar_bases(
        brutos["orders"],
        brutos["items"],
        brutos["products"],
        brutos["customers"],
        brutos["sellers"],
    )

    limpos = {
        "orders": orders,
        "items": items,
        "products": products,
        "customers": customers,
        "sellers": sellers,
    }

    impacto = resumir_impacto_antes_depois(brutos, limpos)
    chaves = relatorio_chaves(orders, items, products, customers, sellers)

    # Referência para a Frente 2 (não é o CSV analítico final).
    orders.to_csv(out / "orders_limpo.csv", index=False)
    items.to_csv(out / "items_limpo.csv", index=False)
    products.to_csv(out / "products_limpo.csv", index=False)
    customers.to_csv(out / "customers_limpo.csv", index=False)
    sellers.to_csv(out / "sellers_limpo.csv", index=False)

    print("=== impacto ===")
    print(impacto.to_string(index=False))
    print("\n=== chaves / cobertura ===")
    for k, v in chaves.items():
        print(f"{k}: {v}")
    print("\nArquivos em data/processed/*_limpo.csv")
