# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`devpub upload`** -- upload images to Dev.to and get their public URLs, so a
  post with figures can be written and published without opening the web editor.
  Supports `--markdown` to print ready-to-paste image tags.
- Session-based credentials (`DEVPUB_SESSION_COOKIE`, `DEVPUB_CSRF_TOKEN`) for the
  upload endpoint, which is session-authenticated rather than API-key-authenticated.

## [0.2.1] - 2026-08-20

### Added

- **Multi-period sparkline breakdown** below the chart showing 7d, 14d, 21d, and 30d trends at a glance
- Each period shows its own sparkline, trend arrow, and total views

### Fixed

- Python 3.10 compatibility: fixed backslash-in-fstring SyntaxError that broke the PyPI package
- Unicode box-drawing characters now use pre-assigned constants instead of inline escapes

## [0.2.0] - 2026-08-20

### Added

- **Enhanced graph rendering** for `devpub stats --graph`:
  - Color gradient bars that fade from blue (low) to cyan to green to gold (peak)
  - Sparkline one-liner below chart for compact trend visualization
  - Trend indicator comparing last 7 days vs previous 7 days (arrow + percentage)
  - Average line with dotted markers and label across the chart
  - Peak marker with bold gold value and date in summary
  - Box-drawing tick marks on Y-axis for cleaner look
  - 12-row chart height (up from 10) for more vertical resolution
  - 4 Y-axis labels at 25%, 50%, 75%, 100% marks
- `--graph` flag now fully functional with `devpub stats --graph`
- Period flag support: `devpub stats --graph -p 7d` (7d, 30d, 90d, 2w, 3m)
- Auto-downsampling when data exceeds terminal width
- 41 unit tests (18 new for enhanced graph helpers)

### Changed

- Chart rendering upgraded from single-color cyan to multi-color gradient
- Summary line now shows bold formatting and peak date
- Y-axis uses box-drawing characters instead of plain pipe

## [0.1.0] - 2026-07-28

### Added

- Initial release
- CLI entry point with Click
- Dev.to API client with V1 Accept header and rate limiting support
- `devpub init` -- initialize a project directory
- `devpub new` -- create articles from templates (default, TIL, tutorial, comparison, experience)
- `devpub push` -- publish or update articles on Dev.to
- `devpub pull` -- download articles from Dev.to to local markdown
- `devpub status` -- show sync state between local and remote
- `devpub validate` -- check articles for issues before publishing
- `devpub stats` -- view analytics (views, reactions, comments, followers)
- `devpub dashboard` -- full analytics dashboard
- `devpub trends` -- discover trending topics
- `devpub search` -- keyword and semantic article search
- `devpub whoami` -- show authenticated user profile
- `devpub doctor` -- check API connectivity and configuration
- Frontmatter-based article model with devto_id tracking
- Config via environment variables and .env files
