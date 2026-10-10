# MathTeacher AI – V13G LiveKit/WebRTC

V13G adds an optional self-hosted LiveKit transport for the AI Teaching Assistant.
It does not replace the existing local-browser audio surface and it does not grant
classroom-control permissions to the media layer.

## Architecture

```text
Browser microphone
    -> LiveKit client
    -> self-hosted LiveKit server
    -> Teaching Assistant session / agent (future V13H+)
    -> audio reply
    -> browser / avatar
```

The browser receives only a short-lived participant token. `LIVEKIT_API_SECRET`
remains on the MathTeacher AI backend.

## Development

1. Install the optional Python package:

```bash
pip install -r requirements-optional-livekit.txt
```

2. Start a local LiveKit server. The official development mode is:

```bash
livekit-server --dev
```

This uses the documented development credentials `devkey` / `secret` and listens
locally by default.

3. Set backend environment variables:

```text
LIVEKIT_URL=ws://127.0.0.1:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
MATHTEACHER_LIVEKIT_URL=ws://127.0.0.1:7880
MATHTEACHER_ENABLE_LIVEKIT=true
```

4. Provide a locally served LiveKit JavaScript client bundle with:

```text
MATHTEACHER_LIVEKIT_CLIENT_JS_URL=/assets/livekit-client.esm.mjs
```

For a development-only external fallback, the client adapter can use the default
CDN URL. Production deployments should serve the pinned JS bundle from the same
MathTeacher AI origin so the realtime stack remains self-hosted.

## Security boundary

- The API secret is backend-only.
- Client tokens are short-lived (maximum 15 minutes from MathTeacher AI UI).
- The token scope is limited to one room and participant identity.
- Media transport has no authority to mutate lessons, slides, classroom state, or
  governance.
- Classroom actions remain behind AI Kernel / Safe Agent / Approval controls.

## V13G scope

V13G establishes real LiveKit token generation and browser-room connection scaffolding.
It does not yet claim a full live voice AI agent: STT/LLM/TTS streaming and barge-in
remain the next layer. The current local voice bridge continues to work independently.
