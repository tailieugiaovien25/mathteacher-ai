# MathTeacher AI Chief Engineer Agent — V1

## Scope

V1 reuses the existing AI Kernel components:
- SafeAgentPlanner and SafeAgentRuntime
- AutonomousOrchestrator
- The existing system_admin.observer skill
- Persistent approval queue and run-history stores

The first release is intentionally observe-and-test only. Its allow-list contains:
- Git branch/worktree status and diff statistics.
- A bounded repository inventory that skips secret/configuration folders, virtual environments, caches, and dependency directories.
- Reading selected Python, TOML, Markdown, and YAML files inside the repository with size limits and credential scrubbing.
- Running at most five explicitly selected test_*.py files beneath src/tests/ using a fixed Python pytest argument vector and a timeout. Arbitrary shell commands are not accepted.

V1 cannot edit or delete source files, create commits, push, merge, deploy, inspect environment variables, or read secret/configuration files. A future maintenance release must add backup/patch tooling as distinct MUTATING tools and retain the ADMIN approval boundary.

## Run on Windows PowerShell

From the project root, activate the existing virtual environment and expose src:

    .\.venv\Scripts\Activate.ps1
    $env:PYTHONPATH = "$PWD\src"
    python -m ai_kernel.chief_engineer_agent --repo-root "$PWD" --objective "Kiểm tra trạng thái Git, kiểm kê mã nguồn và đánh giá các kiểm thử liên quan"

The AI Kernel uses the provider/model configuration already configured for the project. Do not paste API keys into command arguments or reports.

To request a narrow test run, state exact repository test paths in the objective, for example:
src/tests/test_ai_agent_runtime_v8.py

The model planner chooses only from the fixed tool allow-list. The deterministic planner/runtime rejects unknown tools and bounds the number of steps.

## Local state and safety

Run history and approval metadata are stored below:
.mathteacher_ai/chief_engineer/

The folder is excluded from inventory. No source mutation occurs in V1. A run stops when the model returns an empty plan, reaches the configured cycle limit, or encounters a blocked/failed step.
