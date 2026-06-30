# UniPaith docs

Start-here index for repo documentation. For the product/feature specs, see
[`Spec/00-overview.md`](../Spec/00-overview.md) (the canonical, indexed spec set).

## Architecture & contributing
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — system map (frontend / backend / infra / CI).
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — where code goes, layering rules, branch/commit/PR conventions.

## Data & domain standards
- [`INSTITUTION_DATA_STANDARD.md`](INSTITUTION_DATA_STANDARD.md) — institution data shape & rules.
- [`STUDENT_DATA_STANDARD.md`](STUDENT_DATA_STANDARD.md) — student data shape & rules.
- [`NORMALIZATION_STANDARD.md`](NORMALIZATION_STANDARD.md) — normalization rules.
- [`../unipaith-backend/docs/DATA_SEEDING.md`](../unipaith-backend/docs/DATA_SEEDING.md) — **how university data is seeded (registry, not migrations).**

## Operations & integrations
- [`STRIPE_SETUP.md`](STRIPE_SETUP.md) — payments setup.
- [`airtable-prompt-library-setup.md`](airtable-prompt-library-setup.md) — Airtable prompt library.
- [`UX-QA.md`](UX-QA.md) — UX QA notes.

---

*Keep this index current when adding a doc. One source of truth per topic; don't
commit VCS dumps or scratch files here (see `.gitignore`).*
