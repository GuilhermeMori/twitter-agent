---
execution: inline
agent: "rita-revisao"
inputFile: squads/twitter-engagement-squad/output/draft-comments.md
outputFile: squads/twitter-engagement-squad/output/review-result.md
on_reject: 3
---

# Step 04: Review and Notification

In this step, **Rita Review** evaluates Cadu's suggestions and sends a notification email to the user (via Gmail).

## Context Loading

Load these files before executing:
- `squads/twitter-engagement-squad/output/draft-comments.md` — Suggested comments.
- `squads/twitter-engagement-squad/pipeline/data/quality-criteria.md` — Review checklist.
- `squads/twitter-engagement-squad/pipeline/data/anti-patterns.md` — Fatal errors to avoid.

## Instructions

### Process
1. **Apply Scores**: For each [Post-Comment] pair, apply the scores from `quality-criteria.md`.
2. **Check Safety**: Ensure the comment is 100% safe for the Growth Collective brand.
3. **Trigger Gmail**: Execute the `send-comments.js` script sending:
   - **In the email body**: The top 3 comments with the highest scores.
   - **Attached**: All approved comments in Word format.
   - Direct link to the original post for each comment.
   - Review scores and rationale.
4. **Pipeline Verdict**: Save the verdict (APPROVED/REJECTED) in `output/review-result.md`.

## Output Format

The output must follow this exact structure:
```yaml
verdict: "APPROVED"
score: 9.0
rationale: |
  Detailed feedback here. Strengths and suggested improvements.
email_sent: true
```

## Output Example

```yaml
verdict: "APPROVED"
score: 8.5
rationale: |
  Review: The hook is excellent and connects well with the author's pain point. 
  Email sent to guilherme@example.com (via Gmail SMTP).
email_sent: true
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. The comment has grammar or spelling errors.
2. The verdict is REJECTED without a clear justification for Cadu to redo.

## Quality Criteria

- [ ] The email is triggered within 10 seconds.
- [ ] The link to the original post is clickable and correct.
- [ ] The review tone is constructive.
