# Background one-way sync: Windows Claude Desktop GUI sessions -> Google Drive.
# Safe to run while Claude Desktop is open.
# Installed by install-gui-autosync.ps1 to run every 5 minutes via Task Scheduler.

$ErrorActionPreference = "SilentlyContinue"

$ClaudeBase = "$env:APPDATA\Claude\claude-code-sessions"
$GdriveGui = "H:\我的云端硬盘\claude-sync\gui-sessions"
$LogFile = "$env:LOCALAPPDATA\claude-gui-sync.log"

# Find the account folder (same UUID as Mac: 5d19d626.../3bd852dc...)
$UserFolder = Get-ChildItem -Path $ClaudeBase -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $UserFolder) { exit 0 }
$AcctFolder = Get-ChildItem -Path $UserFolder.FullName -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $AcctFolder) { exit 0 }

# Ensure Google Drive destination exists
New-Item -ItemType Directory -Path $GdriveGui -Force | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] sync starting"

# Copy only newer files (mimics rsync --update)
Get-ChildItem -Path "$($AcctFolder.FullName)\*.json" -ErrorAction SilentlyContinue | ForEach-Object {
    $dest = Join-Path $GdriveGui $_.Name
    if (-not (Test-Path $dest) -or ($_.LastWriteTime -gt (Get-Item $dest).LastWriteTime)) {
        Copy-Item -Path $_.FullName -Destination $dest -Force -ErrorAction SilentlyContinue
    }
}

# Also pull newer files FROM Google Drive back to local (bidirectional-ish)
Get-ChildItem -Path "$GdriveGui\*.json" -ErrorAction SilentlyContinue | ForEach-Object {
    $dest = Join-Path $AcctFolder.FullName $_.Name
    if (-not (Test-Path $dest) -or ($_.LastWriteTime -gt (Get-Item $dest).LastWriteTime)) {
        Copy-Item -Path $_.FullName -Destination $dest -Force -ErrorAction SilentlyContinue
    }
}

$count = (Get-ChildItem $GdriveGui -Filter "*.json").Count
$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] sync done ($count files in gdrive)"
