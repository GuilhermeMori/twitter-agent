# Tarefa: Cálculo de Crescimento e Insights

## Objetivo
Transformar os dados brutos em uma análise comparativa de crescimento.

## Instruções
1. Leia `raw-metrics.json`.
2. Pergunte ao usuário (modo `inline`) quais eram os números de seguidores/likes no início do período de comparação, caso esses dados não estejam disponíveis no histórico local.
3. Para cada métrica chave (Followers, Likes, Comments):
   - Calcule o Delta Absoluto: `Atual - Anterior`.
   - Calcule o Delta Percentual: `((Atual - Anterior) / Anterior) * 100`.
4. Identifique se houve crescimento ou queda e atribua um status ("Bom", "Preocupante", "Crítico").
5. Escreva uma narrativa curta explicando o resultado para cada plataforma.

## Regras
- Use apenas os dados confirmados.
- Se os dados anteriores não forem fornecidos, o cálculo não pode ser realizado (informe ao usuário).
- Formate a saída como um rascunho de relatório em `analysis-results.md`.

## Saída Esperada
Arquivo `output/analysis-results.md` com tabelas comparativas e insights preliminares.
