---
task: "find-posts"
order: 1
input: |
  - keywords: Keywords to be searched.
  - min_likes: Minimum number of likes to filter.
  - min_reposts: Minimum number of reposts to filter.
  - min_replies: Minimum number of replies (comments) to filter.
  - interval: Time interval (e.g., 1 hour).
  - target_profiles: List of specific profiles to monitor.
output: |
  - raw-posts: Structured list of found posts.
---

# Find Posts

This process uses Apify to search for posts on Twitter/X based on the configured parameters.

## Process

1. **Configure Apify Search**: Use the `quacker/twitter-search` actor or similar for the keywords and profiles.
2. **Filter by Metrics**: Apply the `min_likes`, `min_replies`, and `min_reposts` limits to each collected post.
3. **Validate Lead Time**: Discard posts outside the `interval` (e.g., older than 1 hour).
4. **Extract Data**: Collect URL, ID, Text, Author, and Metrics (likes, reposts, timestamp).
5. **Structure Output**: Return up to 20 posts in YAML format for the next step.

## Output Format

```yaml
posts:
  - id: "123456789"
    url: "https://twitter.com/user/status/123456789"
    author: "@user"
    text: "The future of AI is fascinating!"
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
    text: "Just tested the new Cursor agents. The power of automation is real! 🚀 #AI #SoftwareEngineer"
    likes: 245
    reposts: 89
    timestamp: "2026-04-01T10:15:00Z"
```

## Quality Criteria

- [ ] All posts have at least the defined `min_likes`.
- [ ] The link (url) is valid and accessible.
- [ ] The text is complete without excessive truncation.

## Veto Conditions

Reject and redo if ANY are true:
1. More than 50% of the posts are unrelated to the keywords.
2. The generated links are broken or point to blocked/suspended profiles.
