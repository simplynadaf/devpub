"""Tests for the Dev.to API client."""

import httpx
import pytest
import respx

from devpub.api.devto import API_V1_ACCEPT, DevtoClient


@pytest.fixture
def client():
    c = DevtoClient(api_key="test-api-key-123")
    yield c
    c.close()


class TestClientInit:
    def test_headers_include_accept(self, client):
        headers = client._headers()
        assert headers["Accept"] == API_V1_ACCEPT

    def test_headers_include_api_key(self, client):
        headers = client._headers()
        assert headers["api-key"] == "test-api-key-123"

    def test_headers_without_api_key(self):
        c = DevtoClient(api_key="")
        headers = c._headers()
        assert "api-key" not in headers
        c.close()


class TestArticleEndpoints:
    @respx.mock
    def test_get_my_articles(self, client):
        respx.get("https://dev.to/api/articles/me/all").mock(
            return_value=httpx.Response(200, json=[{"id": 1, "title": "Test"}])
        )
        result = client.get_my_articles()
        assert len(result) == 1
        assert result[0]["title"] == "Test"

    @respx.mock
    def test_get_my_published(self, client):
        respx.get("https://dev.to/api/articles/me/published").mock(
            return_value=httpx.Response(200, json=[{"id": 2, "title": "Published"}])
        )
        result = client.get_my_published()
        assert result[0]["id"] == 2

    @respx.mock
    def test_get_article(self, client):
        mock_data = {
            "id": 42, "title": "Single", "body_markdown": "content"
        }
        respx.get("https://dev.to/api/articles/42").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = client.get_article(42)
        assert result["id"] == 42
        assert result["body_markdown"] == "content"

    @respx.mock
    def test_create_article(self, client):
        respx.post("https://dev.to/api/articles").mock(
            return_value=httpx.Response(201, json={"id": 99, "url": "https://dev.to/user/new-post"})
        )
        result = client.create_article({"title": "New", "body_markdown": "hi", "published": False})
        assert result["id"] == 99
        assert "dev.to" in result["url"]

    @respx.mock
    def test_update_article(self, client):
        respx.put("https://dev.to/api/articles/99").mock(
            return_value=httpx.Response(200, json={"id": 99, "title": "Updated"})
        )
        result = client.update_article(99, {"title": "Updated"})
        assert result["title"] == "Updated"


class TestAnalyticsEndpoints:
    @respx.mock
    def test_get_analytics_totals(self, client):
        respx.get("https://dev.to/api/analytics/totals").mock(
            return_value=httpx.Response(200, json={"page_views": 5000, "reactions": 200})
        )
        result = client.get_analytics_totals()
        assert result["page_views"] == 5000

    @respx.mock
    def test_get_analytics_historical(self, client):
        respx.get("https://dev.to/api/analytics/historical").mock(
            return_value=httpx.Response(200, json=[{"date": "2026-07-01", "views": 100}])
        )
        result = client.get_analytics_historical(start="2026-07-01")
        assert isinstance(result, list)

    @respx.mock
    def test_get_analytics_referrers(self, client):
        respx.get("https://dev.to/api/analytics/referrers").mock(
            return_value=httpx.Response(200, json=[{"domain": "google.com", "count": 50}])
        )
        result = client.get_analytics_referrers()
        assert result[0]["domain"] == "google.com"


class TestSearchEndpoints:
    @respx.mock
    def test_search_articles(self, client):
        respx.get("https://dev.to/api/articles/search").mock(
            return_value=httpx.Response(200, json=[{"id": 10, "title": "Found"}])
        )
        result = client.search_articles("python")
        assert result[0]["title"] == "Found"

    @respx.mock
    def test_semantic_search(self, client):
        mock_data = [{"id": 11, "title": "Semantic", "similarity": 0.92}]
        respx.get("https://dev.to/api/articles/semantic_search").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = client.semantic_search("machine learning tutorials")
        assert result[0]["similarity"] == 0.92


class TestTrendsEndpoints:
    @respx.mock
    def test_get_trends(self, client):
        respx.get("https://dev.to/api/trends").mock(
            return_value=httpx.Response(200, json=[{"name": "AI", "score": 95}])
        )
        result = client.get_trends()
        assert result[0]["name"] == "AI"


class TestUserEndpoints:
    @respx.mock
    def test_get_me(self, client):
        respx.get("https://dev.to/api/users/me").mock(
            return_value=httpx.Response(200, json={"username": "testuser", "name": "Test"})
        )
        result = client.get_me()
        assert result["username"] == "testuser"


class TestHealthCheck:
    @respx.mock
    def test_health_check_ok(self, client):
        respx.get("https://dev.to/api/health_checks/app").mock(
            return_value=httpx.Response(200)
        )
        assert client.health_check() is True

    @respx.mock
    def test_health_check_down(self, client):
        respx.get("https://dev.to/api/health_checks/app").mock(
            return_value=httpx.Response(503)
        )
        assert client.health_check() is False


class TestContextManager:
    def test_context_manager(self):
        with DevtoClient(api_key="key") as client:
            assert client.api_key == "key"
