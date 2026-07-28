"""Analytics CLI commands for devpub."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devpub.api.devto import DevtoClient
from devpub.core.config import ensure_api_key


def show_stats(
    period: str = "30d",
    graph: bool = False,
    referrers: bool = False,
    followers: bool = False,
    heatmap: bool = False,
):
    """Show analytics for the authenticated user."""
    console = Console()
    api_key = ensure_api_key()

    with DevtoClient(api_key) as client:
        # Default: show totals
        totals = client.get_analytics_totals()
        console.print(
            Panel(
                f"[bold]Your Dev.to Stats[/]\n\n"
                f"  Views:     [cyan]{_format_num(totals.get('page_views', 0))}[/]\n"
                f"  Reactions: [cyan]{_format_num(totals.get('reactions', 0))}[/]\n"
                f"  Comments:  [cyan]{_format_num(totals.get('comments', 0))}[/]\n"
                f"  Followers: [cyan]{_format_num(totals.get('followers', 0))}[/]",
                title="devpub stats",
                border_style="blue",
            )
        )

        if referrers:
            _show_referrers(client, console)

        if followers:
            _show_followers(client, console)


def show_dashboard():
    """Show full analytics dashboard."""
    console = Console()
    api_key = ensure_api_key()

    with DevtoClient(api_key) as client:
        dashboard = client.get_analytics_dashboard()
        console.print(
            Panel(
                "[bold]Full Dashboard[/]\n\n"
                f"{dashboard}",
                title="devpub dashboard",
                border_style="blue",
            )
        )


def _show_referrers(client: DevtoClient, console: Console):
    """Show top traffic referrers."""
    data = client.get_analytics_referrers()
    if not data:
        console.print("[dim]No referrer data available.[/]")
        return

    table = Table(title="Top Referrers")
    table.add_column("Source", style="cyan")
    table.add_column("Views", justify="right")

    for ref in data[:10] if isinstance(data, list) else []:
        table.add_row(ref.get("domain", "unknown"), str(ref.get("count", 0)))

    console.print(table)


def _show_followers(client: DevtoClient, console: Console):
    """Show follower growth."""
    data = client.get_analytics_followers()
    if data:
        console.print(f"\n[bold]Follower Engagement[/]\n{data}")


def _format_num(n: int) -> str:
    """Format large numbers with commas."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)
