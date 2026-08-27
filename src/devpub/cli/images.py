"""Image upload commands for devpub."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from devpub.api.devto import APIError
from devpub.api.uploads import ImageUploader
from devpub.core.config import ensure_session_credentials


def upload_images(files: tuple, markdown: bool = False):
    """Upload image files to Dev.to and print their public URLs.

    Args:
        files: Paths to upload, in the order given.
        markdown: Print ready-to-paste Markdown instead of a table.
    """
    console = Console()

    if not files:
        console.print("[yellow]No files given.[/]")
        console.print("  Example: [cyan]devpub upload cover.png diagram.png[/]")
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
                console.print(f"  [red]Failed:[/] {path.name} -- {e.message}")
                continue
            uploaded.append((path, url))
            console.print(f"  [green]Uploaded:[/] {path.name}")

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

    console.print(
        f"\n[dim]Done. {len(uploaded)} uploaded, {len(failed)} failed.[/]"
    )
