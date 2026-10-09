"""Comment-reading CLI commands for devpub.

Reads the threaded comments on an article through the Forem V1 ``/comments``
endpoint, which is API-key (and largely public) accessible and read-only.

Posting a reply is deliberately not here: Forem V1 exposes no write endpoint
for comments, so it would require the session-cookie bridge used by
``devpub upload``. That is tracked separately and pending a verification spike.
"""

import re
from html import unescape

from rich.console import Console

from devpub.api.devto import APIError, DevtoClient
from devpub.core.config import ensure_api_key

# Indentation applied per nesting level when printing a reply thread.
_INDENT = "    "
# Cap nesting so a deep thread cannot walk indentation off the screen.
_MAX_DEPTH = 6

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]*\n[ \t]*")
_BLANK_LINES_RE = re.compile(r"\n{2,}")


def _html_to_text(html: str) -> str:
    """Reduce a comment's ``body_html`` to readable plain text.

    The API returns rendered HTML; there is no plain-text field. This is a
    deliberately small reducer (strip tags, unescape entities, collapse blank
    lines) rather than a full HTML parser, which would be a new dependency for
    little gain in a terminal.
    """
    if not html:
        return ""
    # Turn block boundaries into newlines before stripping tags so paragraphs
    # do not run together.
    text = re.sub(r"</(p|div|br|li)>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = _TAG_RE.sub("", text)
    text = unescape(text)
    text = _WS_RE.sub("\n", text)
    text = _BLANK_LINES_RE.sub("\n", text)
    return text.strip()


def _render(comment: dict, console: Console, depth: int = 0):
    """Print one comment and recurse into its children."""
    indent = _INDENT * min(depth, _MAX_DEPTH)
    user = comment.get("user") or {}
    username = user.get("username") or user.get("name") or "unknown"
    created = (comment.get("created_at") or "")[:10]
    id_code = comment.get("id_code", "")

    header = f"{indent}[bold cyan]@{username}[/]"
    if created:
        header += f" [dim]· {created}[/]"
    if id_code:
        header += f" [dim]· {id_code}[/]"
    console.print(header)

    body = _html_to_text(comment.get("body_html", ""))
    if body:
        for line in body.splitlines():
            console.print(f"{indent}  {line}")
    else:
        console.print(f"{indent}  [dim](no text)[/]")
    console.print()

    for child in comment.get("children") or []:
        _render(child, console, depth + 1)


def _count(comments: list) -> int:
    """Count every comment in the tree, replies included."""
    total = 0
    for c in comments:
        total += 1 + _count(c.get("children") or [])
    return total


def show_comments(article_id: int, page: int = 1, limit: int = 30):
    """Show the threaded comments on a Dev.to article.

    Args:
        article_id: Numeric ID of the article to read comments from.
        page: Page of top-level comments (replies are always inline).
        limit: Top-level comments per page.
    """
    console = Console()
    api_key = ensure_api_key()

    try:
        with DevtoClient(api_key) as client:
            comments = client.get_comments(article_id, page=page, per_page=limit)
    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")
        return

    if not comments:
        console.print(
            f"[yellow]No comments found on article {article_id}.[/]"
        )
        return

    total = _count(comments)
    console.print(
        f"\n[bold]Comments on article {article_id}[/] "
        f"[dim]({len(comments)} threads, {total} total)[/]\n"
    )

    for comment in comments:
        _render(comment, console)
