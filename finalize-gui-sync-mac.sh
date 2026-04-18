#!/bin/bash
# Finalize Claude Code Desktop GUI session sync with Google Drive (Mac).
# Run AFTER fully quitting Claude Desktop (Cmd+Q on Claude.app).

set -e

CLAUDE_SESSIONS="$HOME/Library/Application Support/Claude/claude-code-sessions"
GDRIVE_GUI="$HOME/Library/CloudStorage/GoogleDrive-leozhu0621@gmail.com/我的云端硬盘/claude-sync/gui-sessions"

echo "==> Finding GUI session folder..."
USER_FOLDER=$(find "$CLAUDE_SESSIONS" -mindepth 1 -maxdepth 1 -type d | head -1)
if [ -z "$USER_FOLDER" ]; then
    echo "No user folder found. Run Claude Desktop once first."
    exit 1
fi
ACCT_FOLDER=$(find "$USER_FOLDER" -mindepth 1 -maxdepth 1 -type d | head -1)
if [ -z "$ACCT_FOLDER" ]; then
    echo "No account folder found."
    exit 1
fi
echo "Local path: $ACCT_FOLDER"

echo "==> Final sync: merging local into Google Drive..."
mkdir -p "$GDRIVE_GUI"
cp -n "$ACCT_FOLDER"/*.json "$GDRIVE_GUI/" 2>/dev/null || true
# Also push newer versions
rsync -a --update "$ACCT_FOLDER/" "$GDRIVE_GUI/" 2>/dev/null || true

echo "==> Removing local account folder..."
rm -rf "$ACCT_FOLDER"

echo "==> Creating symlink..."
ln -s "$GDRIVE_GUI" "$ACCT_FOLDER"

echo "==> Verifying..."
ls -la "$ACCT_FOLDER"
COUNT=$(ls "$ACCT_FOLDER"/*.json 2>/dev/null | wc -l | xargs)
echo ""
echo "Done. $COUNT GUI sessions now live in Google Drive."
echo "Next time you open Claude Desktop, it will read from Google Drive."
