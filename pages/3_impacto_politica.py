
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Impacto da Política de Frete",
    page_icon="📦",
    layout="wide"
)

st.title("Impacto da Política de Frete")

st.write(
    "Análise dos estados onde uma revisão da política de frete "
    "poderia atingir mais clientes."
)

# [IA] registro 13 — consolidação dos indicadores de impacto por estado

@st.cache_data
def carregar_dados():
    return pd.read_csv("data/processed/olist_frete_analitico.csv")


df = carregar_dados()

# Consolidação dos itens por pedido
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
resumo_estado = pedidos.groupby(
    "customer_state",
    as_index=False
).agg(
    total_pedidos=("order_id", "count"),
    total_frete=("valor_frete", "sum"),
    valor_total=("valor_total", "sum")
)

resumo_estado["participacao_frete"] = (
    resumo_estado["total_frete"] /
    resumo_estado["valor_total"] * 100
)

# Filtros
st.subheader("Filtros da análise")

estados = sorted(resumo_estado["customer_state"].unique())

estados_selecionados = st.multiselect(
    "Selecione os estados:",
    options=estados,
    default=estados
)

maximo_pedidos = int(resumo_estado["total_pedidos"].max())

minimo_pedidos = st.slider(
    "Quantidade mínima de pedidos:",
    min_value=1,
    max_value=maximo_pedidos,
    value=1
)

dados_filtrados = resumo_estado[
    (resumo_estado["customer_state"].isin(estados_selecionados)) &
    (resumo_estado["total_pedidos"] >= minimo_pedidos)
].copy()

st.write("Estados encontrados:", len(dados_filtrados))

# Resultados
if not dados_filtrados.empty:

    dados_filtrados = dados_filtrados.sort_values(
        "total_frete",
        ascending=False
    )

    st.subheader("Indicadores de impacto por estado")

    st.dataframe(
        dados_filtrados,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Valor total de frete por estado")

    grafico_frete = dados_filtrados.set_index(
        "customer_state"
    )["total_frete"]

    st.bar_chart(grafico_frete)

    st.subheader("Quantidade de pedidos e participação do frete")

    st.scatter_chart(
        dados_filtrados,
        x="total_pedidos",
        y="participacao_frete",
        size="total_frete"
    )

    st.caption(
        "No gráfico, cada ponto representa um estado. "
        "O tamanho do ponto representa o valor total de frete."
    )

else:
    st.warning("Nenhum estado encontrado com os filtros selecionados.")


