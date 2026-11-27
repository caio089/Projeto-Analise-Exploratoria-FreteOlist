# Dicionário de dados — Anexo C

**Frente 2** · Responsável: João Manoel  
**Tabela:** `data/processed/itens_transformados.csv`  
**Granularidade:** uma linha por item (`order_id` + `order_item_id`)  
**Volume desta execução:** 112.650 linhas e 47 colunas

A limpeza (tipos, texto, pedidos sem item, peso inválido) está na Frente 1. Aqui eu só registro a coluna que ficou na tabela final.

O CSV grava data como texto. No `DataFrame`, `order_purchase_timestamp` é data/hora.

| Coluna | Tipo | Origem | Descrição | Tratamento |
|--------|------|--------|-----------|------------|
| `order_id` | texto | items | Identificador do pedido | Mantido. Chave do merge com orders e da soma por pedido. |
| `order_item_id` | inteiro | items | Número do item dentro do pedido | Mantido. Com `order_id`, identifica a linha. |
| `product_id` | texto | items | Identificador do produto | Mantido. Chave do merge com products. |
| `seller_id` | texto | items | Identificador do vendedor | Mantido. Chave do merge com sellers. |
| `price` | float | items | Preço do item, em real | Valor original, depois da limpeza. Também gerei escala. |
| `freight_value` | float | items | Frete do item, em real | Valor original. Não cortei outlier. Também gerei escala. |
| `customer_id` | texto | orders | Cliente daquele pedido (muda a cada pedido) | Veio no merge com orders. |
| `order_status` | texto | orders | Situação do pedido | Padronizado na limpeza. Não filtrei status nesta frente. |
| `order_purchase_timestamp` | datetime | orders | Data e hora da compra | Convertido na limpeza. Usei para ano e mês. |
| `product_category_name` | texto | products | Categoria do produto | Texto legível para o painel. Vazio da origem já virou `sem_categoria` na limpeza. |
| `product_description_lenght` | float | products | Tamanho do texto da descrição do produto | Mantive. Correlação com o frete foi 0,094, acima do corte de 0,05. 1.603 itens sem esse número. O nome da coluna é o da base (com “lenght”). |
| `product_weight_g` | float | products | Peso do produto, em gramas | Mantido para a pergunta 2. Peso inválido já estava vazio desde a limpeza. 26 itens sem peso. |
| `product_length_cm` | float | products | Comprimento, em cm | Mantido. Entra no volume. 18 itens sem essa medida. |
| `product_height_cm` | float | products | Altura, em cm | Mantido. Entra no volume. 18 itens sem essa medida. |
| `product_width_cm` | float | products | Largura, em cm | Mantido. Entra no volume. 18 itens sem essa medida. |
| `customer_unique_id` | texto | customers | Pessoa, mesmo quando ela faz outro pedido | Mantido para contar cliente de verdade na pergunta 3. |
| `customer_state` | texto | customers | UF do cliente | Mantida em texto. É a UF das perguntas 1 e 3. 27 estados. |
| `seller_state` | texto | sellers | UF do vendedor | Mantida em texto. O frete também depende de onde o produto sai. |
| `volume_cm3` | float | calculada | Comprimento × altura × largura | Feature aritmética. Se falta um lado, fica vazio (18 itens). Não preenchi com média. |
| `soma_price_pedido` | float | calculada | Soma de `price` do mesmo `order_id` | O mesmo valor se repete nos itens daquele pedido. A linha não foi duplicada. |
| `soma_freight_pedido` | float | calculada | Soma de `freight_value` do mesmo `order_id` | Igual à soma de preço: valor do pedido, repetido no item. |
| `frete_sobre_total_pedido` | float | calculada | Frete do pedido dividido por (preço + frete) do pedido | Se o total fosse 0, ficaria vazio. Nesta base foram 0 casos. Vai de 0 até cerca de 0,96. |
| `ano_compra` | inteiro | calculada | Ano de `order_purchase_timestamp` | 2016, 2017 e 2018. |
| `mes_compra` | inteiro | calculada | Mês da compra (1 a 12) | Não virei nome do mês. O número já serve para agrupar. |
| `customer_state_cod` | inteiro | calculada | Código numérico de `customer_state` | `category.codes` do pandas. O texto da UF continua na outra coluna. |
| `seller_state_cod` | inteiro | calculada | Código numérico de `seller_state` | Mesma regra da UF do cliente. |
| `product_category_cod` | inteiro | calculada | Código numérico da categoria | Mesma regra. Não fiz one-hot: são 74 categorias. |
| `price_minmax` | float | calculada | `price` na escala 0 a 1 | MinMax. Se o máximo fosse igual ao mínimo, gravaria 0. |
| `price_zscore` | float | calculada | `price` em Z-score | (valor − média) / desvio. Média 0 e desvio 1 nesta coluna. |
| `freight_value_minmax` | float | calculada | `freight_value` na escala 0 a 1 | MinMax. O frete original continua em `freight_value`. |
| `freight_value_zscore` | float | calculada | `freight_value` em Z-score | Mesma fórmula do preço. |
| `product_weight_g_minmax` | float | calculada | Peso na escala 0 a 1 | MinMax. Item sem peso continua vazio. |
| `product_weight_g_zscore` | float | calculada | Peso em Z-score | Desvio calculado ignorando vazio. |
| `product_length_cm_minmax` | float | calculada | Comprimento na escala 0 a 1 | MinMax. |
| `product_length_cm_zscore` | float | calculada | Comprimento em Z-score | Z-score. |
| `product_height_cm_minmax` | float | calculada | Altura na escala 0 a 1 | MinMax. |
| `product_height_cm_zscore` | float | calculada | Altura em Z-score | Z-score. |
| `product_width_cm_minmax` | float | calculada | Largura na escala 0 a 1 | MinMax. |
| `product_width_cm_zscore` | float | calculada | Largura em Z-score | Z-score. |
| `volume_cm3_minmax` | float | calculada | Volume na escala 0 a 1 | MinMax. Os 18 vazios continuam vazios. |
| `volume_cm3_zscore` | float | calculada | Volume em Z-score | Z-score. |
| `soma_price_pedido_minmax` | float | calculada | Soma de preço do pedido na escala 0 a 1 | MinMax. |
| `soma_price_pedido_zscore` | float | calculada | Soma de preço do pedido em Z-score | Z-score. |
| `soma_freight_pedido_minmax` | float | calculada | Soma de frete do pedido na escala 0 a 1 | MinMax. |
| `soma_freight_pedido_zscore` | float | calculada | Soma de frete do pedido em Z-score | Z-score. |
| `frete_sobre_total_pedido_minmax` | float | calculada | A razão do frete na escala 0 a 1 | MinMax. A razão já é uma fração; a escala só deixa ela no mesmo padrão das outras. |
| `frete_sobre_total_pedido_zscore` | float | calculada | A razão do frete em Z-score | Z-score. |

## Colunas que saíram nesta frente

Não apaguei campo das três perguntas.

| Coluna | Motivo |
|--------|--------|
| `customer_city`, `seller_city` | Filtro simples. A análise pede UF, não cidade. |
| `customer_zip_code_prefix`, `seller_zip_code_prefix` | Filtro simples. CEP não entra nas perguntas. |
| `shipping_limit_date`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date` | Filtro simples. A data que ficou é a da compra. |
| `product_name_lenght` | Correlação com `freight_value` = 0,024 (abaixo de 0,05). |
| `product_photos_qty` | Correlação com `freight_value` = 0,022 (abaixo de 0,05). |

Nenhuma coluna numérica restante tinha variância zero.
