"""Project initialization for devpub."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel


def init_project(path: str = "."):
    """Initialize a devpub project directory."""
    console = Console()
    project_path = Path(path).resolve()
    devpub_dir = project_path / ".devpub"
    articles_dir = project_path / "articles"

    if devpub_dir.exists():
        console.print(f"[yellow]Already initialized:[/] {project_path}")
        return

    # Create directories
    devpub_dir.mkdir(parents=True, exist_ok=True)
    articles_dir.mkdir(parents=True, exist_ok=True)

    # Create .env template
    env_file = devpub_dir / ".env"
    env_file.write_text(
        "# Dev.to API Key — get yours at https://dev.to/settings/extensions\n"
        "DEVPUB_API_KEY=\n"
    )

    # Create .gitignore for devpub dir
    gitignore = devpub_dir / ".gitignore"
    gitignore.write_text(".env\n")

    # Create config
    config_file = devpub_dir / "config.yml"
    config_file.write_text(
        "# devpub configuration\n"
        "# See: https://github.com/simplynadaf/devpub#configuration\n"
        "\n"
        "# Default folder for articles\n"
        "articles_dir: articles\n"
        "\n"
        "# Default publish state for new articles\n"
        "default_published: false\n"
        "\n"
        "# Image hosting (github = auto-upload to repo)\n"
        "image_host: github\n"
    )

    console.print(
        Panel(
            f"[green]Initialized devpub project at:[/] {project_path}\n\n"
            "Created:\n"
            f"  [cyan]{devpub_dir.relative_to(project_path)}/[/] — config directory\n"
            f"  [cyan]{articles_dir.relative_to(project_path)}/[/] — your articles live here\n\n"
            "Next steps:\n"
            "  1. Add your API key: [cyan]edit .devpub/.env[/]\n"
            "     Get it at: https://dev.to/settings/extensions\n\n"
            "  2. Pull your existing articles:\n"
            "     [cyan]devpub pull[/]\n\n"
            "  3. Or create a new one:\n"
            "     [cyan]devpub new \"My First Article\"[/]",
            title="devpub initialized",
            border_style="green",
        )
    )
