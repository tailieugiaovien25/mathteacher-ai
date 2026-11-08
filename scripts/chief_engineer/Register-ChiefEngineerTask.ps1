[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^(?:[01]\d|2[0-3]):[0-5]\d$')]
    [string]$DailyAt,
    [string]$TaskName = "MathTeacherAI-ChiefEngineer-Daily",
    [string]$PythonPath = "",
    [string]$Objective = "Kiểm tra trạng thái Git và kiểm kê cấu trúc repository; chỉ đọc và báo cáo, không chạy pytest, không sửa mã nguồn."
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not (Test-Path -LiteralPath (Join-Path $root ".git"))) {
    throw "RepoRoot không phải Git repository: $root"
}
$runner = Join-Path $root "scripts\chief_engineer\Run-ChiefEngineer.ps1"
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "Chưa tìm thấy runner: $runner"
}
if (-not (Test-Path -LiteralPath (Join-Path $root "src\ai_kernel\chief_engineer_agent.py") -PathType Leaf)) {
    throw "Chưa có Chief Engineer Agent V2 trong repository này."
}

$stateDir = Join-Path $root ".mathteacher_ai\chief_engineer"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$configPath = Join-Path $stateDir "scheduled_task.json"
$resolvedPython = $PythonPath
if ([string]::IsNullOrWhiteSpace($resolvedPython)) {
    $candidate = Join-Path $root ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $resolvedPython = $candidate
    }
    else {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCommand) {
            throw "Không tìm thấy Python. Hãy truyền -PythonPath tới Python có đủ dependencies."
        }
        $resolvedPython = $pythonCommand.Source
    }
}
$resolvedPython = [System.IO.Path]::GetFullPath($resolvedPython)
if (-not (Test-Path -LiteralPath $resolvedPython -PathType Leaf)) {
    throw "PythonPath không tồn tại: $resolvedPython"
}
$config = [ordered]@{
    repo_root = $root
    python_path = $resolvedPython
    objective = $Objective
    created_at = (Get-Date).ToString("o")
    mode = "read_only_no_tests"
}
$config | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $configPath -Encoding UTF8

$powerShell = (Get-Process -Id $PID).Path
if (-not (Test-Path -LiteralPath $powerShell -PathType Leaf)) {
    throw "Không xác định được PowerShell executable đang chạy."
}
$quotedRunner = '"' + $runner + '"'
$quotedConfig = '"' + $configPath + '"'
$arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File $quotedRunner -ConfigPath $quotedConfig"
$action = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::ParseExact($DailyAt, "HH:mm", [Globalization.CultureInfo]::InvariantCulture))
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew -DisallowStartIfOnBatteries:$false -StopIfGoingOnBatteries:$false
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "MathTeacher AI Chief Engineer: daily read-only repository inspection and report."
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

Write-Host "Đã đăng ký lịch Chief Engineer Agent." -ForegroundColor Green
Write-Host "Task: $TaskName"
Write-Host "Lịch: hằng ngày lúc $DailyAt (giờ địa phương của Windows)"
Write-Host "Repository: $root"
Write-Host "Cấu hình: $configPath"
Write-Host "Chế độ: chỉ quan sát/kiểm thử; không tự sửa mã nguồn."
Write-Host "Lần chạy đầu tiên sẽ theo lịch; script này không khởi chạy Agent ngay bây giờ."