# Testes do pipeline — Frente 3

**Responsável:** Ryan  
**Script:** `05_testes_pipeline.py`  
**Data:** 26/11/2026

## Como rodar

```bash
python 04_pipeline.py          # gera o CSV final (um dos testes confere esse arquivo)
python 05_testes_pipeline.py
```

O script roda os 8 cenários em sequência, sem ajuste manual. Se um cenário quebrar, os outros continuam rodando, e no fim ele mostra quantos passaram. Quando algum falha, o script termina com código de saída 1.

## O que todo cenário confere

Em todos os cenários o script chama `preprocessar(...)` e confere:

1. **Não quebra:** a função termina sem erro.
2. **Não duplica linha:** a tabela final tem o mesmo número de linhas que o `items` de entrada.
3. **Chave única:** nenhum par (`order_id`, `order_item_id`) se repete.
4. **Mesmas colunas:** as 47 colunas, na ordem de `COLUNAS_FINAIS` (a do dicionário).
5. **Entrada intacta:** os 5 DataFrames de entrada continuam iguais a uma cópia feita antes da chamada.

## Cenários

| Cenário | Entrada | O que mais confere |
|---------|---------|--------------------|
| pipeline completo | Os 5 CSVs brutos inteiros | 112.650 linhas; 0 itens sem par nos 4 merges; resultado idêntico ao `transformar_bases` do João (`DataFrame.equals`) |
| CSV final x dicionário | `data/processed/olist_frete_analitico.csv` | Tamanho < 100 MB; cabeçalho igual às colunas do `docs/dicionario_dados.md`; 112.650 linhas; chave única; 27 UFs de cliente; UF de vendedor e status dentro dos valores válidos; 74 categorias com `sem_categoria`; anos 2016–2018; meses 1–12; preço > 0 e frete ≥ 0; razão do frete entre 0 e 1; códigos ≥ 0; MinMax entre 0 e 1; vazios só nas colunas e quantidades do dicionário (1.603 descrição, 26 peso, 18 dimensões/volume) |
| categoria ausente | Recorte de 500 pedidos; 20 produtos com a categoria apagada | Os itens desses produtos saem como `sem_categoria`; nenhuma categoria vazia |
| amostra de 1 pedido | 1 pedido sorteado | Só as conferências comuns |
| amostra de 2 pedidos | 2 pedidos sorteados | Só as conferências comuns |
| amostra de 10 pedidos | 10 pedidos sorteados | Só as conferências comuns |
| amostra de 500 pedidos | 500 pedidos sorteados | Só as conferências comuns |
| chave sem match | Recorte de 500 pedidos com um item de produto inexistente, um de vendedor inexistente, um de pedido inexistente e um pedido de cliente inexistente | O item continua na tabela; vazio nas colunas da outra base; UF vazia vira código `-1`; `historico_merges` conta 1 item sem pedido, 1 sem produto, 1 sem vendedor e 2 sem cliente (o item do pedido com cliente falso + o item sem pedido) |

Os recortes usam `recortar_pedidos(...)` com semente fixa (42), então o mesmo `n` sorteia sempre os mesmos pedidos.

## Resultados

### 1ª execução — antes da correção do João

```text
OK     | pipeline completo        |   2.2 s | 112650 linhas x 47 colunas, igual ao transformar_bases do João
OK     | CSV final x dicionário   |   0.7 s | 76.4 MB, 47 colunas na ordem do dicionário, valores e vazios conferidos
OK     | categoria ausente        |   0.2 s | 24 itens de 20 produtos sem categoria viraram sem_categoria
FALHOU | amostra de 1 pedido      |   0.2 s | TypeError: float() argument must be a string or a real number, not 'NAType'
OK     | amostra de 2 pedidos     |   0.2 s | 2 pedido(s), 2 itens
OK     | amostra de 10 pedidos    |   0.2 s | 10 pedido(s), 11 itens
OK     | amostra de 500 pedidos   |   0.2 s | 500 pedido(s), 558 itens
OK     | chave sem match          |   0.3 s | itens sem par: pedido 1, produto 1, cliente 2, vendedor 1; ficaram com campo vazio

7 de 8 cenários passaram
```

**Falha encontrada:** com 1 pedido, toda coluna escalada tem um valor só (máximo = mínimo). O `_minmax` do `03_transformacoes.py` entra no caso "sem variação", mas a linha `pd.Series(pd.NA, ..., dtype="float64")` não consegue criar uma série float com `pd.NA` e quebra. O `_zscore` tinha a mesma linha. Quebrava no pandas 2.2.3 e no 3.0.6. Na base completa esse caso não acontece, então o CSV não era afetado.

**Correção:** o João trocou `pd.NA` por `float("nan")` nas duas funções (commit `a8cc0ed`).

### 2ª execução — com a correção (`a8cc0ed`)

```text
OK     | pipeline completo        |   2.1 s | 112650 linhas x 47 colunas, igual ao transformar_bases do João
OK     | CSV final x dicionário   |   0.7 s | 76.4 MB, 47 colunas na ordem do dicionário, valores e vazios conferidos
OK     | categoria ausente        |   0.2 s | 24 itens de 20 produtos sem categoria viraram sem_categoria
OK     | amostra de 1 pedido      |   0.2 s | 1 pedido(s), 1 itens
OK     | amostra de 2 pedidos     |   0.2 s | 2 pedido(s), 2 itens
OK     | amostra de 10 pedidos    |   0.2 s | 10 pedido(s), 11 itens
OK     | amostra de 500 pedidos   |   0.2 s | 500 pedido(s), 558 itens
OK     | chave sem match          |   0.3 s | itens sem par: pedido 1, produto 1, cliente 2, vendedor 1; ficaram com campo vazio

8 de 8 cenários passaram
```

Ambiente: Python 3.12.10, pandas 3.0.6, numpy 2.5.4, Windows 11.

Repeti a 2ª execução com pandas 2.2.3: também 8 de 8. O CSV gerado nas duas versões é idêntico byte a byte (SHA-256 começando com `ea28a88cd4c535ac`).

## Recorte ao vivo (apresentação)

```bash
python 04_pipeline.py --amostra 300
```

Roda o pipeline em 300 pedidos sorteados e mostra na tela a limpeza, os merges, o tamanho da tabela e as 10 primeiras linhas. Não sobrescreve o CSV final. Resultado em 26/11: 300 pedidos, 342 itens, 342 linhas x 47 colunas, 0 itens sem par.
