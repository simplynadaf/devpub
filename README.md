<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner.svg">
  <img alt="devpub - Write in your editor. Publish to Dev.to. Track what works." src="assets/banner.svg" width="100%">
</picture>

<br><br>

**The Dev.to CLI that uses 98% of the API. Competitors use 20%.**

[![CI](https://github.com/simplynadaf/devpub/actions/workflows/test.yml/badge.svg)](https://github.com/simplynadaf/devpub/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/simplynadaf/devpub/pulls)

<br>

[Getting Started](#quick-start) | [Commands](#commands) | [Configuration](#configuration) | [Contributing](#contributing)

</div>

---

devpub is a command-line tool for developers who write on [Dev.to](https://dev.to). Write articles in your favorite editor, version control them with Git, publish with one command, and track analytics, all from the terminal.

It uses 98% of the Dev.to API surface, including endpoints no other tool touches: semantic search, ML-powered content concepts, and full analytics.

## Why devpub?

Existing Dev.to tools are either abandoned, broken, or only cover basic publishing. devpub is different:

| Feature | devpub | devto-cli | slinkity | dev-to-git |
|---------|--------|-----------|----------|------------|
| Publish from CLI | Yes | Yes | No | No |
| Pull articles to local | Yes | No | No | Yes |
| Terminal analytics | Yes | No | No | No |
| Semantic search | Yes | No | No | No |
| Trend discovery | Yes | No | No | No |
| Article validation | Yes | No | No | No |
| Rate limiting | Yes | No | N/A | No |
| Actively maintained | Yes | No (2y stale) | No | No (3y stale) |

## Installation

**From source (recommended during beta):**

```bash
git clone https://github.com/simplynadaf/devpub.git
cd devpub
pip install -e .
```

**With pip (once published to PyPI):**

```bash
pip install devpub
```

**Requirements:** Python 3.10 or higher.

## Quick Start

```bash
# 1. Set your API key (get it at https://dev.to/settings/extensions)
export DEVPUB_API_KEY=your_key_here

# 2. Initialize a project
devpub init

# 3. Create your first article
devpub new "My Article Title"

# 4. Edit the article in your editor, then publish
devpub push -f articles/my-article-title.md

# 5. Check how it's performing
devpub stats
```

## Commands

### Writing

| Command | Description |
|---------|-------------|
| `devpub init` | Initialize a devpub project (creates `.devpub/` config and `articles/` directory) |
| `devpub new "Title"` | Create a new article from a template |
| `devpub new "Title" -t tutorial` | Use a specific template (default, til, tutorial, comparison, experience) |
| `devpub validate` | Check articles for issues before publishing |
| `devpub validate -f path.md` | Validate a specific file |

### Publishing

| Command | Description |
|---------|-------------|
| `devpub push -f article.md` | Publish or update a specific article |
| `devpub push --all` | Push all articles in your project |
| `devpub push --dry-run` | Preview what would be published |
| `devpub pull` | Download your published articles from Dev.to |
| `devpub pull --all` | Include drafts |
| `devpub status` | Show sync state (local vs Dev.to) |

### Analytics

| Command | Description |
|---------|-------------|
| `devpub stats` | Lifetime totals (views, reactions, comments, followers) |
| `devpub stats --referrers` | Traffic sources |
| `devpub stats --followers` | Follower engagement |
| `devpub dashboard` | Complete analytics with top articles table |

### Discovery

| Command | Description |
|---------|-------------|
| `devpub trends` | Trending topics on Dev.to right now |
| `devpub search "query"` | Keyword search for articles |
| `devpub search "query" --semantic` | AI-powered search by meaning (not just keywords) |

### Utilities

| Command | Description |
|---------|-------------|
| `devpub whoami` | Show your Dev.to profile |
| `devpub doctor` | Check API connectivity and config |
| `devpub --version` | Show version |

## Configuration

devpub looks for your API key in this order:

1. Environment variable: `DEVPUB_API_KEY` or `DEVTO_API_KEY`
2. Project-level: `.devpub/.env`
3. Global: `~/.devpub/.env`

Get your API key at: https://dev.to/settings/extensions

### Project Structure

After `devpub init`, your project looks like:

```
my-blog/
  .devpub/
    .env          # Your API key (gitignored)
    config.yml    # Project settings
  articles/
    my-post.md   # Your articles with frontmatter
```

### Article Frontmatter

```yaml
---
title: "Your Article Title"
published: false
description: "Brief description for SEO"
tags: python, tutorial, beginners
cover_image: https://example.com/image.png
series: "My Series Name"
canonical_url: https://myblog.com/original-post
---

Your article content in Markdown...
```

## Project Status

**devpub is in beta.** Core functionality works and is tested against the live Dev.to API, but:

- The API surface is large and some edge cases may not be handled
- Error messages could be more specific in some situations
- Performance for accounts with 500+ articles could be improved

We follow [semantic versioning](https://semver.org/). Until v1.0, minor versions may include breaking changes (documented in CHANGELOG.md).

## Contributing

We welcome contributions of all kinds. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**Quick version:**

```bash
git clone https://github.com/simplynadaf/devpub.git
cd devpub
pip install -e ".[dev]"
pytest
```

### Ways to contribute

- **Report bugs** -- open an [issue](https://github.com/simplynadaf/devpub/issues/new?template=bug_report.md)
- **Request features** -- open an [issue](https://github.com/simplynadaf/devpub/issues/new?template=feature_request.md)
- **Fix bugs** -- check [good first issues](https://github.com/simplynadaf/devpub/labels/good%20first%20issue)
- **Improve docs** -- README, docstrings, examples
- **Add tests** -- especially for edge cases

### Before submitting a PR

1. Fork the repo and create a branch
2. Make your changes
3. Run `pytest` and `ruff check src/ tests/`
4. Open a PR with a clear description

## Security

If you discover a security vulnerability, please report it responsibly. See [SECURITY.md](SECURITY.md) for details. Do not open a public issue for security vulnerabilities.

## License

[MIT](LICENSE) -- use it however you want.

## Acknowledgments

- Built on the [Forem API](https://developers.forem.com/api/v1) that powers Dev.to
- CLI powered by [Click](https://click.palletsprojects.com/)
- Terminal output by [Rich](https://github.com/Textualize/rich)
- HTTP by [httpx](https://www.python-httpx.org/)

---

<div align="center">

Made by [Sarvar Nadaf](https://sarvarnadaf.com)

If devpub saves you time, consider giving it a star.

</div>
