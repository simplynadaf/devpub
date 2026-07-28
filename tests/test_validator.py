"""Tests for article validation."""


from devpub.core.article import save_article
from devpub.core.validator import _validate_single


class TestValidation:
    def _write_article(self, tmp_path, metadata, body="Body content."):
        filepath = tmp_path / "test.md"
        save_article(filepath, metadata, body)
        return filepath

    def test_valid_article_passes(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "A Good Article Title",
            "published": False,
            "description": "A short description for SEO",
            "tags": "python, testing",
            "cover_image": "https://img.com/cover.png",
        }, body=" ".join(["word"] * 150))
        issues = _validate_single(filepath)
        assert len(issues) == 0

    def test_missing_title(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "",
            "published": False,
        })
        issues = _validate_single(filepath)
        errors = [i for i in issues if i["level"] == "error"]
        assert any("title" in i["message"].lower() for i in errors)

    def test_title_too_long(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "x" * 101,
            "published": False,
            "description": "ok",
            "tags": "python",
        })
        issues = _validate_single(filepath)
        assert any("long" in i["message"].lower() for i in issues)

    def test_too_many_tags(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "Good Title",
            "published": False,
            "description": "ok",
            "tags": "one, two, three, four, five",
        })
        issues = _validate_single(filepath)
        errors = [i for i in issues if i["level"] == "error"]
        assert any("tags" in i["message"].lower() for i in errors)

    def test_missing_description_warning(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "Good Title",
            "published": False,
            "description": "",
            "tags": "python",
        })
        issues = _validate_single(filepath)
        warnings = [i for i in issues if i["level"] == "warning"]
        assert any("description" in i["message"].lower() for i in warnings)

    def test_no_cover_image_warning(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "Good Title",
            "published": False,
            "description": "ok",
            "tags": "python",
        })
        issues = _validate_single(filepath)
        warnings = [i for i in issues if i["level"] == "warning"]
        assert any("cover" in i["message"].lower() for i in warnings)

    def test_empty_body(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "Good Title",
            "published": False,
            "description": "ok",
            "tags": "python",
            "cover_image": "https://img.com/x.png",
        }, body="")
        issues = _validate_single(filepath)
        errors = [i for i in issues if i["level"] == "error"]
        assert any(
            "body" in i["message"].lower() or "empty" in i["message"].lower()
            for i in errors
        )

    def test_invalid_canonical_url(self, tmp_path):
        filepath = self._write_article(tmp_path, {
            "title": "Good Title",
            "published": False,
            "description": "ok",
            "tags": "python",
            "cover_image": "https://img.com/x.png",
            "canonical_url": "not-a-url",
        })
        issues = _validate_single(filepath)
        errors = [i for i in issues if i["level"] == "error"]
        assert any("canonical" in i["message"].lower() for i in errors)
