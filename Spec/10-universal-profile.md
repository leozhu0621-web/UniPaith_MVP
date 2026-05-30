# 10 · Universal Profile — Student Workspace

> The student's durable record. 19 spec sections organized into 13 tabs. Modular, edit-first, completion-tracked. Once data lands here, every other surface (Match, Apply, Workshops, Inbox, Calendar) reads from it.
>
> Status: **draft v1.0** · 2026-05-29 · Routes: `/s/profile` + `?tab=*` deep links · Depends on `01-brand-tokens.md`, `02-design-system.md`, `40-prompt-library-schema.md`, `41-adaptive-intake-engine.md`.

---

## 1. Why this page exists

The student journey is sequenced (Discover → Match → Apply → Connect), but the **data is shared across all four**. A student should never re-enter "I'm a senior CS major at NYU" three times.

The Profile is the canonical durable record. Discover writes to it (via the Adaptive Intake Engine). Match reads from it. Apply pulls from it per program-adaptive checklist. Workshops feedback is anchored to it. Connect surfaces institutions relevant to it.

Three operating principles:
1. **Modular.** Each section can be filled or edited independently. Never one giant form.
2. **Edit-first.** Tap a field → edit in place → save → done. No "Edit mode" toggle.
3. **Completion-tracked.** Per-category and overall completion %, surfaced as a meter at the top of every tab.

---

## 2. Route map

| Route | Purpose |
|---|---|
| `/s/profile` | Default → `?tab=overview`. |
| `/s/profile?tab=overview` | Completion ring + completion-map + next-action queue. |
| `/s/profile?tab=identity` | Identity Layer (deepest profile depth — values, worldview, self-awareness). |
| `/s/profile?tab=academics` | Academics, Test Scores, Languages, Research. |
| `/s/profile?tab=experience` | Activities, Work & Service, Competitions, Portfolio, Online Presence. |
| `/s/profile?tab=goals` | SMART goal stack. |
| `/s/profile?tab=needs` | Maslow-keyed needs map. |
| `/s/profile?tab=strategy` | Active broad strategy + versioned history. |
| `/s/profile?tab=preparation` | Documents, Accommodations, Scheduling, Recommenders. |
| `/s/profile?tab=preferences` | Preferences (location, modality, finances, etc.). |
| `/s/profile?tab=financial` | Financial aid intent + budget. |
| `/s/profile?tab=timeline` | Profile-progress timeline. |
| `/s/profile?tab=analytics` | Profile analytics (completion over time, signal-density chart, peer comparison). |
| `/s/profile?tab=data` | Data Rights & Export (4 consent toggles + portable export + access log + delete account). |

13 tabs total. The 19 spec sections map as follows:

| # | Spec section | Tab |
|---|---|---|
| 1 | Personal | Overview (header block) |
| 2 | Online Presence | Experience |
| 3 | Portfolio | Experience |
| 4 | Academics | Academics |
| 5 | Test Scores | Academics |
| 6 | Activities | Experience |
| 7 | Research | Academics |
| 8 | Languages | Academics |
| 9 | Work & Service | Experience |
| 10 | Competitions | Experience |
| 11 | Documents | Preparation |
| 12 | Accommodations | Preparation |
| 13 | Scheduling | Preparation |
| 14 | Preferences | Preferences |
| 15 | Notifications | **Settings** (`/s/settings`), not Profile |
| 16 | Timeline | Timeline |
| 17 | Analytics | Analytics |
| 18 | Peer Comparison | Analytics |
| 19 | Export | Data Rights |

Plus Discovery-output tabs not in the 19 list but defined by Phase B: **Identity, Goals, Needs, Strategy, Financial**.

---

