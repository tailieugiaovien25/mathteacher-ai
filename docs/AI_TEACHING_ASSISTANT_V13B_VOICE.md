# MathTeacher AI V13B — Teaching Assistant local voice bridge

V13B adds a replaceable local voice stack around the V13 Teaching Assistant Core.

## Components

- `OllamaTeachingBrain`: local HTTP adapter, default model `qwen3:8b`.
- `FasterWhisperSTT`: optional local speech-to-text adapter with lazy dependency loading.
- `CommandTTSAdapter`: generic local TTS adapter so a Vietnamese TTS engine can be swapped later without Kernel changes.
- `TeachingAssistantVoiceBridge`: STT -> local brain -> optional TTS. It does not execute classroom actions.

## First prototype

```text
Audio file / future microphone
        ↓
FasterWhisperSTT
        ↓
TeachingAssistantVoiceBridge
        ↓
OllamaTeachingBrain (qwen3:8b)
        ↓
Vietnamese response text
        ↓
Optional TTS adapter
```

The bridge deliberately does not call classroom tools. Classroom actions must continue through TeachingAssistantController, Safe Agent Runtime and Approval Center.

## Local run

Ollama must be running locally and the chosen model must exist locally. The CLI is intentionally file-based first so audio can be tested without introducing microphone/WebRTC dependencies.

```bash
python -m ai_kernel.voice_cli path/to/audio.wav --model qwen3:8b
```

The `faster-whisper` dependency is optional until voice input is enabled.

## Replacement rule

STT, LLM and TTS are adapters. They can be replaced independently. The Teaching Assistant Core and classroom governance do not depend on a particular provider.
