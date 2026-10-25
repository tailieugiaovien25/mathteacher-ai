# MathTeacher AI – V13F

V13F adds two replaceable realtime surfaces:

1. Local browser lip-sync: the avatar SVG mouth is animated from the returned WAV using WebAudio `AnalyserNode`. It requires no external avatar engine or GPU.
2. Optional self-hosted LiveKit transport descriptor: the app can expose a LiveKit room configuration without making the AI Kernel depend on the LiveKit SDK. LiveKit becomes an optional media transport layer.

The avatar surface remains presentation-only. Classroom actions continue to pass through the Teaching Assistant Controller / Safe Agent / Approval boundaries.

## Optional LiveKit

Set `MATHTEACHER_LIVEKIT_URL` and `MATHTEACHER_LIVEKIT_ROOM` for a self-hosted room. Install the LiveKit SDK separately only when the project actually enables the transport. API credentials are read from the environment and are never stored in source.

The current MathTeacher AI default remains local browser audio + avatar.