## 3. Visual layout (per tab)

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Wordmark]   Discover · Match · Apply · Connect          [avatar]   │← top nav
├──────────────────────────────────────────────────────────────────────┤
│  PROFILE                                                              │← eyebrow
│  Your record                                                          │← H1
│                                                                       │
│  ┌─────────┐  Overview  Identity  Academics  Experience  Goals       │← tab strip
│  │  ◯  72% │  Needs  Strategy  Preparation  Preferences  Financial   │
│  │ ▮▮▮▮▮▮▯ │  Timeline  Analytics  Data                              │← completion ring
│  └─────────┘                                                          │
│                                                                       │
│  ╔════════════════════════════════════════════════════════════╗      │
│  ║  TAB CONTENT — sections below                              ║      │
│  ║                                                              ║      │
│  ╚════════════════════════════════════════════════════════════╝      │
└──────────────────────────────────────────────────────────────────────┘
```

- Completion ring: 64px SVG donut, fill in `--primary` gold, track in `--border`. Below the percentage: small "Last updated 2h ago" line in `--text-mut`.
- Tab strip: horizontal scroll on mobile; wraps on desktop. Active tab gets `--text` color + weight 600 + 2px `--primary` underline.
- Tab content: see §4–§16 per tab.

---

## 4. Overview tab

Header block (Section 1 — Personal):
```
┌───────────────────────────────────────────────────────────────┐
│  [Avatar 80px]                                                 │
│  Sienna Chen           sienna.chen@example.com                 │
│  Senior · CS major · NYU                                       │
│  Brooklyn, NY · he/him                                         │
│  [Edit personal info]                                          │
└───────────────────────────────────────────────────────────────┘
```

Edit triggers a sheet (per `02` §6) with all `Identity, contact, account` fields per `40-prompt-library-schema.md` §3.1.

Completion map (the next 13 cluster cards):
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Identity        │  │ Academics       │  │ Experience      │
│ ●●●●●○  82%     │  │ ●●●●○○  68%     │  │ ●●●○○○  45%     │
│ Last: 2 days    │  │ Last: 1 hour    │  │ Last: 5 days    │
│ [Open]          │  │ [Open]          │  │ [Open]          │
└─────────────────┘  └─────────────────┘  └─────────────────┘
... 13 cluster cards in a 3-column grid (1-col on mobile)
```

Each card: 5-dot completeness indicator + percent + last update + Open link.

Next-action queue:
```
What's next
────────────
1. Add a second recommender — required by 3 of your 5 saved programs    [Add]
2. Confirm your target start term — currently low confidence            [Confirm]
3. Upload an unofficial transcript — match scores improve with grades   [Upload]
4. Connect your LinkedIn — strengthens activity entries                 [Connect]
```

Sourced from `next_questions_to_ask_user` + derived `recommended_next_actions` (per `40` §4.14). Tappable; each opens the relevant tab or modal.

---

## 5. Identity tab

3 sections (Phase B intact):
- **Core values** — free-form list with weight (e.g., "Authenticity 9/10", "Community 7/10").
- **Worldview** — paragraph + tag list (e.g., "Climate as moral imperative", "First-generation immigrant lens").
- **Self-awareness** — paragraph + linked life events.

Each section: edit-in-place; partial-merge PUT (per current Phase B impl).

Below the 3 sections:
```
AI summary
──────────
Sienna leads from a quiet sense of purpose. She came to computer science by way
of music — for the structure, not the gloss — and what makes her tick now is
building useful things for the people right around her…
                                                       [Regenerate · 3 days ago]
```

Generated by `IdentitySummaryAgent` (`42` §11). The Regenerate button calls `/me/identity/regenerate-summary` (existing endpoint). On failure, preserves the previous real summary; never overwrites with stub.

**Privacy note** at top of tab (one-time disclosure, dismissible): "Identity is the deepest layer of your profile. We use this to personalize matches and rationales — nothing here goes to institutions until you choose to share it. Manage in [Data Rights →]."

---

## 6. Academics tab

Four sub-sections, expandable cards:

### 6.1 Academics
Top-level (§3.5 summary fields): GPA + scale, weighted flag, class rank, percentile rank, rigor counts (AP / IB / Honors), honors list, attendance.

Per-course table below: filter by term / level. Add-course CTA. Each row tap → edit sheet.

Transcript upload section below the table: drag-drop zone; status badges (parsing / parsed / partial / failed / verified). On parse success, surface extractions for student to confirm before persisting.

### 6.2 Test Scores
Per `40` §3.6. Each test = one card. Sections + subscores listed under each. Superscore computed automatically (`superscore_computed_values`). Verified status badge.

### 6.3 Languages
Per `40` §3.11. CEFR or ACTFL proficiency picker. Proof type. Can-demonstrate toggle. List view; one row per language.

### 6.4 Research
Per `40` §3.9 (research sub-list). One card per project. Outputs (paper / poster / code / dataset / presentation) as chips. Publication links validated.

---

## 7. Experience tab

Five sub-sections:

### 7.1 Activities
Per `40` §3.9 (activity-shaped entries). One card per activity. Category, role, leadership level, scope, dates, hours.

