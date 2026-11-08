[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath
)

$ErrorActionPreference = "Stop"
$configFullPath = [System.IO.Path]::GetFullPath($ConfigPath)
if (-not (Test-Path -LiteralPath $configFullPath -PathType Leaf)) {
    throw "Không tìm thấy cấu hình Chief Engineer Task: $configFullPath"
}
$config = Get-Content -LiteralPath $configFullPath -Raw -Encoding UTF8 | ConvertFrom-Json
$repoRoot = [System.IO.Path]::GetFullPath([string]$config.repo_root)
$objective = [string]$config.objective

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
    throw "Repo không hợp lệ hoặc không có .git: $repoRoot"
}
if ([string]::IsNullOrWhiteSpace($objective)) {
    throw "Thiếu objective trong cấu hình."
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
    $python = $venvPython
}
else {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Không tìm thấy Python. Hãy cài dependencies trong .venv của dự án."
    }
    $python = $command.Source
}

$stateDir = Join-Path $repoRoot ".mathteacher_ai\chief_engineer"
$logDir = Join-Path $stateDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir "agent_$timestamp.log"

$oldPythonPath = $env:PYTHONPATH
$oldNoBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONPATH = Join-Path $repoRoot "src"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    Push-Location $repoRoot
    "[$(Get-Date -Format o)] Chief Engineer Agent started." | Set-Content -LiteralPath $logPath -Encoding UTF8
    "Repository: $repoRoot" | Add-Content -LiteralPath $logPath -Encoding UTF8
    & $python -m ai_kernel.chief_engineer_agent --repo-root $repoRoot --objective $objective --max-cycles 4 --timeout 90 *>&1 |
        Out-String -Width 240 | Add-Content -LiteralPath $logPath -Encoding UTF8
    $agentExit = $LASTEXITCODE
    "[$(Get-Date -Format o)] ExitCode=$agentExit" | Add-Content -LiteralPath $logPath -Encoding UTF8
    exit $agentExit
}
finally {
    Pop-Location -ErrorAction SilentlyContinue
    $env:PYTHONPATH = $oldPythonPath
    $env:PYTHONDONTWRITEBYTECODE = $oldNoBytecode
}