"""Analytics CLI commands for devpub."""

import math
from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devpub.api.devto import APIError, DevtoClient
from devpub.core.config import ensure_api_key

# Characters for bar chart rendering (increasing height)
BAR_CHARS = " ▁▂▃▄▅▆▇█"
# Sparkline characters (compact one-line trend)
SPARK_CHARS = "▁▂▃▄▅▆▇█"

# Box-drawing characters (assigned to avoid backslash-in-fstring on Python 3.10)
BOX_CORNER = "└"  # └
BOX_HORIZ = "─"   # ─
BOX_TICK = "┤"    # ┤
BOX_VERT = "│"    # │
CHAR_DOT = "·"    # ·
CHAR_LARROW = "←" # ←
CHAR_RARROW = "→" # →
CHAR_UP = "↗"     # ↗
CHAR_DOWN = "↘"   # ↘
CHAR_TRI = "▲"    # ▲
CHAR_BLOCK = "█"  # █


def show_stats(
    period: str = "30d",
    graph: bool = False,
    referrers: bool = False,
    followers: bool = False,
    heatmap: bool = False,
):
    """Show analytics for the authenticated user."""
    console = Console()
    api_key = ensure_api_key()

    try:
        with DevtoClient(api_key) as client:
            # Default: show totals
            totals = client.get_analytics_totals()

            total_views = _extract_total(totals.get("page_views"))
            total_reactions = _extract_total(totals.get("reactions"))
            total_comments = _extract_total(totals.get("comments"))
            total_followers = _extract_total(totals.get("follows"))

            console.print(
                Panel(
                    f"[bold]Your Dev.to Stats[/]\n\n"
                    f"  Views:     [cyan]{_format_num(total_views)}[/]\n"
                    f"  Reactions: [cyan]{_format_num(total_reactions)}[/]\n"
                    f"  Comments:  [cyan]{_format_num(total_comments)}[/]\n"
                    f"  Followers: [cyan]{_format_num(total_followers)}[/]",
                    title="devpub stats",
                    border_style="blue",
                )
            )

            if graph:
                _show_graph(client, console, period)

            if referrers:
                _show_referrers(client, console)

            if followers:
                _show_followers(client, console)

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")


def show_dashboard():
    """Show full analytics dashboard with formatted output."""
    console = Console()
    api_key = ensure_api_key()

    try:
        with DevtoClient(api_key) as client:
            # Totals
            totals = client.get_analytics_totals()

            views = _extract_total(totals.get("page_views"))
            reactions = _extract_total(totals.get("reactions"))
            comments = _extract_total(totals.get("comments"))
            followers = _extract_total(totals.get("follows"))

            console.print("\n[bold]Analytics Dashboard[/]\n")

            # Summary panel
            console.print(
                Panel(
                    f"  Views:     [cyan]{_format_num(views)}[/]\n"
                    f"  Reactions: [cyan]{_format_num(reactions)}[/]\n"
                    f"  Comments:  [cyan]{_format_num(comments)}[/]\n"
                    f"  Followers: [cyan]{_format_num(followers)}[/]",
                    title="Lifetime Totals",
                    border_style="blue",
                )
            )

            # Top articles
            articles = client.get_my_published(per_page=10)
            if articles:
                table = Table(title="Top Articles (by reactions)")
                table.add_column("#", style="dim", width=3)
                table.add_column("Title", style="cyan", max_width=50)
                table.add_column("Views", justify="right")
                table.add_column("Reactions", justify="right", style="green")
                table.add_column("Comments", justify="right")

                # Sort by reactions descending
                sorted_articles = sorted(
                    articles,
                    key=lambda a: a.get("positive_reactions_count", 0),
                    reverse=True,
                )

                for i, art in enumerate(sorted_articles[:10], 1):
                    table.add_row(
                        str(i),
                        art.get("title", "Untitled")[:50],
                        str(art.get("page_views_count", 0)),
                        str(art.get("positive_reactions_count", 0)),
                        str(art.get("comments_count", 0)),
                    )

                console.print(table)

            # Referrers
            _show_referrers(client, console)

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/]")


