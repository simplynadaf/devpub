"""Configuration management for devpub."""

import os
from pathlib import Path

from dotenv import load_dotenv

DEVPUB_DIR = ".devpub"
CONFIG_FILE = "config.yml"
ENV_FILE = ".env"


def find_project_root() -> Path | None:
    """Find the nearest parent directory containing a .devpub folder."""
    current = Path.cwd()
    while current != current.parent:
        if (current / DEVPUB_DIR).is_dir():
            return current
        current = current.parent
    if (current / DEVPUB_DIR).is_dir():
        return current
    return None


def get_config() -> dict:
    """Load configuration from environment and config files.

    Priority order:
    1. Environment variables (DEVPUB_API_KEY, DEVTO_API_KEY)
    2. Project .env file (.devpub/.env)
    3. Global .env file (~/.devpub/.env)
    """
    # Load global .env
    global_env = Path.home() / DEVPUB_DIR / ENV_FILE
    if global_env.exists():
        load_dotenv(global_env)

    # Load project .env (overrides global)
    project_root = find_project_root()
    if project_root:
        project_env = project_root / DEVPUB_DIR / ENV_FILE
        if project_env.exists():
            load_dotenv(project_env, override=True)

    # Also check for .env in current directory
    local_env = Path.cwd() / ".env"
    if local_env.exists():
        load_dotenv(local_env, override=True)

    api_key = (
        os.getenv("DEVPUB_API_KEY")
        or os.getenv("DEVTO_API_KEY")
        or os.getenv("FOREM_API_KEY")
        or ""
    )

    return {
        "api_key": api_key,
        "api_url": os.getenv("DEVPUB_API_URL", "https://dev.to/api"),
        "project_root": str(project_root) if project_root else None,
    }


def ensure_api_key() -> str:
    """Get API key or raise an error with helpful message."""
    config = get_config()
    api_key = config.get("api_key", "")

    if not api_key:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        console.print(
            Panel(
                "[bold red]No API key found![/]\n\n"
                "Set your Dev.to API key using one of:\n\n"
                "  [cyan]export DEVPUB_API_KEY=your_key_here[/]\n"
                "  [cyan]export DEVTO_API_KEY=your_key_here[/]\n\n"
                "Or create a [cyan].env[/] file with:\n"
                "  [dim]DEVPUB_API_KEY=your_key_here[/]\n\n"
                "Get your API key at: [link]https://dev.to/settings/extensions[/]",
                title="Authentication Required",
                border_style="red",
            )
        )
        raise SystemExit(1)

    return api_key
