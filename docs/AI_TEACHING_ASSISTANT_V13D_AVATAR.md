# MathTeacher AI — V13D Avatar + Lip-sync

V13D adds a replaceable presentation layer for the AI Teaching Assistant.

## Design
- `AvatarProfile`: identity/configuration of an avatar.
- `AvatarState`: idle/listening/thinking/speaking/interrupted/stopped.
- `AvatarRenderer`: replaceable renderer contract.
- `LipSyncProvider`: replaceable audio-driven lip-sync contract.
- `TeachingAvatarSession`: maps voice states to avatar frames.

The avatar layer is presentation-only. It cannot execute classroom tools,
modify lessons, change AI governance, or bypass teacher/admin control.

## Engines
The first concrete renderer is dependency-free `StaticAvatarRenderer` so the
UI can be built before a heavy video engine is installed.

`CommandLipSyncProvider` can wrap a local engine such as MuseTalk or another
locally hosted avatar/lip-sync engine. The engine is intentionally not hard-
coded into the Kernel.

## Production/licensing note
MuseTalk's official repository states that its code and trained models are
MIT/commercially usable, while dependencies such as Whisper, ft-mse-vae,
DWPose and S3FD must follow their own licenses. See the upstream repository
before commercial packaging.

LivePortrait's code is MIT, but its repository states that bundled InsightFace
models are non-commercial research-only; commercial deployment therefore
requires replacing that detector/model component or otherwise obtaining the
proper rights.

## Next
V13E will add a realtime WebSocket/WebRTC presentation adapter, followed by a
browser avatar surface and integration with the Teaching Assistant Voice
Session. Classroom actions remain behind the existing Kernel policy boundary.