def _show_graph(client: DevtoClient, console: Console, period: str = "30d"):
    """Render a terminal bar chart of views over time."""
    # Parse period string (e.g., "7d", "30d", "90d")
    days = _parse_period(period)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    try:
        data = client.get_analytics_historical(start=start_str, end=end_str)
    except APIError as e:
        console.print(f"[yellow]Could not fetch historical data: {e.message}[/]")
        return

    if not data:
        console.print("[yellow]No historical data available for this period.[/]")
        return

    # Extract daily view counts
    daily_views = []
    dates = []

    if isinstance(data, dict) and _is_date_keyed(data):
        # Dev.to V1 format: {"2026-07-04": {"page_views": {"total": 152}, ...}, ...}
        for date_key in sorted(data.keys()):
            entry = data[date_key]
            if isinstance(entry, dict):
                views = entry.get("page_views", {})
                if isinstance(views, dict):
                    views = views.get("total", 0)
                daily_views.append(int(views))
                dates.append(date_key)
    elif isinstance(data, list):
        for entry in data:
            views = entry.get("page_views", entry.get("views", 0))
            if isinstance(views, dict):
                views = views.get("total", 0)
            daily_views.append(int(views))
            dates.append(entry.get("date", ""))
    elif isinstance(data, dict):
        # Fallback: some API responses wrap data differently
        entries = data.get("data", data.get("historical", []))
        for entry in entries:
            views = entry.get("page_views", entry.get("views", 0))
            if isinstance(views, dict):
                views = views.get("total", 0)
            daily_views.append(int(views))
            dates.append(entry.get("date", ""))

    if not daily_views:
        console.print("[yellow]No view data found in response.[/]")
        return

    # Render the chart
    console.print()
    _render_bar_chart(console, daily_views, dates, title=f"Views (last {days} days)")

    # Multi-period sparkline summary
    _render_period_sparklines(console, daily_views, dates)


