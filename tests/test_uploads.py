"""Tests for the Dev.to image upload client."""

import httpx
import pytest
import respx

from devpub.api.devto import APIError
from devpub.api.uploads import (
    MAX_UPLOAD_BYTES,
    SESSION_COOKIE_NAME,
    ImageUploader,
)

UPLOAD_URL = "https://dev.to/image_uploads"
UPLOADED_URL = "https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/abc123.png"

# Smallest bytes that still look like a PNG to anything sniffing the header.
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture
def png(tmp_path):
    """A small on-disk PNG."""
    path = tmp_path / "cover.png"
    path.write_bytes(PNG_BYTES)
    return path


@pytest.fixture(autouse=True)
def no_ambient_credentials(monkeypatch):
    """Keep a developer's real credentials out of the tests."""
    for name in (
        "DEVPUB_SESSION_COOKIE",
        "DEVTO_SESSION_COOKIE",
        "DEVPUB_CSRF_TOKEN",
        "DEVTO_CSRF_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)


def uploader() -> ImageUploader:
    return ImageUploader(session_cookie="session-value", csrf_token="csrf-value")


class TestUploaderInit:
    def test_headers_include_csrf_token(self):
        with uploader() as up:
            assert up._headers()["X-CSRF-Token"] == "csrf-value"

    def test_headers_omit_csrf_when_absent(self):
        with ImageUploader(session_cookie="s", csrf_token="") as up:
            assert "X-CSRF-Token" not in up._headers()

    def test_headers_include_origin_for_rails_csrf_check(self):
        with uploader() as up:
            headers = up._headers()
        assert headers["Origin"] == "https://dev.to"
        assert headers["Referer"].startswith("https://dev.to")

    def test_headers_include_user_agent(self):
        with uploader() as up:
            assert "devpub" in up._headers()["User-Agent"]

    def test_bare_cookie_value_is_named(self):
        with uploader() as up:
            assert up._cookies() == {SESSION_COOKIE_NAME: "session-value"}

    def test_pasted_cookie_header_is_parsed(self):
        raw = f"ahoy_visitor=xyz; {SESSION_COOKIE_NAME}=abc123; client_id=q"
        with ImageUploader(session_cookie=raw, csrf_token="c") as up:
            cookies = up._cookies()
        assert cookies[SESSION_COOKIE_NAME] == "abc123"
        assert cookies["ahoy_visitor"] == "xyz"

    def test_empty_cookie_yields_no_cookies(self):
        with ImageUploader(session_cookie="  ", csrf_token="c") as up:
            assert up._cookies() == {}


class TestUploadSuccess:
    @respx.mock
    def test_returns_url_from_links(self, png):
        respx.post(UPLOAD_URL).mock(
            return_value=httpx.Response(200, json={"links": [UPLOADED_URL]})
        )
        with uploader() as up:
            assert up.upload(png) == UPLOADED_URL

    @respx.mock
    def test_accepts_string_link(self, png):
        respx.post(UPLOAD_URL).mock(
            return_value=httpx.Response(200, json={"links": UPLOADED_URL})
        )
        with uploader() as up:
            assert up.upload(png) == UPLOADED_URL

    @respx.mock
    def test_accepts_image_key(self, png):
        respx.post(UPLOAD_URL).mock(
            return_value=httpx.Response(200, json={"image": [UPLOADED_URL]})
        )
        with uploader() as up:
            assert up.upload(png) == UPLOADED_URL

    @respx.mock
    def test_sends_multipart_with_authenticity_token(self, png):
        route = respx.post(UPLOAD_URL).mock(
            return_value=httpx.Response(200, json={"links": [UPLOADED_URL]})
        )
        with uploader() as up:
            up.upload(png)

        request = route.calls.last.request
        assert request.headers["content-type"].startswith("multipart/form-data")
        body = request.content
        assert b"authenticity_token" in body
        assert b"csrf-value" in body
        assert b'name="image[]"' in body
        assert b"cover.png" in body

    @respx.mock
    def test_upload_many_preserves_order(self, tmp_path):
        first = tmp_path / "a.png"
        second = tmp_path / "b.png"
        first.write_bytes(PNG_BYTES)
        second.write_bytes(PNG_BYTES)

        urls = iter(["https://example.com/a.png", "https://example.com/b.png"])
        respx.post(UPLOAD_URL).mock(
            side_effect=lambda request: httpx.Response(200, json={"links": [next(urls)]})
        )
        with uploader() as up:
            result = up.upload_many([first, second])

        assert [p.name for p, _ in result] == ["a.png", "b.png"]
        assert result[0][1].endswith("a.png")
        assert result[1][1].endswith("b.png")


class TestLocalValidation:
    def test_missing_file(self, tmp_path):
        with uploader() as up, pytest.raises(APIError, match="File not found"):
            up.upload(tmp_path / "nope.png")

    def test_unsupported_extension(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("hello")
        with uploader() as up, pytest.raises(APIError, match="not a supported image type"):
            up.upload(path)

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.png"
        path.write_bytes(b"")
        with uploader() as up, pytest.raises(APIError, match="is empty"):
            up.upload(path)

    def test_oversized_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("devpub.api.uploads.MAX_UPLOAD_BYTES", 16)
        path = tmp_path / "big.png"
        path.write_bytes(b"\x00" * 64)
        with uploader() as up, pytest.raises(APIError, match="over the"):
            up.upload(path)

    @respx.mock
    def test_validation_happens_before_any_request(self, tmp_path):
        route = respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, json={}))
        with uploader() as up, pytest.raises(APIError):
            up.upload(tmp_path / "missing.png")
        assert not route.called

    def test_max_upload_limit_is_sane(self):
        assert MAX_UPLOAD_BYTES > 1024 * 1024


