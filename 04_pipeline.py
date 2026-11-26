"""
Frente 3 — pipeline de pré-processamento (Ryan).

Junta a limpeza do Caio (02_limpeza.py) e as transformações do João
(03_transformacoes.py) numa função só: recebe os 5 DataFrames brutos e devolve
a tabela analítica final, com uma linha por item (order_id + order_item_id).
Nenhuma regra de limpeza ou de feature é refeita aqui.

Rodar:
    python 04_pipeline.py                 -> base completa, grava o CSV final
    python 04_pipeline.py --amostra 300   -> recorte de 300 pedidos, só mostra na tela
"""

import argparse
import importlib
import sys
from pathlib import Path

import pandas as pd

# Os arquivos começam com número, então "import 02_limpeza" não funciona.
limpeza = importlib.import_module("02_limpeza")
transformacoes = importlib.import_module("03_transformacoes")

PASTA = Path(__file__).parent
PASTA_RAW = PASTA / "data" / "raw"
CSV_FINAL = PASTA / "data" / "processed" / "olist_frete_analitico.csv"

# lineterminator="\n": o arquivo sai igual no Windows, no Linux e no Mac.
# O 05_testes_pipeline.py usa as mesmas opções para conferir o CSV byte a byte.
OPCOES_CSV = {"index": False, "lineterminator": "\n"}

# Mesma ordem dos parâmetros de preprocessar.
ARQUIVOS_BRUTOS = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
]

# O João tirou essas duas pela correlação com o frete na base completa (diário nº 16).
# Aqui a lista é fixa: se a correlação fosse recalculada em cada recorte,
# a tabela sairia com 47, 48 ou 49 colunas dependendo da amostra.
COLUNAS_TIRADAS_POR_CORRELACAO = ["product_name_lenght", "product_photos_qty"]

# Colunas da tabela final, na ordem do docs/dicionario_dados.md.
COLUNAS_FINAIS = [
    # item
    "order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value",
    # pedido
    "customer_id", "order_status", "order_purchase_timestamp",
    # produto
    "product_category_name", "product_description_lenght", "product_weight_g",
    "product_length_cm", "product_height_cm", "product_width_cm",
    # cliente e vendedor
    "customer_unique_id", "customer_state", "seller_state",
    # features da Frente 2
    "volume_cm3", "soma_price_pedido", "soma_freight_pedido", "frete_sobre_total_pedido",
    "ano_compra", "mes_compra",
    "customer_state_cod", "seller_state_cod", "product_category_cod",
    # escalas (MinMax e Z-score)
    "price_minmax", "price_zscore",
    "freight_value_minmax", "freight_value_zscore",
    "product_weight_g_minmax", "product_weight_g_zscore",
    "product_length_cm_minmax", "product_length_cm_zscore",
    "product_height_cm_minmax", "product_height_cm_zscore",
    "product_width_cm_minmax", "product_width_cm_zscore",
    "volume_cm3_minmax", "volume_cm3_zscore",
    "soma_price_pedido_minmax", "soma_price_pedido_zscore",
    "soma_freight_pedido_minmax", "soma_freight_pedido_zscore",
    "frete_sobre_total_pedido_minmax", "frete_sobre_total_pedido_zscore",
]


def ler_brutos():
    """Lê os 5 CSVs de data/raw/ e devolve orders, items, products, customers, sellers."""
    bases = []
    for arquivo in ARQUIVOS_BRUTOS:
        caminho = PASTA_RAW / arquivo
        if not caminho.exists():
            raise FileNotFoundError(
                f"Falta {arquivo} em data/raw/. Veja no README de onde baixar."
            )
        bases.append(pd.read_csv(caminho))
    return bases


