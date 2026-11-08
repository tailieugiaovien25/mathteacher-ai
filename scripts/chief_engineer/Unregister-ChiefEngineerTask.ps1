[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "Medium")]
param([string]$TaskName = "MathTeacherAI-ChiefEngineer-Daily")

$ErrorActionPreference = "Stop"
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "Không tìm thấy task: $TaskName"
    return
}
if ($PSCmdlet.ShouldProcess($TaskName, "Unregister scheduled task")) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Đã gỡ lịch chạy. Nhật ký, cấu hình Agent và backup không bị xóa."
}