# Projeto-Analise-Exploratoria-FreteOlist

Trabalho final de Ciência de Dados (UNIFSA) — Briefing 4 (precificação de frete Olist).

## Equipe e frentes (PDF seção 2)

| Pessoa | Frente | Entrega | Status |
|--------|--------|---------|--------|
| **Caio** | **Frente 1** | Limpeza + diário (`02_limpeza.py`, `docs/diario_decisoes.md`) | Feita |
| **João Manoel** | Frente 2 | Transforms, features, dicionário | Aguardando |
| **Ryan** | Frente 3 | Pipeline + CSV final | Aguardando |
| **Geroba** | Frente 4 | Painel Streamlit | Aguardando |
| **Erick** | Apoio / entrega | Consolidação PDF e envio (combinar com a equipe) | Aguardando |

Há também EDA de apoio em `notebooks/01_eda.ipynb` (entrada da limpeza).

Roteiro: [`roteiro_frentes.html`](roteiro_frentes.html)

## Perguntas (Briefing 4)

1. Em quais estados o frete pesa mais no valor do pedido?
2. Peso e dimensões justificam o frete cobrado?
3. Onde a revisão do frete teria mais impacto?

## Dados brutos

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Em `data/raw/`: orders, order_items, products, customers, sellers. **Sem** geolocation.

## Ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Frente 1 — limpeza

```bash
python 02_limpeza.py
```

- Função principal: `limpar_bases(orders, items, products, customers, sellers)`
- Diário: `docs/diario_decisoes.md`
- Saída de referência: `data/processed/*_limpo.csv` (gerada localmente; brutos não são alterados)

## Links

- GitHub: https://github.com/caio089/Projeto-Analise-Exploratoria-FreteOlist
- Streamlit: (Frente 4)
