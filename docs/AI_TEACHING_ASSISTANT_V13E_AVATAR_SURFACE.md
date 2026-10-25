# MathTeacher AI — V13E Avatar Surface

V13E adds the first teacher-facing browser surface for the AI Teaching Assistant.

## What is included

- Teacher navigation entry: **AI Trợ giảng**.
- Browser-facing avatar surface using `streamlit.components.v1.html` with the local SVG avatar.
- Explicit avatar states: `idle`, `listening`, `thinking`, `speaking`, `interrupted`, `stopped`.
- Browser microphone input via `st.audio_input` when the installed Streamlit version supports it.
- Optional local processing path:
  - STT: `FasterWhisperSTT`
  - Brain: `OllamaTeachingBrain` (default `qwen3:8b`)
  - Optional TTS: `CommandTTSAdapter` via `MATHTEACHER_TTS_COMMAND`
- Teacher override and stop controls.

## Safety boundary

The avatar/voice surface is presentation and conversation only. It does not
execute classroom tools. Any future command such as opening a slide,
starting a timer, or moving to another activity must pass through the existing
TeachingAssistantController / Safe Agent / Approval policy chain.

## Local runtime

Environment variables supported by the surface:

- `MATHTEACHER_OLLAMA_MODEL` (default `qwen3:8b`)
- `MATHTEACHER_STT_MODEL` (default `small`)
- `MATHTEACHER_STT_DEVICE` (default `cpu`)
- `MATHTEACHER_STT_COMPUTE` (default `int8`)
- `MATHTEACHER_TTS_COMMAND` (optional command template with `{text}` and `{output}`)

V13E deliberately does not hard-code a TTS engine or a heavy avatar/lip-sync
engine. V13D's `TeachingAvatarSession` remains the replaceable presentation
contract for MuseTalk, LivePortrait, OpenAvatarChat, or another local engine.

## Current scope

This is a **browser-facing turn-based surface**, not yet a full WebRTC/WebSocket
continuous streaming implementation. The realtime turn/session engine remains
in V13C and is reusable by a later realtime transport adapter.
