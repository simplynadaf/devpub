"""Sync logic — push and pull articles between local and Dev.to."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from devpub.api.devto import DevtoClient
from devpub.core.article import (
    article_to_api_payload,
    load_article,
    save_article,
)
from devpub.core.config import ensure_api_key


def push_articles(files: tuple = (), push_all: bool = False, dry_run: bool = False):
    """Push local articles to Dev.to."""
    console = Console()
    api_key = ensure_api_key()

    # Determine which files to push
    if files:
        article_paths = [Path(f) for f in files]
    elif push_all:
        article_paths = list(Path(".").rglob("*.md"))
        # Filter to only files with devpub frontmatter
        article_paths = [p for p in article_paths if _is_devpub_article(p)]
    else:
        console.print("[yellow]Specify files with -f or use --all to push everything.[/]")
        console.print("  Example: [cyan]devpub push -f articles/my-post.md[/]")
        return

    if not article_paths:
        console.print("[yellow]No articles found to push.[/]")
        return

    with DevtoClient(api_key) as client:
        for filepath in article_paths:
            if not filepath.exists():
                console.print(f"[red]File not found: {filepath}[/]")
                continue

            article = load_article(filepath)

            if not article["title"]:
                console.print(f"[red]Missing title in: {filepath}[/]")
                continue

            payload = article_to_api_payload(article)

            if dry_run:
                status = "UPDATE" if article.get("devto_id") else "CREATE"
                pub = "published" if article["published"] else "draft"
                console.print(f"  [dim]{status}[/] {filepath} → {pub}")
                continue

            try:
                if article.get("devto_id"):
                    # Update existing
                    result = client.update_article(article["devto_id"], payload)
                    console.print(f"  [green]Updated:[/] {article['title']}")
                else:
                    # Create new
                    result = client.create_article(payload)
                    console.print(f"  [green]Created:[/] {article['title']}")

                # Save the devto_id and url back to frontmatter
                metadata = article["metadata"]
                metadata["devto_id"] = result["id"]
                metadata["devto_url"] = result["url"]
                save_article(filepath, metadata, article["body"])

                console.print(f"     URL: [link]{result['url']}[/]")

            except Exception as e:
                console.print(f"  [red]Failed:[/] {article['title']} — {e}")

    if dry_run:
        console.print("\n[dim]Dry run — nothing was published. Remove --dry-run to push.[/]")


def pull_articles(pull_all: bool = False, folder: str = "articles"):
    """Pull articles from Dev.to to local files."""
    console = Console()
    api_key = ensure_api_key()

    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    with DevtoClient(api_key) as client:
        console.print("[dim]Fetching articles from Dev.to...[/]")

        page = 1
        all_articles = []

        while True:
            if pull_all:
                articles = client.get_my_articles(page=page, per_page=100)
            else:
                articles = client.get_my_published(page=page, per_page=100)

            if not articles:
                break

            all_articles.extend(articles)
            page += 1

            if len(articles) < 100:
                break

        if not all_articles:
            console.print("[yellow]No articles found on Dev.to.[/]")
            return

        console.print(f"Found [cyan]{len(all_articles)}[/] articles. Saving...")

        for art in all_articles:
            # Fetch full article to get body_markdown
            full = client.get_article(art["id"])

            slug = art.get("slug", f"article-{art['id']}")
            filepath = folder_path / f"{slug}.md"

            metadata = {
                "title": full.get("title", ""),
                "published": True,
                "description": full.get("description", ""),
                "tags": ", ".join(full.get("tag_list", [])),
                "cover_image": full.get("cover_image", ""),
                "series": full.get("collection_id"),
                "canonical_url": full.get("canonical_url", ""),
                "devto_id": full["id"],
                "devto_url": full.get("url", ""),
            }

            body = full.get("body_markdown", "")
            save_article(filepath, metadata, body)
            console.print(f"  [green]Saved:[/] {filepath}")

        console.print(f"\n[green]Done![/] Saved {len(all_articles)} articles to [cyan]{folder}/[/]")


def show_status():
    """Show sync status between local and Dev.to."""
    console = Console()
    ensure_api_key()

    # Find local articles
    local_articles = []
    for md_file in Path(".").rglob("*.md"):
        if _is_devpub_article(md_file):
            article = load_article(md_file)
            local_articles.append(article)

    if not local_articles:
        console.print("[yellow]No devpub articles found in this directory.[/]")
        console.print("Run [cyan]devpub pull[/] to download your articles, or")
        console.print("    [cyan]devpub new \"Title\"[/] to create one.")
        return

    table = Table(title="Article Status")
    table.add_column("File", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Dev.to ID", justify="center", style="dim")

    for art in sorted(local_articles, key=lambda a: a["filepath"]):
        if art.get("devto_id"):
            if art["published"]:
                status = "[green]published[/]"
            else:
                status = "[yellow]draft[/]"
        else:
            status = "[blue]new (not pushed)[/]"

        table.add_row(
            art["filepath"],
            art["title"][:40],
            status,
            str(art.get("devto_id", "")),
        )

    console.print(table)
    console.print(f"\nTotal: {len(local_articles)} articles")


def _is_devpub_article(filepath: Path) -> bool:
    """Check if a markdown file is a devpub-managed article (has title in frontmatter)."""
    try:
        import frontmatter

        post = frontmatter.load(filepath)
        return "title" in post.metadata
    except Exception:
        return False
