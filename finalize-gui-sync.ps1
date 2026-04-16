# Finalize Claude Code Desktop GUI session sync with Google Drive (Windows).
# Run AFTER fully quitting Claude Desktop app.
# Requires: PowerShell running as Administrator (or Developer Mode ON).

$ErrorActionPreference = "Stop"

$ClaudeSessions = "$env:APPDATA\Claude\claude-code-sessions"
$GdriveGui = "H:\我的云端硬盘\claude-sync\gui-sessions"

Write-Host "==> Finding GUI session folder..."
$UserFolder = Get-ChildItem -Path $ClaudeSessions -Directory | Select-Object -First 1
if (-not $UserFolder) {
    Write-Host "No user folder found. Run Claude Desktop once first."
    exit 1
}
$AcctFolder = Get-ChildItem -Path $UserFolder.FullName -Directory | Select-Object -First 1
if (-not $AcctFolder) {
    Write-Host "No account folder found."
    exit 1
}
Write-Host "Local path: $($AcctFolder.FullName)"

Write-Host "==> Final sync: merging local into Google Drive..."
Copy-Item -Path "$($AcctFolder.FullName)\*.json" -Destination $GdriveGui -Force -ErrorAction SilentlyContinue

Write-Host "==> Removing local account folder..."
Remove-Item -Recurse -Force $AcctFolder.FullName

Write-Host "==> Creating symlink..."
New-Item -ItemType SymbolicLink -Path $AcctFolder.FullName -Target $GdriveGui | Out-Null

Write-Host "==> Verifying..."
Get-Item $AcctFolder.FullName | Select-Object FullName, LinkType, Target
$Count = (Get-ChildItem $AcctFolder.FullName -Filter "*.json").Count
Write-Host ""
Write-Host "Done. $Count GUI sessions now live in Google Drive."
Write-Host "Next time you open Claude Desktop, it will read from Google Drive."
