# MathTeacher AI Chief Engineer Agent — V2

## Architecture

The Agent reuses the existing AI Kernel:
- SafeAgentPlanner and SafeAgentRuntime
- AutonomousOrchestrator
- system_admin.observer for read-only inspection
- system_admin.maintenance for the approval-gated source patch tool
- Persistent approval queue and run-history stores

## Read-only inspection

The observer allow-list contains:
- Git branch/worktree status and diff statistics.
- Bounded repository inventory; skips secret/configuration folders, virtual environments, caches, dependencies and local AI state.
- Reading selected Python, TOML, Markdown and YAML files inside the repository with size limits and credential scrubbing.
- Running at most five explicitly selected test_*.py files beneath src/tests/ using a fixed Python pytest argument vector and a timeout. Arbitrary shell commands are not accepted.

Run from the project root in Windows PowerShell:

    .\.venv\Scripts\Activate.ps1
    $env:PYTHONPATH = "$PWD\src"
    python -m ai_kernel.chief_engineer_agent --repo-root "$PWD" --objective "Kiểm tra trạng thái Git, kiểm kê mã nguồn và kiểm thử liên quan"

The Agent uses the AI provider/model configured for the existing AI Kernel. Do not paste API keys into command arguments, patch proposals, or reports.

## V2 source patch flow

V2 can apply a proposed patch only when all checks below pass:
1. The proposal targets 1–5 existing Python files under src/; creating, deleting, renaming, or modifying files outside src/ is not supported.
2. Every file includes its expected SHA-256. A changed source file invalidates the proposal.
3. New Python content must parse successfully and must not contain recognized credential patterns.
4. The proposal is stored under .mathteacher_ai/chief_engineer/patches/ and a pending approval is created. Preparing a patch does not change source files.
5. The ADMIN must inspect the unified diff, type the exact confirmation phrase, and provide a local ADMIN token.
6. Before writing source, the Agent creates a backup under .mathteacher_ai/chief_engineer/backups/<patch_id>/.
7. Writes use temporary files and atomic replacement. If a multi-file write fails, already-written files are restored from backup; the Agent records rollback state.

No source patch is automatically applied by the model planner. The V1 inspection tool allow-list remains read-only. The separate maintenance tool is MUTATING and requires the existing Kernel approval flow.

### Let the AI draft a proposal

The configured AI Kernel can draft a full-file replacement for up to three explicitly selected Python files under src/. The combined source sent to the model is limited to 24,000 characters; files containing recognized credential patterns are refused. The model response is checked against the exact path allow-list and revalidated by the deterministic patch validator.

Example:

    python -m ai_kernel.chief_engineer_agent --repo-root "$PWD" --draft-patch-for "src/portal_v2/ui/example.py" --rationale "Sửa lỗi kiểm tra dữ liệu đầu vào"

This command only creates a pending proposal, prints the generated diff, and reports patch_id/approval_id. It does not modify source files. Inspect the diff carefully before running the ADMIN approval command below.

### Prepare a proposal

Create a UTF-8 JSON file (keep local proposal files under .mathteacher_ai/ so Git ignores them) with this shape:

    {
      "rationale": "Lý do và phạm vi của bản vá",
      "changes": [
        {
          "path": "src/example/module.py",
          "expected_sha256": "64-character-lowercase-sha256-of-current-file",
          "content": "COMPLETE new Python file content"
        }
      ]
    }

Get the current SHA-256 in PowerShell:

    (Get-FileHash .\src\example\module.py -Algorithm SHA256).Hash.ToLowerInvariant()

Prepare the proposal:

    python -m ai_kernel.chief_engineer_agent --repo-root "$PWD" --prepare-patch-file ".mathteacher_ai\proposal.json"

Record the returned patch_id and approval_id. The command reports source_changed=false.

### Approve and apply

For the current PowerShell session, create a temporary random ADMIN token. Do not write it into the repository or share it in chat:

    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $env:MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN = ([BitConverter]::ToString($bytes) -replace '-', '').ToLowerInvariant()
    $rng.Dispose()

Then run:

    python -m ai_kernel.chief_engineer_agent --repo-root "$PWD" --approve-patch-id "<approval_id>" --admin-actor "local-admin"

The CLI displays the unified diff before asking for the exact text:

    APPLY PATCH <approval_id>

It then prompts for the ADMIN token without echoing it. The token is not printed in Agent output. Clear the temporary environment variable when finished:

    Remove-Item Env:MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN

If the source SHA changed, the diff is stale, approval does not match, the token is wrong, or backup creation fails, source is not modified.

## Local state and limitations

Run history, approvals, patch proposals and backups live below:

    .mathteacher_ai/chief_engineer/

The entire .mathteacher_ai/ folder is ignored by Git. Backups are local to the machine and are not uploaded to GitHub automatically.

The Agent is a foreground process when invoked from PowerShell; V2 does not install a Windows scheduled task or run in the background. The patch workflow has CI coverage on GitHub Actions but still requires a local Windows test before being used on production source files.
