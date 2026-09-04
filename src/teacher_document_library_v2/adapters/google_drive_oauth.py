"""Google Drive OAuth and file-storage adapter using the minimal drive.file scope."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
from io import BytesIO
import secrets
import time
from typing import Any, Mapping

from teacher_document_library_v2.storage import StoredDocumentFile


DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
GOOGLE_DRIVE_SCOPES = (
    DRIVE_FILE_SCOPE,
    DRIVE_READONLY_SCOPE,
)
DEFAULT_FOLDER_NAME = "MathTeacher-AI"
OAUTH_STATE_MAX_AGE_SECONDS = 10 * 60


@dataclass(frozen=True)
class GoogleOAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str

    @classmethod
    def from_environment(cls, values: Mapping[str, str]) -> "GoogleOAuthSettings | None":
        client_id = values.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
        client_secret = values.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
        redirect_uri = values.get("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8501").strip()
        if not client_id or not client_secret or not redirect_uri:
            return None
        return cls(client_id, client_secret, redirect_uri)

    def client_config(self) -> dict[str, dict[str, object]]:
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            }
        }


def create_authorization_request(settings: GoogleOAuthSettings) -> tuple[str, str]:
    from google_auth_oauthlib.flow import Flow

    state = create_signed_oauth_state(settings.client_secret)
    code_verifier = derive_code_verifier(state, settings.client_secret)
    flow = Flow.from_client_config(
        settings.client_config(),
        scopes=list(GOOGLE_DRIVE_SCOPES),
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = settings.redirect_uri
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url, state


def create_signed_oauth_state(signing_key: str, now: int | None = None) -> str:
    if not signing_key.strip():
        raise ValueError("OAuth state signing key must not be empty")
    timestamp = int(time.time() if now is None else now)
    payload = f"{timestamp}.{secrets.token_urlsafe(24)}"
    signature = hmac.new(
        signing_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).digest()
    encoded = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{payload}.{encoded}"


def validate_signed_oauth_state(
    state: str,
    signing_key: str,
    *,
    now: int | None = None,
    max_age_seconds: int = OAUTH_STATE_MAX_AGE_SECONDS,
) -> None:
    try:
        timestamp_text, nonce, received = state.split(".", 2)
        timestamp = int(timestamp_text)
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("OAuth state is invalid") from error
    if not nonce or not received or not signing_key.strip():
        raise ValueError("OAuth state is invalid")
    payload = f"{timestamp}.{nonce}"
    expected_bytes = hmac.new(
        signing_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).digest()
    expected = base64.urlsafe_b64encode(expected_bytes).decode("ascii").rstrip("=")
    if not hmac.compare_digest(received, expected):
        raise ValueError("OAuth state is invalid")
    current = int(time.time() if now is None else now)
    age = current - timestamp
    if age < -30 or age > max_age_seconds:
        raise ValueError("OAuth state has expired")


def derive_code_verifier(state: str, signing_key: str) -> str:
    """Derive the same PKCE verifier on both sides of a stateless callback."""
    if not state.strip() or not signing_key.strip():
        raise ValueError("OAuth state and signing key must not be empty")
    digest = hmac.new(
        signing_key.encode("utf-8"),
        f"pkce.{state}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def exchange_authorization_code(
    settings: GoogleOAuthSettings, *, code: str, state: str
) -> dict[str, object]:
    from google_auth_oauthlib.flow import Flow

    if not code.strip() or not state.strip():
        raise ValueError("OAuth code and state must not be empty")
    flow = Flow.from_client_config(
        settings.client_config(),
        scopes=list(GOOGLE_DRIVE_SCOPES),
        state=state,
        code_verifier=derive_code_verifier(state, settings.client_secret),
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = settings.redirect_uri
    flow.fetch_token(code=code)
    return credentials_to_dict(flow.credentials)


def credentials_to_dict(credentials: Any) -> dict[str, object]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or GOOGLE_DRIVE_SCOPES),
    }


def credentials_from_dict(payload: Mapping[str, object]):
    from google.oauth2.credentials import Credentials

    return Credentials(
        token=payload.get("token"),
        refresh_token=payload.get("refresh_token"),
        token_uri=payload.get("token_uri"),
        client_id=payload.get("client_id"),
        client_secret=payload.get("client_secret"),
        scopes=payload.get("scopes"),
    )


class GoogleDriveFileStorage:
    def __init__(self, credentials: Any, folder_name: str = DEFAULT_FOLDER_NAME) -> None:
        self._credentials = credentials
        self._folder_name = folder_name.strip() or DEFAULT_FOLDER_NAME
        self._service = None
        self._folder_id = None

    def upload(self, content: bytes, file_name: str, mime_type: str) -> StoredDocumentFile:
        from googleapiclient.http import MediaIoBaseUpload

        if not isinstance(content, bytes) or not content:
            raise ValueError("file content must not be empty")
        safe_name = self._safe_file_name(file_name)
        service = self._drive_service()
        body = {"name": safe_name, "parents": [self._ensure_folder()]}
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mime_type, resumable=True)
        row = service.files().create(
            body=body,
            media_body=media,
            fields="id,name,mimeType,size,webViewLink",
        ).execute()
        return StoredDocumentFile(
            provider="google_drive_oauth",
            file_id=str(row["id"]),
            file_name=str(row.get("name") or safe_name),
            mime_type=str(row.get("mimeType") or mime_type),
            size_bytes=int(row.get("size") or len(content)),
            web_view_link=row.get("webViewLink"),
        )

    def delete(self, file_id: str) -> bool:
        if not file_id or not str(file_id).strip():
            raise ValueError("file_id must not be empty")
        self._drive_service().files().delete(fileId=str(file_id).strip()).execute()
        return True

    def _drive_service(self):
        if self._service is None:
            from googleapiclient.discovery import build

            self._service = build("drive", "v3", credentials=self._credentials, cache_discovery=False)
        return self._service

    def _ensure_folder(self) -> str:
        if self._folder_id:
            return self._folder_id
        escaped = self._folder_name.replace("'", "\\'")
        response = self._drive_service().files().list(
            q=(
                f"name = '{escaped}' and mimeType = 'application/vnd.google-apps.folder' "
                "and trashed = false"
            ),
            spaces="drive",
            fields="files(id,name)",
            pageSize=1,
        ).execute()
        rows = response.get("files", [])
        if rows:
            self._folder_id = str(rows[0]["id"])
        else:
            row = self._drive_service().files().create(
                body={"name": self._folder_name, "mimeType": "application/vnd.google-apps.folder"},
                fields="id",
            ).execute()
            self._folder_id = str(row["id"])
        return self._folder_id

    @staticmethod
    def _safe_file_name(value: str) -> str:
        name = str(value).replace("\\", "/").rsplit("/", 1)[-1].strip()
        if not name or name in (".", ".."):
            raise ValueError("file_name must not be empty")
        return name[:255]

    def list_folder_tree(
        self,
        folder_id: str,
        *,
        recursive: bool = True,
        mime_type: str | None = None,
    ) -> tuple[StoredDocumentFile, ...]:
        # Strictly read-only Drive folder traversal for Smart Up.
        normalized_folder_id = str(folder_id).strip()
        if not normalized_folder_id:
            raise ValueError("folder_id must not be empty")

        service = self._drive_service()
        folder_mime = "application/vnd.google-apps.folder"
        queue = [normalized_folder_id]
        seen_folders = {normalized_folder_id}
        found: list[StoredDocumentFile] = []

        while queue:
            parent_id = queue.pop(0)
            escaped_parent = parent_id.replace("'", "\\'")
            page_token = None

            while True:
                response = service.files().list(
                    q=(
                        f"'{escaped_parent}' in parents "
                        "and trashed = false"
                    ),
                    spaces="drive",
                    fields=(
                        "nextPageToken,"
                        "files(id,name,mimeType,size,webViewLink)"
                    ),
                    pageSize=1000,
                    pageToken=page_token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                ).execute()

                for row in response.get("files", []):
                    row_id = str(row.get("id") or "").strip()
                    row_name = str(row.get("name") or "").strip()
                    row_mime = str(row.get("mimeType") or "").strip()

                    if not row_id:
                        continue

                    if row_mime == folder_mime:
                        if recursive and row_id not in seen_folders:
                            seen_folders.add(row_id)
                            queue.append(row_id)
                        continue

                    if mime_type and row_mime != mime_type:
                        continue

                    found.append(
                        StoredDocumentFile(
                            provider="google_drive_oauth",
                            file_id=row_id,
                            file_name=row_name,
                            mime_type=row_mime,
                            size_bytes=int(row.get("size") or 0),
                            web_view_link=row.get("webViewLink"),
                        )
                    )

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

        return tuple(found)

    def download(
        self,
        file_id: str,
    ) -> bytes:
        """Download one file through the authenticated Drive service."""
        from io import BytesIO

        from googleapiclient.discovery import build
        from googleapiclient.http import (
            MediaIoBaseDownload,
        )

        normalized_id = str(
            file_id
        ).strip()

        if not normalized_id:
            raise ValueError(
                "file_id must not be empty"
            )

        service = getattr(
            self,
            "_service",
            None,
        )

        if service is None:
            service = getattr(
                self,
                "service",
                None,
            )

        if service is None:
            credentials = getattr(
                self,
                "_credentials",
                None,
            )

            if credentials is None:
                credentials = getattr(
                    self,
                    "credentials",
                    None,
                )

            if credentials is None:
                raise RuntimeError(
                    "Google Drive credentials "
                    "are not available."
                )

            service = build(
                "drive",
                "v3",
                credentials=credentials,
                cache_discovery=False,
            )

        request = (
            service.files()
            .get_media(
                fileId=normalized_id
            )
        )

        stream = BytesIO()

        downloader = MediaIoBaseDownload(
            stream,
            request,
        )

        done = False

        while not done:
            _, done = (
                downloader.next_chunk()
            )

        return stream.getvalue()
