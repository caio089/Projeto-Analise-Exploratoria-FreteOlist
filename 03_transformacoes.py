# Frente 2 — junta as bases limpas e cria as colunas da analise.
# A limpeza nao entra aqui. Ela ja esta no 02_limpeza.py.

import importlib
from pathlib import Path

import pandas as pd

limpeza = importlib.import_module("02_limpeza")

# Essas colunas nao respondem as 3 perguntas. Saem no filtro simples.
COLUNAS_FILTRO_SIMPLES = [
    "customer_city",
    "customer_zip_code_prefix",
    "seller_city",
    "seller_zip_code_prefix",
    "shipping_limit_date",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

# Correlacao com o frete. Abaixo disso eu tiro, se a coluna nao for protegida.
LIMIAR_CORR = 0.05

# Nao posso tirar o que as perguntas usam, nem o que eu acabei de criar.
COLUNAS_PROTEGIDAS = [
    "order_id",
    "order_item_id",
    "product_id",
    "customer_id",
    "customer_unique_id",
    "seller_id",
    "order_status",
    "order_purchase_timestamp",
    "price",
    "freight_value",
    "customer_state",
    "seller_state",
    "product_category_name",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
    "volume_cm3",
    "soma_price_pedido",
    "soma_freight_pedido",
    "frete_sobre_total_pedido",
    "ano_compra",
    "mes_compra",
    "customer_state_cod",
    "seller_state_cod",
    "product_category_cod",
]

# Escala so faz sentido nesses numeros. Id, mes e codigo ficam como estao.
COLUNAS_PARA_ESCALA = [
    "price",
    "freight_value",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
    "volume_cm3",
    "soma_price_pedido",
    "soma_freight_pedido",
    "frete_sobre_total_pedido",
]


def juntar_tabelas(items, orders, products, customers, sellers):
    # Parto do item. Cada merge tem que ser N:1, senao a linha de frete duplica.
    n = len(items)

    df = items.merge(orders, on="order_id", how="left", validate="many_to_one")
    if len(df) != n:
        raise ValueError("merge com orders mudou a quantidade de linhas")

    df = df.merge(products, on="product_id", how="left", validate="many_to_one")
    if len(df) != n:
        raise ValueError("merge com products mudou a quantidade de linhas")

    df = df.merge(customers, on="customer_id", how="left", validate="many_to_one")
    if len(df) != n:
        raise ValueError("merge com customers mudou a quantidade de linhas")

    df = df.merge(sellers, on="seller_id", how="left", validate="many_to_one")
    if len(df) != n:
        raise ValueError("merge com sellers mudou a quantidade de linhas")

    return df


def criar_features(df):
    df = df.copy()

    for col in ("product_length_cm", "product_height_cm", "product_width_cm"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # volume da caixa. Se faltar um lado, o resultado fica vazio.
    df["volume_cm3"] = (
        df["product_length_cm"] * df["product_height_cm"] * df["product_width_cm"]
    )

    # soma do pedido repetida em cada item, sem multiplicar a linha
    por_pedido = df.groupby("order_id")[["price", "freight_value"]].transform("sum")
    df["soma_price_pedido"] = por_pedido["price"]
    df["soma_freight_pedido"] = por_pedido["freight_value"]

    total = df["soma_price_pedido"] + df["soma_freight_pedido"]
    df["frete_sobre_total_pedido"] = pd.NA
    pode_dividir = total > 0
    df.loc[pode_dividir, "frete_sobre_total_pedido"] = (
        df.loc[pode_dividir, "soma_freight_pedido"] / total[pode_dividir]
    )
    df["frete_sobre_total_pedido"] = pd.to_numeric(
        df["frete_sobre_total_pedido"], errors="coerce"
    )

    df["ano_compra"] = df["order_purchase_timestamp"].dt.year
    df["mes_compra"] = df["order_purchase_timestamp"].dt.month

    return df


def codificar_categorias(df):
    df = df.copy()
    # O texto continua. O numero e so pra quem for usar modelo depois.
    df["customer_state_cod"] = df["customer_state"].astype("category").cat.codes
    df["seller_state_cod"] = df["seller_state"].astype("category").cat.codes
    df["product_category_cod"] = df["product_category_name"].astype("category").cat.codes
    return df


def _minmax(serie):
    serie = pd.to_numeric(serie, errors="coerce")
    menor = serie.min(skipna=True)
    maior = serie.max(skipna=True)
    # max igual a min: nao tem escala. Deixo 0 onde existe valor.
    if pd.isna(menor) or pd.isna(maior) or maior == menor:
        saida = pd.Series(float("nan"), index=serie.index, dtype="float64")
        saida.loc[serie.notna()] = 0.0
        return saida
    return (serie - menor) / (maior - menor)


def _zscore(serie):
    serie = pd.to_numeric(serie, errors="coerce")
    media = serie.mean(skipna=True)
    desvio = serie.std(skipna=True)
    if pd.isna(desvio) or desvio == 0:
        saida = pd.Series(float("nan"), index=serie.index, dtype="float64")
        saida.loc[serie.notna()] = 0.0
        return saida
    return (serie - media) / desvio


def aplicar_minmax_zscore(df):
    df = df.copy()
    for col in COLUNAS_PARA_ESCALA:
        if col not in df.columns:
            continue
        df[col + "_minmax"] = _minmax(df[col])
        df[col + "_zscore"] = _zscore(df[col])
    return df


def selecionar_atributos(df):
    filtro = [col for col in COLUNAS_FILTRO_SIMPLES if col in df.columns]
    df = df.drop(columns=filtro)

    proteger = set(COLUNAS_PROTEGIDAS)
    correlacao = df.corr(numeric_only=True)
    saiu_corr = []
    var_zero = []

    if "freight_value" in correlacao.columns:
        serie_corr = correlacao["freight_value"]
        for col in list(df.columns):
            if col in proteger:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            variancia = df[col].var(skipna=True)
            if pd.isna(variancia) or variancia == 0:
                var_zero.append(col)
                df = df.drop(columns=[col])
                continue
            valor = serie_corr.get(col, pd.NA)
            if pd.notna(valor) and abs(float(valor)) < LIMIAR_CORR:
                saiu_corr.append((col, round(float(valor), 4), round(float(variancia), 4)))
                df = df.drop(columns=[col])

    relatorio = {
        "filtro_simples": filtro,
        "saiu_correlacao": saiu_corr,
        "variancia_zero": var_zero,
    }
    return df, relatorio


def transformar_bases(orders, items, products, customers, sellers):
    df = juntar_tabelas(items, orders, products, customers, sellers)
    df = criar_features(df)
    df = codificar_categorias(df)
    df, relatorio = selecionar_atributos(df)
    df = aplicar_minmax_zscore(df)
    relatorio["linhas"] = len(df)
    relatorio["razao_vazia"] = int(df["frete_sobre_total_pedido"].isna().sum())
    relatorio["volume_vazio"] = int(df["volume_cm3"].isna().sum())
    return df, relatorio


if __name__ == "__main__":
    raw = Path("data/raw")
    out = Path("data/processed")
    out.mkdir(parents=True, exist_ok=True)

    orders = pd.read_csv(raw / "olist_orders_dataset.csv")
    items = pd.read_csv(raw / "olist_order_items_dataset.csv")
    products = pd.read_csv(raw / "olist_products_dataset.csv")
    customers = pd.read_csv(raw / "olist_customers_dataset.csv")
    sellers = pd.read_csv(raw / "olist_sellers_dataset.csv")

    orders, items, products, customers, sellers = limpeza.limpar_bases(
        orders, items, products, customers, sellers
    )

    linhas_item = len(items)
    df, relatorio = transformar_bases(orders, items, products, customers, sellers)

    df.to_csv(out / "itens_transformados.csv", index=False)

    print("linhas de item antes do merge:", linhas_item)
    print("linhas depois:", relatorio["linhas"])
    print("colunas:", len(df.columns))
    print("razao vazia (total do pedido era 0):", relatorio["razao_vazia"])
    print("volume vazio:", relatorio["volume_vazio"])
    print("filtro simples:", relatorio["filtro_simples"])
    print("variancia zero:", relatorio["variancia_zero"])
    print("saiu por correlacao:")
    for item in relatorio["saiu_correlacao"]:
        print(" ", item)
    print("colunas finais:")
    print(list(df.columns))
    print("arquivo: data/processed/itens_transformados.csv")
