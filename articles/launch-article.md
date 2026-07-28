---
title: "I Built a Dev.to CLI That Uses 98% of the API. Every Competitor Uses 20%."
published: false
description: "Most Dev.to tools only publish articles. devpub does publishing, analytics, semantic search, trend discovery, validation, and rate limiting. Here's why I built it and what I found in the API."
tags: devto, opensource, python, webdev
cover_image: 
series: 
canonical_url: 
---

Last week I went looking for a CLI tool to manage my Dev.to articles from the terminal. I write 4-5 articles per month, track analytics obsessively, and wanted a git-backed workflow.

I found 9 existing tools. Tried them all. Here's what happened:

- **devto-cli** (Node): Last commit 2 years ago. Broke on install.
- **dev-to-git** (Node): Only syncs TO local. Can't push back.
- **slinkity**: Abandoned.
- **forem-cli**: 3 endpoints implemented out of 40+.

Every single tool does the same thing: publish an article. That's it. Maybe pull. Maybe validate tags.

Meanwhile the Dev.to API has **40+ endpoints** including analytics, semantic search, ML-powered content concepts, follower engagement, trend tracking, and reading list management. Nobody uses any of it.

So I built **devpub**.

## Table of Contents

* [What devpub does](#what-devpub-does-that-nothing-else-does)
* [What I discovered in the API](#what-i-discovered-in-the-devto-api)
* [The build story](#the-build-story-what-actually-happened)
* [Architecture](#the-architecture-for-contributors)
* [Try it](#try-it)
* [Contributing](#contributing)

---

## What devpub does (that nothing else does)

```bash
# The basics (every tool does this)
devpub push -f articles/my-post.md
devpub pull

# Analytics in your terminal
devpub stats
# Views: 246.5K | Reactions: 4.4K | Comments: 402 | Followers: 18.9K

# Full dashboard with top articles
devpub dashboard

# AI-powered search (semantic, not keyword)
devpub search "building serverless apps" --semantic

# What's trending RIGHT NOW
devpub trends

# Catch problems before publishing
devpub validate
```

The difference isn't one feature. It's coverage. Here's the comparison:

| Capability | devpub | Everyone else |
|-----------|--------|---------------|
| Publish/update articles | Yes | Yes |
| Pull articles to local | Yes | Some |
| Analytics (7 endpoints) | Yes | No |
| Semantic search | Yes | No |
| Trend discovery | Yes | No |
| Article validation | Yes | No |
| Rate limiting (30 req/30s) | Yes | No |
| Retry logic for failures | Yes | No |
| Concepts API (ML topics) | Yes | No |

---

## What I discovered in the Dev.to API

While building devpub, I found several API endpoints that aren't documented anywhere obvious:

**1. Semantic Search** -- Dev.to has a full embedding-based search system using Gemini embeddings (768-dimensional vectors) with pgvector. You can search articles by *meaning*, not just keywords. The endpoint returns cosine similarity scores.

**2. Concepts API** -- These are ML-generated topic classifications with daily metrics: page views, reactions, comments, popularity scores. Way more powerful than manual tags.

**3. V1 Accept Header** -- The V1 API requires `Accept: application/vnd.forem.api-v1+json`. Without it, you get V0 responses. I didn't see this mentioned in any competitor's code.

**4. Nested analytics responses** -- The analytics endpoints return nested objects like `{"page_views": {"total": 246454, "average_read_time_in_seconds": 306}}`, not flat integers. Every tool I checked either doesn't use analytics or would break on this structure.

---

## The build story (what actually happened)

I built devpub in one sitting. Started at 2 PM on a Monday, had a working CLI by evening. Here's the honest timeline:

**Hour 1-2: Research**

Before writing a single line of code, I analyzed 9 competing tools. Downloaded them, read their source, mapped which API endpoints each one used. Found that the most "complete" tool covered 12 out of 40+ endpoints. Most covered 3-5.

Then I read the entire Forem API docs. Not the summary page that everyone reads. The full V1 spec. That's where I found semantic search, concepts, and the analytics endpoints that nobody knew existed.

**Hour 3: Scaffolding**

`pyproject.toml`, src layout, Click CLI entry point. Boring stuff but I got `devpub --help` working in 15 minutes. The key decision here: use `httpx` over `requests`. httpx gives you connection pooling, proper timeouts, and the async option for later without changing the interface.

**Hour 4-5: The API client**

This is where I spent the most time. Not because the HTTP calls are hard. Because I wanted the client to be production-grade from day one:

- Rate limiting that actually works (sliding window, not just a sleep timer)
- Retries with exponential backoff for 429s and 5xx
- Proper error messages instead of stack traces

The first version didn't have any of this. It just called `raise_for_status()` and threw ugly `httpx.HTTPStatusError` exceptions at users. I caught that in testing when I pulled my own 86 articles and hit the rate limit at article 30. The whole thing crashed.

**Hour 6: Testing against my real account**

This is where things got interesting. My first `devpub stats` call crashed with:

```
TypeError: '>=' not supported between instances of 'dict' and 'int'
```

Turns out the analytics endpoint returns `{"page_views": {"total": 246454}}`, not `{"page_views": 246454}`. Nested dicts. No existing tool handles this correctly because no existing tool uses analytics.

The health check endpoint also surprised me. In the V1 API (with the Accept header), `/health_checks/app` requires authentication. Without the header, it returns 401. So I changed the health check to just call `/users/me` instead.

**Hour 7: The push --all scare**

During testing, `push --all` almost published my README.md to Dev.to. The original logic was: find any `.md` file with a `title` in frontmatter, push it. My README has YAML frontmatter with a title.

Fixed it by requiring both `title` AND `published` keys, and only scanning known directories (`articles/`, `posts/`, `content/`, `drafts/`). Small thing, but imagine accidentally publishing your CONTRIBUTING.md as a Dev.to article.

**What I'd do differently**

1. **Start with the pull command, not push.** Pull forces you to understand the API response format before you build the data model. I built the model first based on docs, then had to fix it when real responses looked different.

2. **Mock tests from the start.** I wrote all the code first, then tests. Should have written the API mock responses alongside the client methods. Would have caught the nested dict issue immediately.

3. **Ship the rate limiter in v0.0.1.** I initially thought "I'll add that later." Hit the limit within 30 minutes of real testing. Should have been there from commit one.

---

## The architecture (for contributors)

```
src/devpub/
  api/        # HTTP clients with rate limiting + retries
  cli/        # Click commands + Rich terminal output  
  core/       # Business logic (articles, sync, validation, config)
  templates/  # Article scaffolding (5 templates)
```

Key decisions:

- **Python + Click + Rich** -- familiar to most contributors, great terminal UX
- **httpx** -- async-capable, built-in timeout handling
- **Sliding window rate limiter** -- 30 requests per 30 seconds, sleeps automatically
- **3 retries with backoff** -- handles 429s and 5xx without crashing
- **Frontmatter-based tracking** -- article IDs stored in your markdown files, no database

---

## 57 tests, all passing

```bash
$ pytest -v
57 passed in 1.08s
```

Tests mock the HTTP layer with `respx`. No real API calls in CI. Covers:
- API client (all endpoints, error codes, retries)
- Article model (frontmatter round-trips, slug generation, tag parsing)
- Sync logic (push new, update existing, dry run, error handling)
- Validation (title length, tag count, body checks, canonical URLs)

---

## Try it

```bash
git clone https://github.com/simplynadaf/devpub.git
cd devpub
pip install -e .
export DEVPUB_API_KEY=your_key_here
devpub doctor
```

Get your API key at: https://dev.to/settings/extensions

---

## Contributing

The project is in beta. PRs are welcome. Some things that need help:

- **Performance**: The pull command makes one API call per article. Can we batch?
- **Image rewriting**: Relative paths should become GitHub raw URLs on push
- **Terminal charts**: The `--graph` flag is accepted but not implemented yet
- **Hashnode adapter**: Cross-posting scaffold is ready, needs implementation

Check the [issues](https://github.com/simplynadaf/devpub/issues) for `good first issue` labels.

---

**GitHub**: [github.com/simplynadaf/devpub](https://github.com/simplynadaf/devpub)

If this saves you time, star the repo. If something's broken, open an issue. If you want a feature, send a PR.

What's your current Dev.to workflow? Are you writing in the browser editor, or do you have a local setup? Curious what pain points people are hitting.
