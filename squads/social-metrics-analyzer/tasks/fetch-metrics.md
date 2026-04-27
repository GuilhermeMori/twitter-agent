# Tarefa: Coleta de Métricas (Apify)

## Objetivo
Extrair métricas puras do Twitter, LinkedIn e Instagram utilizando a skill Apify.

## Instruções
1. Leia o arquivo `research-focus.md` para obter as URLs dos perfis e o período de interesse.
2. Identifique quais atores do Apify são necessários (ex: `social-media-stats-scraper`).
3. Execute o Apify via `execution: subagent` para coletar:
   - Follower count.
   - Post likes e comment counts (se disponíveis no ator).
4. Salve o resultado bruto consolidado em `raw-metrics.json`.

## Regras
- Utilize a skill `apify` para todas as coletas.
- Se uma plataforma falhar, reporte o erro claramente no log, mas continue com as outras.
- Não tente interpretar os dados, apenas extraia e salve.

## Saída Esperada
Um arquivo JSON em `output/raw-metrics.json` contendo as métricas de cada rede social mapeada.
