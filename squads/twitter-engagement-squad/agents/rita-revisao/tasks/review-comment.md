---
task: "review-comment"
order: 1
input: |
  - post: O post original (texto, autor, link).
  - comment: O comentário sugerido pelo Cadu.
  - criteria: O arquivo `quality-criteria.md`.
output: |
  - verdict: APROVADO | REPROVADO.
  - score: Nota de 1 a 10.
  - rationale: Justificativa detalhada.
  - email_sent: Status da notificação via Gmail.
---

# Review Comment

Este processo avalia a qualidade da interação e notifica o usuário via Gmail para a decisão final.

## Process

1. **Avaliar Critérios**: Pontuar o comentário em ganchos (hooks), tom de voz, engajamento e segurança.
2. **Checar Relevância**: O post original é valioso o suficiente para a Gbm?
3. **Gerar Veredito**: Se a média for >= 8/10 e segurança for 10/10, o veredito é APROVADO condicional.
4. **Enviar Notificação Gmail**: Utilizar o `blotato` para disparar um e-mail com:
   - Link direto para o post no Twitter/X.
   - Texto original do post.
   - Sugestão de resposta do Cadu.
5. **Registrar Resultado**: Salvar o status e preparar o pipeline para o checkpoint humano.

## Output Format

```yaml
verdict: "APROVADO"
score: 8.5
rationale: |
  O gancho é forte ("Cursor em outro nível") e a pergunta final induz resposta. 
  A segurança de marca está garantida. Nota 10 em relevância técnica.
email_sent: true
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
verdict: "REPROVADO"
score: 4.0
rationale: |
  O comentário soa muito como um robô ("Legal post, continue assim"). 
  Não há gancho de engajamento nem valor agregado. Reenviar para o Cadu.
email_sent: false
```

## Quality Criteria

- [ ] O veredito é fundamentado nos critérios do `quality-criteria.md`.
- [ ] O link original do post está incluído na análise.
- [ ] A segurança de marca (Brand Safety) é avaliada rigorosamente.

## Veto Conditions

Reject and redo if ANY are true:
1. O comentário for aprovado mas possuir erros gramaticais óbvios.
2. O agente aprovar um post com conteúdo ofensivo ou tóxico.
3. Não for gerado o gatilho de e-mail quando o comentário for promissor.
