# MathTeacher AI V13C — Realtime Voice

V13C moves the Teaching Assistant from file-audio processing to a local microphone,
turn detection, and turn-based realtime conversation.

## Flow

`Microphone -> RMS VAD -> WAV turn -> existing STT -> local Ollama brain -> optional TTS`

The microphone and realtime session do **not** execute classroom actions. Any classroom
intent must continue through the existing Teaching Assistant Controller / Safe Agent /
Approval stack.

## Local dependencies

The runtime keeps imports lazy so the rest of MathTeacher AI does not require microphone
packages. To enable the local microphone prototype, install `sounddevice` in the project's
Python environment. The existing V13B STT adapter can use `faster-whisper` when installed.

## Control and safety

- Teacher interruption remains outside the audio loop and can stop the session immediately.
- `MUTATING` and `GOVERNANCE` actions are not executed by voice code.
- Audio turn files are local temporary artifacts by default and can be redirected with
  `RealtimeVoiceConfig.output_dir`.
- Model/runtime remain replaceable through the existing TeachingVoice adapters.

## Prototype limitations

V13C is turn-based rather than full-duplex streaming. It uses simple RMS energy detection
for utterance segmentation. A later realtime transport can replace the microphone adapter
without changing the Teaching Assistant Core contract.
