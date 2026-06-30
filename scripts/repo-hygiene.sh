#!/usr/bin/env bash
# Repo hygiene — prune merged local branches and stale worktrees.
# Dry-run by default; pass --apply to actually delete. Never touches `main`
# or your current branch. Remote-branch sprawl is best fixed at the source by
# enabling "Automatically delete head branches" in GitHub repo settings.
set -euo pipefail

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

cur=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $cur (protected)"
git fetch -q origin main

echo
echo "== Local branches already merged into origin/main =="
merged=$(git branch --merged origin/main --format '%(refname:short)' \
  | grep -vxE "main|$cur" || true)
if [ -z "$merged" ]; then
  echo "  (none)"
else
  echo "$merged" | sed 's/^/  /'
  if [ "$APPLY" = 1 ]; then
    echo "$merged" | xargs -r -n1 git branch -d
    echo "  deleted."
  fi
fi

echo
echo "== Pruning stale worktrees (path no longer exists) =="
git worktree prune -v || true

echo
if [ "$APPLY" = 0 ]; then
  echo "Dry-run. Re-run with --apply to delete the merged local branches above."
else
  echo "Applied."
fi
echo "Reminder: enable GitHub repo setting 'Automatically delete head branches' to stop the 700+ remote-branch sprawl at the source."
