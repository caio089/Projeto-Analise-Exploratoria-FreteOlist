# Diagnóstico EDA e contrato de saída — Caio (etapa 01 — EDA)

Material técnico inicial (EDA) usado como entrada da **Frente 1 — limpeza (Caio)**.
Os arquivos originais em `data/raw/` permanecem intactos; a limpeza opera em cópias via `02_limpeza.py`.

## 1. Contexto de negócio

A Olist conecta pequenos vendedores a compradores em marketplace. O frete aparece por item (`freight_value`) e impacta a percepção de preço. O projeto deve responder, com evidências:

1. Em quais estados o frete pesa mais no valor do pedido?
2. Peso e dimensões justificam o frete cobrado?
3. Onde a revisão do frete teria mais impacto?

## 2. Datasets utilizados

| Arquivo | Linhas | Colunas | Papel |
|---------|-------:|--------:|-------|
| `olist_orders_dataset.csv` | 99.441 | 8 | Pedido, status, datas, `customer_id` |
| `olist_order_items_dataset.csv` | 112.650 | 7 | Item do pedido, preço, frete, `product_id`, `seller_id` |
| `olist_products_dataset.csv` | 32.951 | 9 | Categoria, peso e dimensões |
| `olist_customers_dataset.csv` | 99.441 | 5 | UF/cidade do cliente |
| `olist_sellers_dataset.csv` | 3.095 | 4 | UF/cidade do vendedor |

Base excluída: geolocation (fora do escopo do roteiro).

## 3. Granularidade e chaves

### Granularidade analítica de item

Uma linha = um item de pedido, identificada por:

```text
(order_id, order_item_id)
```

- Pergunta 1 e métricas de pedido: agregar depois para **uma observação por `order_id`** (somas de preço e frete).
- Pergunta 2: manter **granularidade de item**.
- Pergunta 3: comparar carga relativa de frete com volume de clientes/pedidos por recorte (ex.: UF).

### Contrato de relacionamento (chaves)

| De | Para | Chave | Cardinalidade observada |
|----|------|-------|-------------------------|
| `order_items` → `orders` | `order_id` | N:1 | 100% dos itens encontram pedido |
| `orders` → `customers` | `customer_id` | N:1 | 100% dos pedidos encontram cliente |
| `order_items` → `products` | `product_id` | N:1 | 100% dos itens encontram produto |
| `order_items` → `sellers` | `seller_id` | N:1 | 100% dos itens encontram vendedor |

Chaves únicas nas tabelas de referência (EDA):

- `orders.order_id` — único
- `order_items (order_id, order_item_id)` — único
- `products.product_id` — único
- `customers.customer_id` — único
- `sellers.seller_id` — único

Duplicatas de linha completa: **0** em todas as cinco tabelas.

## 4. Dados necessários às três perguntas

| Pergunta | Campos essenciais | Observação |
|----------|-------------------|------------|
| 1 — frete por estado | `customer_state`, `order_id`, `price`, `freight_value` | Agregar preço e frete por pedido antes de comparar UFs |
| 2 — peso/dimensões vs frete | `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`, `freight_value` | Volume (`volume_cm3`) calculado na Frente 2, em `03_transformacoes.py` |
| 3 — impacto da revisão | `customer_state` (e/ou outras dimensões), agregados de frete e contagem de pedidos/clientes | Critérios transparentes; sem simular política nesta etapa |

## 5. Diagnóstico (achados da EDA)

### Tipos e datas

- Datas em `orders` e `shipping_limit_date` em `items` estão como **texto** → conversão na limpeza (Caio — Frente 1).
- Monetários (`price`, `freight_value`) já numéricos; dimensões/peso em `float`.

### Nulos

| Tabela | Campo | Nulos |
|--------|-------|------:|
| orders | `order_approved_at` | 160 |
| orders | `order_delivered_carrier_date` | 1.783 |
| orders | `order_delivered_customer_date` | 2.965 |
| products | `product_category_name` (+ nome/desc/fotos) | 610 |
| products | peso e dimensões | 2 |

`customers` e `sellers` sem nulos. `order_items` sem nulos.

### Inconsistências e extremos (exemplos reais)

- **775 pedidos sem itens** — em geral `unavailable` (603) ou `canceled` (164); também `created` (5), `invoiced` (2), `shipped` (1). Impactam merge pedido↔item.
- Status dominante: `delivered` (96.478); demais status precisam de critério explícito na limpeza.
- Frete mínimo 0 (383 itens); máximo 409,68; média ≈ 20,03.
- Preço mínimo 0,85; máximo 6.735; sem valores negativos de preço/frete.
- Em 4.119 itens o frete é **maior** que o preço do item (não é erro automático; sinalizar para análise).
- Peso: 4 produtos com `product_weight_g <= 0`; 2 produtos sem peso/dimensões.
- Itens por pedido: média ≈ 1,14; máximo 21 (maioria monoitem).

### Distribuições geográficas (amostra)

- Clientes concentrados em SP, RJ, MG.
- Vendedores concentrados em SP, PR, MG.

## 6. Contrato de saída para as próximas etapas

A limpeza (Caio — Frente 1) e as transformações (Frente 2) devem preservar:

1. Identificadores: `order_id`, `order_item_id`, `product_id`, `customer_id`, `seller_id`.
2. Valores monetários originais: `price`, `freight_value`.
3. UF do cliente: `customer_state` (pergunta 1 e 3).
4. Peso e dimensões do produto (pergunta 2).
5. Timestamp de compra: `order_purchase_timestamp` (mês e ano extraídos na Frente 2).
6. Granularidade final da tabela analítica: **item** (`order_id` + `order_item_id`), com colunas agregadas de pedido quando necessário, sem multiplicar linhas indevidamente nos merges.

Decisões formais de limpeza: ver `docs/diario_decisoes.md` e `02_limpeza.py`.

## 7. Escopo da EDA (este documento)

- Não substitui a Frente 1; apenas diagnostica.
- Feature engineering, pipeline e painel ficam nas frentes seguintes.
