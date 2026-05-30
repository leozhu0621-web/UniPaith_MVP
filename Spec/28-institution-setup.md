# 28 · Institution Setup (First-Run Wizard)

> The institution onboarding flow at `/i/setup` — the guided multi-step wizard a new institution completes before reaching the dashboard. Expands the first-run sketch in `04` §11 into a build contract. Orchestrates the already-specced editors (`20` profile, `21` programs, `22` data) into a sequenced first-run experience.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/i/setup`. Entry: invitation email → `/signup?invite=<token>` → `/i/setup`. Exit: `/i/dashboard`.

---

## 1. Purpose

Turn a brand-new institution account into a publishable, matchable presence with the least friction. The wizard is **orchestration, not new surface** — each step is a focused slice of an existing editor, sequenced so the institution reaches "first program live + first data uploaded" quickly. This is architecture-flow **Stage 0 (Institution Setup)** realized as onboarding.

---

## 2. Entry & gating

- Institutions are invite-only in MVP: an admin invitation email carries `/signup?invite=<token>`.
- After signup + email verification, first login routes to `/i/setup` (not the dashboard) until setup is marked complete.
- `RequireAuth` + `institution_admin` guard. A `setup_complete` flag on the institution gates the redirect; once true, `/i/setup` is reachable but no longer forced.
- Resumable: the wizard persists step progress; leaving and returning resumes at the last incomplete step.

---

## 3. Steps

A 4-step wizard with a progress rail; each step saves immediately (no big-bang submit).

```
┌────────────────────────────────────────────────────────────────────┐
│  [UP]  Set up your institution                          Step 2 of 4 │
│  ●━━━━━●━━━━━○━━━━━○                                                  │
│  Profile   Program   Data   Invite team                             │
├────────────────────────────────────────────────────────────────────┤
│  STEP CONTENT (a focused slice of the relevant editor)              │
│                                                  [Back]  [Continue] │
└────────────────────────────────────────────────────────────────────┘
```

### 3.1 Step 1 — Institution profile basics
A reduced form over the profile editor (`20`): legal/display name, type (community college / regional public / …), location, primary domain (for SES sender + trackable links), short description, logo (text wordmark per brand — no decorative imagery).
→ Produces a minimally publishable institution profile.

### 3.2 Step 2 — Your first program
A reduced slice of the program editor (`21`): name, degree type, modality, one intake/deadline, requirements summary, cost basics. "Add more details later."
→ Produces one publishable `ProgramCard` so the institution is matchable.

### 3.3 Step 3 — Upload data (optional, skippable)
A pointer into Data Upload (`22`): "Upload admissions history or a prospect list to power analytics + matching." Clearly skippable ("I'll do this later") — never blocks completion.
→ Seeds the value-for-data loop (`06` §4.3) when provided.

### 3.4 Step 4 — Invite your team (optional)
Invite colleagues with roles (admissions / recruiter / marketing / IT) — a slice of `1D` §3.1. Skippable.
→ Sets up collaboration; each invite audit-logged (`34`).

### 3.5 Finish
On finish (or "Skip to dashboard" after Step 2): set `setup_complete=true` → `/i/dashboard` with empty-state nudges ("Publish your program", "Upload your first dataset") for anything skipped.

---

## 4. Completion model

- **Minimum to finish:** Step 1 (profile) + Step 2 (one program). Steps 3–4 are optional.
- The dashboard (`30`) shows a setup-progress card until profile + program are published; skipped optional steps surface as dashboard nudges, not blockers.
- `setup_complete` unlocks the full nav; before that, nav is dimmed to keep focus on setup.

---

## 5. Data shape

```ts
type InstitutionSetupState = {
  institution_id: string;
  step: 1 | 2 | 3 | 4 | 'done';
  steps_complete: { profile: boolean; program: boolean; data: boolean; team: boolean };
  setup_complete: boolean;
  first_program_id: string | null;
};
```
Endpoints: `GET /i/setup` · `PATCH /i/setup/step` · `POST /i/setup/complete`. Each step delegates to the underlying editor's endpoints (`20`/`21`/`22`/`1D`), so there is no duplicate persistence.

---

## 6. States

- **Fresh invite:** Step 1, empty.
- **Resumed:** lands on last incomplete step with prior input intact.
- **Skipped optional:** dashboard nudge cards.
- **Already complete:** `/i/setup` shows a read-only summary + "Edit in Settings/Programs" links (not forced).

---

## 7. AI integration

- Optional: `CampaignAudienceCopySuggester` (`42` §16) can draft the institution description in Step 1; institution edits before saving. No AI is required to complete setup.

---

## 8. Brand compliance

- Wordmark/monogram only; no decorative imagery (editorial brand).
- Progress rail uses `--secondary`; the single completion moment (finish) may use the one earned gold accent (`02` §15).
- Mobile: single-column steps, sticky Continue bar (`02b` §7).

---

## 9. Gaps (relative to current code)

- A wizard exists in spirit (`04` §11) but is not built as a resumable, step-persisted flow.
- `setup_complete` gating flag is NEW.
- Reuses `20`/`21`/`22`/`1D` editors — those must expose "reduced/first-run" variants of their forms.

---

## 10. Tests

- New invite forces `/i/setup` until profile + program published.
- Each step persists independently; resume works.
- Skip Step 3/4 → finish allowed → dashboard nudges appear.
- `setup_complete` flips nav from dimmed to full.
- Team invites audit-logged.

---

## 11. Copy

- "Set up your institution" / "Step N of 4".
- "Add your first program" / "Add more details later".
- "Upload admissions history or a prospect list" / "I'll do this later".
- "Invite your team" / "Skip to dashboard".

---

## 12. Open questions

- **Self-serve vs invite-only.** MVP is invite-only; self-serve institution signup is a Phase-2 growth lever.
- **Verification gate.** Should an institution be verified (real org) before its programs go live to students? Recommend a light review for the first program in MVP; automated later.
- **Student onboarding parity.** The student first-run counterpart is specced in `1B` (Stage-1 discovery chat) + `04` §4.5/§11 — see those, not this doc.
