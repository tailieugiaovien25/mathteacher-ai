# MathTeacher AI – V13G LiveKit/WebRTC

V13G adds optional self-hosted LiveKit/WebRTC transport for the AI Teaching Assistant.
It is additive: local-browser audio remains available without LiveKit.

Included:
- `src/ai_kernel/teaching_livekit.py` – short-lived backend token + browser client contract
- `src/ai_kernel/teaching_realtime_transport.py` – LiveKit transport config/status
- `src/portal_v2/ui/teaching_assistant_avatar_surface_streamlit.py` – optional LiveKit panel
- `src/tests/test_teaching_livekit_v13g.py` – focused contract tests
- `requirements-optional-livekit.txt`
- `docs/AI_TEACHING_ASSISTANT_V13G_LIVEKIT.md`

Enable only in an environment where a self-hosted LiveKit server is available.
Do not place `LIVEKIT_API_SECRET` in browser code.
