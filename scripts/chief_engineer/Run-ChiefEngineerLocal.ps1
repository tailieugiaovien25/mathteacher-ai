[CmdletBinding()]
param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$entryPoint = Join-Path $repoRoot "chief_engineer_agent_local_app.py"
if (-not (Test-Path -LiteralPath $entryPoint -PathType Leaf)) {
    throw "Không tìm thấy giao diện AI Agent local: $entryPoint"
}

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Không tìm thấy Python."
    }
    $python = $pythonCommand.Source
}

$oldPythonPath = $env:PYTHONPATH
$oldLocalFallback = $env:MATH_TEACHER_AI_LOCAL_FALLBACK_ENABLED
try {
    $env:PYTHONPATH = Join-Path $repoRoot "src"
    $env:MATH_TEACHER_AI_LOCAL_FALLBACK_ENABLED = "false"
    Push-Location $repoRoot
    & $python -m streamlit run $entryPoint --server.address 127.0.0.1 --server.port $Port
    exit $LASTEXITCODE
}
finally {
    Pop-Location -ErrorAction SilentlyContinue
    $env:PYTHONPATH = $oldPythonPath
    $env:MATH_TEACHER_AI_LOCAL_FALLBACK_ENABLED = $oldLocalFallback
}
