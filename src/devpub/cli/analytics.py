"""Analytics CLI commands for devpub."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devpub.api.devto import APIError, DevtoClient
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

    try:
        with DevtoClient(api_key) as client:
            # Default: show totals
            totals = client.get_analytics_totals()

            total_views = _extract_total(totals.get("page_views"))
            total_reactions = _extract_total(totals.get("reactions"))
            total_comments = _extract_total(totals.get("comments"))
            total_followers = _extract_total(totals.get("follows"))

            console.print(
                Panel(
                    f"[bold]Your Dev.to Stats[/]\n\n"
                    f"  Views:     [cyan]{_format_num(total_views)}[/]\n"
                    f"  Reactions: [cyan]{_format_num(total_reactions)}[/]\n"
                    f"  Comments:  [cyan]{_format_num(total_comments)}[/]\n"
                    f"  Followers: [cyan]{_format_num(total_followers)}[/]",
                    title="devpub stats",
                    border_style="blue",
                )
            )

            if referrers:
                _show_referrers(client, console)

            if followers:
                _show_followers(client, console)

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")


def show_dashboard():
    """Show full analytics dashboard with formatted output."""
    console = Console()
    api_key = ensure_api_key()

    try:
        with DevtoClient(api_key) as client:
            # Totals
            totals = client.get_analytics_totals()

            views = _extract_total(totals.get("page_views"))
            reactions = _extract_total(totals.get("reactions"))
            comments = _extract_total(totals.get("comments"))
            followers = _extract_total(totals.get("follows"))

            console.print("\n[bold]Analytics Dashboard[/]\n")

            # Summary panel
            console.print(
                Panel(
                    f"  Views:     [cyan]{_format_num(views)}[/]\n"
                    f"  Reactions: [cyan]{_format_num(reactions)}[/]\n"
                    f"  Comments:  [cyan]{_format_num(comments)}[/]\n"
                    f"  Followers: [cyan]{_format_num(followers)}[/]",
                    title="Lifetime Totals",
                    border_style="blue",
                )
            )

            # Top articles
            articles = client.get_my_published(per_page=10)
            if articles:
                table = Table(title="Top Articles (by reactions)")
                table.add_column("#", style="dim", width=3)
                table.add_column("Title", style="cyan", max_width=50)
                table.add_column("Views", justify="right")
                table.add_column("Reactions", justify="right", style="green")
                table.add_column("Comments", justify="right")

                # Sort by reactions descending
                sorted_articles = sorted(
                    articles,
                    key=lambda a: a.get("positive_reactions_count", 0),
                    reverse=True,
                )

                for i, art in enumerate(sorted_articles[:10], 1):
                    table.add_row(
                        str(i),
                        art.get("title", "Untitled")[:50],
                        str(art.get("page_views_count", 0)),
                        str(art.get("positive_reactions_count", 0)),
                        str(art.get("comments_count", 0)),
                    )

                console.print(table)

            # Referrers
            _show_referrers(client, console)

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")


def _show_referrers(client: DevtoClient, console: Console):
    """Show top traffic referrers."""
    try:
        data = client.get_analytics_referrers()
    except APIError:
        return

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
    """Show follower engagement."""
    try:
        data = client.get_analytics_followers()
    except APIError:
        return

    if data:
        console.print(f"\n[bold]Follower Engagement[/]\n{data}")


def _format_num(n: int) -> str:
    """Format large numbers for display."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _extract_total(value) -> int:
    """Extract total from an analytics field.

    The Dev.to API returns nested dicts like {"total": 5000, ...}
    for analytics fields, not flat integers.
    """
    if isinstance(value, dict):
        return value.get("total", 0)
    if isinstance(value, (int, float)):
        return int(value)
    return 0
