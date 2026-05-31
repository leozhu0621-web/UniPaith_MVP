# 10 · Discovery — Type-First Program Search

> The student-facing program search engine. Type-first natural-language entry, LLM query interpretation into editable constraint chips, filters, and a programs-only result format. Sits inside `/s/explore` below the StrategyView.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/s/explore` (search + filters region). Companion: `09-program-match.md`.

---

## 1. Purpose

Two entry modes:
1. **Type a query in natural language.** "MS in Computer Science in California under $50k starting fall 2027."
2. **Pick a broad genre tile.** Computer Science · Business · Health · etc.

Both open the program library with constraints applied. The library returns **programs** (not schools, not mixed entity types). School / location / major in the query are treated as **scope constraints** that filter programs.

---

## 2. Visual layout (Discovery region inside `/s/explore`)

```
Search [What kind of program are you looking for?              ⌕ ]

[ Or browse:  CS · Business · Health · Arts · Engineering · Law · ... ]

[Degree · Master's ✕] [Location · California ✕] [Budget · ≤ $50k ✕] [+ Add]
[Filters ▾] [Sort: Relevance ▾] [Saved view ▾]

RESULTS (24)
┌──────────┐ ┌──────────┐ ┌──────────┐
│ ProgramCard│ ProgramCard│ ProgramCard│
└──────────┘ └──────────┘ └──────────┘
...
```

---

## 3. Search submit flow

1. Student types query → presses Enter (or 800ms debounce).
2. POST query → `DiscoveryQueryInterpreter` (`45-ai-agents-claude.md` §12).
3. Response: list of structured constraints (each `{category, value, display, confidence}`).
4. Render each as a chip.
5. Run library search with chips → return programs.

If `confidence < 70` on any chip: chip rendered with a small `?` icon prompting the student to confirm.

---

## 4. Constraint chips (CRITICAL pattern)

Per `02-design-system.md` §9. Each chip is independently editable + removable.

```
┌──────────────────────────────┐
│ Degree · Master's        ✕   │
└──────────────────────────────┘
```

**Click the label** → edit-in-place sheet/dropdown for that field type.
**Click ✕** → remove the chip; re-run search.

Categories supported:
- `degree_level` (enum: certificate, associate, bachelor, master, doctorate, professional).
- `major` (free-text autocomplete from CIP taxonomy).
- `location` (country / region / city / metro).
- `budget` (range slider).
- `format` (in_person / online / hybrid).
- `start_term` (season + year).
- `duration` (range slider).
- `selectivity` (low / med / high / very_high).
- `other` (free-text — for nuance the interpreter can't categorize).

Each chip is also a filter — the chip strip and the filters panel stay in sync.

---

## 5. Filters panel

Open via [Filters ▾]. Mirrors `42-prompt-library-schema.md` filter set + program-specific fields. Per Master Paper:

- Country / state / city / distance from selected.
- Campus setting (urban / suburban / rural).
- Degree level + type.
- Delivery format.
- Estimated total cost range.
- Field of study + major.
- Prerequisite flags.
- Program duration.
- Program name / school name.
- Acceptance rate range.
- Tuition range + max tuition ceiling.
- Start term.

**Featured filters** (when student has stated them — surfaced separately):
- Best return within my constraints.
- Cost-to-outcome ratios.
- Employer concentration level / feedback score / hire rate.
- Employment / underemployment rate.
- Graduate placement geography distribution.
- Internship to offer conversion rate.
- Payback period bands.
- Salary distribution ranges.
- Starting salary bands.
- Top hiring employers.

Filters and chips coexist: filters apply persistently; chips are session-derived from query.

---

## 6. Sort options

- Relevance (default — match relevance score from search engine).
- Fitness score (when matches available).
- Confidence score.
- Tuition (ascending).
- Tuition (descending).
- Acceptance rate (ascending).
- Acceptance rate (descending).
- Deadline (earliest).
- Recently added.

---

## 7. Programs-only result format

Per Master Paper: "Search results are displayed as programs, not mixed entity types."

- Student types a school name → school becomes scope; results = programs in that school.
- Student types a location → location becomes scope; results = programs in that region.
- Student types a major → major becomes constraint; results = programs across the library that match.

Each result is a `ProgramCard` (`02-design-system.md` §5). Three hover actions: Save / Add to Compare / Open.

---

## 8. Compare tray

A global compare tray accumulates selected programs across sessions. Lives at the bottom of the viewport:

```
[ 3 programs in Compare · Open compare ]
```

Click → `/s/explore?compare=open` opens a side-by-side compare sheet with:
- Program structure + format.
- Location + setting.
- Cost + affordability.
- Access + competitiveness.
- Outcomes + employer signals.

Maximum 4 programs in compare. Beyond that, "remove one to add another."

---

## 9. Data shape

```ts
type ConstraintChip = {
  id: string;
  category: 'degree_level' | 'major' | 'location' | 'budget' | 'format' |
            'start_term' | 'duration' | 'selectivity' | 'other';
  value: string | number | { min: number; max: number };
  display: string;
  confidence: number;     // 0-100
  user_confirmed: boolean;
};

type SearchRequest = {
  query: string | null;
  chips: ConstraintChip[];
  filters: FilterState;
  sort: SortOption;
  page: number;
};
```

Endpoints:
- `POST /me/search/programs` — body: SearchRequest; returns `{results: ProgramCard[], total: int}`.
- `POST /me/search/interpret` — body: `{query: string}`; returns chips (calls `DiscoveryQueryInterpreter`).
- `GET /me/compare` — current compare set.
- `POST /me/compare/add` / `DELETE /me/compare/:program_id` — manage set.

---

## 10. URL state

- `q=` — current query text.
- `chips=` — JSON-encoded chip list.
- `filters=` — JSON-encoded filter state.
- `sort=` — sort option.
- `compare=open` — compare sheet open.

Deep-link reproducible. Sharing a URL reproduces the exact results view.

---

## 11. States

- **Empty (first visit, no query)** — show genre tiles + "Or type what you're looking for above" hint.
- **Loading** — skeleton grid of 6 cards.
- **No results (too narrow)** — "No programs match. Try removing a chip or widening Budget." + suggested-relaxation links.
- **No results (too broad)** — "Showing 5,000+ programs. Add a constraint to narrow."
- **Interpreter low-confidence** — chips render with `?` icon; student must confirm.
- **Search service down** — fall back to keyword search; banner "Limited search active."

---

## 12. AI integration

| Agent | Trigger | Output |
|---|---|---|
| `DiscoveryQueryInterpreter` | Search submit | Constraint chips |
| Future: `MatchRerankAgent` (Phase 14) | After initial search | Re-rank with personalized weights |

---

## 13. Brand compliance

- Chips: pill radius, 1px `--accent` border, `--surface` bg, `--text` label.
- Active filter count: `--accent` color badge.
- Genre tiles: `--muted` bg, no decorative icons (Lucide-only).
- No gold in the chips region — gold is reserved for the Compare tray CTA at the bottom.

---

## 14. Gaps (from `47`)

- G-S3 (major): structured constraint chips not yet wired.
- G-AI6 (major): `DiscoveryQueryInterpreter` agent doesn't exist.
- Currently single NLP-summary chip; spec calls for per-constraint chips.

---

## 15. Tests

- Query "MS CS in California under $50k" → 3 chips (degree, location, budget).
- Remove chip → re-search.
- Click chip → edit-in-place → re-search.
- Genre tile → opens library with category scope chip.
- URL chip state survives reload.
- Compare tray persists across page navigation.

---

## 16. Copy

- "What kind of program are you looking for?" (placeholder).
- "Or browse:" (genre tiles label).
- "+ Add" (add a chip manually).
- "Filters" / "Sort" / "Saved view".
- "Showing X programs" (results count).
- "No programs match. Try removing a chip or widening Budget."
- "Limited search active" (fallback banner).
- "Just to confirm — did you mean X?" (low-confidence chip prompt).

---

## 17. Open questions

- **Genre tile categories.** Master Paper says "Computer Science and Data" — full catalog TBD. Recommend: 12 tiles covering 80% of CIP top-level groupings.
- **Saved views.** Should users save a (chips + filters + sort) tuple as a named view? Recommend yes, in Phase 2; for MVP, URL-based bookmarking suffices.
- **Search infrastructure.** Currently uses backend `searchPrograms` (likely Postgres FTS or pgvector). For scale, may need Elasticsearch / Algolia. Defer.
- **Compare tray persistence.** Cross-device? Recommend: persist server-side per user (table `student_compare_lists`).
