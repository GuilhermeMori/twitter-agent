---
task: "find-posts"
order: 1
input: |
  - keywords: Palavras-chave a serem pesquisadas.
  - min_likes: Quantidade mínima de likes para filtrar.
  - min_reposts: Quantidade mínima de reposts para filtrar.
  - interval: Intervalo de tempo (ex: 1 hora).
  - target_profiles: Lista de perfis específicos para monitorar.
output: |
  - raw-posts: Lista estruturada com os posts encontrados.
---

# Find Posts

Este processo utiliza o Apify para buscar posts no Twitter/X com base nos parâmetros configurados.

## Process

1. **Configurar Busca no Apify**: Utilizar o ator `quacker/twitter-search` ou similar para as palavras-chave e perfis.
2. **Filtrar por Métricas**: Aplicar os limites de `min_likes` e `min_reposts` em cada post coletado.
3. **Validar Lead Time**: Descartar posts fora do `interval` (ex: mais antigos que 1 hora).
4. **Extrair Dados**: Coletar URL, ID, Texto, Autor e Métricas (likes, reposts).
5. **Estruturar Saída**: Retornar até 20 posts em formato YAML/Markdown para o próximo passo.

## Output Format

```yaml
posts:
  - id: "123456789"
    url: "https://twitter.com/user/status/123456789"
    author: "@user"
    text: "O futuro da IA é fascinante!"
    likes: 156
    reposts: 42
    timestamp: "2026-04-01T10:00:00Z"
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
posts:
  - id: "1774780000000000000"
    url: "https://x.com/isatool_ai/status/177478..."
    author: "@isatool_ai"
    text: "Acabei de testar os novos agentes do Cursor. O poder da automação é real! 🚀 #IA #SoftwareEngineer"
    likes: 245
    reposts: 89
    timestamp: "2026-04-01T10:15:00Z"
```

## Quality Criteria

- [ ] Todos os posts possuem pelo menos o `min_likes` definido.
- [ ] O link (url) é válido e acessível.
- [ ] O texto está completo, sem truncamento excessivo.

## Veto Conditions

Reject and redo if ANY are true:
1. Mais de 50% dos posts não possuem relação com as keywords.
2. Os links gerados estão quebrados ou apontam para perfis bloqueados/suspensos.
