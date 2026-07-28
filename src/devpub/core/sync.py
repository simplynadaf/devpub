"""Sync logic -- push and pull articles between local and Dev.to."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from devpub.api.devto import APIError, DevtoClient
from devpub.core.article import (
    article_to_api_payload,
    load_article,
    save_article,
)
from devpub.core.config import ensure_api_key

# Only scan files inside these directories for --all push
ARTICLES_DIRS = ["articles", "posts", "content", "drafts"]


def push_articles(files: tuple = (), push_all: bool = False, dry_run: bool = False):
    """Push local articles to Dev.to."""
    console = Console()
    api_key = ensure_api_key()

    # Determine which files to push
    if files:
        article_paths = [Path(f) for f in files]
    elif push_all:
        article_paths = _find_pushable_articles()
    else:
        console.print("[yellow]Specify files with -f or use --all to push everything.[/]")
        console.print("  Example: [cyan]devpub push -f articles/my-post.md[/]")
        return

    if not article_paths:
        console.print("[yellow]No articles found to push.[/]")
        return

    with DevtoClient(api_key) as client:
        success_count = 0
        fail_count = 0

        for filepath in article_paths:
            if not filepath.exists():
                console.print(f"[red]File not found: {filepath}[/]")
                fail_count += 1
                continue

            article = load_article(filepath)

            if not article["title"]:
                console.print(f"[red]Missing title in: {filepath}[/]")
                fail_count += 1
                continue

            payload = article_to_api_payload(article)

            if dry_run:
                status = "UPDATE" if article.get("devto_id") else "CREATE"
                pub = "published" if article["published"] else "draft"
                console.print(f"  [dim]{status}[/] {filepath} -> {pub}")
                continue

            try:
                if article.get("devto_id"):
                    result = client.update_article(article["devto_id"], payload)
                    console.print(f"  [green]Updated:[/] {article['title']}")
                else:
                    result = client.create_article(payload)
                    console.print(f"  [green]Created:[/] {article['title']}")

                # Save the devto_id and url back to frontmatter
                metadata = article["metadata"]
                metadata["devto_id"] = result["id"]
                metadata["devto_url"] = result["url"]
                save_article(filepath, metadata, article["body"])

                console.print(f"     URL: [link]{result['url']}[/]")
                success_count += 1

            except APIError as e:
                console.print(f"  [red]Failed:[/] {article['title']} -- {e.message}")
                fail_count += 1
            except Exception as e:
                console.print(f"  [red]Failed:[/] {article['title']} -- {e}")
                fail_count += 1

    if dry_run:
        console.print(
            "\n[dim]Dry run -- nothing was published. Remove --dry-run to push.[/]"
        )
    elif success_count or fail_count:
        console.print(
            f"\n[dim]Done. {success_count} succeeded, {fail_count} failed.[/]"
        )


def pull_articles(pull_all: bool = False, folder: str = "articles"):
    """Pull articles from Dev.to to local files."""
    console = Console()
    api_key = ensure_api_key()

    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    with DevtoClient(api_key) as client:
        console.print("[dim]Fetching article list from Dev.to...[/]")

        # Step 1: Collect all article summaries (paginated)
        page = 1
        all_articles = []

        while True:
            try:
                if pull_all:
                    articles = client.get_my_articles(page=page, per_page=100)
                else:
                    articles = client.get_my_published(page=page, per_page=100)
            except APIError as e:
                console.print(f"[red]Error fetching articles: {e.message}[/]")
                return

            if not articles:
                break

            all_articles.extend(articles)
            page += 1

            if len(articles) < 100:
                break

        if not all_articles:
            console.print("[yellow]No articles found on Dev.to.[/]")
            return

        total = len(all_articles)
        console.print(f"Found [cyan]{total}[/] articles. Downloading...")

        # Step 2: Fetch each article's full body
        # The rate limiter in DevtoClient handles throttling automatically
        saved = 0
        for i, art in enumerate(all_articles, 1):
            try:
                full = client.get_article(art["id"])
            except APIError as e:
                console.print(
                    f"  [red]Failed:[/] {art.get('title', 'unknown')} -- {e.message}"
                )
                continue

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
            saved += 1

            # Progress indicator every 10 articles
            if total > 10 and i % 10 == 0:
                console.print(f"  [dim]...{i}/{total}[/]")

        console.print(
            f"\n[green]Done![/] Saved {saved}/{total} articles to [cyan]{folder}/[/]"
        )


def show_status():
    """Show sync status between local articles.

    This checks local files only -- no API key or network needed.
    """
    console = Console()

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


def _find_pushable_articles() -> list[Path]:
    """Find articles safe to push.

    Only scans known article directories and requires both 'title' and
    'published' keys in frontmatter to avoid accidentally pushing READMEs
    or other markdown files.
    """
    import frontmatter

    candidates = []

    # Check known article directories
    for dir_name in ARTICLES_DIRS:
        dir_path = Path(dir_name)
        if dir_path.is_dir():
            candidates.extend(dir_path.rglob("*.md"))

    # Also check if there's a configured articles_dir from .devpub/config.yml
    # (fall back to scanning current dir but with strict checks)
    if not candidates:
        candidates = list(Path(".").rglob("*.md"))

    results = []
    for filepath in candidates:
        try:
            post = frontmatter.load(filepath)
            # Require both title and published to be a devpub article
            if "title" in post.metadata and "published" in post.metadata:
                results.append(filepath)
        except Exception:
            continue

    return results


def _is_devpub_article(filepath: Path) -> bool:
    """Check if a markdown file is a devpub-managed article."""
    try:
        import frontmatter

        post = frontmatter.load(filepath)
        return "title" in post.metadata and "published" in post.metadata
    except Exception:
        return False
