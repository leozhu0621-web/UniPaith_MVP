# Windows Setup — UniPaith MVP

Follow these steps ONCE on your Windows desktop to mirror your Mac dev environment and sync Claude Code sessions via Google Drive.

## 1. Install prerequisites

Open PowerShell **as Administrator** and run:

```powershell
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Python.Python.3.12 -e
winget install --id Docker.DockerDesktop -e
winget install --id Google.GoogleDrive -e
```

Then close and reopen PowerShell (not as admin this time) and install Claude Code:

```powershell
npm install -g @anthropic-ai/claude-code
```

Verify everything:
```powershell
git --version
node --version
python --version
docker --version
claude --version
```

## 2. Sign in to Google Drive

Open **Google Drive** from the Start menu. Sign in with `leozhu0621@gmail.com` (same account as Mac). Pick "Stream files" during setup.

After sign-in, Google Drive mounts as a drive letter — usually `G:\` (or similar). Look for `G:\My Drive\` in File Explorer. Inside, you should see:
```
G:\My Drive\claude-sync\unipaith-sessions\
```
With ~11 `.jsonl` files. **Wait for all of them to finish downloading** (green check marks, not blue spinners).

## 3. Clone the repo

```powershell
cd $env:USERPROFILE\Desktop
git clone https://github.com/leozhu0621-web/UniPaith_MVP.git
cd UniPaith_MVP
```

## 4. Create the session symlink

Claude Code needs to find sessions at a Windows-specific path. We'll symlink that path to Google Drive.

**First, find the Windows path hash** — run Claude once to make it create the folder:

```powershell
cd $env:USERPROFILE\Desktop\UniPaith_MVP
claude
# Type /exit immediately once Claude starts
```

Check what folder it created:
```powershell
dir "$env:USERPROFILE\.claude\projects\"
```

You'll see one folder named something like `C--Users-leozhu-Desktop-UniPaith-MVP`. Copy that exact name.

**Enable Developer Mode** so you can create symlinks without admin:
- Open Settings → Privacy & security → For developers → Enable "Developer Mode"

**Then create the symlink** (replace `<FOLDER_NAME>` with what you saw above, and verify the Google Drive letter):

```powershell
$WinHash = "<FOLDER_NAME>"
$Target = "G:\My Drive\claude-sync\unipaith-sessions"
$Link = "$env:USERPROFILE\.claude\projects\$WinHash"

# Remove the empty folder Claude just created
Remove-Item -Recurse -Force $Link

# Create the symlink
New-Item -ItemType SymbolicLink -Path $Link -Target $Target
```

## 5. Verify it works

```powershell
cd $env:USERPROFILE\Desktop\UniPaith_MVP
claude --resume
```

You should see the same 11 sessions from your Mac. Pick any one to resume.

## 6. Optional: set up local backend (for running tests/dev server on Windows)

If you want to run the full stack on Windows (not just Claude Code):

```powershell
cd $env:USERPROFILE\Desktop\UniPaith_MVP

# Backend
cd unipaith-backend
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
cd ..

# Frontend
cd frontend
npm ci
cd ..

# Postgres (needs Docker Desktop running)
cd unipaith-backend
docker compose up -d
```

---

## Daily workflow

1. **Before starting:** check Google Drive is "Up to date" (menu bar icon)
2. **Open PowerShell** → `cd UniPaith_MVP` → `claude --resume`
3. **When done:** exit Claude, wait ~30 seconds for Google Drive to sync
4. **Before switching to Mac:** confirm Google Drive finished uploading

### Rules (important!)
- ❌ **Don't run Claude on both machines simultaneously** — creates conflict files
- ✅ **Wait ~30s after closing** before switching machines
- ✅ **If you see a `(conflict copy)` file** in Google Drive, keep the bigger/newer one and delete the others