### 7.2 Work & Service
Per `40` §3.8. One card per role. Internship / part-time / full-time / volunteer / fellowship.

### 7.3 Competitions
Per `40` §3.9 sub. One card per competition.

### 7.4 Portfolio
Per `40` §3.10. Top-level fields + grid of pieces. Each piece: thumbnail (where possible), title, type, tags. Add piece via drag-drop or link.

### 7.5 Online Presence
Per `40` §3.1 online links subset. LinkedIn, GitHub, personal site, others. URL validation status badges.

---

## 8. Goals tab

Per `40` §3.12 + the existing `student_goals` model.

SMART goal stack grouped by category:
- **Academic** (degree, major, etc.)
- **Social** (connection, networking)
- **Personal** (finance, wellbeing)

Each goal card:
- Title (e.g., "Get into a top-20 MS in Computer Science by Fall 2027").
- SMART breakdown: Specific / Measurable / Achievable / Relevant / Time-bound text.
- Source badge: `from_discovery` vs `manual`.
- Confidence dot row (1-5 dots filled).
- Edit / Archive / Delete actions.

Add-goal CTA opens a wizard with the SMART prompts.

---

## 9. Needs tab

Per `40` §3.13 + `student_needs` model.

Maslow-keyed map (top-down):

```
Self-actualization
  events · alums · career support · mental support · over-sea education
  ────────────────────────────────────────────
  [need card] [need card] [need card]   [+ Add]

Self-esteem
  scholarship · career & support · social bias · peer-stress
  ────────────────────────────────────────────
  [need card] [need card]                [+ Add]

Social
  community · culture · inter-personal atmosphere · diversity · inclusion
  ────────────────────────────────────────────
  …

Safety
  healthcare · finance · environment · policy
  …

Physiological
  housing · food
  …
```

Each need card: name + description + severity badge (`must_have` / `strong_preference` / `nice_to_have`) + source badge (`from_discovery` / `manual` / `inferred`).

---

## 10. Strategy tab

Per `student_strategies` table. Read-mostly.

Active strategy card (top):
```
ACTIVE
Your strategy                          v3 · updated 2 days ago

Career path:   Software Engineer in privacy-focused product work
Degree path:   Master's in CS with HCI concentration
Academic:      Aim for top 30 programs with strong systems + HCI faculty
Financial:     $30-50k/yr ceiling; prioritize TA-funded programs
Geographic:    East Coast preferred; will consider remote PhD

Narrative
─────────
Sienna's path is bounded by a clear sense of what she wants to build…
[4 paragraphs total]

[Edit (creates a draft)]  [Regenerate]
```

Edit creates a clone with status `draft`; editing the draft doesn't activate it. "Activate" sets the new version active (and archives the old).

Versions list below: chronological list of past strategies; each can be re-activated.

Generated by `StrategyAgent` (`42` §10).

---

## 11. Preparation tab

Four sub-sections:

### 11.1 Documents
Repository of uploads. Drag-drop. Per file: type, name, size, upload date, verification status, replace, delete.

### 11.2 Accommodations
Per `40` §3.2. Free-form details + documentation status. Privacy-gated.

### 11.3 Scheduling
Available times for interviews / advising / visits. Weekly recurrence grid + per-date overrides.

### 11.4 Recommenders
Per `40` §3.7. One card per recommender. Status pipeline (not_requested → requested → in_progress → submitted). Request action sends an email; tracks via `recommendation_platform`.

---

## 12. Preferences tab

Per `40` §3.14. Structured pickers:
- Institution size, type, setting, religious affiliation.
- Application platform preference, admission round preference.
- Program format, internship requirement, delivery flexibility.
- Schedule preference, support services needed (multi-select).
- Campus culture (free-form).
- Importance ratings (4 sliders).
- Target institution list, target program list.

---

## 13. Financial tab

Per `40` §3.13 financial fields:
- Budget band (slider).
- Max tuition, max total COA.
- Needs financial aid, scholarship required, employer sponsorship.

Plus existing financial-aid intent state from the legacy `FinancialAidPage`.

Aid-likelihood preview powered by `aid_scholarship_likelihood_band` output.

---

## 14. Timeline tab

Profile-progress timeline: chronological list of all profile changes with timestamps + source badges.

Includes: form saves, document uploads, Discovery chat extractions (with link to original message), institution-supplied updates (e.g., recommender submitted).

Filter by: source, category, date range.

---

## 15. Analytics tab

Two views:

