---
execution: inline
agent: "cadu-comentario"
inputFile: squads/twitter-engagement-squad/output/raw-posts.md
outputFile: squads/twitter-engagement-squad/output/draft-comments.md
format: "twitter-post"
---

# Step 03: Generate Comments

In this step, **Cadu Copy** creates response suggestions for the selected posts.

## Context Loading

Load these files before executing:
- `squads/twitter-engagement-squad/output/raw-posts.md` — Posts collected by Beto.
- `squads/twitter-engagement-squad/pipeline/data/tone-of-voice.md` — Tone of voice guide.
- `squads/twitter-engagement-squad/pipeline/data/output-examples.md` — Examples of good responses.

## Instructions

### Process
1. **Select Tone of Voice**: Read `tone-of-voice.md` and apply the "Strategic Partner" tone (unless otherwise indicated).
2. **Language**: Write ALL comments in ENGLISH.
3. **Draft Comments**: Write the complete response using strategic line breaks and **ABSOLUTELY ZERO EMOJIS**.
4. **Organic Conclusion**: Finalize the text so the conversation can continue naturally. This can be a strong opinion, agreement, or a real question if it makes sense. Avoid the fixed final question pattern.
5. **Save Suggestions**: Export the list to `output/draft-comments.md`.

## Output Format

The output must follow this exact structure for each post:
```yaml
drafts:
  - post_id: "..."
    suggestion: |
      [Hook]

      [Content]

      [Final prompt/thought]
```

## Output Example

```yaml
drafts:
  - post_id: "1774781234567890123"
    suggestion: |
      That efficiently scale wall at $2-3M is real. 🤯
      
      Unified strategies are the only way to break through at this stage. At Growth Collective, we specialize in high-growth DTC strategies that sync Meta and Google spend.

      Have you considered moving to a blended MER model? 🤔
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. More than 280 characters per suggestion.
2. Use of external links in the body of the comment.
3. Excessive corporate tone (clichés).
4. USAGE OF ANY EMOJI (Immediate Veto).

## Quality Criteria

- [ ] The comment uses strategic line breaks.
- [ ] The opening hook is powerful (scroll-stop).
- [ ] The tone is consultative and innovation-focused.
- [ ] Any scores (1 to 10) have justification.
- [ ] In case of rejection, the necessary changes are listed.
- [ ] Brand Safety Check: The comment is 100% free of emojis?
