from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import html
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
) -> LiveKitParticipantToken:
    """Generate a short-lived token; API secret remains server-side.

    Requires the optional `livekit-api` package. The function deliberately imports
    it lazily so MathTeacher AI remains runnable without LiveKit installed.
    """
    if not room_name.strip() or not identity.strip():
        raise ValueError("room_name và identity không được để trống")
    ttl = max(60, min(int(ttl_seconds), 3600))
    api_key = os.environ.get("LIVEKIT_API_KEY", "").strip()
    api_secret = os.environ.get("LIVEKIT_API_SECRET", "").strip()
    if not api_key or not api_secret:
        raise RuntimeError("Thiếu LIVEKIT_API_KEY/LIVEKIT_API_SECRET ở backend.")

    try:
        from livekit import api  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Chưa cài livekit-api; hãy cài trong môi trường server.") from exc

    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=bool(can_publish_audio or can_publish_video),
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
    safe_url = html.escape(server_url, quote=True)
    safe_token = html.escape(token, quote=True)
    safe_name = html.escape(display_name, quote=True)
    if not js_url:
        js_url = "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs"
    safe_js = html.escape(js_url, quote=True)
    return f"""
<div class='lk-ta' style='font-family:Arial,sans-serif;padding:10px;border:1px solid #d7dee8;border-radius:12px'>
  <div style='font-weight:700'>{safe_name}</div>
  <div id='lk-status' style='margin:6px 0'>Đang chuẩn bị kết nối…</div>
  <button id='lk-connect' type='button'>🔊 Kết nối realtime</button>
  <button id='lk-stop' type='button' style='margin-left:6px'>⏹ Ngắt</button>
</div>
<script type='module'>
import * as LivekitClient from '{safe_js}';
const url = {server_url!r};
const token = {token!r};
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
