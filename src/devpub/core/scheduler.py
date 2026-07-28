"""Scheduling logic for devpub.

Allows articles to have a `schedule` field in frontmatter (ISO datetime).
When the scheduled time arrives, the article is published automatically
via `devpub push --scheduled` or a GitHub Action cron trigger.
"""

from datetime import datetime, timezone
from pathlib import Path


def get_scheduled_articles(folder: str = "articles") -> list[dict]:
    """Find articles with a schedule field whose time has passed."""
    from devpub.core.article import load_article
    from devpub.core.sync import _is_devpub_article

    ready = []
    now = datetime.now(timezone.utc)

    for md_file in Path(folder).rglob("*.md"):
        if not _is_devpub_article(md_file):
            continue

        article = load_article(md_file)
        schedule_str = article["metadata"].get("schedule")

        if not schedule_str:
            continue

        try:
            scheduled_at = datetime.fromisoformat(schedule_str)
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            if scheduled_at <= now and not article["published"]:
                ready.append(article)
        except (ValueError, TypeError):
            continue

    return ready


def publish_scheduled(folder: str = "articles", dry_run: bool = False):
    """Publish all articles whose schedule time has passed."""
    from rich.console import Console

    from devpub.api.devto import APIError, DevtoClient
    from devpub.core.article import article_to_api_payload, save_article
    from devpub.core.config import ensure_api_key

    console = Console()
    api_key = ensure_api_key()
    articles = get_scheduled_articles(folder)

    if not articles:
        console.print("[dim]No scheduled articles ready to publish.[/]")
        return

    console.print(f"Found {len(articles)} article(s) ready to publish.\n")

    with DevtoClient(api_key) as client:
        for article in articles:
            filepath = Path(article["filepath"])

            if dry_run:
                console.print(f"  [dim]WOULD PUBLISH[/] {filepath}")
                continue

            try:
                # Set published to true
                payload = article_to_api_payload(article)
                payload["published"] = True

                if article.get("devto_id"):
                    result = client.update_article(article["devto_id"], payload)
                else:
                    result = client.create_article(payload)

                # Update local file
                metadata = article["metadata"]
                metadata["published"] = True
                metadata["devto_id"] = result["id"]
                metadata["devto_url"] = result["url"]
                save_article(filepath, metadata, article["body"])

                console.print(f"  [green]Published:[/] {article['title']}")
                console.print(f"     URL: [link]{result['url']}[/]")

            except APIError as e:
                console.print(f"  [red]Failed:[/] {article['title']} -- {e.message}")

    if dry_run:
        console.print("\n[dim]Dry run. Use without --dry-run to publish.[/]")
