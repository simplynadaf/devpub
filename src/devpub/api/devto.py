"""Dev.to (Forem) API client for devpub."""

import time
from typing import Any

import httpx

from devpub.core.config import get_config

API_BASE_URL = "https://dev.to/api"
API_V1_ACCEPT = "application/vnd.forem.api-v1+json"
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds


class APIError(Exception):
    """Raised when the Dev.to API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class DevtoClient:
    """HTTP client for the Dev.to / Forem API V1."""

    def __init__(self, api_key: str | None = None):
        config = get_config()
        self.api_key = api_key or config.get("api_key", "")
        self.base_url = config.get("api_url", API_BASE_URL)
        self._client: httpx.Client | None = None
        self._request_timestamps: list[float] = []

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
            "User-Agent": "devpub/0.1.0 (https://github.com/simplynadaf/devpub)",
        }
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    def _throttle(self):
        """Enforce rate limit: max RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW seconds."""
        now = time.monotonic()
        # Remove timestamps older than the window
        cutoff = now - RATE_LIMIT_WINDOW
        self._request_timestamps = [
            t for t in self._request_timestamps if t > cutoff
        ]
        # If at the limit, sleep until the oldest request expires
        if len(self._request_timestamps) >= RATE_LIMIT_REQUESTS:
            sleep_time = self._request_timestamps[0] - cutoff
            if sleep_time > 0:
                time.sleep(sleep_time)
        self._request_timestamps.append(time.monotonic())

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> httpx.Response:
        """Make an HTTP request with rate limiting and retries."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            self._throttle()
            try:
                resp = self.client.request(method, path, params=params, json=json)
            except httpx.HTTPError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (attempt + 1))
                    continue
                raise APIError(0, f"Network error: {e}") from e

            if resp.status_code == 429:
                # Rate limited -- wait and retry
                retry_after = int(resp.headers.get("retry-after", RATE_LIMIT_WINDOW))
                if attempt < MAX_RETRIES - 1:
                    time.sleep(retry_after)
                    continue
                raise APIError(429, "Rate limited. Try again later.")

            if resp.status_code >= 500:
                # Server error -- retry
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (attempt + 1))
                    continue
                raise APIError(resp.status_code, f"Server error: {resp.text[:200]}")

            if resp.status_code == 401:
                raise APIError(401, "Invalid API key. Check your DEVPUB_API_KEY.")

            if resp.status_code == 403:
                raise APIError(403, "Access denied. Your API key may lack permissions.")

            if resp.status_code == 404:
                raise APIError(404, f"Not found: {path}")

            if resp.status_code >= 400:
                body = resp.text[:200]
                raise APIError(resp.status_code, f"API error: {body}")

            return resp

        # Should not reach here, but just in case
        raise APIError(0, f"Request failed after {MAX_RETRIES} retries: {last_error}")

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # --- Articles ---

    def get_my_articles(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get all articles for the authenticated user."""
        resp = self._request("GET", "/articles/me/all", params={"page": page, "per_page": per_page})
        return resp.json()

    def get_my_published(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get published articles for the authenticated user."""
        resp = self._request(
            "GET", "/articles/me/published", params={"page": page, "per_page": per_page}
        )
        return resp.json()

    def get_my_unpublished(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get draft/unpublished articles for the authenticated user."""
        resp = self._request(
            "GET", "/articles/me/unpublished", params={"page": page, "per_page": per_page}
        )
        return resp.json()

    def get_article(self, article_id: int) -> dict:
        """Get a single article by ID."""
        resp = self._request("GET", f"/articles/{article_id}")
        return resp.json()

    def create_article(self, article_data: dict) -> dict:
        """Create a new article on Dev.to."""
        resp = self._request("POST", "/articles", json={"article": article_data})
        return resp.json()

    def update_article(self, article_id: int, article_data: dict) -> dict:
        """Update an existing article on Dev.to."""
        resp = self._request("PUT", f"/articles/{article_id}", json={"article": article_data})
        return resp.json()

    # --- Analytics ---

    def get_analytics_totals(
        self, article_id: int | None = None, organization_id: int | None = None
    ) -> dict:
        """Get lifetime analytics totals."""
        params: dict[str, Any] = {}
        if article_id:
            params["article_id"] = article_id
        if organization_id:
            params["organization_id"] = organization_id
        resp = self._request("GET", "/analytics/totals", params=params)
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
        resp = self._request("GET", "/analytics/historical", params=params)
        return resp.json()

    def get_analytics_past_day(self, article_id: int | None = None) -> dict:
        """Get hourly analytics for the last 24 hours."""
        params: dict[str, Any] = {}
        if article_id:
            params["article_id"] = article_id
        resp = self._request("GET", "/analytics/past_day", params=params)
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
        resp = self._request("GET", "/analytics/referrers", params=params)
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
        resp = self._request("GET", "/analytics/follower_engagement", params=params)
        return resp.json()

    def get_analytics_heatmap(self, end: str | None = None) -> dict:
        """Get activity heatmap metrics."""
        params: dict[str, Any] = {}
        if end:
            params["end"] = end
        resp = self._request("GET", "/analytics/heatmap", params=params)
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
        resp = self._request("GET", "/analytics/dashboard", params=params)
        return resp.json()

    # --- Trends ---

    def get_trends(self, page: int = 1, per_page: int = 10) -> list[dict]:
        """Get current trending topics."""
        resp = self._request("GET", "/trends", params={"page": page, "per_page": per_page})
        return resp.json()

    def get_trend(self, id_or_slug: str) -> dict:
        """Get details of a single trend."""
        resp = self._request("GET", f"/trends/{id_or_slug}")
        return resp.json()

    def get_trend_articles(
        self, id_or_slug: str, page: int = 1, per_page: int = 10
    ) -> list[dict]:
        """Get articles belonging to a trend."""
        resp = self._request(
            "GET", f"/trends/{id_or_slug}/articles", params={"page": page, "per_page": per_page}
        )
        return resp.json()

    # --- Search ---

    def search_articles(self, query: str, page: int = 1, per_page: int = 10) -> list[dict]:
        """Keyword search for articles."""
        resp = self._request(
            "GET", "/articles/search", params={"q": query, "page": page, "per_page": per_page}
        )
        return resp.json()

    def semantic_search(
        self, query: str, page: int = 1, per_page: int = 10, threshold: float | None = None
    ) -> list[dict]:
        """AI-powered semantic search for articles."""
        params: dict[str, Any] = {"q": query, "page": page, "per_page": per_page}
        if threshold is not None:
            params["threshold"] = threshold
        resp = self._request("GET", "/articles/semantic_search", params=params)
        return resp.json()

    # --- Concepts ---

    def get_concepts(self, page: int = 1, per_page: int = 10, days: int = 7) -> list[dict]:
        """Get accessible concepts with metrics."""
        resp = self._request(
            "GET", "/concepts", params={"page": page, "per_page": per_page, "days": days}
        )
        return resp.json()

    def search_concepts(
        self, query: str, per_page: int = 10, threshold: float | None = None
    ) -> list[dict]:
        """Semantic search for concepts."""
        params: dict[str, Any] = {"q": query, "per_page": per_page}
        if threshold is not None:
            params["threshold"] = threshold
        resp = self._request("GET", "/concepts/search", params=params)
        return resp.json()

    # --- Tags ---

    def get_tags(self, page: int = 1, per_page: int = 10) -> list[dict]:
        """Get available tags."""
        resp = self._request("GET", "/tags", params={"page": page, "per_page": per_page})
        return resp.json()

    def get_followed_tags(self) -> list[dict]:
        """Get tags the user follows."""
        resp = self._request("GET", "/follows/tags")
        return resp.json()

    # --- Followers ---

    def get_followers(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get the authenticated user's followers."""
        resp = self._request(
            "GET", "/followers/users", params={"page": page, "per_page": per_page}
        )
        return resp.json()

    # --- Reactions ---

    def toggle_reaction(self, category: str, reactable_id: int, reactable_type: str) -> dict:
        """Toggle a reaction on an article/comment/user."""
        resp = self._request(
            "POST",
            "/reactions/toggle",
            params={
                "category": category,
                "reactable_id": reactable_id,
                "reactable_type": reactable_type,
            },
        )
        return resp.json()

    # --- Reading List ---

    def get_readinglist(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """Get the user's reading list."""
        resp = self._request(
            "GET", "/readinglist", params={"page": page, "per_page": per_page}
        )
        return resp.json()

    # --- User ---

    def get_me(self) -> dict:
        """Get the authenticated user's profile."""
        resp = self._request("GET", "/users/me")
        return resp.json()

    # --- Health ---

    def health_check(self) -> bool:
        """Check if the API is reachable and auth works."""
        try:
            self.get_me()
            return True
        except APIError:
            return False
        except httpx.HTTPError:
            return False
