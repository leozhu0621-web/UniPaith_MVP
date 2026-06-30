# Data seeding — university profiles

**TL;DR — data is data, not schema history.** University profiles are seeded by an
idempotent runner over a registry, **not** by per-university Alembic migrations.

## Why this exists

Each `src/unipaith/data/<slug>_profile.py` exposes `apply(session) -> bool`, which
UPSERTs that university's canonical data. Historically every data edit shipped as
its own Alembic migration that called `apply()`. With many PRs in flight, each new
migration created a new Alembic head, so two data PRs routinely collided into a
**dual head** that had to be hand-merged. The git history carries dozens of
`fix(alembic): merge dual head …` commits, and ~73% of all migrations were data
loads. That churn is the single biggest source of messy, conflict-heavy PRs.

The fix: seed profiles as **data** — one idempotent pass over the registry — so a
data change is "edit the profile + re-seed," never "add a migration / fork a head."

## How to add or edit university data

1. Edit (or add) `src/unipaith/data/<slug>_profile.py`. Keep the uniform
   `apply(session: Session) -> bool` entry point. A new file auto-registers — the
   registry discovers `*_profile.py` from disk (`unipaith/data/profiles.py`).
2. Re-seed:
   ```bash
   python -m scripts.seed_profiles            # all profiles
   python -m scripts.seed_profiles mit yale   # just these
   ```
3. **Do not** add an Alembic migration whose `upgrade()` imports `unipaith.data`
   or calls `<x>_profile.apply()`. CI (`data-seeding-guard`) flags this. Migrations
   are for **schema (DDL)** only.

## Migrations vs. seeding — the rule

| Change | Mechanism |
|---|---|
| Table/column/index/constraint (DDL) | Alembic migration |
| University profile content (rows) | Edit profile → `scripts/seed_profiles.py` |

## Operational notes

- `seed_all(session)` does not commit — the caller owns the transaction (same
  convention the migrations used). The runner wraps it in `engine.begin()`.
- Profiles are independent and idempotent; order doesn't matter.
- `tests/test_profiles_registry.py` asserts the registry covers every
  `*_profile.py` and that each `apply` is uniform — so the path can't silently rot.

## Keeping a single Alembic head (B2)

The remaining migrations (schema only, far fewer) must stay single-head.
`tests/test_spec_03_compliance.py` asserts one head in CI. To stop post-merge
auto-merge races, enable the GitHub branch-protection setting **"Require branches
to be up to date before merging"** so a second PR must rebase onto the new head
before it can land.

## Roadmap (not done in this PR)

This PR is **additive** — it introduces the registry, runner, test, and guard
without removing the historical data migrations. The follow-up (its own PR, needs
a DB to verify state equivalence): retire the 462 data migrations and squash the
Alembic history to a baseline at the current schema, with seeding moved fully to
the runner. See the structural assessment, item **B2**.
