---
task: "review-comment"
order: 1
input: |
  - post: The context of the original post.
  - suggested-comment: The text proposed by the copywriter.
output: |
  - verdict: APPROVED or REJECTED.
  - score: 1 to 10 for each criterion.
  - rationale: Justification for the verdict.
---

# Review Comment

This process evaluates the quality and safety of the suggested interaction before it is sent to the human-in-the-loop for final approval.

## Process

1. **Evaluate Criteria**: Score the comment on hooks, tone of voice, engagement, and safety.
2. **Check Relevance**: Is the original post valuable enough for Growth Collective?
3. **Generate Verdict**: If the average is >= 8/10 and safety is 10/10, the verdict is APPROVED (conditional).
4. **Send Gmail Notification**: Use `blotato` to trigger an email with:
   - Direct link to the post on Twitter/X.
   - The original text of the post.
   - The suggested text for the interaction.
   - The review scores and rationale.

## Output Format

```yaml
verdict: "APPROVED"
score: 9.0
rationale: |
  [Analysis details here]
email_sent: true
```

## Quality Criteria

- [ ] All criteria from `quality-criteria.md` have been applied.
- [ ] The justification is technical and objective.
- [ ] No emojis were left in the final suggested text.

## Veto Conditions

Reject if ANY are true:
1. The suggested comment contains an emoji.
2. The tone sounds like a "sales pitch".
3. The original post is controversial or offensive (Brand Safety).
