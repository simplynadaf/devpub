"""Hashnode API adapter for devpub (cross-posting support).

This module implements the platform adapter interface for Hashnode,
enabling cross-posting articles from Dev.to to Hashnode with
canonical URL management.

Status: Work in progress
"""

from typing import Any

# Hashnode uses GraphQL API
HASHNODE_API_URL = "https://gql.hashnode.com"


class HashnodeClient:
    """GraphQL client for Hashnode API."""

    def __init__(self, api_key: str | None = None, publication_id: str | None = None):
        self.api_key = api_key or ""
        self.publication_id = publication_id or ""
        self._client = None

    def publish_article(self, article_data: dict) -> dict:
        """Publish an article to Hashnode.

        Args:
            article_data: Dict with title, body_markdown, tags, cover_image,
                         canonical_url, etc.

        Returns:
            Dict with id, url, slug from Hashnode response.
        """
        raise NotImplementedError("Hashnode adapter is under development")

    def get_my_articles(self, page: int = 1, per_page: int = 10) -> list[dict]:
        """Get articles from user's Hashnode publication."""
        raise NotImplementedError("Hashnode adapter is under development")

    def _graphql_query(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        """Execute a GraphQL query against Hashnode API."""
        raise NotImplementedError("Hashnode adapter is under development")
