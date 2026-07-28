"""Tests for the article model and frontmatter handling."""


import pytest

from devpub.core.article import (
    _parse_tags,
    _slugify,
    article_to_api_payload,
    create_article,
    load_article,
    save_article,
)


class TestSlugify:
    def test_basic_title(self):
        assert _slugify("Hello World") == "hello-world"

    def test_special_characters(self):
        assert _slugify("What's New in Python 3.12?") == "whats-new-in-python-312"

    def test_multiple_spaces(self):
        assert _slugify("Too   Many   Spaces") == "too-many-spaces"

    def test_leading_trailing_hyphens(self):
        assert _slugify("  --Hello--  ") == "hello"

    def test_unicode(self):
        assert _slugify("Caf and Rsum") == "caf-and-rsum"


class TestParseTags:
    def test_comma_separated(self):
        assert _parse_tags("python, aws, devops") == ["python", "aws", "devops"]

    def test_list_input(self):
        assert _parse_tags(["python", "aws"]) == ["python", "aws"]

    def test_empty_string(self):
        assert _parse_tags("") == []

    def test_hashtags(self):
        assert _parse_tags("#python, #aws") == ["python", "aws"]

    def test_space_separated(self):
        assert _parse_tags("python aws devops") == ["python", "aws", "devops"]


class TestLoadSaveArticle:
    def test_round_trip(self, tmp_path):
        filepath = tmp_path / "test-article.md"
        metadata = {
            "title": "Test Article",
            "published": False,
            "description": "A test",
            "tags": "python, testing",
        }
        body = "This is the article body.\n\nWith multiple paragraphs."

        save_article(filepath, metadata, body)
        assert filepath.exists()

        loaded = load_article(filepath)
        assert loaded["title"] == "Test Article"
        assert loaded["published"] is False
        assert loaded["description"] == "A test"
        assert loaded["body"].strip() == body.strip()

    def test_load_with_devto_id(self, tmp_path):
        filepath = tmp_path / "synced.md"
        metadata = {
            "title": "Synced Article",
            "published": True,
            "devto_id": 12345,
            "devto_url": "https://dev.to/user/synced-article",
        }
        save_article(filepath, metadata, "Body content")

        loaded = load_article(filepath)
        assert loaded["devto_id"] == 12345
        assert loaded["devto_url"] == "https://dev.to/user/synced-article"


class TestArticleToApiPayload:
    def test_minimal_article(self):
        article = {
            "title": "My Post",
            "body": "Hello world",
            "published": False,
            "tags": [],
            "description": "",
            "series": None,
            "canonical_url": None,
            "cover_image": None,
            "organization_id": None,
        }
        payload = article_to_api_payload(article)
        assert payload == {
            "title": "My Post",
            "body_markdown": "Hello world",
            "published": False,
        }

    def test_full_article(self):
        article = {
            "title": "Full Post",
            "body": "Content here",
            "published": True,
            "tags": ["python", "tutorial"],
            "description": "A full article",
            "series": "My Series",
            "canonical_url": "https://myblog.com/post",
            "cover_image": "https://img.com/cover.png",
            "organization_id": 42,
        }
        payload = article_to_api_payload(article)
        assert payload["title"] == "Full Post"
        assert payload["published"] is True
        assert payload["tags"] == "python, tutorial"
        assert payload["description"] == "A full article"
        assert payload["series"] == "My Series"
        assert payload["canonical_url"] == "https://myblog.com/post"
        assert payload["main_image"] == "https://img.com/cover.png"
        assert payload["organization_id"] == 42


class TestCreateArticle:
    def test_create_default(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_article("My New Post", template="default", folder="articles")

        filepath = tmp_path / "articles" / "my-new-post.md"
        assert filepath.exists()

        content = filepath.read_text()
        assert "My New Post" in content
        assert "published: false" in content

    def test_create_tutorial(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_article("Building a REST API", template="tutorial", folder="posts")

        filepath = tmp_path / "posts" / "building-a-rest-api.md"
        assert filepath.exists()

        content = filepath.read_text()
        assert "Building a REST API" in content
        assert "Prerequisites" in content

    def test_create_duplicate_fails(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_article("Duplicate", template="default", folder="articles")

        with pytest.raises(SystemExit):
            create_article("Duplicate", template="default", folder="articles")

    def test_create_unknown_template_fails(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit):
            create_article("Bad Template", template="nonexistent", folder="articles")
