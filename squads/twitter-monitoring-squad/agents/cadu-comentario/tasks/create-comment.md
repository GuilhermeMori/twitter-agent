---
task: "create-comment"
order: 1
input: |
  - post: The text and metadata of the original post.
  - tone: The selected tone of voice (e.g., Strategic Partner).
output: |
  - suggestion: The text of the suggested comment.
---

# Create Comment

This process transforms a monitored post into an engaging response suggestion.

## Process

1. **Analyze Context**: Identify the main point of the post (pain point, win, news).
2. **Choose Hook**: Create an opening sentence (scroll-stop) that validates or refutes the post with impact.
3. **Develop Value**: Add a line of intelligent contribution or reaction.
4. **Insert CTA**: End with an open question or an invitation to reply.
5. **Format**: Apply strategic line breaks (max 2-3 lines per block).

## Output Format

```yaml
suggestion: |
  [Strong Hook]

  [Brief value-added comment]

  [Engagement question/prompt at the end]
```

## Output Example

> Use as quality reference, not as rigid template.

```yaml
suggestion: |
  That efficiently scale wall at $2-3M is real.

  Most founders juggle too many siloed agencies. At Growth Collective, we see that unified strategies are the only way to break through.

  Are you tracking blended MER or just in-platform ROAS?
```

## Quality Criteria

- [ ] The comment does not exceed 280 characters.
- [ ] The tone matches the one chosen from `tone-of-voice.md`.
- [ ] The original post is clearly mentioned or referenced.

## Veto Conditions

Reject and redo if ANY are true:
1. The comment sounds like a generic bot ("Good post!", "I agree").
2. The comment includes external links in the body.
3. There is no question or invitation to reply at the end.
4. USAGE OF ANY EMOJI.
