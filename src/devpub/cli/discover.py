"""Content discovery CLI commands for devpub."""

from rich.console import Console
from rich.table import Table

from devpub.api.devto import APIError, DevtoClient
from devpub.core.config import ensure_api_key


def show_trends(days: int = 7):
    """Show trending topics on Dev.to."""
    console = Console()

    try:
        # Trends endpoint is public -- no auth needed
        with DevtoClient() as client:
            trends = client.get_trends(per_page=15)
    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")
        return

    if not trends:
        console.print("[yellow]No trends data available.[/]")
        return

    console.print("\n[bold]Trending on Dev.to[/]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Topic", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Articles", justify="right")
    table.add_column("Description", style="dim", max_width=50)

    for i, trend in enumerate(trends, 1):
        table.add_row(
            str(i),
            trend.get("name", "Unknown"),
            str(trend.get("score", 0)),
            str(trend.get("articles_count", 0)),
            (trend.get("description", "") or "")[:50],
        )

    console.print(table)
    console.print(
        "\n[dim]Tip: Write about trending topics with few articles"
        " -- your post will stand out.[/]"
    )


def search_articles(query: str, semantic: bool = False, limit: int = 10):
    """Search for articles on Dev.to."""
    console = Console()
    api_key = ensure_api_key()

    try:
        with DevtoClient(api_key) as client:
            if semantic:
                console.print(f"[dim]Semantic search for: \"{query}\"[/]\n")
                results = client.semantic_search(query=query, per_page=limit)
            else:
                console.print(f"[dim]Searching for: \"{query}\"[/]\n")
                results = client.search_articles(query=query, per_page=limit)
    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")
        return

    if not results:
        console.print("[yellow]No results found.[/]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="cyan", max_width=60)
    table.add_column("Reactions", justify="right", style="green")

    if semantic:
        table.add_column("Similarity", justify="right", style="yellow")

    for i, art in enumerate(results, 1):
        row = [
            str(i),
            art.get("title", "Untitled")[:60],
            str(art.get(
                "public_reactions_count",
                art.get("positive_reactions_count", 0),
            )),
        ]
        if semantic:
            sim = art.get("similarity", 0)
            row.append(f"{sim:.1%}" if sim else "--")

        table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]Showing {len(results)} results.[/]")
