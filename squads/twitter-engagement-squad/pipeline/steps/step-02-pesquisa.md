---
execution: subagent
agent: "beto-busca"
inputFile: squads/twitter-engagement-squad/output/research-focus.md
outputFile: squads/twitter-engagement-squad/output/raw-posts.md
model_tier: "powerful"
---

# Step 02: Buscar Posts Relevantes

Nesta etapa, o **Beto Busca** varre o Twitter/X em busca de posts que atendam aos critérios de engajamento e palavras-chave definidos.

## Context Loading

Load these files before executing:
- `squads/twitter-engagement-squad/output/research-focus.md` — Parâmetros de busca do usuário.
- `squads/twitter-engagement-squad/pipeline/data/research-brief.md` — Estratégias de pesquisa.

## Instructions

### Process
1. **Interpretar Foco**: Ler o `research-focus.md` e extrair as palavras-chave e filtros.
2. **Executar Apify**: Chamar a habilidade `apify` com os parâmetros extraídos.
3. **Filtrar Resultados**: Aplicar a lógica de engajamento (likes/reposts) nos dados brutos.
4. **Exportar YAML**: Salvar a lista de posts filtrados em `output/raw-posts.md`.
    - **CRÍTICO**: O arquivo deve conter APENAS o código YAML puro. NÃO use blocos de código Markdown (` ```yaml `) dentro do arquivo final.
    - **MÍNIMO**: Se nenhum post qualificado for encontrado, retorne uma lista vazia: `posts: []`.

## Output Format

O output deve seguir exatamente esta estrutura YAML:
```yaml
posts:
  - id: "..."
    url: "..."
    author: "@..."
    text: "..."
    likes: ...
    reposts: ...
    timestamp: "..."
```

## Output Example

```yaml
posts:
  - id: "1774781234567890123"
    url: "https://x.com/tech_expert/status/1774781234567890123"
    author: "@tech_expert"
    text: "O potencial dos agentes autônomos para escalar negócios é bizarro. 🤯"
    likes: 312
    reposts: 104
    timestamp: "2026-04-01T10:30:00Z"
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. Menos de 3 posts forem encontrados (tente suavizar os filtros levemente).
2. O arquivo XML/JSON do Apify estiver corrompido ou vazio.

## Quality Criteria

- [ ] Os posts possuem o lead time correto.
- [ ] O autor e a URL estão completos.
- [ ] O engajamento total é alto o suficiente.