class TestUploadErrors:
    @respx.mock
    def test_expired_session_explains_how_to_refresh(self, png):
        respx.post(UPLOAD_URL).mock(return_value=httpx.Response(401, text="unauthorized"))
        with uploader() as up, pytest.raises(APIError, match="fresh session cookie") as exc:
            up.upload(png)
        assert exc.value.status_code == 401

    @respx.mock
    def test_forbidden_is_treated_as_session_problem(self, png):
        respx.post(UPLOAD_URL).mock(return_value=httpx.Response(403, text="forbidden"))
        with uploader() as up, pytest.raises(APIError, match="fresh session cookie"):
            up.upload(png)

    @respx.mock
    def test_unprocessable_points_at_csrf(self, png):
        respx.post(UPLOAD_URL).mock(return_value=httpx.Response(422, text="invalid"))
        with uploader() as up, pytest.raises(APIError, match="CSRF token"):
            up.upload(png)

    @respx.mock
    def test_server_error_surfaces_status(self, png):
        respx.post(UPLOAD_URL).mock(return_value=httpx.Response(500, text="boom"))
        with uploader() as up, pytest.raises(APIError, match="Upload failed") as exc:
            up.upload(png)
        assert exc.value.status_code == 500

    @respx.mock
    def test_network_error_is_wrapped(self, png):
        respx.post(UPLOAD_URL).mock(side_effect=httpx.ConnectError("no route"))
        with uploader() as up, pytest.raises(APIError, match="Network error"):
            up.upload(png)

    @respx.mock
    def test_non_json_response(self, png):
        respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, text="<html>nope</html>"))
        with uploader() as up, pytest.raises(APIError, match="non-JSON"):
            up.upload(png)

    @respx.mock
    def test_json_error_field_is_reported(self, png):
        respx.post(UPLOAD_URL).mock(
            return_value=httpx.Response(200, json={"error": "Invalid image file"})
        )
        with uploader() as up, pytest.raises(APIError, match="Invalid image file"):
            up.upload(png)

    @respx.mock
    def test_unrecognised_shape_fails_loudly(self, png):
        respx.post(UPLOAD_URL).mock(
            return_value=httpx.Response(200, json={"something": "unexpected"})
        )
        with uploader() as up, pytest.raises(APIError, match="Could not find an image URL"):
            up.upload(png)


class TestCredentialSources:
    def test_reads_devpub_env_vars(self, monkeypatch):
        monkeypatch.setenv("DEVPUB_SESSION_COOKIE", "from-env")
        monkeypatch.setenv("DEVPUB_CSRF_TOKEN", "csrf-from-env")
        with ImageUploader() as up:
            assert up.session_cookie == "from-env"
            assert up.csrf_token == "csrf-from-env"

    def test_reads_devto_env_var_aliases(self, monkeypatch):
        monkeypatch.setenv("DEVTO_SESSION_COOKIE", "alias-session")
        monkeypatch.setenv("DEVTO_CSRF_TOKEN", "alias-csrf")
        with ImageUploader() as up:
            assert up.session_cookie == "alias-session"
            assert up.csrf_token == "alias-csrf"

    def test_explicit_arguments_win_over_env(self, monkeypatch):
        monkeypatch.setenv("DEVPUB_SESSION_COOKIE", "from-env")
        with ImageUploader(session_cookie="explicit", csrf_token="c") as up:
            assert up.session_cookie == "explicit"