def preprocessar(orders, items, products, customers, sellers):
    """
    Recebe os 5 DataFrames brutos (como vieram do CSV) e devolve a tabela final.
    Os DataFrames de entrada não mudam: a limpeza do Caio trabalha em cópia.
    """
    orders, items, products, customers, sellers = limpeza.limpar_bases(
        orders, items, products, customers, sellers
    )

    # Histórico dos merges na base completa (python 04_pipeline.py, 26/11/2026).
    # Todos partem do item, com how="left" e validate="many_to_one":
    #
    #   merge            chave         tipo        linhas antes -> depois   itens sem par
    #   items + orders   order_id      left, N:1   112.650 -> 112.650       0
    #   + products       product_id    left, N:1   112.650 -> 112.650       0
    #   + customers      customer_id   left, N:1   112.650 -> 112.650       0
    #   + sellers        seller_id     left, N:1   112.650 -> 112.650       0
    #
    # O juntar_tabelas para com erro se algum merge mudar a quantidade de linhas.
    # Item sem par continua na tabela, com campo vazio nas colunas da outra base.
    df = transformacoes.juntar_tabelas(items, orders, products, customers, sellers)

    # Mesma ordem do transformar_bases do João. Só a seleção de atributos
    # usa a lista fixa em vez de recalcular a correlação.
    df = transformacoes.criar_features(df)
    df = transformacoes.codificar_categorias(df)
    df = df.drop(
        columns=transformacoes.COLUNAS_FILTRO_SIMPLES + COLUNAS_TIRADAS_POR_CORRELACAO
    )
    df = transformacoes.aplicar_minmax_zscore(df)

    if len(df) != len(items):
        raise ValueError(f"{len(items)} itens viraram {len(df)} linhas")
    if df.duplicated(subset=["order_id", "order_item_id"]).any():
        raise ValueError("chave (order_id, order_item_id) repetida na tabela final")
    if list(df.columns) != COLUNAS_FINAIS:
        sobrando = [col for col in df.columns if col not in COLUNAS_FINAIS]
        faltando = [col for col in COLUNAS_FINAIS if col not in df.columns]
        raise ValueError(
            f"as colunas não batem com COLUNAS_FINAIS. Sobrando: {sobrando}. "
            f"Faltando: {faltando}. (Listas vazias = só a ordem mudou.) "
            "Se a mudança no 03 foi de propósito, atualize COLUNAS_FINAIS e o dicionário."
        )
    return df


def historico_merges(orders, items, products, customers, sellers):
    """
    Refaz os 4 merges do juntar_tabelas, um de cada vez, só para medir cada um.
    Recebe as bases já limpas. A tabela final continua vindo do preprocessar.
    """
    linhas = []
    df = items
    for nome, chave, outra_tabela in [
        ("items + orders", "order_id", orders),
        ("+ products", "product_id", products),
        ("+ customers", "customer_id", customers),
        ("+ sellers", "seller_id", sellers),
    ]:
        antes = len(df)
        # indicator=True cria a coluna _merge, que marca "left_only" no item sem par
        df = df.merge(outra_tabela, on=chave, how="left", indicator=True)
        linhas.append({
            "merge": nome,
            "chave": chave,
            "tipo": "left, N:1",
            "linhas_antes": antes,
            "linhas_depois": len(df),
            "linhas_outra_tabela": len(outra_tabela),
            "itens_sem_par": int((df["_merge"] == "left_only").sum()),
        })
        df = df.drop(columns="_merge")
    return pd.DataFrame(linhas)


def recortar_pedidos(orders, items, n):
    """Sorteia n pedidos que têm item e devolve orders e items só com eles."""
    # Semente fixa: o mesmo n sorteia sempre os mesmos pedidos.
    pedidos = items["order_id"].drop_duplicates().sample(n, random_state=42)
    return orders[orders["order_id"].isin(pedidos)], items[items["order_id"].isin(pedidos)]


if __name__ == "__main__":
    # O argparse recusa "--amostra" sem número, "--amostra abc" e argumento a mais,
    # em vez de cair na base completa e sobrescrever o CSV sem avisar.
    parser = argparse.ArgumentParser(description="Pipeline da Frente 3")
    parser.add_argument("--amostra", type=int, metavar="N",
                        help="roda só em N pedidos sorteados e não grava o CSV")
    amostra = parser.parse_args().amostra

    orders, items, products, customers, sellers = ler_brutos()

    if amostra is not None:
        total = items["order_id"].nunique()
        if not 1 <= amostra <= total:
            sys.exit(f"--amostra precisa estar entre 1 e {total} pedidos")
        orders, items = recortar_pedidos(orders, items, amostra)
        print(f"recorte: {amostra} pedidos sorteados (semente 42)\n")

    df = preprocessar(orders, items, products, customers, sellers)

    # A limpeza roda de novo só para montar os dois históricos abaixo.
    limpos = limpeza.limpar_bases(orders, items, products, customers, sellers)
    nomes = ["orders", "items", "products", "customers", "sellers"]
    impacto = limpeza.resumir_impacto_antes_depois(
        dict(zip(nomes, [orders, items, products, customers, sellers])),
        dict(zip(nomes, limpos)),
    )

    print("=== limpeza (Frente 1): linhas antes e depois ===")
    print(impacto.to_string(index=False))
    print("\n=== merges (Frente 2) ===")
    print(historico_merges(*limpos).to_string(index=False))
    print(f"\ntabela final: {len(df)} linhas x {len(df.columns)} colunas")
    print("chave (order_id, order_item_id) única, uma linha por item")

    if amostra is not None:
        colunas = ["order_id", "order_item_id", "customer_state", "price",
                   "freight_value", "frete_sobre_total_pedido"]
        print()
        print(df[colunas].head(10).to_string(index=False))
    else:
        df.to_csv(CSV_FINAL, **OPCOES_CSV)
        tamanho = CSV_FINAL.stat().st_size / 1024 / 1024
        print(f"arquivo: data/processed/{CSV_FINAL.name} ({tamanho:.1f} MB)")
