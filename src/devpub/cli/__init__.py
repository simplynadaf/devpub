"""devpub CLI entry point."""

import click

from devpub import __version__


@click.group()
@click.version_option(version=__version__, prog_name="devpub")
@click.pass_context
def cli(ctx):
    """devpub -- Write in your editor. Publish to Dev.to. Track what works.

    \b
    New to writing?     devpub trends
    Already writing?    devpub pull
    Want to grow?       devpub stats
    Ready to publish?   devpub push
    Got images?         devpub upload
    """
    ctx.ensure_object(dict)


@cli.command()
@click.option("--path", default=".", help="Directory to initialize as a devpub project.")
def init(path):
    """Initialize a devpub project in the current directory."""
    from devpub.core.project import init_project

    init_project(path)


@cli.command()
@click.argument("title")
@click.option("--template", "-t", default="default", help="Article template to use.")
@click.option("--folder", "-f", default="articles", help="Folder to create article in.")
def new(title, template, folder):
    """Create a new article from a template."""
    from devpub.core.article import create_article

    create_article(title, template=template, folder=folder)


@cli.command()
@click.option("--file", "-f", multiple=True, help="Specific file(s) to push.")
@click.option("--all", "push_all", is_flag=True, help="Push all modified articles.")
@click.option("--dry-run", is_flag=True, help="Show what would be published without publishing.")
def push(file, push_all, dry_run):
    """Publish or update articles to Dev.to."""
    from devpub.core.sync import push_articles

    push_articles(files=file, push_all=push_all, dry_run=dry_run)


@cli.command()
@click.option("--all", "pull_all", is_flag=True, help="Pull all articles including drafts.")
@click.option("--folder", "-f", default="articles", help="Folder to save articles to.")
def pull(pull_all, folder):
    """Download your articles from Dev.to."""
    from devpub.core.sync import pull_articles

    pull_articles(pull_all=pull_all, folder=folder)


@cli.command()
@click.argument("files", nargs=-1, type=click.Path())
@click.option(
    "--markdown", "-m", is_flag=True, help="Print Markdown image tags instead of a table."
)
def upload(files, markdown):
    """Upload images to Dev.to and get their URLs.

    \b
    The Forem API has no image endpoint, so this uses the same
    session-authenticated endpoint as the web editor. It needs
    DEVPUB_SESSION_COOKIE and DEVPUB_CSRF_TOKEN rather than your API key --
    run it once without them for instructions on where to find them.
    """
    from devpub.cli.images import upload_images

    upload_images(files=files, markdown=markdown)


@cli.command()
def status():
    """Show sync state between local articles and Dev.to."""
    from devpub.core.sync import show_status

    show_status()


@cli.command()
@click.option("--file", "-f", multiple=True, help="Specific file(s) to validate.")
def validate(file):
    """Check articles for issues before publishing."""
    from devpub.core.validator import validate_articles

    validate_articles(files=file)


@cli.command()
@click.option("--period", "-p", default="30d", help="Time period (e.g., 7d, 30d, 90d).")
@click.option("--graph", is_flag=True, help="Show historical time-series graph.")
@click.option("--referrers", is_flag=True, help="Show traffic sources.")
@click.option("--followers", is_flag=True, help="Show follower growth.")
@click.option("--heatmap", is_flag=True, help="Show activity by day/hour.")
def stats(period, graph, referrers, followers, heatmap):
    """View your Dev.to analytics."""
    from devpub.cli.analytics import show_stats

    show_stats(
        period=period,
        graph=graph,
        referrers=referrers,
        followers=followers,
        heatmap=heatmap,
    )


@cli.command()
def dashboard():
    """Show complete analytics dashboard."""
    from devpub.cli.analytics import show_dashboard

    show_dashboard()


@cli.command()
@click.option("--days", "-d", default=7, help="Number of days to look back.")
def trends(days):
    """Discover trending topics on Dev.to."""
    from devpub.cli.discover import show_trends

    show_trends(days=days)


@cli.command()
@click.argument("query")
@click.option("--semantic", is_flag=True, help="Use AI-powered semantic search.")
@click.option("--limit", "-l", default=10, help="Number of results.")
def search(query, semantic, limit):
    """Search Dev.to articles."""
    from devpub.cli.discover import search_articles

    search_articles(query=query, semantic=semantic, limit=limit)


@cli.command()
def whoami():
    """Show your Dev.to profile info."""
    from devpub.cli.utils import show_whoami

    show_whoami()


@cli.command()
def doctor():
    """Check API connectivity and configuration."""
    from devpub.cli.utils import run_doctor

    run_doctor()


if __name__ == "__main__":
    cli()
