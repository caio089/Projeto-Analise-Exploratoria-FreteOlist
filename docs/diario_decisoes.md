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

---

# Diário de Decisões — Anexo B (continuação)

**Frente 2 (transformação e feature engineering)** · Responsável: João Manoel  
**Base:** saídas da Frente 1 (`limpar_bases`) · Olist  

Rodei `python 03_transformacoes.py`. A limpeza não foi refeita. Os números abaixo saíram dessa execução. A tabela continua com uma linha por item.

| Nº | Etapa | Problema encontrado | Decisão tomada | Justificativa | Impacto nos dados |
|----|-------|---------------------|----------------|---------------|-------------------|
| 9 | Merges | Juntar orders, products, customers e sellers no item pode multiplicar linha se a chave do outro lado repetir. Aí o frete entra duas vezes. | Juntei nesta ordem: items → orders (`order_id`) → products (`product_id`) → customers (`customer_id` do pedido) → sellers (`seller_id` do item). Conferi se o número de linhas mudou. | O diagnóstico já tinha esses joins como N:1. Se a linha cresce, a pergunta 1 infla preço e frete. Por isso a checagem ficou no código, não só no olho. | 112.650 linhas antes e 112.650 depois. Nenhum merge multiplicou item. |
| 10 | Feature aritmética | A pergunta 2 fala de dimensão, mas comprimento, altura e largura separados não dizem o tamanho da caixa. | Criei `volume_cm3` = comprimento × altura × largura. | É a conta mais direta de volume. Se um lado está vazio, o volume fica vazio. Não preenchi com média, pelo mesmo motivo da limpeza: não quero inventar tamanho. | 18 itens ficaram sem volume (faltou dimensão). O resto recebeu a coluna nova. Nenhuma linha foi apagada. |
| 11 | Feature de agregação | `price` e `freight_value` são do item. As perguntas 1 e 3 olham o pedido. | Somei preço e frete por `order_id` (`soma_price_pedido` e `soma_freight_pedido`) e repeti o valor em cada item daquele pedido. | Agregar antes de comparar UF é o que o contrato pede. Usei `transform`, então a soma volta na mesma linha e a base não vira uma linha por pedido. | 0 linhas criadas ou removidas. A soma do pedido aparece em todo item daquele `order_id`. |
| 12 | Feature de razão | Quero a parte do frete no valor do pedido, não só no item. Se preço + frete der 0, a divisão quebra. | `frete_sobre_total_pedido` = soma do frete / (soma do preço + soma do frete). Se o total for 0, deixo vazio. | A pergunta 1 é “em quais estados o frete pesa mais”. No item isso engana quando o pedido tem vários produtos. Total zero não apareceu, mas deixei a proteção. | 0 razões vazias. A razão ficou entre 0 e cerca de 0,96. Não somei essa coluna de novo: ela já é do pedido inteiro. |
| 13 | Feature temporal | A data de compra estava só como timestamp. | Extraí `ano_compra` e `mes_compra` de `order_purchase_timestamp`. | O painel e a frente do Ryan podem recortar período sem converter data de novo. Mantive o timestamp original. | Anos 2016, 2017 e 2018. Mês de 1 a 12. 0 linhas removidas. |
| 14 | Codificação | UF e categoria são texto. Modelo costuma pedir número, e o painel precisa do nome legível. | Criei `customer_state_cod`, `seller_state_cod` e `product_category_cod`. As colunas de texto continuam. | Se eu trocasse o texto pelo número, o painel ia mostrar código no lugar de SP. One-hot de 74 categorias ia espalhar coluna demais sem ajudar as três perguntas. | 27 UFs de cliente e 74 categorias. O texto original não saiu. |
| 15 | MinMax e Z-score | Preço, frete, peso, dimensão e volume estão em unidades diferentes. Se o máximo for igual ao mínimo, ou o desvio for 0, a fórmula divide por zero. | Gerei `_minmax` e `_zscore` para preço, frete, peso, três dimensões, volume, somas do pedido e a razão. O valor original ficou. Se não houver variação, a escala vira 0 onde existe número. | As perguntas usam o valor em real e em grama. A escala é apoio, não substituto. Não escalei id, mês, ano nem código de categoria. | Nenhuma dessas colunas tinha variância zero nesta base. MinMax de `price` foi de 0 a 1. Z-score de `price` ficou com média 0 e desvio 1. |
| 16 | Seleção de atributos | Tinha coluna que não entra nas perguntas (cidade, CEP, datas de entrega) e outras numéricas fracas perto do frete. | Tirei cidade, CEP e as datas que não são a compra. Nas numéricas que sobraram, tirei as com correlação absoluta com `freight_value` abaixo de 0,05. Não mexi em `customer_state`, `price`, `freight_value`, peso, dimensões e ids. | Cidade e CEP não respondem as três perguntas e ainda incham a tabela. O corte de 0,05 é simples: abaixo disso a coluna quase não anda junto com o frete. Peso e dimensão ficam mesmo com correlação que for, porque a pergunta 2 depende deles. | Saíram 9 colunas no filtro (cidades, CEPs e 5 datas). Por correlação saíram `product_name_lenght` (0,024) e `product_photos_qty` (0,022). `product_description_lenght` ficou (correlação 0,094). Variância zero: nenhuma. Base final: 112.650 linhas e 47 colunas. |

