from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from ai_kernel.teaching_livekit_local_agent import (  # noqa: E402
    LocalLiveKitAgentConfig,
    LocalLiveKitAgentSession,
)
from ai_kernel.teaching_realtime_agent import (  # noqa: E402
    AIKernelStreamingBrain,
    RealtimeVoiceAgent,
    RealtimeVoiceAgentConfig,
    ZeroTTSStreamingAdapter,
)


def _float32le_to_int16le(data: bytes) -> bytes:
    """Convert ZeroTTS float32 PCM to LiveKit int16 PCM."""
    import numpy as np

    samples = np.frombuffer(data, dtype=np.float32)
    samples = np.clip(samples, -1.0, 1.0)
    return (samples * 32767.0).astype(np.int16).tobytes()


def build_runtime(on_audio_chunk=None) -> LocalLiveKitAgentSession:
    brain_config = RealtimeVoiceAgentConfig(
        ollama_base_url=os.environ.get("MATHTEACHER_OLLAMA_URL", "http://127.0.0.1:11434"),
        ollama_model=os.environ.get("MATHTEACHER_AI_LOCAL_LLM_MODEL", os.environ.get("MATH_TEACHER_AI_MODEL", "qwen3:0.6b")),
    )
    brain = AIKernelStreamingBrain()
    tts = ZeroTTSStreamingAdapter(
        model_name=os.environ.get("MATHTEACHER_LOCAL_TTS_MODEL", "zeroweight-ai/ZeroTTS"),
        voice=os.environ.get("MATHTEACHER_LOCAL_TTS_VOICE", "maichi"),
    )
    agent = RealtimeVoiceAgent(brain=brain, tts=tts, config=brain_config)
    return LocalLiveKitAgentSession(
        agent=agent,
        config=LocalLiveKitAgentConfig(
            stt_model=os.environ.get("MATHTEACHER_LOCAL_STT_MODEL", "small"),
            stt_device=os.environ.get("MATHTEACHER_LOCAL_STT_DEVICE", "auto"),
            stt_compute_type=os.environ.get("MATHTEACHER_LOCAL_STT_COMPUTE_TYPE", "int8"),
        ),
        on_audio_chunk=on_audio_chunk,
    )


def run_livekit_worker() -> None:
    """Run a self-hosted LiveKit participant using local STT/LLM/TTS."""
    try:
        from livekit import rtc
        from livekit.agents import AgentServer, AutoSubscribe, JobContext, cli
    except ImportError as exc:
        raise RuntimeError(
            "ChÆ°a cÃ i livekit-agents/livekit-rtc. HÃ£y cÃ i requirements-optional-teaching-agent.txt."
        ) from exc

    server = AgentServer(num_idle_processes=1)

    @server.rtc_session(agent_name=os.environ.get("MATHTEACHER_LIVEKIT_AGENT_NAME", "mathteacher-ta"))
    async def entrypoint(ctx: JobContext) -> None:
        print("DIAG_JOB_ENTRYPOINT_START", flush=True)
        room = ctx.room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        print(
            "DIAG_JOB_CONNECTED",
            f"room={room.name}",
            flush=True,
        )
        audio_source = rtc.AudioSource(48_000, 1)
        audio_track = rtc.LocalAudioTrack.create_audio_track("mathteacher-ai-voice", audio_source)
        publish_options = rtc.TrackPublishOptions()
        publish_options.source = rtc.TrackSource.SOURCE_MICROPHONE
        await room.local_participant.publish_track(audio_track, publish_options)

        async def publish_audio(chunk: bytes) -> None:
            chunk = _float32le_to_int16le(chunk)
            frame = rtc.AudioFrame(
                data=chunk,
                sample_rate=48_000,
                num_channels=1,
                samples_per_channel=len(chunk) // 2,
            )
            await audio_source.capture_frame(frame)

        runtime = build_runtime(on_audio_chunk=publish_audio)

        async def consume_track(track) -> None:
            stream = rtc.AudioStream(
                track,
                sample_rate=16_000,
                num_channels=1,
                frame_size_ms=30,
            )
            try:
                async for event in stream:
                    await runtime.consume_frame(event.frame.data.tobytes(), block_ms=30)
            finally:
                await stream.aclose()
                await runtime.flush()

        @room.on("track_published")
        def on_track_published(publication, participant) -> None:
            print(
                "DIAG_TRACK_PUBLISHED",
                f"kind={publication.kind}",
                f"participant={participant.identity}",
                f"track_sid={publication.sid}",
                flush=True,
            )
            if publication.kind == rtc.TrackKind.KIND_AUDIO:
                publication.set_subscribed(True)
        @room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant) -> None:
            print(
                "DIAG_TRACK_SUBSCRIBED",
                f"kind={track.kind}",
                f"participant={participant.identity}",
                f"track_sid={publication.sid}",
                flush=True,
            )
            del publication, participant
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                asyncio.create_task(consume_track(track))

        await ctx.wait_for_participant()

        for participant in room.remote_participants.values():
            for publication in participant.track_publications.values():
                if publication.kind == rtc.TrackKind.KIND_AUDIO and publication.track is not None:
                    publication.set_subscribed(True)

    cli.run_app(server)


if __name__ == "__main__":
    run_livekit_worker()
