
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Peso e Dimensões",
    page_icon="📦",
    layout="wide"
)

st.title("Peso e Dimensões dos Produtos")

st.write(
    "Análise da relação entre o peso, o volume "
    "e o valor do frete cobrado."
)

# [IA] registro 15 — revisão e organização da análise física dos produtos

@st.cache_data
def carregar_dados():
    return pd.read_csv("data/processed/olist_frete_analitico.csv")


df = carregar_dados()

dados_analise = df.dropna(
    subset=[
        "product_weight_g",
        "volume_cm3",
        "freight_value"
    ]
).copy()

dados_analise["product_category_name"] = (
    dados_analise["product_category_name"].fillna("Não informado")
)

st.caption(
    f"Registros utilizados na análise: {len(dados_analise)} "
    f"de {len(df)} registros originais."
)

# Faixas de peso
dados_analise["faixa_peso"] = pd.cut(
    dados_analise["product_weight_g"],
    bins=[0, 500, 1000, 3000, 5000, 10000, float("inf")],
    labels=[
        "Até 500g",
        "500g a 1kg",
        "1kg a 3kg",
        "3kg a 5kg",
        "5kg a 10kg",
        "Acima de 10kg"
    ],
    include_lowest=True
)

# Faixas de volume
dados_analise["faixa_volume"] = pd.qcut(
    dados_analise["volume_cm3"],
    q=5,
    duplicates="drop"
)

# Filtros
st.subheader("Filtros da análise")

categorias = sorted(
    dados_analise["product_category_name"].unique()
)

categorias_selecionadas = st.multiselect(
    "Selecione as categorias:",
    options=categorias,
    default=categorias
)

if categorias_selecionadas:

    dados_filtrados = dados_analise[
        dados_analise["product_category_name"].isin(
            categorias_selecionadas
        )
    ].copy()

    peso_maximo_disponivel = int(
        dados_filtrados["product_weight_g"].max()
    )

    peso_maximo_slider = max(
        500,
        ((peso_maximo_disponivel + 499) // 500) * 500
    )

    peso_maximo = st.slider(
        "Peso máximo dos produtos (gramas):",
        min_value=0,
        max_value=peso_maximo_slider,
        value=peso_maximo_slider,
        step=500
    )

    dados_filtrados = dados_filtrados[
        dados_filtrados["product_weight_g"] <= peso_maximo
    ].copy()

    st.write("Itens após os filtros:", len(dados_filtrados))

    if not dados_filtrados.empty:

        # Análise de peso
        resumo_peso = dados_filtrados.groupby(
            "faixa_peso",
            observed=True
        ).agg(
            quantidade_itens=("order_id", "count"),
            peso_medio=("product_weight_g", "mean"),
            frete_medio=("freight_value", "mean")
        ).reset_index()

        st.subheader("Relação entre peso e frete")

        st.dataframe(
            resumo_peso,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Frete médio por faixa de peso")

        grafico_peso = resumo_peso.set_index("faixa_peso")[
            "frete_medio"
        ]

        st.bar_chart(grafico_peso)

        # Análise de volume
        resumo_volume = dados_filtrados.groupby(
            "faixa_volume",
            observed=True
        ).agg(
            quantidade_itens=("order_id", "count"),
            volume_medio=("volume_cm3", "mean"),
            frete_medio=("freight_value", "mean")
        ).reset_index()

        resumo_volume["faixa_volume"] = (
            resumo_volume["faixa_volume"].astype(str)
        )

        st.subheader("Relação entre dimensões (volume) e frete")

        st.dataframe(
            resumo_volume,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Frete médio por faixa de volume")

        grafico_volume = resumo_volume.set_index("faixa_volume")[
            "frete_medio"
        ]

        st.bar_chart(grafico_volume)

        st.caption(
            "O volume em cm³ representa a combinação "
            "do comprimento, altura e largura dos produtos."
        )

    else:
        st.warning("Nenhum produto encontrado com os filtros selecionados.")

else:
    st.warning("Selecione pelo menos uma categoria para visualizar a análise.")
