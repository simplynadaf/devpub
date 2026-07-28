# Contributing to devpub

First off, thanks for considering contributing to devpub. Every contribution matters — whether it's a bug report, feature suggestion, documentation fix, or code change.

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- A Dev.to account (for integration testing)

### Development Setup

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/devpub.git
cd devpub

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Verify everything works
pytest
ruff check src/ tests/
devpub --version
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_api.py

# Run a specific test
pytest tests/test_api.py::TestArticleEndpoints::test_create_article
```

### Linting

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix safe issues
ruff check --fix src/ tests/
```

## How to Contribute

### Reporting Bugs

Found a bug? [Open an issue](https://github.com/simplynadaf/devpub/issues/new?template=bug_report.md) with:

- Steps to reproduce
- Expected vs actual behavior
- Your Python version and OS
- Full error output (redact your API key)

### Suggesting Features

Have an idea? [Open a feature request](https://github.com/simplynadaf/devpub/issues/new?template=feature_request.md). Include:

- The problem you're solving
- Proposed CLI interface (example commands)
- Why existing solutions don't work

### Submitting Code

1. **Find or create an issue** — discuss before building
2. **Fork and branch** — `git checkout -b feature/my-change` or `fix/the-bug`
3. **Write code** — follow the existing style
4. **Add tests** — new features need tests, bug fixes need regression tests
5. **Run checks** — `pytest` and `ruff check src/ tests/` must pass
6. **Commit clearly** — use conventional commit messages:
   - `feat: add concepts command`
   - `fix: handle empty tag list on push`
   - `docs: update installation instructions`
   - `test: add coverage for rate limiting`
7. **Open a PR** — fill out the template, reference the issue

### Good First Issues

New here? Look for issues labeled [`good first issue`](https://github.com/simplynadaf/devpub/labels/good%20first%20issue). These are scoped, well-defined tasks suitable for newcomers.

## Code Style

- **Formatter/Linter:** [ruff](https://docs.astral.sh/ruff/) (configured in pyproject.toml)
- **Line length:** 100 characters
- **Type hints:** Encouraged for public functions
- **Docstrings:** Required for public functions and classes
- **Imports:** Sorted by ruff (isort-compatible)

### Architecture

```
src/devpub/
  api/        # HTTP clients (Dev.to adapter, future: Hashnode, Medium)
  cli/        # Click command definitions and output formatting
  core/       # Business logic (articles, sync, validation, config)
  templates/  # Article templates
```

Key principles:
- `api/` talks to external services — all HTTP lives here
- `core/` has no knowledge of CLI formatting — returns data
- `cli/` handles user interaction, formatting, error display
- Tests mock at the HTTP level using `respx`

## Testing Guidelines

- Use `respx` to mock HTTP calls — never hit the real API in tests
- Use `tmp_path` fixture for filesystem tests
- Use `monkeypatch.setenv` for environment variables
- Test both success and error paths
- One assertion per concept (multiple asserts in a test are fine if related)

## Release Process

Releases are handled by maintainers:

1. Update version in `src/devpub/__init__.py`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.x.y`
4. Push tag: `git push --tags`
5. GitHub Action publishes to PyPI

## Questions?

Open a [discussion](https://github.com/simplynadaf/devpub/discussions) or comment on an existing issue. No question is too small.

---

Thank you for helping make devpub better.
