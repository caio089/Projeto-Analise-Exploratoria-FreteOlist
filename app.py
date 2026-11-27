import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Análise de Frete Olist",
    page_icon="📦",
    layout="wide"
)

st.title("Análise Exploratória de Frete — Olist")

st.write(
    "Dashboard desenvolvido para analisar os custos de frete "
    "no comércio eletrônico brasileiro."
)

st.info(
    "As análises serão disponibilizadas após a integração "
    "dos dados finais do projeto."
)


import pandas as pd

# [IA] registro 1 — leitura do arquivo final para validar a integração

df = pd.read_csv("data/processed/olist_frete_analitico.csv")

st.write("Dados carregados com sucesso!")
st.write("Quantidade de linhas:", len(df))
st.write("Quantidade de colunas:", len(df.columns))
