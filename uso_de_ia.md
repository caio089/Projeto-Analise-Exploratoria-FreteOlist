# Uso de IA (Anexo D)

| Nº | Data | Integrante | Ferramenta | Etapa e o que foi pedido | O que foi aproveitado | O que a equipe alterou ou verificou | Link |
|----|------|------------|------------|--------------------------|----------------------|-------------------------------------|------|
| 1 | 25/11/2026 | Caio | Cursor | Tirar dúvida sobre o PDF: o que é cada frente e o que entra na Frente 1 | Confirmei que Frente 1 = limpeza + diário | Conferi de novo na seção 2 do enunciado | - |
| 2 | 25/11/2026 | Caio | Cursor | Revisar se a limpeza e o diário cobriam nulos, datas, outliers e pedidos sem item | Checklist do que conferir antes do handoff | Rodei `02_limpeza.py` e conferi as contagens do impacto | - |
| 3 | 26/11/2026 | João Manoel | Cursor | Dúvida se o cliente entra pelo `customer_id` do pedido e se esse merge duplica item | Confirmei que o join é N:1 e que a contagem de linhas tem que bater | Rodei `03_transformacoes.py`: 112.650 antes e depois | - |
| 4 | 26/11/2026 | João Manoel | Cursor | Perguntei o que fazer na razão quando preço + frete do pedido dá zero | Deixar o campo vazio nesse caso, em vez de estourar a divisão | Coloquei a condição no código e contei: 0 pedidos com total zero | - |
| 5 | 26/11/2026 | João Manoel | Cursor | Dúvida no MinMax e no Z-score quando não há variação na coluna | Vi que a conta divide por zero. O combinado foi gravar 0 e não apagar a coluna original | Nenhuma coluna escalada tinha variância zero. Conferi média 0 e desvio 1 no Z-score de `price` | - |
| 6 | 26/11/2026 | Ryan | Claude | Usei Claude para melhorar o código | - | - | - |

Diário de decisões, sumário executivo, respostas de negócio e conclusões foram escritos pela equipe, sem IA.
