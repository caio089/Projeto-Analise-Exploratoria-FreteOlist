# Diário de Decisões — Anexo B

**Frente 1 (limpeza e tratamento)** · Responsável: Caio  
**Base:** Briefing 4 (precificação de frete) · Olist  

Registrei cada decisão abaixo depois de olhar a EDA e rodar `python 02_limpeza.py` nos CSVs brutos. Os impactos (contagem e %) saíram dessa execução.

| Nº | Etapa | Problema encontrado | Decisão tomada | Justificativa | Impacto nos dados |
|----|-------|---------------------|----------------|---------------|-------------------|
| 1 | Tipos / datas | As datas em `orders` e o `shipping_limit_date` em `items` estavam como texto. | Converti tudo com `to_datetime(..., errors="coerce")`. Se vier lixo, vira NaT. | Eu preciso das datas em formato de verdade pra qualquer análise de tempo depois. Usei `coerce` porque preferi NaT controlado a estourar erro no meio do processo. | 5 colunas de data em orders + 1 em items convertidas. `order_approved_at` segue com 160 NaT (já eram nulos na base). |
| 2 | Padronização de texto | UF, cidade e status podiam vir com caixa/espaço diferente; 610 produtos sem categoria. | UF em maiúsculo sem espaço; status em minúsculo; cidade só com `strip`; categoria vazia vira `sem_categoria`. | Nas perguntas 1 e 3 a gente agrupa por estado. Se “sp” e “SP” aparecerem separados, a conta fica errada. Preferi marcar categoria faltando com um nome claro do que deixar nulo escondido. | 610 produtos (1,85% de `products`) ficaram como `sem_categoria`. Nas outras tabelas só padronizei texto, sem tirar linha. |
| 3 | Chaves / duplicatas | Se a chave de negócio repetir, o merge depois multiplica linha e infla frete/preço. | `drop_duplicates` por chave (`order_id`; `order_id`+`order_item_id`; `product_id`; `customer_id`; `seller_id`) e removi linha sem identificador mínimo. | A EDA já apontou granularidade de item e joins N:1. Mesmo com 0 duplicata na prática, deixei a regra no código pra limpeza ser segura se a base mudar. | 0 linhas removidas por duplicata ou chave nula nas 5 tabelas. |
| 4 | Monetários / outliers | Frete vai até R$ 409,68 e preço até R$ 6.735; tem frete zero e casos de frete maior que o preço. | Só tirei preço/frete negativo ou não numérico. Não cortei extremo alto nem frete zero. | O cliente quer saber se o frete é caro e se faz sentido. Se eu cortar os valores altos agora, eu maquio a resposta. Frete maior que o preço pode ser real. Negativo, pra mim, não faz sentido e aí sim eu tiro. | 0 linhas removidas em `items` (não tinha negativo). Frete igual: média ≈ 20,03; mediana 16,27; máx. 409,68. |
| 5 | Peso e dimensões | 2 produtos sem peso/dimensão e 4 com peso ≤ 0. | Mantive o produto. Peso/dimensão inválidos viram NaN. Não preenchi com média. | A pergunta 2 liga frete com peso e dimensão. Se eu inventar peso médio, eu crio uma relação falsa. Melhor NaN explícito pra tratar depois com critério claro. | Peso ausente no fim: **6** (2 nulos + 4 que zerei). Dimensões nulas originais: 2. **0** produtos excluídos. |
| 6 | Pedidos sem item | 775 pedidos sem linha em `order_items` (quase tudo `unavailable`/`canceled`). | Removi esses pedidos de `orders`. Mantive todos os itens. Merge futuro parte de `items`. | Sem item não tem `price` nem `freight_value`. Pro briefing de frete esses pedidos só atrapalham a contagem. | `orders`: 99.441 → **98.666** (−775; **0,78%**). `items` ficou igual (112.650). |
| 7 | Status do pedido | Tem pedido que não é `delivered` e mesmo assim tem item/frete. | Não filtrei a base só por status nesta frente. Status ficou padronizado pra quem for filtrar depois. | Se eu deixar só `delivered` agora, eu apago frete que foi cobrado em outros status. Acho mais honesto filtrar isso na análise/painel, com a regra escrita, e não esconder na limpeza. | Depois da limpeza: delivered 96.478; shipped 1.106; canceled 461; invoiced 312; processing 301; unavailable 6; approved 2. |
| 8 | Integridade referencial | Antes do merge da Frente 2, preciso saber se sobrou chave órfã. | Conferi items→orders, orders→customers, items→products e items→sellers depois da limpeza. | Se passar órfão, o join cria nulo em cascata ou some com linha sem a gente perceber. Quis deixar isso fechado aqui. | Cobertura **100%** nos quatro relacionamentos; 0 órfãos. Chaves únicas ok nas 5 tabelas. |

## Comparativo de volume (antes → depois)

| Tabela | Antes | Depois | Removidas | % |
|--------|------:|-------:|----------:|--:|
| orders | 99.441 | 98.666 | 775 | 0,78% |
| order_items | 112.650 | 112.650 | 0 | 0% |
| products | 32.951 | 32.951 | 0 | 0% |
| customers | 99.441 | 99.441 | 0 | 0% |
| sellers | 3.095 | 3.095 | 0 | 0% |

## A limpeza mudou o frete?

Não no miolo da distribuição. Como eu não removi item e não cortei outlier de frete, o `freight_value` ficou com o mesmo comportamento (mesmo describe). O que mudou de verdade foi: tipos/textos arrumados, peso inválido virando NaN e a saída dos 775 pedidos sem item.

## Como reproduzir

```bash
python 02_limpeza.py
```

Isso gera `data/processed/*_limpo.csv`. Os brutos em `data/raw/` não são alterados.

## Fora do escopo desta frente

- Feature engineering, encoding, MinMax/Z-score  
- Pipeline final e CSV analítico  
- Painel e resposta de negócio  
