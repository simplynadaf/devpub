# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-28

### Added

- Initial release
- CLI entry point with Click
- Dev.to API client with V1 Accept header and rate limiting support
- `devpub init` — initialize a project directory
- `devpub new` — create articles from templates (default, TIL, tutorial, comparison, experience)
- `devpub push` — publish or update articles on Dev.to
- `devpub pull` — download articles from Dev.to to local markdown
- `devpub status` — show sync state between local and remote
- `devpub validate` — check articles for issues before publishing
- `devpub stats` — view analytics (views, reactions, comments, followers)
- `devpub dashboard` — full analytics dashboard
- `devpub trends` — discover trending topics
- `devpub search` — keyword and semantic article search
- `devpub whoami` — show authenticated user profile
- `devpub doctor` — check API connectivity and configuration
- Frontmatter-based article model with devto_id tracking
- Config via environment variables and .env files
