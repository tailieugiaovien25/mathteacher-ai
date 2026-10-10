from __future__ import annotations

import argparse
from pathlib import Path

from .teaching_voice import FasterWhisperSTT, OllamaTeachingBrain, TeachingAssistantVoiceBridge, TeachingVoiceConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="MathTeacher AI - local Teaching Assistant voice prototype")
    parser.add_argument("audio", type=Path, help="File audio đầu vào (wav/mp3/...).")
    parser.add_argument("--model", default="qwen3:8b", help="Ollama model local")
    parser.add_argument("--ollama", default="http://127.0.0.1:11434", help="Ollama base URL")
    parser.add_argument("--stt-model", default="small", help="faster-whisper model size")
    args = parser.parse_args()

    config = TeachingVoiceConfig(ollama_model=args.model, ollama_base_url=args.ollama)
    brain = OllamaTeachingBrain(config)
    if not brain.health():
        raise SystemExit("Ollama local chưa sẵn sàng. Hãy bật Ollama và bảo đảm model đã được tải.")
    bridge = TeachingAssistantVoiceBridge(
        stt=FasterWhisperSTT(model_size=args.stt_model),
        brain=brain,
        config=config,
    )
    turn = bridge.process_audio(args.audio)
    print(f"Bạn: {turn.transcript.text}")
    print(f"Trợ giảng: {turn.response_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
