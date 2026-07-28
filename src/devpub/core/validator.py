"""Article validation for devpub."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from devpub.core.article import load_article


def validate_articles(files: tuple = ()):
    """Validate articles for common issues before publishing."""
    console = Console()

    if files:
        article_paths = [Path(f) for f in files]
    else:
        article_paths = [p for p in Path(".").rglob("*.md") if _has_frontmatter(p)]

    if not article_paths:
        console.print("[yellow]No articles found to validate.[/]")
        return

    total_issues = 0

    for filepath in article_paths:
        if not filepath.exists():
            console.print(f"[red]File not found: {filepath}[/]")
            continue

        issues = _validate_single(filepath)
        total_issues += len(issues)

        if issues:
            console.print(f"\n[bold]{filepath}[/]")
            for issue in issues:
                icon = "x" if issue["level"] == "error" else "!"
                color = "red" if issue["level"] == "error" else "yellow"
                console.print(f"  [{color}][{icon}] {issue['message']}[/]")
        else:
            console.print(f"  [green]OK[/] {filepath} — all good!")

    if total_issues == 0:
        console.print(
            Panel(
                "[green]All articles passed validation! Ready to push.[/]",
                border_style="green",
            )
        )
    else:
        msg = f"Found {total_issues} issue(s) across {len(article_paths)} file(s)."
        console.print(f"\n[yellow]{msg}[/]")


def _validate_single(filepath: Path) -> list[dict]:
    """Validate a single article file. Returns list of issues."""
    issues = []
    article = load_article(filepath)

    # Title checks
    if not article["title"]:
        issues.append({"level": "error", "message": "Missing title"})
    elif len(article["title"]) > 100:
        title_len = len(article["title"])
        issues.append({
            "level": "warning",
            "message": f"Title too long ({title_len} chars, aim for <70)",
        })
    elif len(article["title"]) < 10:
        issues.append({
            "level": "warning",
            "message": "Title very short -- consider making it more descriptive",
        })

    # Description
    if not article["description"]:
        issues.append({
            "level": "warning",
            "message": "Missing description (important for SEO)",
        })
    elif len(article["description"]) > 160:
        desc_len = len(article["description"])
        issues.append({
            "level": "warning",
            "message": f"Description too long ({desc_len} chars, aim for <160)",
        })

    # Tags
    if not article["tags"]:
        issues.append({"level": "warning", "message": "No tags specified"})
    elif len(article["tags"]) > 4:
        tag_count = len(article["tags"])
        issues.append({
            "level": "error",
            "message": f"Too many tags ({tag_count}). Dev.to allows max 4.",
        })

    # Body content
    body = article["body"]
    if not body or len(body.strip()) < 50:
        issues.append({
            "level": "error",
            "message": "Article body is empty or too short",
        })
    else:
        word_count = len(body.split())
        if word_count < 100:
            issues.append({
                "level": "warning",
                "message": f"Very short article ({word_count} words)",
            })

        # Check for placeholder text
        placeholders = ["Write your article here", "<!-- ", "TODO", "FIXME"]
        for ph in placeholders:
            if ph in body and ph != "<!-- ":
                issues.append({
                    "level": "warning",
                    "message": f"Contains placeholder text: '{ph}'",
                })

    # Cover image
    if not article.get("cover_image"):
        issues.append({
            "level": "warning",
            "message": "No cover image (articles with images get more engagement)",
        })

    # Canonical URL check for cross-posts
    if article.get("canonical_url"):
        url = article["canonical_url"]
        if not url.startswith("http"):
            issues.append({"level": "error", "message": f"Invalid canonical URL: {url}"})

    return issues


def _has_frontmatter(filepath: Path) -> bool:
    """Quick check if a file has YAML frontmatter."""
    try:
        content = filepath.read_text(encoding="utf-8")
        return content.startswith("---")
    except Exception:
        return False