### 15.1 Profile analytics
- Completion ring (large) + per-category completion bars.
- Completion timeline (sparkline: % over time).
- Signal density chart (how many signals filled per category).
- "Strongest sections / weakest sections" callouts.

### 15.2 Peer comparison
Anonymized aggregate vs students with similar target programs.
- "Your profile is more complete than X% of similar students."
- Side-by-side bars: your-vs-peer-median per category.

Privacy: only shows if `consent.analytics=true`. Otherwise: "Peer comparison requires analytics consent. Manage in Data Rights."

---

## 16. Data tab

Per `43-data-rights-privacy.md` §8 student rights surface.

- **Consent toggles** (4 levers per `43` §2). Each toggle: 1-line explanation + "Last changed" + change history link.
- **Portable export** — JSON (full structured) + PDF (human-readable) of every signal.
- **Common App / Coalition format export** (MVP-extend, `92` §2) — maps the Universal Profile onto the Common App / Coalition field schema so the student can carry their work into those platforms (the "apply once, go anywhere" payoff). A field-mapping layer translates `profile field → Common App field`; unmapped fields are listed so nothing is silently dropped. Read-only in MVP (no write-back API to Common App).
- **LinkedIn import** (MVP-extend, `92` §2) — pre-fill Work / Education / Skills via the external-link channel (`41` §5.3); imported fields land `source: student-link`, confidence 75, student-confirmable. One-way (LinkedIn → UniPaith) in MVP.
- **Access log** table: who saw your data, when, what fields.
- **Delete account** button (in a "Danger zone" card): triggers 30-day grace + full purge.

---

## 17. Component breakdown

```
ProfileLayout
├── ProfileNav (tab strip + completion ring)
├── Tab: Overview
│   ├── PersonalHeader
│   ├── CompletionMap (13 cluster cards)
│   └── NextActionQueue
├── Tab: Identity
│   ├── ValuesEditor
│   ├── WorldviewEditor
│   ├── SelfAwarenessEditor
│   └── IdentitySummaryCard (with Regenerate)
├── Tab: Academics
│   ├── AcademicsSection
│   ├── TestScoresSection
│   ├── LanguagesSection
│   └── ResearchSection
├── Tab: Experience
│   ├── ActivitiesSection
│   ├── WorkServiceSection
│   ├── CompetitionsSection
│   ├── PortfolioSection
│   └── OnlinePresenceSection
├── Tab: Goals → GoalsStack
├── Tab: Needs → NeedsMap
├── Tab: Strategy → StrategyView + StrategyVersionsList
├── Tab: Preparation → DocumentsRepo + AccommodationsCard + SchedulingGrid + RecommendersList
├── Tab: Preferences → PreferencesForm
├── Tab: Financial → FinancialForm + AidLikelihoodCard
├── Tab: Timeline → ProfileTimeline
├── Tab: Analytics → ProfileAnalyticsView + PeerComparisonView
└── Tab: Data → ConsentTogglesPanel + PortableExportCard + AccessLogTable + DangerZoneCard
```

---

## 18. Data shape

Backend reads/writes via the Prompt Library schema (see `40-prompt-library-schema.md` §8). Frontend API client per existing patterns in `frontend/src/api/`.

Key types (TypeScript):

```ts
type ProfileOverview = {
  personal: PersonalRecord;
  completion: {
    overall_pct: number;
    per_category: Array<{ category: string; pct: number; last_updated: ISO8601 }>;
  };
  next_actions: Array<{ action: string; reason: string; deep_link: string }>;
};

type PersonalRecord = {
  legal_name: string;
  preferred_name: string | null;
  primary_email: string;
  primary_phone_number: string | null;
  date_of_birth: ISO8601;
  preferred_pronouns: string;
  current_address: Address;
  // … per `40` §3.1
};

type CompletionCategory =
  | 'identity' | 'academics' | 'experience' | 'goals' | 'needs'
  | 'strategy' | 'preparation' | 'preferences' | 'financial' | 'data';
```

The full list of types maps 1:1 to `40` field tables.

---

## 19. States

Each tab handles:
- **Loading** — skeleton placeholders for the cards.
- **Empty** — friendly nudge per section (e.g., "No activities yet. Add your first to surface relevant programs.").
- **Error** — toast + retry on save fail; banner + retry on load fail.
- **Success (Saved)** — inline "Saved at 14:32" by the section header for 2s, then fades.

