# Contributing to devpub

Thanks for your interest in contributing to devpub!

## Development Setup

```bash
# Clone the repo
git clone https://github.com/simplynadaf/devpub.git
cd devpub

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/ tests/
```

## Making Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-change`
3. Make your changes
4. Add tests for new functionality
5. Run `pytest` and `ruff check` to verify
6. Commit with a clear message
7. Open a pull request

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Line length limit: 100 characters
- Type hints are encouraged
- Write docstrings for public functions

## Testing

- All new features need tests
- Use `respx` to mock HTTP calls to the Dev.to API
- Run `pytest -v` for verbose output

## Reporting Issues

- Check existing issues first
- Include steps to reproduce
- Include your Python version and OS

## Pull Request Guidelines

- Keep PRs focused on a single change
- Update documentation if needed
- Add a line to CHANGELOG.md under "Unreleased"
