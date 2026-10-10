# MathTeacher AI V13 — AI Teaching Assistant Core

V13 is the first contract layer for the avatar teaching assistant. It does **not** yet bundle a heavy avatar/runtime dependency. The goal is to make the assistant replaceable at the component level while keeping MathTeacher AI Kernel and classroom governance stable.

## Core contract

`TeachingAssistantController` sits between a future STT/LLM/TTS/avatar front end and the existing Safe Agent Runtime.

- Persona: `TeachingPersonaProfile`
- Classroom policy: `TeachingAssistantPolicy`
- Proposed actions: `TeachingAssistantAction`
- Session control: `TeachingAssistantSession`
- Modes: co-teacher, MC, technical operator, activity facilitator

Teacher override is a first-class state. When the teacher takes control, the assistant proposes no classroom actions.

## First local prototype stack

1. Local LLM: Qwen3 8B via Ollama. Ollama currently exposes a local HTTP API for `qwen3:8b`.
2. Vietnamese STT: PhoWhisper-small is a Vietnamese Whisper fine-tune; the current Hugging Face model card lists BSD-3-Clause.
3. Vietnamese TTS: use a replaceable adapter. Kokoro-82M is Apache-2.0 but its official model card is English-only, so it is not the first Vietnamese voice choice. Vietnamese TTS candidates must be checked per-model for commercial licensing before production use.
4. Avatar/realtime: OpenAvatarChat is a useful reference because it explicitly separates ASR, LLM, TTS and avatar components and supports interruptible realtime interaction. LiveKit Agents is another candidate for realtime voice-agent transport and is Apache-2.0; the LiveKit server can be self-hosted.
5. Classroom actions stay inside MathTeacher AI's existing tool/approval boundary.

## Important license note

OpenMAIC has materially changed over time. The official repository currently reports MIT licensing for the 2026-08 release line, while certain bundled third-party packages retain their own licenses. Do not copy bundled components into MathTeacher AI without recording their individual license terms.

## V13 test target

The initial implementation must prove:

- persona supports MC/co-teacher/technical-facilitator modes;
- read-only classroom actions can be proposed;
- mutating actions require explicit confirmation;
- teacher can interrupt/take control immediately;
- stop state is durable within the session;
- no STT/TTS/avatar dependency is required by the Kernel.
