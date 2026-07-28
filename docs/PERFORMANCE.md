# Performance Notes

## Pull Command (v0.1.0)

Current behavior: `devpub pull` makes N+1 API calls (1 list call per page + 1 GET per article for body_markdown).

For accounts with many articles:
- 50 articles: ~20 seconds
- 100 articles: ~60 seconds
- 200 articles: ~120 seconds

### Planned optimization

The Dev.to list endpoint already returns `body_markdown` for the authenticated
user's own articles when using `/articles/me/all` or `/articles/me/published`.

Fix: check if body_markdown is present in the list response and skip the
individual fetch when it is. This would reduce pull to just 1-2 API calls
for most users.

### Workaround

For now, use pagination on the Dev.to side:
```bash
# Pull only recent articles (default: published only)
devpub pull
```