## O que a Frente 2 não fez

Não respondi as três perguntas de negócio e não montei o painel. Isso fica com o Ryan e o Geroba. O arquivo `data/processed/itens_transformados.csv` é a tabela desta frente, gerada na hora. Os brutos em `data/raw/` não mudam.

## Como reproduzir

```bash
python 03_transformacoes.py
```  

---

# Diário de Decisões — Anexo B (continuação)

**Frente 3 (pipeline e reprodutibilidade)** · Responsável: Ryan  
**Base:** funções da Frente 1 (`limpar_bases`) e da Frente 2 (`03_transformacoes.py`) · Olist  

Rodei `python 04_pipeline.py` e `python 05_testes_pipeline.py`. Não refiz a limpeza nem as transformações: o pipeline só chama as funções do Caio e do João. Os números abaixo saíram dessas execuções.

| Nº | Etapa | Problema encontrado | Decisão tomada | Justificativa | Impacto nos dados |
|----|-------|---------------------|----------------|---------------|-------------------|
| 17 | Pipeline único | A limpeza e as transformações rodavam em scripts separados, cada um lendo os CSVs e gravando um arquivo intermediário. | Criei `preprocessar(orders, items, products, customers, sellers)` no `04_pipeline.py`. Ela chama `limpar_bases` e depois as funções do João, na mesma ordem do `transformar_bases`. Importei os dois arquivos com `importlib`, porque o nome começa com número. | Uma chamada leva dos brutos à tabela final, sem copiar regra de ninguém. Se alguém mudar uma regra da limpeza ou de uma feature, o pipeline já usa a versão nova. Se a mudança criar ou tirar coluna, o pipeline para e mostra qual coluna mudou, e aí é preciso atualizar `COLUNAS_FINAIS` e o dicionário junto. | Base completa: 112.650 itens → 112.650 linhas e 47 colunas. Resultado idêntico ao `transformar_bases` do João (`DataFrame.equals`). |
| 18 | Seleção de atributos | O `selecionar_atributos` recalcula a correlação e a variância nos dados que recebe. Em recortes de 2 a 5.000 pedidos, a tabela saiu com 47, 48 ou 49 colunas, às vezes sem `product_description_lenght`. | No pipeline, usei como lista fixa a seleção que o João fez na base completa: filtro simples + `product_name_lenght` e `product_photos_qty`. | O painel e os testes precisam das mesmas colunas em qualquer execução. A escolha das colunas foi feita uma vez, na base inteira, e ficou registrada no nº 16. | Sempre 47 colunas, na ordem do dicionário. Na base completa, igual ao resultado do João. |
| 19 | Chave sem par | A limpeza não tira item sem pedido, produto, cliente ou vendedor, e os merges são `left`. | Mantive o item na tabela, com vazio nas colunas da outra base. O pipeline mostra quantos itens ficaram sem par em cada merge (`historico_merges`). | Tirar o item apagaria frete que foi cobrado. Com a contagem na tela, o problema não passa sem ninguém ver. | Base real: 0 itens sem par nos 4 merges. No teste com ids inventados, os itens ficaram na tabela com campos vazios, e a UF vazia virou código `-1`. |
| 20 | Códigos e escalas | `*_cod`, `*_minmax` e `*_zscore` são calculados sobre os dados que entram no pipeline. | Não mudei o cálculo. Registrei que esses valores só valem dentro da mesma execução. | Num recorte, SP pode ter outro código e a escala muda. Para comparar recortes, o certo é usar as colunas originais (UF em texto, preço, frete). | Nenhuma mudança na base completa. |
| 21 | CSV final | O painel precisa de um arquivo único, e o GitHub não aceita arquivo acima de 100 MB. | Gravei `data/processed/olist_frete_analitico.csv` sem índice, com quebra de linha `\n` e sem arredondar. | Assim o arquivo sai igual no Windows, no Linux e no Mac. Arredondar mudaria os números da Frente 2. Uma regra no `.gitattributes` mantém o LF também no checkout do Windows. | 112.650 linhas, 47 colunas, 76,4 MB. Igual byte a byte no pandas 2.2.3 e no 3.0.6. |
| 22 | Testes | Precisava mostrar que o pipeline funciona fora da base cheia, sem ajuste manual. | Escrevi `05_testes_pipeline.py` com 8 cenários: completo, CSV x dicionário, categoria ausente, amostras de 1, 2, 10 e 500 pedidos e chave sem match. Todos conferem linhas, chave única, colunas e entrada sem alteração. | Um teste automático roda igual toda vez e pode ser repetido na apresentação. | 1ª rodada: 7 de 8 (o de 1 pedido quebrou no `_minmax` da Frente 2). O João corrigiu no commit `a8cc0ed`. 2ª rodada: 8 de 8. Depois da revisão do PR, os testes passaram a comparar as linhas com os itens limpos e o CSV versionado com a saída atual. 3ª rodada: 8 de 8. Detalhes em `docs/testes_pipeline.md`. |

## O que a Frente 3 não fez

Não mudei regra de limpeza nem de transformação, não respondi as perguntas de negócio e não montei o painel.

## Como reproduzir

```bash
python 04_pipeline.py
python 05_testes_pipeline.py
```
