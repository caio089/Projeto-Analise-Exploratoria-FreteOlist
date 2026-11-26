# Pipeline de pré-processamento — Frente 3

**Responsável:** Ryan  
**Código:** `04_pipeline.py` · **Testes:** `05_testes_pipeline.py` (resultados em `docs/testes_pipeline.md`)  
**Saída:** `data/processed/olist_frete_analitico.csv`

## Objetivo

Sair dos 5 CSVs brutos da Olist e chegar à tabela analítica final com uma única chamada, sempre do mesmo jeito. O pipeline não cria regra nova. Ele junta a limpeza da Frente 1 (Caio) e as transformações da Frente 2 (João) na ordem certa, confere o resultado e grava o CSV que o painel usa.

## Entrada e saída

- **Entrada:** `orders`, `items`, `products`, `customers` e `sellers`, como vieram do CSV, sem nenhum tratamento. Esses DataFrames não são alterados: a limpeza trabalha em cópia.
- **Saída:** um DataFrame com **uma linha por item de pedido**, identificada por (`order_id`, `order_item_id`), com as 47 colunas do `docs/dicionario_dados.md`. Na base completa são 112.650 linhas.

## Etapas

```text
5 CSVs brutos (data/raw/)
   │
   ▼
limpar_bases ............................ Frente 1 (02_limpeza.py)
   tipos e datas → textos → chaves nulas → duplicatas
   → preço/frete negativos → peso e dimensões inválidos → pedidos sem item
   │
   ▼
juntar_tabelas .......................... Frente 2 (03_transformacoes.py)
   items + orders + products + customers + sellers (left, N:1)
   │
   ▼
criar_features → codificar_categorias ... Frente 2
   volume, somas do pedido, razão do frete, ano e mês, códigos de UF e categoria
   │
   ▼
seleção de atributos (lista fixa) ....... Frente 3
   tira cidade, CEP, 5 datas, product_name_lenght e product_photos_qty
   │
   ▼
aplicar_minmax_zscore ................... Frente 2
   │
   ▼
conferência final ....................... Frente 3
   mesmas linhas que items, chave única, 47 colunas na ordem do dicionário
   │
   ▼
data/processed/olist_frete_analitico.csv
```

Como os arquivos começam com número (`02_`, `03_`), o `04_pipeline.py` importa os outros dois com `importlib.import_module`.

## Histórico da limpeza (base completa)

| Tabela | Linhas antes | Linhas depois | Removidas |
|--------|-------------:|--------------:|----------:|
| orders | 99.441 | 98.666 | 775 (0,78%) — pedidos sem item |
| items | 112.650 | 112.650 | 0 |
| products | 32.951 | 32.951 | 0 |
| customers | 99.441 | 99.441 | 0 |
| sellers | 3.095 | 3.095 | 0 |

## Histórico dos merges (base completa)

Todos os merges partem do item, com `how="left"` e `validate="many_to_one"`. O `juntar_tabelas` para com erro se algum merge mudar a quantidade de linhas.

| Merge | Chave | Tipo | Linhas antes | Linhas depois | Linhas da outra tabela | Itens sem par |
|-------|-------|------|-------------:|--------------:|-----------------------:|--------------:|
| items + orders | `order_id` | left, N:1 | 112.650 | 112.650 | 98.666 | 0 |
| + products | `product_id` | left, N:1 | 112.650 | 112.650 | 32.951 | 0 |
| + customers | `customer_id` (do pedido) | left, N:1 | 112.650 | 112.650 | 99.441 | 0 |
| + sellers | `seller_id` | left, N:1 | 112.650 | 112.650 | 3.095 | 0 |

Essas duas tabelas saem na tela toda vez que o `04_pipeline.py` roda (`historico_merges` e `resumir_impacto_antes_depois`).

## Decisões da Frente 3

1. **Seleção de atributos fixa.** O `selecionar_atributos` da Frente 2 recalcula a correlação com o frete nos dados que recebe. Em recortes de 2 a 5.000 pedidos, a tabela saía com 47, 48 ou 49 colunas. O pipeline usa a decisão que o João tomou na base completa (diário nº 16) como lista fixa. Assim a tabela tem sempre as mesmas colunas. Na base completa o resultado é idêntico ao do `transformar_bases`.
2. **Item sem par fica na tabela.** Se um item não acha pedido, produto, cliente ou vendedor, ele continua na tabela, com vazio nas colunas da outra base. O pipeline mostra quantos itens ficaram sem par em cada merge. Na base real são 0.
3. **Códigos e escalas valem dentro da execução.** Os códigos (`*_cod`) e as escalas (`*_minmax`, `*_zscore`) são calculados sobre os dados que entram. Num recorte, SP pode receber outro código. Para comparar recortes, usar as colunas originais (UF em texto, preço, frete, peso).
4. **CSV reproduzível.** O CSV é gravado sem índice, com quebra de linha `\n` e sem arredondar. O arquivo sai igual byte a byte no pandas 2.2.3 e no 3.0.6. Tem 76,4 MB, abaixo do limite de 100 MB do GitHub.

## Como reproduzir

```bash
pip install -r requirements.txt
python 04_pipeline.py                 # gera o CSV final
python 05_testes_pipeline.py          # 8 cenários, todos devem passar
python 04_pipeline.py --amostra 300   # recorte rápido para mostrar ao vivo
```

## Limitações

- Os valores de `*_cod`, `*_minmax` e `*_zscore` de um recorte não são comparáveis com os da base completa (decisão 3).
- A lista de colunas tiradas por correlação foi decidida na base de 2016–2018. Se a base mudar, vale rodar o `selecionar_atributos` de novo na base inteira e atualizar a lista.
- O pipeline não filtra status de pedido. Esse filtro fica para a análise e o painel, como decidido na Frente 1 (diário nº 7).
