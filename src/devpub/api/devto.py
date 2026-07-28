"""Dev.to (Forem) API client for devpub."""

from typing import Any

import httpx

from devpub.core.config import get_config

API_BASE_URL = "https://dev.to/api"
API_V1_ACCEPT = "application/vnd.forem.api-v1+json"
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 30  # seconds


class DevtoClient:
    """HTTP client for the Dev.to / Forem API V1."""

    def __init__(self, api_key: str | None = None):
        config = get_config()
        self.api_key = api_key or config.get("api_key", "")
        self.base_url = config.get("api_url", API_BASE_URL)
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self._headers(),
                timeout=30.0,
            )
        return self._client

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": API_V1_ACCEPT,
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ─── Articles ────────────────────────────────────────────────────────────

    def get_my_articles(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get all articles for the authenticated user."""
        resp = self.client.get(
            "/articles/me/all",
            params={"page": page, "per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    def get_my_published(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get published articles for the authenticated user."""
        resp = self.client.get(
            "/articles/me/published",
            params={"page": page, "per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    def get_my_unpublished(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get draft/unpublished articles for the authenticated user."""
        resp = self.client.get(
            "/articles/me/unpublished",
            params={"page": page, "per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    def get_article(self, article_id: int) -> dict:
        """Get a single article by ID."""
        resp = self.client.get(f"/articles/{article_id}")
        resp.raise_for_status()
        return resp.json()

    def create_article(self, article_data: dict) -> dict:
        """Create a new article on Dev.to."""
        resp = self.client.post("/articles", json={"article": article_data})
        resp.raise_for_status()
        return resp.json()

    def update_article(self, article_id: int, article_data: dict) -> dict:
        """Update an existing article on Dev.to."""
        resp = self.client.put(f"/articles/{article_id}", json={"article": article_data})
        resp.raise_for_status()
        return resp.json()

    # ─── Analytics ───────────────────────────────────────────────────────────

    def get_analytics_totals(
        self, article_id: int | None = None, organization_id: int | None = None
    ) -> dict:
        """Get lifetime analytics totals."""
        params: dict[str, Any] = {}
        if article_id:
            params["article_id"] = article_id
        if organization_id:
            params["organization_id"] = organization_id
        resp = self.client.get("/analytics/totals", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_analytics_historical(
        self, start: str, end: str | None = None, article_id: int | None = None
    ) -> dict:
        """Get historical analytics over a date range."""
        params: dict[str, Any] = {"start": start}
        if end:
            params["end"] = end
        if article_id:
            params["article_id"] = article_id
        resp = self.client.get("/analytics/historical", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_analytics_past_day(self, article_id: int | None = None) -> dict:
        """Get hourly analytics for the last 24 hours."""
        params: dict[str, Any] = {}
        if article_id:
            params["article_id"] = article_id
        resp = self.client.get("/analytics/past_day", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_analytics_referrers(
        self, start: str | None = None, end: str | None = None
    ) -> dict:
        """Get traffic referrer analytics."""
        params: dict[str, Any] = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        resp = self.client.get("/analytics/referrers", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_analytics_followers(
        self, start: str | None = None, end: str | None = None
    ) -> dict:
        """Get follower engagement analytics."""
        params: dict[str, Any] = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        resp = self.client.get("/analytics/follower_engagement", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_analytics_heatmap(self, end: str | None = None) -> dict:
        """Get activity heatmap metrics."""
        params: dict[str, Any] = {}
        if end:
            params["end"] = end
        resp = self.client.get("/analytics/heatmap", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_analytics_dashboard(
        self, start: str | None = None, end: str | None = None
    ) -> dict:
        """Get complete analytics dashboard bundle."""
        params: dict[str, Any] = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        resp = self.client.get("/analytics/dashboard", params=params)
        resp.raise_for_status()
        return resp.json()

    # ─── Trends ──────────────────────────────────────────────────────────────

    def get_trends(self, page: int = 1, per_page: int = 10) -> list[dict]:
        """Get current trending topics."""
        resp = self.client.get(
            "/trends", params={"page": page, "per_page": per_page}
        )
        resp.raise_for_status()
        return resp.json()

    def get_trend(self, id_or_slug: str) -> dict:
        """Get details of a single trend."""
        resp = self.client.get(f"/trends/{id_or_slug}")
        resp.raise_for_status()
        return resp.json()

    def get_trend_articles(
        self, id_or_slug: str, page: int = 1, per_page: int = 10
    ) -> list[dict]:
        """Get articles belonging to a trend."""
        resp = self.client.get(
            f"/trends/{id_or_slug}/articles",
            params={"page": page, "per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Search ──────────────────────────────────────────────────────────────

    def search_articles(self, query: str, page: int = 1, per_page: int = 10) -> list[dict]:
        """Keyword search for articles."""
        resp = self.client.get(
            "/articles/search",
            params={"q": query, "page": page, "per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    def semantic_search(
        self, query: str, page: int = 1, per_page: int = 10, threshold: float | None = None
    ) -> list[dict]:
        """AI-powered semantic search for articles."""
        params: dict[str, Any] = {"q": query, "page": page, "per_page": per_page}
        if threshold is not None:
            params["threshold"] = threshold
        resp = self.client.get("/articles/semantic_search", params=params)
        resp.raise_for_status()
        return resp.json()

    # ─── Concepts ────────────────────────────────────────────────────────────

    def get_concepts(self, page: int = 1, per_page: int = 10, days: int = 7) -> list[dict]:
        """Get accessible concepts with metrics."""
        resp = self.client.get(
            "/concepts",
            params={"page": page, "per_page": per_page, "days": days},
        )
        resp.raise_for_status()
        return resp.json()

    def search_concepts(
        self, query: str, per_page: int = 10, threshold: float | None = None
    ) -> list[dict]:
        """Semantic search for concepts."""
        params: dict[str, Any] = {"q": query, "per_page": per_page}
        if threshold is not None:
            params["threshold"] = threshold
        resp = self.client.get("/concepts/search", params=params)
        resp.raise_for_status()
        return resp.json()

    # ─── Tags ────────────────────────────────────────────────────────────────

    def get_tags(self, page: int = 1, per_page: int = 10) -> list[dict]:
        """Get available tags."""
        resp = self.client.get("/tags", params={"page": page, "per_page": per_page})
        resp.raise_for_status()
        return resp.json()

    def get_followed_tags(self) -> list[dict]:
        """Get tags the user follows."""
        resp = self.client.get("/follows/tags")
        resp.raise_for_status()
        return resp.json()

    # ─── Followers ───────────────────────────────────────────────────────────

    def get_followers(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get the authenticated user's followers."""
        resp = self.client.get(
            "/followers/users", params={"page": page, "per_page": per_page}
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Reactions ───────────────────────────────────────────────────────────

    def toggle_reaction(self, category: str, reactable_id: int, reactable_type: str) -> dict:
        """Toggle a reaction on an article/comment/user."""
        resp = self.client.post(
            "/reactions/toggle",
            params={
                "category": category,
                "reactable_id": reactable_id,
                "reactable_type": reactable_type,
            },
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Reading List ────────────────────────────────────────────────────────

    def get_readinglist(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get the user's reading list."""
        resp = self.client.get(
            "/readinglist", params={"page": page, "per_page": per_page}
        )
        resp.raise_for_status()
        return resp.json()

    # ─── User ────────────────────────────────────────────────────────────────

    def get_me(self) -> dict:
        """Get the authenticated user's profile."""
        resp = self.client.get("/users/me")
        resp.raise_for_status()
        return resp.json()

    # ─── Health ──────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Check if the API is reachable."""
        try:
            resp = self.client.get("/health_checks/app")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False
