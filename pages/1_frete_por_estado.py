
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Frete por Estado",
    page_icon="📦",
    layout="wide"
)

st.title("Frete por Estado")

st.write(
    "Análise do impacto do frete no valor total dos pedidos."
)

# [IA] registro 14 — organização dos indicadores e filtros por estado

@st.cache_data
def carregar_dados():
    return pd.read_csv("data/processed/olist_frete_analitico.csv")


df = carregar_dados()

# Consolidação dos valores por pedido
pedidos = df.groupby(
    ["order_id", "customer_state"],
    as_index=False
).agg(
    valor_produtos=("price", "sum"),
    valor_frete=("freight_value", "sum")
)

pedidos["valor_total"] = (
    pedidos["valor_produtos"] + pedidos["valor_frete"]
)

# Indicadores por estado
estados = pedidos.groupby(
    "customer_state",
    as_index=False
).agg(
    total_pedidos=("order_id", "count"),
    total_produtos=("valor_produtos", "sum"),
    total_frete=("valor_frete", "sum"),
    valor_total=("valor_total", "sum")
)

estados["percentual_frete"] = (
    estados["total_frete"] / estados["valor_total"]
) * 100

estados = estados.sort_values(
    "percentual_frete",
    ascending=False
)

# Filtros
st.subheader("Filtros da análise")

lista_estados = sorted(estados["customer_state"].unique())

estados_selecionados = st.multiselect(
    "Selecione os estados:",
    options=lista_estados,
    default=lista_estados
)

minimo_pedidos = st.slider(
    "Quantidade mínima de pedidos:",
    min_value=1,
    max_value=int(estados["total_pedidos"].max()),
    value=1
)

estados_filtrados = estados[
    (estados["customer_state"].isin(estados_selecionados)) &
    (estados["total_pedidos"] >= minimo_pedidos)
].copy()

# Resultados
if not estados_filtrados.empty:

    st.subheader("Participação do frete por estado")

    st.dataframe(
        estados_filtrados,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Comparação entre os estados")

    grafico = estados_filtrados.set_index(
        "customer_state"
    )["percentual_frete"]

    st.bar_chart(grafico)

    st.caption(
        "O percentual representa a participação do frete "
        "no valor total dos pedidos de cada estado."
    )

else:
    st.warning("Nenhum estado encontrado com os filtros selecionados.")
