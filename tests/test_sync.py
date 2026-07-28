"""Tests for sync logic."""


import httpx
import respx

from devpub.core.article import save_article
from devpub.core.sync import _is_devpub_article, pull_articles, push_articles


class TestIsDevpubArticle:
    def test_valid_article(self, tmp_path):
        filepath = tmp_path / "article.md"
        save_article(filepath, {"title": "Test"}, "body")
        assert _is_devpub_article(filepath) is True

    def test_plain_markdown(self, tmp_path):
        filepath = tmp_path / "readme.md"
        filepath.write_text("# Just a readme\n\nNo frontmatter here.")
        assert _is_devpub_article(filepath) is False

    def test_nonexistent_file(self, tmp_path):
        filepath = tmp_path / "missing.md"
        assert _is_devpub_article(filepath) is False


class TestPushArticles:
    @respx.mock
    def test_push_new_article(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEVPUB_API_KEY", "test-key")

        filepath = tmp_path / "post.md"
        save_article(filepath, {
            "title": "New Post",
            "published": False,
            "tags": "python",
        }, "Article body content")

        respx.post("https://dev.to/api/articles").mock(
            return_value=httpx.Response(201, json={
                "id": 100,
                "url": "https://dev.to/user/new-post-abc",
                "title": "New Post",
            })
        )

        push_articles(files=(str(filepath),))

        # Verify the file was updated with devto_id
        import frontmatter
        post = frontmatter.load(filepath)
        assert post.metadata["devto_id"] == 100

    @respx.mock
    def test_push_existing_article(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEVPUB_API_KEY", "test-key")

        filepath = tmp_path / "existing.md"
        save_article(filepath, {
            "title": "Existing Post",
            "published": True,
            "devto_id": 50,
        }, "Updated body content")

        respx.put("https://dev.to/api/articles/50").mock(
            return_value=httpx.Response(200, json={
                "id": 50,
                "url": "https://dev.to/user/existing-post",
                "title": "Existing Post",
            })
        )

        push_articles(files=(str(filepath),))

    def test_push_dry_run(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEVPUB_API_KEY", "test-key")

        filepath = tmp_path / "draft.md"
        save_article(filepath, {
            "title": "Draft Post",
            "published": False,
        }, "Draft content")

        push_articles(files=(str(filepath),), dry_run=True)
        # No API calls should be made in dry run


class TestPullArticles:
    @respx.mock
    def test_pull_published(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEVPUB_API_KEY", "test-key")

        respx.get("https://dev.to/api/articles/me/published").mock(
            return_value=httpx.Response(200, json=[
                {"id": 1, "slug": "my-first-post", "title": "My First Post"},
            ])
        )
        respx.get("https://dev.to/api/articles/1").mock(
            return_value=httpx.Response(200, json={
                "id": 1,
                "slug": "my-first-post",
                "title": "My First Post",
                "description": "A post",
                "body_markdown": "Hello from Dev.to!",
                "tag_list": ["python"],
                "cover_image": None,
                "collection_id": None,
                "canonical_url": "",
                "url": "https://dev.to/user/my-first-post",
            })
        )

        pull_articles(folder=str(tmp_path / "articles"))

        filepath = tmp_path / "articles" / "my-first-post.md"
        assert filepath.exists()

        import frontmatter
        post = frontmatter.load(filepath)
        assert post.metadata["title"] == "My First Post"
        assert post.metadata["devto_id"] == 1
        assert "Hello from Dev.to!" in post.content
