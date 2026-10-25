# MathTeacher AI — Open-Source AI Stack V2

## Mục tiêu

MathTeacher AI sử dụng kiến trúc local-first/self-hosted. Nghiệp vụ không phụ thuộc trực tiếp vào model hoặc runtime.

## Lớp model

- Qwen3: mặc định cho tiếng Việt, toán, coding, agent và tác vụ chung.
- DeepSeek-R1: chuyên reasoning/toán khi ADMIN bật profile phù hợp.
- Mistral Small 3.1: nhánh tài liệu/vision khi hạ tầng đủ mạnh.

## Lớp runtime

- Ollama: local/dev/máy giáo viên.
- vLLM: server production/GPU nhiều phiên.
- llama.cpp: offline/CPU/GGUF.

## Lớp orchestration

AI Kernel của MathTeacher AI là contract lõi. Agent/RAG/orchestration chỉ là plugin/layer phía trên. Không cho framework bên ngoài nắm quyền governance.

## Quyền ADMIN

ADMIN quản lý model profile, provider, capability, feature flag, policy và audit. USER chỉ gọi capability đã được cấp.

## Chuẩn hóa giáo án

AI là advisory inspector. Bộ transformer deterministic thực hiện thay đổi DOCX. Independent audit xác nhận before/after. Release chỉ được phép khi compliance gate cho PASS/REVIEW theo policy.
