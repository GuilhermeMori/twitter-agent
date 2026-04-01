---
execution: inline
agent: "cadu-comentario"
inputFile: squads/twitter-engagement-squad/output/raw-posts.md
outputFile: squads/twitter-engagement-squad/output/draft-comments.md
format: "twitter-post"
---

# Step 03: Gerar Comentários

Nesta etapa, o **Cadu Comentário** cria sugestões de respostas descontraídas para os posts selecionados.

## Context Loading

Load these files before executing:
- `squads/twitter-engagement-squad/output/raw-posts.md` — Posts coletados pelo Beto.
- `squads/twitter-engagement-squad/pipeline/data/tone-of-voice.md` — Guia de tom de voz.
- `squads/twitter-engagement-squad/pipeline/data/output-examples.md` — Exemplos de boas respostas.

## Instructions

### Process
1. **Selecionar Tom de Voz**: Ler o `tone-of-voice.md` e aplicar o tom "Descontraído e Ágil" (salvo indicação contrária).
2. **Idioma**: Escrever TODOS os comentários em INGLÊS, independente do idioma dos posts ou das preferências do usuário.
3. **Gerar Hooks (inline)**: Para cada post, criar 3 opções de ganchos (hooks) e selecionar o melhor internamente.
4. **Draftar Comentários**: Escrever a resposta completa usando quebras de linha e **ABSOLUTAMENTE ZERO EMOJIS**.
5. **Conclusão Orgânica**: Finalizar o texto de forma que a conversa possa continuar naturalmente. Pode ser uma opinião forte, uma concordância ou, somente se fizer sentido real, uma pergunta pontual. Evitar o padrão fixo de pergunta ao final.
6. **Salvar Sugestões**: Exportar a lista em `output/draft-comments.md`.

## Output Format

O output deve seguir exatamente esta estrutura para cada post:
```yaml
drafts:
  - post_id: "..."
    suggestion: |
      [Hook]

      [Conteúdo]

      [Pergunta final] 🚀
```

## Output Example

```yaml
drafts:
  - post_id: "1774781234567890123"
    suggestion: |
      Massa demais essa visão! 🤯
      
      Acredito que os agentes autônomos são o divisor de águas entre quem escala e quem fica preso no operacional. Aqui na Gbm a gente foca nisso 100%.

      Você já usa algum squad automatizado ou ainda está explorando? 🤔
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. Mais de 280 caracteres por sugestão.
2. Uso de links externos no corpo do comentário.
3. Tom corporativo excessivo (clichês).
4. USO DE QUALQUER EMOJI (Veto Imediato).

## Quality Criteria

- [ ] O comentário utiliza quebras de linha estratégica.
- [ ] O gancho de abertura (hook) é potente (scroll-stop).
- [ ] O tom é amigável e inovador.
- [ ] Todas as notas (1 a 10) possuem justificativa.
- [ ] Em caso de reprovação, as mudanças necessárias estão listadas.
- [ ] Verificação de Brand Safety: O comentário está 100% livre de emojis?
- [ ] O e-mail de notificação (via Blotato) contém o link do post e o texto sugerido.
