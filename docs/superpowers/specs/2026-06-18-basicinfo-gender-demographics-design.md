# Basic info → demographics: gender field + 3-month lock + screen-filling layout (design)

**Date:** 2026-06-18 · **Status:** Approved by founder (direct direction) · **Scope:** full-stack (1 additive column)

## Problem
The Basic info tab (`/s/profile`) renders a narrow, left-hugging `max-w-2xl` form that leaves most of the screen empty (founder flagged the layout). It also doesn't surface **gender** — a basic demographic — even though the `gender_identity` column already exists. Founder direction: Basic info should be the demographics surface, and gender (a basic demographic) should be changeable only **once every 3 months**.

## Backend (additive)
- **Column:** add `gender_identity_updated_at` (`DateTime(timezone=True)`, nullable) to `student_profiles`. Migration revision `gendlock3mo`, down_revision `uwseedmerge1` (current single head). `gender_identity` (existing free `String(50)`) holds the value.
- **Response:** `StudentProfileResponse` gains `gender_identity_updated_at: datetime | None`.
- **Enforcement** (in `StudentService.update_profile`, `services/student_service.py`): if the update sets `gender_identity` to a value **different** from the stored one AND the stored `gender_identity_updated_at` is non-null AND less than **90 days** ago → reject with **HTTP 422** ("Gender can be changed once every 3 months. You can update it again on {date}."). On an allowed change (first set, or ≥90 days since the last change) apply it and set `gender_identity_updated_at = now (UTC)`. Editing other fields while gender is unchanged never touches the timestamp and is never blocked. `gender_identity` stays a protected attribute (fairness/segment services unchanged).

## Frontend
- **Layout fix:** `OverviewTab` container `max-w-2xl` (left-hugging) → `mx-auto max-w-4xl` (centered, fills the screen). Demographic fields become a responsive grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`) so they fill the width instead of stacking in a narrow column.
- **Gender field:** add a shared `Select` to `BasicInfoForm` for `gender_identity` with options **Woman · Man · Non-binary · Another identity · Prefer not to say** (the stored value is the label string — backward compatible with the free-text column).
- **3-month lock UI:** from `gender_identity_updated_at`, compute `lockedUntil = +90d`. While `now < lockedUntil`, the gender Select is **disabled** with helper text "You can change this again on {date}."; when editable and already set, a quiet hint "Changing your gender locks it for 3 months." A 422 on save surfaces a courteous toast. Graceful when the field is absent (no lock).
- Demographics lead (First name · Last name · Gender · Date of birth · Pronouns · Nationality · Country of residence); Bio + Goals stay as an "About you" block below. Semantic tokens, dark-safe, sentence-case labels.

## Out of scope
No change to the fairness/segment protected-attribute handling; no new gender free-text input (fixed options); Goals/Bio kept (not removed).

## Verification
Backend: single alembic head, ruff, tests (CI). Frontend: tsc 0 · build 0 · eslint 0 · vitest green. Ship full-stack as one PR; verify gender field + lock live.
