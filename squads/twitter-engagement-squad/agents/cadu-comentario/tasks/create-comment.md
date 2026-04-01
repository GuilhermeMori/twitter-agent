---
task: "create-comment"
order: 1
input: |
  - post: O texto e metadados do post original.
  - tone: O tom de voz selecionado (ex: Descontraído).
output: |
  - suggestion: O texto do comentário sugerido.
---

# Create Comment

Este processo transforma um post monitorado em uma sugestão de resposta engajadora.

## Process

1. **Analisar Contexto**: Identificar o ponto principal do post (dor, conquista, notícia).
2. **Escolher Hook**: Criar uma frase de abertura (scroll-stop) que valide ou refute o post com impacto.
3. **Desenvolver Valor**: Adicionar uma linha de contribuição ou reação inteligente.
4. **Inserir CTA**: Terminar com uma pergunta aberta ou convite à resposta.
5. **Formatar**: Aplicar quebras de linha estratégicas (max 2-3 linhas por bloco).

## Output Format

```yaml
suggestion: |
  [Hook chamativo]

  [Breve comentário com valor]

  [Pergunta de engajamento no final] 🤔
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
suggestion: |
  Massa demais esse ponto! 🤯

  Muita gente esquece que o segredo não é só a IA, mas como o humano guia o processo. Aqui na Gbm a gente vê isso todo dia nos squads.

  Você acha que o próximo passo é o agente codar direto de um áudio, ou ainda estamos longe disso? 🤔
```

## Quality Criteria

- [ ] O comentário não ultrapassa 280 caracteres.
- [ ] O tom combina com o escolhido no `tone-of-voice.md`.
- [ ] O post original é mencionado ou referenciado claramente.

## Veto Conditions

Reject and redo if ANY are true:
1. O comentário soa como um robô genérico ("Bom post!", "Concordo").
2. O comentário inclui links externos no corpo.
3. Não há pergunta ou gancho de resposta no final.
