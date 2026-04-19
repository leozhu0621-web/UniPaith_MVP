# One-time installer for Windows Claude Desktop GUI session auto-sync.
# Run once in an Administrator PowerShell:
#   cd $env:USERPROFILE\UniPaith_MVP
#   .\install-gui-autosync.ps1

$ErrorActionPreference = "Stop"

$TaskName = "ClaudeGUISync"
$ScriptPath = "$env:USERPROFILE\UniPaith_MVP\sync-claude-gui-to-gdrive.ps1"

if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: $ScriptPath not found. Pull the repo first."
    exit 1
}

Write-Host "==> Registering scheduled task '$TaskName'..."

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 365)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -Hidden

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Sync Claude Desktop GUI sessions to Google Drive every 5 minutes" | Out-Null

Write-Host "==> Running sync once now to verify..."
& $ScriptPath

Write-Host ""
Write-Host "Installed. Check log at: $env:LOCALAPPDATA\claude-gui-sync.log"
Write-Host "Task Scheduler name: $TaskName (repeats every 5 min)"
