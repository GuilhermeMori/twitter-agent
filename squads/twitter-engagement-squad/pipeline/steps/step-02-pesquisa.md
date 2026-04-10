---
execution: subagent
agent: "beto-busca"
inputFile: squads/twitter-engagement-squad/output/research-focus.md
outputFile: squads/twitter-engagement-squad/output/raw-posts.md
model_tier: "powerful"
---

# Step 02: Search for Relevant Posts

In this step, **Beto Research** sweeps Twitter/X for posts that meet the defined engagement criteria and keywords.

## Context Loading

Load these files before executing:
- `squads/twitter-engagement-squad/output/research-focus.md` — User search parameters.
- `squads/twitter-engagement-squad/pipeline/data/research-brief.md` — Search strategies.

## Instructions

### Process
1. **Interpret Focus**: Read `research-focus.md` and extract keywords and filters.
2. **Execute Apify**: Call the `apify` skill with the extracted parameters.
3. **Filter Results**: Apply engagement logic (likes/reposts) to the raw data.
4. **Export YAML**: Save the filtered list of posts in `output/raw-posts.md`.
    - **CRITICAL**: The file must contain ONLY pure YAML code. DO NOT use Markdown code blocks (` ```yaml `) inside the final file.
    - **MINIMUM**: If no qualified posts are found, return an empty list: `posts: []`.

## Output Format

The output must follow this exact YAML structure:
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
    text: "The potential of autonomous agents to scale businesses is insane. 🤯"
    likes: 312
    reposts: 104
    timestamp: "2026-04-01T10:30:00Z"
```

## Veto Conditions

Reject and redo if ANY of these are true:
1. Fewer than 3 posts are found (try softening the filters slightly).
2. The Apify XML/JSON file is corrupted or empty.

## Quality Criteria

- [ ] Posts have the correct lead time.
- [ ] Author and URL are complete.
- [ ] Total engagement is high enough.
