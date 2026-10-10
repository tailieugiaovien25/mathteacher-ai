# AI Trợ giảng – LiveKit self-host (optional)

MathTeacher AI keeps LiveKit as an optional realtime media transport. The Teaching Assistant contracts do not depend on the LiveKit SDK.

For local development, LiveKit's self-hosted WebSocket endpoint can be `ws://localhost:7880`. In production, LiveKit recommends TLS termination, a public domain, and the required WebRTC/TURN ports. See the official self-hosting documentation before exposing it publicly.

Recommended environment variables:

```text
MATHTEACHER_LIVEKIT_URL=ws://127.0.0.1:7880
MATHTEACHER_LIVEKIT_ROOM=mathteacher-ai-teaching-assistant
LIVEKIT_API_KEY=<keep outside source>
LIVEKIT_API_SECRET=<keep outside source>
```

The current V13F surface does not require LiveKit to run. It uses browser-local audio + WebAudio lip-sync by default. LiveKit should be enabled only after the self-hosted server and token service are configured.
