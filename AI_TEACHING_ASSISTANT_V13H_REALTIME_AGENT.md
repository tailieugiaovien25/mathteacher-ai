# MathTeacher AI – V13H Realtime Voice Agent

V13H adds a provider-agnostic realtime voice controller with explicit barge-in.

## Local-first stack

- LLM: Ollama / Qwen3 (`ollama:qwen3:8b` by default)
- STT: faster-whisper local adapter
- TTS: ZeroTTS local Vietnamese streaming adapter
- Transport: optional self-hosted LiveKit

The LiveKit Agents framework can host Python realtime agents in LiveKit rooms and
handles realtime media, turn handling and interruptions. MathTeacher AI keeps its
own Kernel, Teaching Assistant Policy and Classroom Action boundary around it.

## Safety boundary

This layer produces conversation and audio only. It does not execute classroom
tools directly. Any slide/stage/timer/quiz operation must still pass through the
Teaching Assistant Controller, Safe Agent Runtime, and the existing policy /
approval gates.

## Barge-in

When a teacher starts speaking while the assistant is producing audio, the active
response task is cancelled and the agent enters `interrupted`. The transport layer
must then resume listening for the new teacher turn.

## Runtime prerequisites

Install optional dependencies from `requirements-optional-teaching-agent.txt`.
The first local TTS/LLM model use may download/caches model weights depending on
local setup. For a fully offline deployment, pre-cache the models first.

## What is verified here

The controller, streaming contracts, Ollama JSONL parsing, cancellation semantics,
and LiveKit runtime descriptor are tested without requiring LiveKit Server, Ollama,
or model weights to be installed in the development environment.
