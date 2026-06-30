<!-- Keep PRs small and single-purpose. See CONTRIBUTING.md. -->

## What & why
<!-- One or two sentences. Link the issue/spec if there is one. -->

## Type
<!-- delete those that don't apply -->
feat · fix · perf · refactor · docs · test · ci · build · chore · data(repair/enrich)

## Checklist
- [ ] Single logical change; PR is reviewable in one sitting
- [ ] Title is conventional: `type(scope): summary`
- [ ] Backend: `services/` does not import `api/`; ran `pytest -n auto` + `ruff`
- [ ] Frontend: pages read data only via `api/` modules; ran lint + typecheck + build
- [ ] No new data-as-code (`*_profile.py`) or files > ~800 LOC (split instead)
- [ ] Alembic: rebased my migration onto the current head (single head preserved)
- [ ] No `*.log`, dumps, secrets, or parallel working copies committed
- [ ] Will delete this branch after merge

## Notes for the reviewer
<!-- Anything non-obvious: trade-offs, follow-ups, screenshots. -->
