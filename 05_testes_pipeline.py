"""
Testes automáticos do pipeline (Frente 3).

Rodar depois do python 04_pipeline.py (um dos testes confere o CSV gerado):
    python 05_testes_pipeline.py

Todo cenário confere: não quebra, não duplica nem perde linha (compara com os itens
depois da limpeza), chave (order_id, order_item_id) única, mesmas colunas da tabela
final e DataFrames de entrada sem alteração.
"""

import importlib
import re
import sys
import time

import pandas as pd

pipeline = importlib.import_module("04_pipeline")
limpeza = pipeline.limpeza
transformacoes = pipeline.transformacoes

UFS = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}
STATUS = {"delivered", "shipped", "canceled", "invoiced", "processing", "unavailable", "approved"}

# Únicas colunas que podem ter vazio na base real, com a quantidade do dicionário.
VAZIOS_ESPERADOS = {
    "product_description_lenght": 1603,
    "product_weight_g": 26,
    "product_length_cm": 18,
    "product_height_cm": 18,
    "product_width_cm": 18,
    "volume_cm3": 18,
}


def rodar_e_conferir(orders, items, products, customers, sellers):
    """Roda o pipeline e faz as conferências que valem para todo cenário."""
    entradas = [orders, items, products, customers, sellers]
    copias = [base.copy() for base in entradas]

    df = pipeline.preprocessar(orders, items, products, customers, sellers)

    # Compara com os itens que sobram da limpeza, não com o bruto:
    # item com preço negativo, por exemplo, sai na limpeza e não é erro do pipeline.
    itens_limpos = limpeza.limpar_bases(orders, items, products, customers, sellers)[1]
    assert len(df) == len(itens_limpos), f"{len(itens_limpos)} itens viraram {len(df)} linhas"
    assert not df.duplicated(subset=["order_id", "order_item_id"]).any(), "chave repetida"
    assert list(df.columns) == pipeline.COLUNAS_FINAIS, "colunas diferentes"
    for base, copia in zip(entradas, copias):
        assert base.equals(copia), "o pipeline alterou um DataFrame de entrada"
    return df


def teste_completo(brutos):
    df = rodar_e_conferir(*brutos)
    assert len(df) == 112650, f"esperava 112650 linhas, veio {len(df)}"

    limpos = limpeza.limpar_bases(*brutos)
    historico = pipeline.historico_merges(*limpos)
    assert (historico["linhas_depois"] == historico["linhas_antes"]).all(), "merge mudou linhas"
    assert historico["itens_sem_par"].sum() == 0, "item sem par na base real"

    # Na base completa a seleção fixa tem que dar exatamente o resultado do João.
    df_joao, _ = transformacoes.transformar_bases(*limpos)
    assert df.equals(df_joao), "diferente do transformar_bases do João"

    # O CSV versionado tem que ser exatamente o que o pipeline gera hoje.
    csv_atual = df.to_csv(**pipeline.OPCOES_CSV).encode("utf-8")
    assert pipeline.CSV_FINAL.read_bytes() == csv_atual, (
        "CSV desatualizado: rode python 04_pipeline.py"
    )
    return (
        f"{len(df)} linhas x {len(df.columns)} colunas, igual ao transformar_bases "
        "do João e ao CSV versionado"
    )


def colunas_do_dicionario():
    texto = (pipeline.PASTA / "docs" / "dicionario_dados.md").read_text(encoding="utf-8")
    tabela = texto.split("## Colunas que saíram")[0]
    return re.findall(r"^\| `(\w+)` \|", tabela, flags=re.MULTILINE)


def teste_csv_final():
    tamanho = pipeline.CSV_FINAL.stat().st_size / 1024 / 1024
    assert tamanho < 100, f"CSV com {tamanho:.1f} MB"
    df = pd.read_csv(pipeline.CSV_FINAL)

    # colunas e granularidade
    assert list(df.columns) == colunas_do_dicionario(), "cabeçalho diferente do dicionário"
    assert len(df) == 112650
    assert not df.duplicated(subset=["order_id", "order_item_id"]).any()

    # valores possíveis
    assert set(df["customer_state"]) == UFS
    assert set(df["seller_state"]) <= UFS
    assert set(df["order_status"]) <= STATUS
    assert df["product_category_name"].nunique() == 74
    assert "sem_categoria" in set(df["product_category_name"])
    assert set(df["ano_compra"]) == {2016, 2017, 2018}
    assert set(df["mes_compra"]) == set(range(1, 13))
    assert (df["price"] > 0).all() and (df["freight_value"] >= 0).all()
    assert df["frete_sobre_total_pedido"].between(0, 1).all()
    for col in ("customer_state_cod", "seller_state_cod", "product_category_cod"):
        assert (df[col] >= 0).all(), f"{col} com código -1 (texto vazio)"
    for col in df.columns:
        if col.endswith("_minmax"):
            assert df[col].dropna().between(0, 1).all(), f"{col} fora de 0 a 1"

    # vazios: só onde o dicionário diz, e na quantidade dele
    for col in df.columns:
        original = col.removesuffix("_minmax").removesuffix("_zscore")
        esperado = VAZIOS_ESPERADOS.get(original, 0)
        assert df[col].isna().sum() == esperado, f"{col}: {df[col].isna().sum()} vazios"
    return f"{tamanho:.1f} MB, 47 colunas na ordem do dicionário, valores e vazios conferidos"


