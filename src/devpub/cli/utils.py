"""Utility CLI commands for devpub."""

from rich.console import Console
from rich.panel import Panel

from devpub.api.devto import APIError, DevtoClient
from devpub.core.config import ensure_api_key


def show_whoami():
    """Show the authenticated user's profile."""
    console = Console()
    api_key = ensure_api_key()

    try:
        with DevtoClient(api_key) as client:
            user = client.get_me()
    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")
        return

    console.print(
        Panel(
            f"[bold]{user.get('name', 'Unknown')}[/] (@{user.get('username', '')})\n\n"
            f"  Articles:  {user.get('articles_count', '?')}\n"
            f"  Followers: {user.get('followers_count', '?')}\n"
            f"  Website:   {user.get('website_url', '--')}\n"
            f"  GitHub:    {user.get('github_username', '--')}\n"
            f"  Joined:    {_safe_date(user.get('joined_at'))}",
            title="Your Dev.to Profile",
            border_style="blue",
        )
    )


def run_doctor():
    """Check devpub configuration and API connectivity."""
    console = Console()

    checks = []

    # Check 1: API key configured
    from devpub.core.config import get_config

    config = get_config()
    api_key = config.get("api_key", "")

    if api_key:
        masked = f"...{api_key[-4:]}"
        checks.append(("API key configured", True, masked))
    else:
        checks.append(("API key configured", False, "Not found"))

    # Check 2: API reachable
    if api_key:
        with DevtoClient(api_key) as client:
            is_healthy = client.health_check()
            checks.append(("Dev.to API reachable", is_healthy, ""))

            # Check 3: Auth works
            if is_healthy:
                try:
                    user = client.get_me()
                    checks.append(
                        ("Authentication valid", True, f"@{user.get('username', '?')}")
                    )
                except APIError as e:
                    checks.append(("Authentication valid", False, e.message[:50]))
                except Exception as e:
                    checks.append(("Authentication valid", False, str(e)[:50]))
    else:
        checks.append(("Dev.to API reachable", None, "Skipped (no key)"))
        checks.append(("Authentication valid", None, "Skipped (no key)"))

    # Check 4: Project initialized
    from devpub.core.config import find_project_root

    root = find_project_root()
    checks.append(("Project initialized", root is not None, str(root or "Not found")))

    # Display results
    console.print("\n[bold]devpub doctor[/]\n")

    all_good = True
    for name, passed, detail in checks:
        if passed is True:
            icon = "[green]OK[/]"
        elif passed is False:
            icon = "[red]FAIL[/]"
            all_good = False
        else:
            icon = "[dim]SKIP[/]"

        detail_str = f" [dim]({detail})[/]" if detail else ""
        console.print(f"  {icon} {name}{detail_str}")

    if all_good:
        console.print("\n[green]Everything looks good! Ready to use devpub.[/]")
    else:
        console.print(
            "\n[yellow]Some checks failed. Fix the issues above to get started.[/]"
        )


def _safe_date(value: str | None) -> str:
    """Extract date portion safely."""
    if not value:
        return "--"
    return value[:10]
