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

    Image uploads additionally read DEVPUB_SESSION_COOKIE and DEVPUB_CSRF_TOKEN,
    since the upload endpoint is session-authenticated rather than key-authenticated.
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

    session_cookie = (
        os.getenv("DEVPUB_SESSION_COOKIE") or os.getenv("DEVTO_SESSION_COOKIE") or ""
    )
    csrf_token = os.getenv("DEVPUB_CSRF_TOKEN") or os.getenv("DEVTO_CSRF_TOKEN") or ""

    return {
        "api_key": api_key,
        "api_url": os.getenv("DEVPUB_API_URL", "https://dev.to/api"),
        "site_url": os.getenv("DEVPUB_SITE_URL", "https://dev.to"),
        "session_cookie": session_cookie,
        "csrf_token": csrf_token,
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


def ensure_session_credentials() -> tuple[str, str]:
    """Get the session cookie and CSRF token, or explain how to obtain them.

    Image uploads cannot use the API key: Forem's API V1 has no image endpoint,
    so devpub posts to the same session-authenticated endpoint the editor uses.
    """
    config = get_config()
    session_cookie = config.get("session_cookie", "")
    csrf_token = config.get("csrf_token", "")

    if session_cookie and csrf_token:
        return session_cookie, csrf_token

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            "[bold red]No Dev.to session credentials found![/]\n\n"
            "Uploading images needs a browser session, not an API key -- the\n"
            "Forem API has no image endpoint.\n\n"
            "[bold]To get them:[/]\n"
            "  1. Open [link]https://dev.to/new[/] while logged in\n"
            "  2. DevTools -> Application -> Cookies -> copy [cyan]_Devto_Forem_Session[/]\n"
            "  3. DevTools -> Elements -> copy the [cyan]content[/] of\n"
            "     [dim]<meta name=\"csrf-token\">[/]\n\n"
            "Then add them to [cyan].devpub/.env[/]:\n"
            "  [dim]DEVPUB_SESSION_COOKIE=...[/]\n"
            "  [dim]DEVPUB_CSRF_TOKEN=...[/]\n\n"
            "[yellow]These are login credentials -- keep them out of version control.[/]\n"
            "They expire; re-copy them when uploads start failing with 401/403.",
            title="Session Required",
            border_style="red",
        )
    )
    raise SystemExit(1)