def teste_categoria_ausente(brutos):
    orders, items, products, customers, sellers = brutos
    orders, items = pipeline.recortar_pedidos(orders, items, 500)

    # Apaga a categoria de 20 produtos que aparecem no recorte.
    sem_categoria = items["product_id"].drop_duplicates().head(20)
    products = products.copy()
    products.loc[products["product_id"].isin(sem_categoria), "product_category_name"] = None

    df = rodar_e_conferir(orders, items, products, customers, sellers)
    afetados = df["product_id"].isin(sem_categoria)
    assert (df.loc[afetados, "product_category_name"] == "sem_categoria").all()
    assert df["product_category_name"].notna().all()
    return f"{afetados.sum()} itens de 20 produtos sem categoria viraram sem_categoria"


def teste_amostra(brutos, n):
    orders, items, products, customers, sellers = brutos
    orders, items = pipeline.recortar_pedidos(orders, items, n)
    df = rodar_e_conferir(orders, items, products, customers, sellers)
    return f"{n} pedido(s), {len(df)} itens"


def teste_chave_sem_match(brutos):
    orders, items, products, customers, sellers = brutos
    orders, items = pipeline.recortar_pedidos(orders, items, 500)
    orders, items = orders.copy(), items.copy()

    # Cada alteração aponta para um id que não existe na outra tabela.
    linha_produto, linha_vendedor, linha_pedido = items.index[:3]
    items.loc[linha_produto, "product_id"] = "produto_inexistente"
    items.loc[linha_vendedor, "seller_id"] = "vendedor_inexistente"
    items.loc[linha_pedido, "order_id"] = "pedido_inexistente"
    pedido_cliente_falso = orders["order_id"].iloc[-1]
    orders.loc[orders["order_id"] == pedido_cliente_falso, "customer_id"] = "cliente_inexistente"

    df = rodar_e_conferir(orders, items, products, customers, sellers)

    limpos = limpeza.limpar_bases(orders, items, products, customers, sellers)
    sem_par = pipeline.historico_merges(*limpos).set_index("chave")["itens_sem_par"]
    itens_cliente_falso = (items["order_id"] == pedido_cliente_falso).sum()
    assert sem_par["order_id"] == 1
    assert sem_par["product_id"] == 1
    assert sem_par["seller_id"] == 1
    # o item sem pedido também fica sem cliente
    assert sem_par["customer_id"] == itens_cliente_falso + 1

    # o item continua na tabela, com vazio nas colunas da outra base
    produto = df[df["product_id"] == "produto_inexistente"]
    vendedor = df[df["seller_id"] == "vendedor_inexistente"]
    pedido = df[df["order_id"] == "pedido_inexistente"]
    cliente = df[df["order_id"] == pedido_cliente_falso]
    assert produto["product_category_name"].isna().all()
    assert vendedor["seller_state"].isna().all()
    assert pedido["order_status"].isna().all() and pedido["customer_state"].isna().all()
    assert cliente["customer_state"].isna().all()
    assert (cliente["customer_state_cod"] == -1).all()
    return (
        f"itens sem par: pedido {sem_par['order_id']}, produto {sem_par['product_id']}, "
        f"cliente {sem_par['customer_id']}, vendedor {sem_par['seller_id']}; ficaram com campo vazio"
    )


if __name__ == "__main__":
    brutos = pipeline.ler_brutos()

    cenarios = [
        ("pipeline completo", lambda: teste_completo(brutos)),
        ("CSV final x dicionário", teste_csv_final),
        ("categoria ausente", lambda: teste_categoria_ausente(brutos)),
        ("amostra de 1 pedido", lambda: teste_amostra(brutos, 1)),
        ("amostra de 2 pedidos", lambda: teste_amostra(brutos, 2)),
        ("amostra de 10 pedidos", lambda: teste_amostra(brutos, 10)),
        ("amostra de 500 pedidos", lambda: teste_amostra(brutos, 500)),
        ("chave sem match", lambda: teste_chave_sem_match(brutos)),
    ]

    falhas = 0
    for nome, teste in cenarios:
        inicio = time.time()
        # Um cenário que quebra não pode impedir os outros de rodar.
        try:
            resultado, detalhe = "OK", teste()
        except Exception as erro:
            resultado, detalhe = "FALHOU", f"{type(erro).__name__}: {erro}"
            falhas += 1
        print(f"{resultado:6} | {nome:24} | {time.time() - inicio:5.1f} s | {detalhe}")

    print(f"\n{len(cenarios) - falhas} de {len(cenarios)} cenários passaram")
    sys.exit(1 if falhas else 0)
