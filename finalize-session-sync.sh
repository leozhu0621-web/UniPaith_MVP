#!/bin/bash
# Finalize Claude session sync with Google Drive.
# Run this AFTER fully quitting Claude Code (Cmd+Q on Claude.app, not just closing window).

set -e

GDRIVE_SESSIONS="$HOME/Library/CloudStorage/GoogleDrive-leozhu0621@gmail.com/我的云端硬盘/claude-sync/unipaith-sessions"
LOCAL_SESSIONS="$HOME/.claude/projects/-Users-leozhu-Desktop----Platform-UniPaith-MVP"

echo "==> Final sync: pushing any last changes to Google Drive..."
rsync -a "$LOCAL_SESSIONS/" "$GDRIVE_SESSIONS/"

echo "==> Removing local sessions folder..."
rm -rf "$LOCAL_SESSIONS"

echo "==> Creating symlink to Google Drive folder..."
ln -s "$GDRIVE_SESSIONS" "$LOCAL_SESSIONS"

echo "==> Verifying symlink..."
ls -la "$LOCAL_SESSIONS"
COUNT=$(ls "$LOCAL_SESSIONS"/*.jsonl 2>/dev/null | wc -l | xargs)
echo ""
echo "✅ Done. $COUNT session files now live in Google Drive."
echo "Next time you open Claude in this project, it will read from Google Drive."
