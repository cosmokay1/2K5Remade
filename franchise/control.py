"""Required remote control handshake for live AI clients. Fail closed."""
import json
import subprocess
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class AccessDisabled(RuntimeError):
    pass


def validate_control(data: dict) -> None:
    if (type(data) is not dict or type(data.get("protocol")) is not int
            or data["protocol"] != 1):
        raise AccessDisabled("AI handshake protocol is unsupported")
    if data.get("enabled") is not True:
        raise AccessDisabled("AI franchise decisions are disabled remotely")
    try:
        expires = datetime.fromisoformat(data["expires_at"])
        if expires.tzinfo is None or expires <= datetime.now(timezone.utc):
            raise ValueError("Expired")
    except (KeyError, TypeError, ValueError):
        raise AccessDisabled("AI handshake grant is missing or expired") from None


class GoogleControl:
    """Read a private GCS switch afresh at each handshake, without cached grants.

    The object is admin-owned. Future distributed clients must have read access
    only. An unavailable object denies access. No signed URLs or API keys are used.
    """
    def __init__(self, *, project: str, bucket: str, object_name: str,
                 use_gcloud_login: bool = False):
        self.project = project
        self.bucket = bucket
        self.object_name = object_name
        self.use_gcloud_login = use_gcloud_login

    def __call__(self):
        try:
            if self.use_gcloud_login:
                token = subprocess.run(
                    ["gcloud", "auth", "print-access-token", "--project", self.project],
                    capture_output=True, text=True, check=True, timeout=15).stdout.strip()
            else:
                import google.auth
                from google.auth.transport.requests import Request as AuthRequest
                credentials, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/devstorage.read_only"])
                credentials.refresh(AuthRequest())
                token = credentials.token
            if not token:
                raise AccessDisabled("AI handshake credentials unavailable")
            url = ("https://storage.googleapis.com/storage/v1/b/"
                   + quote(self.bucket, safe="") + "/o/"
                   + quote(self.object_name, safe="") + "?alt=media")
            request = Request(url, headers={"Authorization": f"Bearer {token}",
                                            "Cache-Control": "no-cache"})
            with urlopen(request, timeout=10) as response:
                data = json.load(response)
            validate_control(data)
        except AccessDisabled:
            raise
        except Exception:
            # Credential errors, missing object, timeout and malformed responses
            # all deny access. Never continue using a previous successful check.
            raise AccessDisabled("AI handshake unavailable; decisions are disabled") from None
