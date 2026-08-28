"""Image upload commands for devpub."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from devpub.api.devto import APIError
from devpub.api.uploads import ImageUploader
from devpub.core.config import ensure_session_credentials


def upload_images(files: tuple, markdown: bool = False, as_json: bool = False):
    """Upload image files to Dev.to and print their public URLs.

    Args:
        files: Paths to upload, in the order given.
        markdown: Print ready-to-paste Markdown instead of a table.
        as_json: Print a machine-readable JSON result to stdout (for scripting).

    Exits non-zero if any file failed to upload.
    """
    console = Console()
    # In --json mode, keep stdout pure JSON; send all human output to stderr.
    log = Console(stderr=True) if as_json else console

    if not files:
        log.print("[yellow]No files given.[/]")
        log.print("  Example: [cyan]devpub upload cover.png diagram.png[/]")
        return

    session_cookie, csrf_token = ensure_session_credentials()

    uploaded: list[tuple[Path, str]] = []
    failed: list[tuple[Path, str]] = []

    with ImageUploader(session_cookie, csrf_token) as uploader:
        for raw_path in files:
            path = Path(raw_path).expanduser()
            try:
                url = uploader.upload(path)
            except APIError as e:
                failed.append((path, e.message))
                log.print(f"  [red]Failed:[/] {path.name} -- {e.message}")
                continue
            uploaded.append((path, url))
            log.print(f"  [green]Uploaded:[/] {path.name}")

    if as_json:
        print(json.dumps(_json_result(uploaded, failed), indent=2))
    else:
        _print_human(console, uploaded, failed, markdown=markdown)

    if failed:
        sys.exit(1)


def _json_result(uploaded, failed) -> dict:
    return {
        "uploaded": [{"file": p.name, "path": str(p), "url": url} for p, url in uploaded],
        "failed": [{"file": p.name, "path": str(p), "error": err} for p, err in failed],
    }


def _print_human(console: Console, uploaded, failed, markdown: bool):
    if uploaded:
        if markdown:
            console.print()
            for path, url in uploaded:
                # Print via the file object so Rich cannot reinterpret the markup.
                print(f"![{path.stem}]({url})")
        else:
            table = Table(title="Uploaded Images", show_lines=False)
            table.add_column("File", style="cyan", no_wrap=True)
            table.add_column("URL")
            for path, url in uploaded:
                table.add_row(path.name, url)
            console.print()
            console.print(table)

    console.print(f"\n[dim]Done. {len(uploaded)} uploaded, {len(failed)} failed.[/]")
