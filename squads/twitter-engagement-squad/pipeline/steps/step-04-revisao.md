---
execution: inline
agent: "rita-revisao"
inputFile: squads/twitter-engagement-squad/output/draft-comments.md
outputFile: squads/twitter-engagement-squad/output/review-result.md
on_reject: 3
---

# Step 04: Revisão e Notificação

Nesta etapa, o **Rita Revisão** avalia as sugestões do Cadu e envia um e-mail de notificação para o usuário (Gmail).

## Context Loading

Load these files before executing:
- `squads/twitter-engagement-squad/output/draft-comments.md` — Comentários sugeridos.
- `squads/twitter-engagement-squad/pipeline/data/quality-criteria.md` — Checklist de revisão.
- `squads/twitter-engagement-squad/pipeline/data/anti-patterns.md` — Erros fatais a evitar.

## Instructions

### Process
1. **Ponderar Notas**: Para cada par de [Post-Comentário], aplicar as notas do `quality-criteria.md`.
2. **Checar Segurança**: Garantir que o comentário é 100% seguro para a marca da Gbm.
3. **Disparar Gmail**: Executar o script `send-comments.js` enviando:
   - **No corpo do e-mail**: Os 3 primeiros comentários com melhor score
   - **Em anexo (Word)**: Todos os comentários aprovados em formato Word
   - Link do post original para cada comentário
   - Scores e notas da revisão
4. **Veredito de Pipeline**: Salvar o veredito (APROVADO/REPROVADO) em `output/reviewed-comments.md`.

## Output Format

O output deve seguir exatamente esta estrutura:
```yaml
verdict: "APROVADO"
score: 9.0
rationale: |
  Feedback detalhado aqui. Pontos fortes e melhorias sugeridas.
email_sent: true
```

## Output Example

```yaml
verdict: "APROVADO"
score: 8.5
rationale: |
  Review: O gancho é excelente e conecta bem com a dor do autor. 
  E-mail enviado para guilherme@example.com (via Gmail SMTP).
email_sent: true
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. O comentário possuir erros de concordância ou digitação.
2. O veredito for REPROVADO sem uma justificativa clara para o Cadu refazer.

## Quality Criteria

- [ ] O e-mail deve ser disparado em menos de 10 segundos.
- [ ] O link para o post original é clicável e correto.
- [ ] O tom da revisão é construtivo.
