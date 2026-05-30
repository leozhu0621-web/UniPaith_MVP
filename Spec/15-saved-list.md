# 15 · Saved List

> The student's saved hub. Programs + schools saved from Discovery / Match / Detail pages. Organized as an intentional shortlist with reach/target/safer grouping, priority labels, tags/notes, compare, and one-click conversion to an application.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s/saved`.

---

## 1. Purpose

Saved is the bridge between Discovery / Match (decide what to consider) and My Applications (actually apply). The student curates here.

Two views: **Saved Programs** and **Saved Schools**.

---

## 2. Visual layout

```
SAVED
Your shortlist

[ Programs (24) ] [ Schools (8) ]

View: [Grouped by tier ▾]  Sort: [Match score ▾]  Filter: [All ▾]

─ REACH (3) ─────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────────┐
│ ProgramCard  · Priority [Considering ▾]  · Notes [+ Add]      │
│ Save · Compare · Start application                            │
└────────────────────────────────────────────────────────────────┘
... rows

─ TARGET (12) ───────────────────────────────────────────────────
... rows

─ SAFER (9) ─────────────────────────────────────────────────────
... rows

[Compare selected (3) →]
```

---

## 3. Tabs

### 3.1 Saved Programs (default)
Per-row: full ProgramCard + per-row priority dropdown + notes + actions.

### 3.2 Saved Schools
Per-row: SchoolCard. Less curation needed; schools are mainly bookmarks.

---

## 4. Organization tools

### 4.1 Grouping
- Grouped by tier (default): Reach / Target / Safer per `02-design-system.md` §9.
- Grouped by priority: Considering / Planning to apply / Applied / Dropped.
- Flat list.

### 4.2 Priority labels
Per saved program: `considering` (default), `planning_to_apply`, `applied`, `dropped`. Persisted server-side (per `90` G-S5 — currently UI-only; needs backend wiring).

### 4.3 Tags & notes
Free-text notes: "why I saved this", "things to verify". Tags from a free-text autocomplete on the student's own tag dictionary.

### 4.4 Status labels
Independent of priority — derived from application existence: `considering` (default) | `application_started` | `submitted` | `accepted` | `rejected` | `waitlisted` | `dropped`.

---

## 5. Compare

Same compare tray as `12-discovery.md` §8. Select multiple rows → "Compare selected (N)" CTA → side-by-side comparison.

Compare table dimensions (per Master Paper):
- Program structure + format.
- Location + setting.
- Cost + affordability.
- Access + competitiveness.
- Outcomes + employer signals.
- **Match scores** (fitness + confidence) — best-value indicators highlighted.

Max 4 programs in one compare.

---

## 6. One-click conversion to application

On a saved program row: "Start application" button.
- Creates a new `applications` row with `program_id`, carries over priority + notes.
- Navigates to `/s/applications/:newAppId`.
- Sets the saved row's `status` to `application_started`.

---

## 7. Data shape

```ts
type SavedProgram = {
  id: string;
  program_id: string;
  program: ProgramCard;
  saved_at: ISO8601;
  priority: 'considering' | 'planning_to_apply' | 'applied' | 'dropped';
  status: 'considering' | 'application_started' | 'submitted' | 'accepted' | 'rejected' | 'waitlisted' | 'dropped';
  tags: string[];
  notes: string;
  band_label: 'reach' | 'target' | 'safer';
};
```

Endpoints:
- `GET /me/saved` — list.
- `POST /me/saved/programs` — body: `{program_id}`.
- `PATCH /me/saved/programs/:program_id` — body: `{priority?, notes?, tags?}`.
- `DELETE /me/saved/programs/:program_id` — remove.
- `POST /me/saved/programs/:program_id/start-application` — creates app, returns `app_id`.
- `POST /me/saved/compare` — body: `{program_ids: string[]}` → returns compare table data.

---

## 8. States

- **Empty (no saves):** "Save programs from Match or Discovery to see them here." + "Open Match →" CTA.
- **Loading:** card-grid skeleton.
- **Bulk action loading:** disable selection; show inline spinner on the action button.
- **Comparison empty:** "Select at least 2 programs to compare."

---

## 9. AI integration

None directly. Programs in saved already carry MatchRationale via the cached lookup; opening "Why this match" popover from any card uses the same agent.

---

## 10. Brand compliance

- Band-section headers (Reach / Target / Safer) use eyebrow style + the corresponding band badge color.
- Priority dropdown uses `--secondary` text on hover; no gold.
- Notes field follows input pattern from `02-design-system.md` §4.
- Compare CTA uses `--secondary` (cobalt) — primary action; not gold.

---

## 11. Gaps (from `90`)

- G-S5 (major): priority `considering / planning_to_apply / applied / dropped` is `useState` only; needs `saved_lists.priority` column + PATCH endpoint.
- Compare table reads legacy `match_score`/`match_tier`; should read `fitness_score` + `confidence_score`.

---

## 12. Tests

- Save / unsave from Discovery → appears in saved list.
- Priority change persists across reload.
- Start application creates app and navigates.
- Compare selects multiple → table shows expected columns.
- Tier grouping correct for fixture data.

---

## 13. Copy

- "Your shortlist" (H1).
- "Save programs from Match or Discovery to see them here."
- "Considering" / "Planning to apply" / "Applied" / "Dropped" (priority).
- "Start application →".
- "Compare selected (N) →".
- "Open Match →" (empty-state CTA).

---

## 14. Open questions

- **Tag taxonomy.** Free-form vs platform-suggested tags? Recommend free-form; show student's most-used tags in autocomplete; never force a canonical set.
- **Reach/Target/Safer recomputation.** When does it recompute? Spec: on profile change + program-version change. Same triggers as match rationale cache invalidation.
- **Drop priority semantics.** Does "dropped" hide from main view? Recommend filter chip lets the user toggle.
