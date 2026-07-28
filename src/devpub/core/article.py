"""Article model and frontmatter handling."""

import re
from pathlib import Path

import frontmatter

DEFAULT_TEMPLATE = """---
title: "{title}"
published: false
description: ""
tags:
cover_image:
series:
canonical_url:
---

Write your article here...
"""

TEMPLATES = {
    "default": DEFAULT_TEMPLATE,
    "til": """---
title: "TIL: {title}"
published: false
description: ""
tags: todayilearned
cover_image:
---

## What I Learned

<!-- Brief explanation of what you discovered -->

## The Problem

<!-- What were you trying to do? -->

## The Solution

<!-- What fixed it / what you found -->

## Why It Matters

<!-- One sentence on why others should care -->
""",
    "tutorial": """---
title: "{title}"
published: false
description: ""
tags: tutorial, beginners
cover_image:
series:
---

## Introduction

<!-- What will the reader build/learn? Why should they care? -->

## Prerequisites

<!-- What do they need before starting? -->

## Step 1: Setup

<!-- First step with code -->

## Step 2: Implementation

<!-- Core implementation -->

## Step 3: Testing

<!-- Verify it works -->

## What We Built

<!-- Summary of the result -->

## Next Steps

<!-- Where to go from here -->
""",
    "comparison": """---
title: "{title}"
published: false
description: ""
tags:
cover_image:
---

## The Problem Both Solve

<!-- What shared problem are you comparing solutions for? -->

## Option A: [Name]

### Pros
-

### Cons
-

## Option B: [Name]

### Pros
-

### Cons
-

## When to Use Each

| Use Case | Best Choice | Why |
|----------|-------------|-----|
|  |  |  |

## My Recommendation

<!-- Your opinionated take -->
""",
    "experience": """---
title: "{title}"
published: false
description: ""
tags:
cover_image:
---

## Context

<!-- What were you doing? Why? -->

## What I Expected

<!-- Going in, what did you think would happen? -->

## What Actually Happened

<!-- The reality — good and bad -->

## Key Lessons

1.
2.
3.

## Would I Do It Again?

<!-- Honest verdict -->
""",
}


def create_article(title: str, template: str = "default", folder: str = "articles"):
    """Create a new article from a template."""
    from rich.console import Console

    console = Console()

    # Get template content
    tmpl = TEMPLATES.get(template)
    if not tmpl:
        console.print(f"[red]Unknown template: {template}[/]")
        console.print(f"Available: {', '.join(TEMPLATES.keys())}")
        raise SystemExit(1)

    # Generate filename from title
    slug = _slugify(title)
    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    filepath = folder_path / f"{slug}.md"

    if filepath.exists():
        console.print(f"[yellow]File already exists: {filepath}[/]")
        raise SystemExit(1)

    # Write file
    content = tmpl.format(title=title)
    filepath.write_text(content)

    console.print(f"[green]Created:[/] {filepath}")
    console.print(f"   Template: [cyan]{template}[/]")
    console.print(f"   Edit and run [cyan]devpub push -f {filepath}[/] when ready.")


def load_article(filepath: Path) -> dict:
    """Load an article from a markdown file with frontmatter."""
    post = frontmatter.load(filepath)

    return {
        "filepath": str(filepath),
        "metadata": dict(post.metadata),
        "body": post.content,
        "title": post.metadata.get("title", ""),
        "published": post.metadata.get("published", False),
        "tags": _parse_tags(post.metadata.get("tags", "")),
        "description": post.metadata.get("description", ""),
        "series": post.metadata.get("series", None),
        "canonical_url": post.metadata.get("canonical_url", None),
        "cover_image": post.metadata.get("cover_image", None),
        "organization_id": post.metadata.get("organization_id", None),
        "devto_id": post.metadata.get("devto_id", None),
        "devto_url": post.metadata.get("devto_url", None),
    }


def save_article(filepath: Path, metadata: dict, body: str):
    """Save an article to a markdown file with frontmatter."""
    post = frontmatter.Post(body, **metadata)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(frontmatter.dumps(post))


def article_to_api_payload(article: dict) -> dict:
    """Convert a local article dict to a Dev.to API payload."""
    payload: dict = {
        "title": article["title"],
        "body_markdown": article["body"],
        "published": article["published"],
    }

    if article.get("tags"):
        tags = article["tags"]
        payload["tags"] = tags if isinstance(tags, str) else ", ".join(tags)
    if article.get("description"):
        payload["description"] = article["description"]
    if article.get("series"):
        payload["series"] = article["series"]
    if article.get("canonical_url"):
        payload["canonical_url"] = article["canonical_url"]
    if article.get("cover_image"):
        payload["main_image"] = article["cover_image"]
    if article.get("organization_id"):
        payload["organization_id"] = article["organization_id"]

    return payload


def _slugify(title: str) -> str:
    """Convert title to a URL-friendly slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    slug = slug.strip("-")
    return slug


def _parse_tags(tags) -> list[str]:
    """Parse tags from various formats."""
    if isinstance(tags, list):
        return [t.strip() for t in tags if t.strip()]
    if isinstance(tags, str):
        # Handle comma-separated or space-separated
        return [t.strip().strip("#") for t in re.split(r"[,\s]+", tags) if t.strip()]
    return []
