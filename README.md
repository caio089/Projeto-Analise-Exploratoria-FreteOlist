# Projeto-Analise-Exploratoria-FreteOlist

Trabalho final de Ciência de Dados (UNIFSA) — Briefing 4 (precificação de frete Olist).

## Equipe e frentes (PDF seção 2)

| Pessoa | Frente | Entrega | Status |
|--------|--------|---------|--------|
| **Caio** | **Frente 1** | Limpeza + diário (`02_limpeza.py`, `docs/diario_decisoes.md`) | Feita |
| **João Manoel** | Frente 2 | Transforms, features, dicionário (`03_transformacoes.py`, `docs/dicionario_dados.md`) | Feita |
| **Ryan** | Frente 3 | Pipeline + CSV final (`04_pipeline.py`, `05_testes_pipeline.py`) | Feita |
| **Geroba** | Frente 4 | Painel Streamlit | Aguardando |
| **Erick** | Apoio / entrega | Consolidação PDF e envio (combinar com a equipe) | Aguardando |

Há também EDA de apoio em `notebooks/01_eda.ipynb` (entrada da limpeza).

O que falta (João / Ryan / Geroba / Erick): [`docs/o_que_falta_fazer.md`](docs/o_que_falta_fazer.md)

## Perguntas (Briefing 4)

1. Em quais estados o frete pesa mais no valor do pedido?
2. Peso e dimensões justificam o frete cobrado?
3. Onde a revisão do frete teria mais impacto?

## Dados brutos

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Baixe o zip do Kaggle e coloque estes 5 arquivos em `data/raw/` (a pasta não vai para o GitHub):

```text
data/raw/
├── olist_orders_dataset.csv
├── olist_order_items_dataset.csv
├── olist_products_dataset.csv
├── olist_customers_dataset.csv
└── olist_sellers_dataset.csv
```

Os outros arquivos do zip (geolocation, payments, reviews e tradução de categoria) não são usados.

## Ambiente

Linux, Mac ou Git Bash no Windows:

```bash
python3 -m venv .venv
source .venv/bin/activate        # no Git Bash do Windows: source .venv/Scripts/activate
pip install -r requirements.txt
```

PowerShell no Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Testado com Python 3.12 e pandas 2.2.3 e 3.0.6 (o CSV final sai idêntico nas duas versões).

Todos os comandos abaixo rodam na pasta raiz do projeto.

## Frente 1 — limpeza

```bash
python 02_limpeza.py
```

- Função principal: `limpar_bases(orders, items, products, customers, sellers)`
- Diário: `docs/diario_decisoes.md`
- Saída de referência: `data/processed/*_limpo.csv` (gerada localmente; brutos não são alterados)

## Frente 2 — transformações

```bash
python 03_transformacoes.py
```

- Chama `limpar_bases` do `02_limpeza.py` e não refaz a limpeza
- Saída: `data/processed/itens_transformados.csv` (gerada localmente)
- Dicionário: `docs/dicionario_dados.md`
- Decisões: continuação em `docs/diario_decisoes.md`

## Frente 3 — pipeline e CSV final

```bash
python 04_pipeline.py                 # base completa: gera o CSV final
python 05_testes_pipeline.py          # 8 cenários de teste (rodar depois do 04)
python 04_pipeline.py --amostra 300   # recorte de 300 pedidos, só mostra na tela
```

- Função principal: `preprocessar(orders, items, products, customers, sellers)`. Recebe os 5 DataFrames brutos e devolve a tabela final, uma linha por item. Chama `limpar_bases` (Frente 1) e as funções do `03_transformacoes.py` (Frente 2).
- Saída: `data/processed/olist_frete_analitico.csv` (112.650 linhas, 47 colunas, 76,4 MB). Esse arquivo fica no repositório.
- Colunas: as mesmas do `docs/dicionario_dados.md`
- Descrição do pipeline e histórico dos merges: `docs/pipeline.md`
- Testes e resultados: `docs/testes_pipeline.md`

Para usar a função em outro script (o painel, por exemplo):

```python
import importlib

pipeline = importlib.import_module("04_pipeline")
df = pipeline.preprocessar(*pipeline.ler_brutos())
```

## Links

- GitHub: https://github.com/caio089/Projeto-Analise-Exploratoria-FreteOlist
- Streamlit: (Frente 4)
