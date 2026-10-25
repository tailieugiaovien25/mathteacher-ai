# MathTeacher AI V13F – Teaching Assistant Realtime Avatar

This patch adds:

- dependency-free browser lip-sync for the existing SVG teaching avatar;
- audio data embedding in the avatar surface;
- optional LiveKit self-hosted transport configuration;
- deterministic lip-sync cue generation from PCM WAV;
- tests and setup notes.

The patch is incremental: apply it on top of the MathTeacher AI source that already contains V13E.

It does not install heavy avatar engines or LiveKit automatically.
