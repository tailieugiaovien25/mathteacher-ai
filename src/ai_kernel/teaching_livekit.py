from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import html
import json
import os
from typing import Any


@dataclass(frozen=True)
class LiveKitParticipantToken:
    token: str
    room_name: str
    identity: str
    ttl_seconds: int


def generate_livekit_access_token(
    *,
    room_name: str,
    identity: str,
    name: str | None = None,
    ttl_seconds: int = 900,
    can_publish_audio: bool = True,
    can_publish_video: bool = False,
    can_subscribe_audio: bool = True,
    can_subscribe_video: bool = True,
    api_key_env: str = "LIVEKIT_API_KEY",
    api_secret_env: str = "LIVEKIT_API_SECRET",
) -> LiveKitParticipantToken:
    """Generate a short-lived token; API secret remains server-side.

    Requires the optional `livekit-api` package. The function deliberately imports
    it lazily so MathTeacher AI remains runnable without LiveKit installed.
    """
    if not room_name.strip() or not identity.strip():
        raise ValueError("room_name và identity không được để trống")
    ttl = max(60, min(int(ttl_seconds), 3600))
    api_key = os.environ.get(str(api_key_env), "").strip()
    api_secret = os.environ.get(str(api_secret_env), "").strip()
    if not api_key or not api_secret:
        raise RuntimeError("Thiếu LIVEKIT_API_KEY/LIVEKIT_API_SECRET ở backend.")

    try:
        from livekit import api  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Chưa cài livekit-api; hãy cài trong môi trường server.") from exc

    publish_sources = []
    if can_publish_audio:
        publish_sources.append("microphone")
    if can_publish_video:
        publish_sources.append("camera")

    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=bool(publish_sources),
        can_publish_sources=publish_sources,
        can_subscribe=bool(can_subscribe_audio or can_subscribe_video),
    )

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(name or identity)
        .with_grants(grants)
        .with_ttl(dt.timedelta(seconds=ttl))
        .to_jwt()
    )
    return LiveKitParticipantToken(token, room_name, identity, ttl)


def _script_json(value: str) -> str:
    """Serialize data as a JavaScript string without permitting script-tag breakout."""
    return (
        json.dumps(str(value), ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def build_livekit_client_html(
    *,
    server_url: str,
    token: str,
    display_name: str = "AI Trợ giảng",
    client_js_url: str | None = None,
) -> str:
    """Build a small browser client for a self-hosted LiveKit room.

    The LiveKit client SDK URL is configurable so deployments can serve a local
    bundled ESM build. A CDN URL is only a development fallback.
    """
    js_url = (client_js_url or os.environ.get("MATHTEACHER_LIVEKIT_CLIENT_JS_URL", "")).strip()
    safe_name = html.escape(display_name, quote=True)
    if not js_url:
        js_url = "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs"
    script_server_url = _script_json(server_url)
    script_token = _script_json(token)
    script_js_url = _script_json(js_url)
    return f"""
<div class='lk-ta' style='font-family:Arial,sans-serif;padding:10px;border:1px solid #d7dee8;border-radius:12px'>
  <div style='font-weight:700'>{safe_name}</div>
  <div id='lk-status' style='margin:6px 0'>Đang chuẩn bị kết nối…</div>
  <button id='lk-connect' type='button'>🔊 Kết nối realtime</button>
  <button id='lk-stop' type='button' style='margin-left:6px'>⏹ Ngắt</button>
</div>
<script type='module'>
import * as LivekitClient from {script_js_url};
const url = {script_server_url};
const token = {script_token};
const status = document.getElementById('lk-status');
let room = null;
function setStatus(t) {{ if (status) status.textContent = t; }}
async function connect() {{
  try {{
    if (room) await room.disconnect();
    room = new LivekitClient.Room();
    room.on(LivekitClient.RoomEvent.Connected, () => setStatus('Đã kết nối LiveKit.'));
    room.on(LivekitClient.RoomEvent.Disconnected, () => setStatus('Đã ngắt LiveKit.'));
    room.on(LivekitClient.RoomEvent.ConnectionStateChanged, state => setStatus('Trạng thái: ' + state));
    await room.connect(url, token);
    await room.localParticipant.setMicrophoneEnabled(true);
    setStatus('Đã kết nối và bật microphone.');
  }} catch (err) {{
    setStatus('Lỗi LiveKit: ' + (err?.message || err));
  }}
}}
async function stop() {{
  try {{ if (room) await room.disconnect(); }} finally {{ room = null; setStatus('Đã ngắt.'); }}
}}
document.getElementById('lk-connect')?.addEventListener('click', connect);
document.getElementById('lk-stop')?.addEventListener('click', stop);
</script>
"""


__all__ = ["LiveKitParticipantToken", "generate_livekit_access_token", "build_livekit_client_html"]
