from pathlib import Path
import importlib.util
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_kernel.teaching_livekit import build_livekit_client_html
from ai_kernel.teaching_realtime_transport import LiveKitTransportConfig, build_livekit_room_descriptor


def _load_ui():
    path = ROOT / "portal_v2" / "ui" / "teaching_assistant_avatar_surface_streamlit.py"
    spec = importlib.util.spec_from_file_location("ta_surface_v13g", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_livekit_descriptor_and_browser_bridge():
    cfg = LiveKitTransportConfig(url="ws://127.0.0.1:7880", room_name="ta-v13g")
    descriptor = build_livekit_room_descriptor(cfg, identity_suffix="teacher")
    assert descriptor.identity == "mathteacher-ta-teacher"
    html = build_livekit_client_html(
        server_url=cfg.url,
        token="short-lived-token",
        display_name="Trợ giảng Toán",
        client_js_url="/assets/livekit-client.esm.mjs",
    )
    assert "Room" in html
    assert "setMicrophoneEnabled" in html
    assert "short-lived-token" in html
    assert "/assets/livekit-client.esm.mjs" in html


def test_livekit_html_serializes_script_values_safely():
    html = build_livekit_client_html(
        server_url="wss://livekit.example.test';alert(1);//",
        token="token</script><script>alert(1)</script>",
        client_js_url="https://cdn.example.test/sdk.mjs?value=</script>",
    )
    assert "const url = \"wss://livekit.example.test';alert(1);//\";" in html
    assert "token</script>" not in html
    assert "\\u003c/script\\u003e" in html
    assert 'import * as LivekitClient from "https://cdn.example.test/sdk.mjs?value=\\u003c/script\\u003e";' in html


def test_livekit_transport_stays_optional():
    cfg = LiveKitTransportConfig(url="ws://127.0.0.1:7880", room_name="ta-v13g")
    assert cfg.publish_audio is True
    assert cfg.publish_video is True
    assert cfg.subscribe_audio is True
    assert cfg.subscribe_video is True


def test_ui_exports_livekit_panel():
    module = _load_ui()
    assert callable(module.render_livekit_realtime_panel)




def test_token_generation_keeps_secret_server_side(monkeypatch):
    import os
    from ai_kernel.teaching_livekit import generate_livekit_access_token

    grants_seen = []
    credentials_seen = []

    class FakeGrants:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            grants_seen.append(kwargs)

    class FakeToken:
        def __init__(self, key, secret):
            self.key = key
            self.secret = secret
            credentials_seen.append((key, secret))
            self.calls = []
        def with_identity(self, value): self.calls.append(("identity", value)); return self
        def with_name(self, value): self.calls.append(("name", value)); return self
        def with_grants(self, value): self.calls.append(("grants", value.kwargs)); return self
        def with_ttl(self, value): self.calls.append(("ttl", int(value.total_seconds()))); return self
        def to_jwt(self): return "JWT-TEST"

    fake_api = types.SimpleNamespace(
        VideoGrants=FakeGrants,
        AccessToken=FakeToken,
    )
    fake_livekit = types.SimpleNamespace(api=fake_api)
    monkeypatch.setitem(sys.modules, "livekit", fake_livekit)
    monkeypatch.setenv("LIVEKIT_API_KEY", "devkey")
    monkeypatch.setenv("LIVEKIT_API_SECRET", "server-only-secret")

    result = generate_livekit_access_token(room_name="room", identity="teacher", ttl_seconds=120)
    assert result.token == "JWT-TEST"
    assert result.ttl_seconds == 120
    assert grants_seen[-1]["can_publish"] is True
    assert grants_seen[-1]["can_publish_sources"] == ["microphone"]
    assert grants_seen[-1]["can_publish_data"] is False

    generate_livekit_access_token(
        room_name="room", identity="teacher",
        can_publish_audio=True, can_publish_video=True,
    )
    assert grants_seen[-1]["can_publish_sources"] == ["microphone", "camera"]

    generate_livekit_access_token(
        room_name="room", identity="observer",
        can_publish_audio=False, can_publish_video=False,
    )
    assert grants_seen[-1]["can_publish"] is False
    assert grants_seen[-1]["can_publish_sources"] == []

    monkeypatch.setenv("CUSTOM_LIVEKIT_KEY_NAME", "custom-key-value")
    monkeypatch.setenv("CUSTOM_LIVEKIT_SECRET_NAME", "custom-secret-value")
    generate_livekit_access_token(
        room_name="room", identity="teacher",
        api_key_env="CUSTOM_LIVEKIT_KEY_NAME",
        api_secret_env="CUSTOM_LIVEKIT_SECRET_NAME",
    )
    assert credentials_seen[-1] == ("custom-key-value", "custom-secret-value")

if __name__ == "__main__":
    test_livekit_descriptor_and_browser_bridge()
    test_livekit_transport_stays_optional()
    test_ui_exports_livekit_panel()
    print("4/4 PASS")