def _render_bar_chart(
    console: Console,
    values: list[int],
    labels: list[str],
    title: str = "Chart",
    chart_height: int = 12,
    chart_width: int = 50,
):
    """Render an enhanced vertical bar chart with color gradients, sparkline, and trend."""
    if not values:
        return

    max_val = max(values)
    min_val = min(values)

    if max_val == 0:
        console.print(f"[dim]{title}: all values are zero[/]")
        return

    # If we have more data points than chart width, downsample
    if len(values) > chart_width:
        values, labels = _downsample(values, labels, chart_width)

    # Title with trend indicator
    trend = _trend_indicator(values)
    console.print(f"\n  [bold]{title}[/]  {trend}\n")

    avg_val = sum(values) // len(values) if values else 0

    # Y-axis labels and bars with color gradient
    for row in range(chart_height, 0, -1):
        line_parts = []

        # Y-axis label with tick marks
        if row == chart_height:
            y_label = _format_num(max_val)
        elif row == int(chart_height * 0.75):
            y_label = _format_num(int(max_val * 0.75))
        elif row == chart_height // 2:
            y_label = _format_num(max_val // 2)
        elif row == int(chart_height * 0.25):
            y_label = _format_num(int(max_val * 0.25))
        else:
            y_label = ""

        # Use box-drawing tick mark
        tick = "┤" if y_label else "│"
        line_parts.append(f"  {y_label:>6} {tick}")

        # Average line row (closest row to avg value)
        avg_row = int((avg_val / max_val) * chart_height) if max_val > 0 else 0
        is_avg_row = row == avg_row and avg_row > 0

        # Bar characters with color gradient
        for idx, val in enumerate(values):
            ratio = val / max_val if max_val > 0 else 0
            bar_row_ratio = row / chart_height
            color = _value_to_color(ratio)

            if ratio >= bar_row_ratio:
                line_parts.append(f"[{color}]█[/]")
            elif ratio >= (row - 1) / chart_height:
                # Partial fill
                frac = (ratio - (row - 1) / chart_height) * chart_height
                char_idx = min(int(frac * (len(BAR_CHARS) - 1)), len(BAR_CHARS) - 1)
                line_parts.append(f"[{color}]{BAR_CHARS[char_idx]}[/]")
            elif is_avg_row:
                line_parts.append("[dim]·[/]")
            else:
                line_parts.append(" ")

        # Average label on the right
        if is_avg_row:
            line_parts.append(f" [dim]← avg ({_format_num(avg_val)})[/]")

        console.print("".join(line_parts))

    # X-axis with box-drawing
    bar_count = len(values)
    console.print(f"  {'':>6} └{'─' * bar_count}")

    # X-axis labels (show first, middle, last)
    if labels and len(labels) >= 3:
        first = _short_date(labels[0])
        mid = _short_date(labels[len(labels) // 2])
        last = _short_date(labels[-1])

        spacing = bar_count // 2
        x_axis = f"  {'':>6}  {first}"
        x_axis += " " * max(1, spacing - len(first) - len(mid) // 2)
        x_axis += mid
        x_axis += " " * max(1, spacing - len(mid) // 2 - len(last))
        x_axis += last
        console.print(f"[dim]{x_axis}[/]")
    elif labels:
        console.print(f"[dim]  {'':>6}  {_short_date(labels[0])} → {_short_date(labels[-1])}[/]")

    # Sparkline with label
    spark = _sparkline(values)
    console.print(f"\n  [dim]trend:[/] {spark}")

    # Summary line with peak marker
    total = sum(values)
    peak_idx = values.index(max_val)
    peak_date = _short_date(labels[peak_idx]) if peak_idx < len(labels) else ""

    console.print(
        f"\n  Total: [bold]{_format_num(total)}[/] │ "
        f"Avg: [bold]{_format_num(avg_val)}[/]/day │ "
        f"Peak: [bold yellow]{_format_num(max_val)}[/] [dim]▲ {peak_date}[/]"
    )


def _render_period_sparklines(console: Console, all_values: list[int], all_labels: list[str]):
    """Render sparklines for 7d, 14d, 21d, and 30d periods with trend and total."""
    periods = [
        (7, " 7 days"),
        (14, "14 days"),
        (21, "21 days"),
        (30, "30 days"),
    ]

    console.print("\n  [bold]Period Breakdown[/]\n")

    for days, label in periods:
        if len(all_values) < days:
            continue

        values = all_values[-days:]
        spark = _sparkline(values)
        trend = _trend_indicator(values)
        total = sum(values)

        # Pad sparkline to consistent width for alignment
        pad = 32 - len(spark)
        padding = " " * max(pad, 1)

        console.print(
            f"  [dim]{label}:[/] {spark}{padding}{trend}   [dim]Total: {_format_num(total)}[/]"
        )


def _show_referrers(client: DevtoClient, console: Console):
    """Show top traffic referrers."""
    try:
        data = client.get_analytics_referrers()
    except APIError:
        return

    if not data:
        console.print("[dim]No referrer data available.[/]")
        return

    table = Table(title="Top Referrers")
    table.add_column("Source", style="cyan")
    table.add_column("Views", justify="right")

    for ref in data[:10] if isinstance(data, list) else []:
        table.add_row(ref.get("domain", "unknown"), str(ref.get("count", 0)))

    console.print(table)


def _show_followers(client: DevtoClient, console: Console):
    """Show follower engagement."""
    try:
        data = client.get_analytics_followers()
    except APIError:
        return

    if data:
        console.print(f"\n[bold]Follower Engagement[/]\n{data}")


def _format_num(n: int) -> str:
    """Format large numbers for display."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _extract_total(value) -> int:
    """Extract total from an analytics field.

    The Dev.to API returns nested dicts like {"total": 5000, ...}
    for analytics fields, not flat integers.
    """
    if isinstance(value, dict):
        return value.get("total", 0)
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _parse_period(period: str) -> int:
    """Parse a period string like '7d', '30d', '90d' into days."""
    period = period.strip().lower()
    if period.endswith("d"):
        try:
            return int(period[:-1])
        except ValueError:
            pass
    elif period.endswith("w"):
        try:
            return int(period[:-1]) * 7
        except ValueError:
            pass
    elif period.endswith("m"):
        try:
            return int(period[:-1]) * 30
        except ValueError:
            pass
    # Default to 30 days
    return 30


def _short_date(date_str: str) -> str:
    """Convert '2026-07-15' to 'Jul 15'."""
    if not date_str or len(date_str) < 10:
        return date_str or ""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%b %d")
    except ValueError:
        return date_str[:10]


def _is_date_keyed(data: dict) -> bool:
    """Check if a dict uses date strings as keys (e.g., '2026-07-04')."""
    if not data:
        return False
    first_key = next(iter(data))
    # Quick check: date keys look like YYYY-MM-DD
    return (
        isinstance(first_key, str)
        and len(first_key) >= 10
        and first_key[4] == "-"
        and first_key[7] == "-"
    )


def _value_to_color(ratio: float) -> str:
    """Map a 0-1 ratio to a Rich color string (blue -> cyan -> green -> gold)."""
    if ratio < 0.25:
        # Blue range
        g = int(100 + ratio * 4 * 80)
        return f"rgb(50,{g},220)"
    elif ratio < 0.50:
        # Cyan range
        r = int((ratio - 0.25) * 4 * 50)
        return f"rgb({r},200,200)"
    elif ratio < 0.75:
        # Green range
        b = int(200 - (ratio - 0.50) * 4 * 150)
        return f"rgb(0,210,{b})"
    elif ratio < 0.95:
        # Lime range
        r = int((ratio - 0.75) * 5 * 200)
        return f"rgb({r},220,50)"
    else:
        # Gold (peak)
        return "rgb(255,200,0)"


def _sparkline(values: list[int]) -> str:
    """Generate a compact sparkline string from values."""
    if not values:
        return ""
    max_v = max(values) or 1
    return "".join(
        SPARK_CHARS[min(int(v / max_v * 7), 7)] for v in values
    )


def _trend_indicator(values: list[int]) -> str:
    """Compare recent 7 days vs previous 7 days, return trend arrow + percentage."""
    if len(values) < 14:
        if len(values) >= 4:
            recent = sum(values[-(len(values) // 2):])
            previous = sum(values[:len(values) // 2])
            if previous == 0:
                return "[green]↗ new[/]"
            pct = ((recent - previous) / previous) * 100
            if pct > 5:
                return f"[green]↗ +{pct:.0f}%[/]"
            elif pct < -5:
                return f"[red]↘ {pct:.0f}%[/]"
            else:
                return f"[dim]→ {pct:+.0f}%[/]"
        return ""
    recent = sum(values[-7:])
    previous = sum(values[-14:-7])
    if previous == 0:
        return "[green]↗ new[/]"
    pct = ((recent - previous) / previous) * 100
    if pct > 5:
        return f"[green]↗ +{pct:.0f}%[/]"
    elif pct < -5:
        return f"[red]↘ {pct:.0f}%[/]"
    else:
        return f"[dim]→ {pct:+.0f}%[/]"


def _downsample(values: list[int], labels: list[str], target: int) -> tuple:
    """Reduce data points by averaging adjacent values."""
    chunk_size = math.ceil(len(values) / target)
    new_values = []
    new_labels = []

    for i in range(0, len(values), chunk_size):
        chunk = values[i : i + chunk_size]
        new_values.append(sum(chunk) // len(chunk))
        new_labels.append(labels[i] if i < len(labels) else "")

    return new_values, new_labels
