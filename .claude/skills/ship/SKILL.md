---
name: ship
description: >
  Use when a verified change on UniPaith is ready to go to production — when asked
  to "ship", "deploy", "push it online", "merge and deploy", "take it live", or to
  build a numbered spec end-to-end and confirm it live. Drives the
  commit → merge → auto-deploy → verify-live loop for the frontend
  (app.unipaith.co) and backend (api.unipaith.co). Knows the alembic-head,
  secrets-baseline, squash-skew, and sibling-worktree-merge gotchas.
---

# Ship to production (UniPaith)

Standing rule (CLAUDE.md): every verified change goes online in the same turn.
"Done" = **committed → merged to `main` → auto-deployed → confirmed live**, not
written on disk. This skill is that loop, with the project's real commands and
gotchas baked in.

## The gate — never ship red

Run and confirm BEFORE committing:

- **Frontend:** `cd frontend && npx tsc -p tsconfig.app.json --noEmit` · `npm run build` · `npx eslint <changed files>` (warnings don't fail CI's `eslint src/`; **0 errors** is the bar). If you touched user-facing copy: `npm run voice-lint`.
- **Backend:** `make test-backend` (or targeted `pytest`) green, AND `cd unipaith-backend && PYTHONPATH=src alembic heads` shows **exactly one head**.

If a step fails, fix it — do not proceed.

## Alembic dual-head check (backend only)

`alembic heads` printing **two heads** fails the deploy gate (`test_alembic_has_single_head`). Concurrent merges cause this. Fix:

1. `alembic merge -m "merge heads <topic>" <head1> <head2>` — use a **session-unique** revision id (don't reuse another session's merge id).
2. Re-run the suite, confirm `alembic heads` shows one head.

## The loop

1. **Branch fresh off `origin/main`** (avoids squash-skew when other sessions merged):
   `git fetch origin main -q && git checkout -b claude/<topic> origin/main` — then re-apply your change if it was on an old branch.
2. **Commit.** If the **detect-secrets** pre-commit hook aborts with "baseline file was updated", run `git add .secrets.baseline` and commit again — it's expected, not a real secret.
3. **Push + PR:** `git push -u origin claude/<topic>` then `gh pr create --base main ...`.
4. **Merge once CI is green:** `gh pr merge <N> --squash`. The repo merges on squash even with non-blocking checks. If `--delete-branch` errors with *"main is already used by worktree"*, ignore it — the **GitHub merge still succeeded**; confirm via step 5.
5. **Confirm main moved:** `git fetch origin main -q && git log --oneline -1 origin/main` shows your squash commit (`… (#N)`).

## Deploy + verify live

Deploy auto-triggers on push to `main` (GitHub Actions **Deploy Frontend** / **Deploy Backend**).

- **Watch:** `gh run list --branch main --workflow "Deploy Frontend" --limit 1` → `gh run watch <id> --exit-status`.
- **Verify frontend live** (grep the deployed CloudFront bundle for a string/class unique to your change):
  `curl -s https://app.unipaith.co/index.html` → find `assets/index-*.js` → fetch it → follow the lazy chunk ref (e.g. `ProfilePage-*.js` → `IdentityTab-*.js`) → grep your marker. New marker present + old marker absent = live.
- **Verify backend live:** `curl` the new endpoint on `https://api.unipaith.co` — `422` (not `404`) means the route exists; `/api/v1/health` returns `200`.
- **Docs-only changes** (CLAUDE.md, specs) aren't built artifacts — there's no deploy to verify; merging to `main` is the completion.

**Report the live URL** and confirm: working tree clean · `main` at the new commit · deploy succeeded.

## Spec-to-production mode

When asked to ship a numbered spec end-to-end: read `docs/superpowers/specs/…` (spec {N}), plan it, implement backend + frontend + tests following existing patterns, then run the gate and the loop above. Do not stop until the feature is verified live in production with its URL.

## Gotchas

| Symptom | Fix |
|---|---|
| Pre-commit "baseline file was updated" | `git add .secrets.baseline`, re-commit |
| `test_alembic_has_single_head` fails | merge-migration with a session-unique id |
| `gh pr merge --delete-branch` errors on sibling worktree | merge still succeeded; verify `origin/main` moved |
| Local branch behind on unrelated commits | branch fresh off `origin/main`, re-apply your commit |
| Live bundle hash ≠ local build hash | normal (CI build graph differs); grep the chunk for your marker instead |
| Worktree `frontend/node_modules` empty | symlink main's, or `npm ci` |

See CLAUDE.md → **Deployment Workflow**, **Git / Worktrees**, and **Ship to Production Every Time** for the authoritative rules.