Save pattern is autosave (debounced 800ms) for in-place edits; explicit Save button on multi-field sheets.

---

## 20. AI integration

| Surface | Agent | Trigger | Visibility |
|---|---|---|---|
| Identity tab → AI summary | `IdentitySummaryAgent` (`42` §11) | Initial + Regenerate button | Inline card; AI badge per `02` §15 |
| Strategy tab → Generated strategy | `StrategyAgent` (`42` §10) | First-time generate + Regenerate button | Inline card; AI badge + Why popover |
| Next-action queue | Derived from `next_questions_to_ask_user` + `recommended_next_actions` | Continuous | Each item shows source signal as a tooltip |
| Peer comparison | System-derived (rule-based) | Continuous | Disabled when `consent.analytics=false` |

---

## 21. Brand compliance checklist

- [ ] All colors via tokens (`--primary` for completion ring, `--accent` for eyebrows, `--text-mut` for meta text).
- [ ] Europa font only.
- [ ] No decorative imagery — content tells the story.
- [ ] Gold + cobalt together ≤ 15% of the visual area on any tab.
- [ ] Active tab gets the one yellow underline; no other gold accents in the tab strip.
- [ ] Eyebrow "PROFILE" at 12px / 600 / 0.22em uppercase, color `--accent`.
- [ ] Saved indicator uses `success` status (not gold).
- [ ] AI badges per `02` §15.

---

## 22. Current state vs spec — what to build

Per `90-current-vs-spec-gap-audit.md` G-S1:
- Current Overview tab is a long single-scroll super-page spanning 18 sections.
- Current tab strip has 7 tabs (Overview, Identity, Goals, Needs, Strategy, Essays & Resume legacy, Recommenders, Financial).
- Missing tab: Analytics (with peer comparison).
- Missing tab: Data Rights (the four-consent panel + export + access log + delete).
- Missing tab: Timeline (separate from the existing Phase-B widgets).

**Action steps:**
1. Reorganize tabs per §2 (13 tabs from the current 7).
2. Move Recommenders into Preparation; Financial into Preferences? No — keep Financial separate; spec calls it out.
3. Build Analytics tab with the two views.
4. Build Data Rights tab per `43` §8.
5. Build Timeline tab.
6. Migrate Essays & Resume legacy out (per `16-workshops.md`).
7. Wire `consent.training` lever (per `43` §2).
8. Persist Profile change events to `student_profile_timeline_events` table for the Timeline view.

Estimated effort: 4 engineering days.

---

## 23. Tests

- Tab routing: every `?tab=` value resolves and persists across reloads.
- Autosave debounce.
- AI summary regenerate failure → previous value preserved.
- Strategy clone-and-modify flow.
- Completion percent computed correctly per category.
- Consent toggles persist + audit-log + affect downstream AI calls.
- Portable export downloads JSON + PDF.
- Delete account: grace period + reversibility + final purge.

---

## 24. Copy strings (verbatim)

- "Your record" (H1).
- "Last updated 2h ago" / "Last updated 2 days ago" / "Last updated just now".
- "What's next" (next-action queue header).
- "Identity is the deepest layer of your profile…" (privacy disclosure).
- "Saved" (autosave indicator).
- "Manage in Data Rights →" (consent CTA).
- "Peer comparison requires analytics consent" (empty state when analytics off).
- "We couldn't reach the AI service. Showing your last summary." (fallback note).
- "Danger zone" (account-deletion card header).
- "Delete account" → confirm modal: "Are you sure? Your account and all profile data will be permanently deleted after a 30-day grace period."

---

## 25. Open questions / known gaps

- **Notifications section.** Lives in Settings, not Profile. Confirm with brand owner that this is the right home (alternative: a sub-section of Data Rights).
- **Financial tab vs Preferences.** Spec puts them separate; engineering simplicity suggests merging. Confirm.
- **Timeline tab population.** Need to decide which events show: every save? only meaningful changes? A daily-rollup? Recommend: every save + Discovery extractions + institution-supplied updates; filter UI for noise.
- **Peer-comparison source data.** Currently `peer_comparison_snapshot` is a stub. Aggregation pipeline needs design — recommend nightly compute per (target_major_field × target_degree_level × consent.analytics=true) cohort.
- **Editing inside the Discovery chat.** Should a student be able to mark a Discovery-extracted value as wrong from inside the profile tab (vs. only from the clarifications queue)? Recommend: yes; profile edit creates a `student-confirmed` override with confidence 95.
