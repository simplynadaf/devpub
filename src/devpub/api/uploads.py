"""Image upload client for Dev.to.

The Forem API V1 exposes no image endpoint, so there is no way to get a local
file onto Dev.to with an API key alone. The web editor posts to
``/image_uploads``, which authenticates with a browser session and a CSRF token
instead. That different auth model is why this lives apart from
:class:`~devpub.api.devto.DevtoClient` rather than becoming another method on it.

Because the endpoint is not part of the published API, treat it as best-effort:
it can change without notice, and a failure here should never be fatal to a push.
"""

import mimetypes
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any

import httpx

from devpub.api.devto import APIError
from devpub.core.config import get_config

SITE_URL = "https://dev.to"
UPLOAD_PATH = "/image_uploads"
SESSION_COOKIE_NAME = "_Devto_Forem_Session"

# Dev.to rejects larger payloads; fail locally instead of wasting the round trip.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg"}
)


class ImageUploader:
    """Uploads images through the Dev.to editor's ``/image_uploads`` endpoint."""

    def __init__(
        self,
        session_cookie: str | None = None,
        csrf_token: str | None = None,
    ):
        config = get_config()
        self.session_cookie = session_cookie or config.get("session_cookie", "")
        self.csrf_token = csrf_token or config.get("csrf_token", "")
        self.site_url = config.get("site_url", SITE_URL)
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.site_url,
                headers=self._headers(),
                cookies=self._cookies(),
                timeout=120.0,  # image bodies are far slower than JSON
            )
        return self._client

    def _headers(self) -> dict[str, str]:
        """Build headers. Rails checks Origin as well as the CSRF token."""
        headers = {
            "Accept": "*/*",
            "Origin": self.site_url,
            "Referer": f"{self.site_url}/new",
            "User-Agent": "devpub/0.2.1 (https://github.com/simplynadaf/devpub)",
        }
        if self.csrf_token:
            headers["X-CSRF-Token"] = self.csrf_token
        return headers

    def _cookies(self) -> dict[str, str]:
        """Accept either a bare session value or a whole copied cookie header.

        Copying one value out of devtools is easy to get wrong, so a pasted
        ``a=1; b=2`` string is parsed rather than rejected.
        """
        raw = self.session_cookie.strip()
        if not raw:
            return {}
        if "=" not in raw:
            return {SESSION_COOKIE_NAME: raw}

        jar = SimpleCookie()
        jar.load(raw)
        return {key: morsel.value for key, morsel in jar.items()}

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def upload(self, path: str | Path) -> str:
        """Upload one image and return its public Dev.to URL.

        Raises:
            APIError: the file is unusable, or Dev.to rejected the upload.
        """
        file_path = Path(path).expanduser()
        self._validate(file_path)

        mime, _ = mimetypes.guess_type(file_path.name)
        with file_path.open("rb") as handle:
            files = {"image[]": (file_path.name, handle, mime or "application/octet-stream")}
            data = {"authenticity_token": self.csrf_token}
            try:
                resp = self.client.post(UPLOAD_PATH, files=files, data=data)
            except httpx.HTTPError as e:
                raise APIError(0, f"Network error uploading {file_path.name}: {e}") from e

        self._raise_for_status(resp, file_path)
        return self._extract_url(resp, file_path)

    def upload_many(self, paths) -> list[tuple[Path, str]]:
        """Upload several images, preserving input order."""
        return [(Path(p).expanduser(), self.upload(p)) for p in paths]

    @staticmethod
    def _validate(file_path: Path):
        if not file_path.is_file():
            raise APIError(0, f"File not found: {file_path}")

        if file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            allowed = ", ".join(sorted(ALLOWED_SUFFIXES))
            raise APIError(
                0,
                f"{file_path.name} is not a supported image type. Allowed: {allowed}",
            )

        size = file_path.stat().st_size
        if size == 0:
            raise APIError(0, f"{file_path.name} is empty.")
        if size > MAX_UPLOAD_BYTES:
            limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
            raise APIError(
                0,
                f"{file_path.name} is {size / 1024 / 1024:.1f}MB, over the {limit_mb}MB limit.",
            )

    @staticmethod
    def _raise_for_status(resp: httpx.Response, file_path: Path):
        if resp.status_code in (401, 403):
            raise APIError(
                resp.status_code,
                "Dev.to rejected the session. Copy a fresh session cookie and CSRF "
                "token from the editor -- see `devpub upload --help`.",
            )
        if resp.status_code == 422:
            raise APIError(
                422,
                f"Dev.to could not process {file_path.name}. The CSRF token is often "
                "stale when this happens; re-copy it and retry.",
            )
        if resp.status_code >= 400:
            raise APIError(resp.status_code, f"Upload failed: {resp.text[:200]}")

    @staticmethod
    def _extract_url(resp: httpx.Response, file_path: Path) -> str:
        """Pull the uploaded URL out of the response.

        The endpoint is undocumented, so accept the shapes it has been seen to
        return and fail loudly rather than silently handing back a wrong value.
        """
        try:
            payload: Any = resp.json()
        except ValueError as e:
            raise APIError(0, f"Dev.to returned a non-JSON upload response: {e}") from e

        if isinstance(payload, dict):
            for key in ("links", "image", "images"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
                if isinstance(value, list) and value and isinstance(value[0], str):
                    return value[0]
            if isinstance(payload.get("error"), str):
                raise APIError(0, f"Dev.to error uploading {file_path.name}: {payload['error']}")

        raise APIError(
            0,
            f"Could not find an image URL in the upload response for {file_path.name}. "
            f"Response was: {str(payload)[:200]}",
        )
