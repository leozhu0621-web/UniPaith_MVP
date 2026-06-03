# 79 · Data Tables, Dense Lists & the Institution Workspace — Build Spec

> Make the institution side feel like an enterprise system-of-record, not a demo: one reusable dense-table system (sort, paginate/virtualize, density, row-selection + bulk actions, keyboard, export, saved views) applied to every admissions queue, plus the operational-credibility finish the papers demand. This is the bulk of the "both sides" coverage. Extends the `Table` primitive (`02` §8) and the virtualization mechanism (`54` §8). Companion to `75`, `76` (tokens), `80` (keyboard), `31`/`32`/`28`/`36` (institution surfaces).
>
> Status: **draft v2.0** · 2026-06-02 · v2 = first issue. Counts from the 2026-06-02 audit.

---

## 1. What exists vs what to build (ground truth)

`components/ui/Table.tsx` is a good start — **sticky header, zebra rows, overflow-x, built-in loading skeleton + empty message**. But it stops there, and the institution surfaces that need density most don't even paginate.

- **No pagination.** Only 4 institution files reference paging; real pager UI exists in just 2 (`AuditLogPage.tsx`, `segments/AudiencePreview.tsx`). `PipelinePage`, `StudentDetailPage`, `InquiriesPage`, `CampaignsPage`, and the recruitment/list views render **unbounded** result sets. Student `ExplorePage` loads `page_size: 50` with no "load more."
- **No sort, density, selection, or export** built into `Table`; columns are typed `any` (`render?: (row: any)`).
- **The Kanban** (`PipelinePage`, dnd-kit) has list/review/priority views but no keyboard path (`80`), `min-w-[240px]` columns that overflow on small screens, and `as any` on a Badge variant (`:97`).
- Analytics (`analytics/OverviewTab.tsx`) is the *best* institution surface (recharts + semantic tokens + skeletons + per-chart error/empty) — its patterns should propagate, not be one-offs.

**Principle (from the papers):** the institution side is the "AI admission operating system" — its credibility comes from **system-of-record trust, auditability, and human-in-the-loop control**, not delight (`75` §2.5). The competitor lesson is explicit: Liaison/legacy CAS lose on "dated, inconsistent" workflow UX; Element451 wins on a "modern, contemporary" admissions UI. The bar is **modern, consistent, dense-but-legible, and obviously human-controlled.** Cobalt only — no gold on the institution side.

---

## 2. The reusable dense-table system

Extend `Table.tsx` into a `DataTable` that every institution list consumes. One component, declarative columns:

```tsx
<DataTable
  columns={cols}            // typed Column<Row>[] — no more `any`
  data={rows}
  getRowId
  sort                      // controlled multi-sort, URL-synced (54 §2 URL state)
  pagination | virtualized  // pick per surface (§2.3)
  selection                 // row checkboxes → bulk-action bar (§2.4)
  density                   // "comfortable" | "compact" (§2.5)
  onExport                  // CSV (§2.6)
  stickyFirstColumn         // for wide tables (§2.1)
  emptyState errorState     // 67 components
/>
```

### 2.1 Column model
Typed `Column<Row>` (kills the `any`): `{ id, header, accessor, width?, align?, sortable?, sticky?, render? }`. Wide tables pin the identifying first column (`stickyFirstColumn`) so the applicant/program name stays visible while scrolling horizontally. Numeric columns right-align; status columns use `BandBadge`/status chips.

### 2.2 Sorting
Header click toggles asc/desc/none; shift-click adds a secondary sort. Sort state lives in the URL (`?sort=match:desc,name:asc`) per `54` §2 so it survives reload and is shareable. A clear sort affordance + aria-sort on the header (`80`).

### 2.3 Pagination vs virtualization
- **Server-paginated** (default for admissions queues): cursor pagination from `50` §5, `keepPreviousData` so the table doesn't flash on page change (`54` §3). Pager footer: page size selector (25/50/100), range ("1–50 of 2,431"), prev/next.
- **Virtualized** (long client-held lists > 50 rows — pipeline, feed, inbox): `@tanstack/react-virtual` per `54` §8. Never render thousands of DOM rows.
- **Rule:** no surface fetches or renders an unbounded set. Every list is one of these two.

### 2.4 Row selection + bulk-action bar
Checkbox column → header "select all (this page)". When ≥1 row selected, a **bulk-action bar** docks (count + actions: assign, advance stage, message, export, tag). This is the admissions workhorse (batch decisions already exist server-side per `31`/`34`); the UI makes them first-class. Bulk destructive actions route through `ConfirmDialog` (`78`).

### 2.5 Density modes
A comfortable/compact toggle (persisted in `ui-store`). Compact tightens row height + padding for power users scanning hundreds of applicants (the Linear/ATS density bar) without abandoning the 4px rhythm (`76` §5). Default comfortable; remember the choice.

### 2.6 CSV export
`onExport` streams the current view (respecting filters + sort) to CSV — institutions live in spreadsheets. `AuditLogPage` already has `?format=csv`; generalize. Export reflects what's on screen, not a different query.

### 2.7 Saved views
Reuse the saved-search mechanism (`56`) so an admissions reviewer can save "Unread + Reach band + sort by fit" as a named view and return to it. URL-state-backed (`54` §2), so a view is just a saved URL.

---

## 3. Institution-workspace finish (operational credibility)

Apply the system + a consistent operational shell across the dense surfaces:

| Surface | File | Density work |
|---|---|---|
| Admissions pipeline | `PipelinePage.tsx` | `DataTable` list view + virtualized Kanban (§4); bulk-action bar; sort by fit/date/stage |
| Applicant review | `StudentDetailPage.tsx` | paginate the per-applicant lists; sticky identity header; reviewer-control affordances visible |
| Inquiries | `InquiriesPage.tsx` | `DataTable` + assignment + overdue sort; bulk assign |
| Attribution analytics | `analytics/*` | already strong — propagate its error/empty/skeleton patterns; export |
| Audit log | `AuditLogPage.tsx` | already paginates + CSV — align to `DataTable` |
| Recruitment | `recruitment/*Tab` | `DataTable` for prospect lists; bulk segment/convert |
| Campaigns / segments | `CampaignsPage.tsx`, `segments/*` | paginate; bulk actions |

**Cross-cutting operational shell:**
- **Human-in-the-loop is visible** (paper guarantee, `75` §2.5): any AI-assisted column/row carries `AIBadge`; the *action* (advance, decide, message) is always a reviewer control, never auto-applied. Decision surfaces state "you're deciding" explicitly.
- **Consistent toolbar** above every table: search (debounced 200ms, `53` §3) + filters (URL-synced) + density toggle + export + saved-views, in the same order everywhere.
- **Cobalt only.** No gold on institution surfaces (`76` §2.4). Status uses status tones.
- **Result counts + freshness**: "2,431 applicants · updated just now" — system-of-record signals (`75` §2.5).

---

## 4. The pipeline Kanban (special case)

`PipelinePage` Kanban is the densest interactive surface:
- **Virtualize** columns (cards can number in the hundreds per stage).
- **Keyboard DnD** via dnd-kit's keyboard sensor + ARIA (`80`): pick up / move / drop a card without a mouse, with `aria-live` announcements ("Moved Jordan to Interview"). Today there is no keyboard path at all.
- **Mobile/overflow**: `min-w-[240px]` columns overflow; on small screens collapse to a stage-switcher + single-column list (the list view), not a broken horizontal scroll (`03` responsive).
- Fix the `as any` Badge variant (`:97`) → typed.
- Stage-move stays optimistic with rollback (`54` §4) + the success confirmation (subtle, cobalt — not the gold beat; gold is student-only).

---

## 5. Other dense lists (non-table)

The same "no unbounded list" rule applies to the feed (`20`) and inboxes (`17`/`29`): virtualize > 50 rows (`54` §8), infinite scroll with scroll-position restore (`53` §3). These aren't tables but share the pagination discipline.

---

## 6. Build tasks (checklist)

- [ ] Extend `Table.tsx` → `DataTable` with typed `Column<Row>`, controlled multi-sort (URL-synced), pagination + virtualization modes, row selection + bulk-action bar, density toggle, CSV export, sticky first column, `QueryError`/`EmptyState` slots.
- [ ] Replace unbounded fetches: `PipelinePage`, `StudentDetailPage`, `InquiriesPage`, `CampaignsPage`, recruitment/segment lists → paginated or virtualized.
- [ ] Add the consistent table toolbar (search + filters + density + export + saved-views) across institution surfaces.
- [ ] Kanban: virtualize columns, add keyboard DnD + ARIA announcements, mobile collapse, fix `as any`.
- [ ] Wire saved views via `56`; persist density in `ui-store`.
- [ ] Make AI-assisted columns carry `AIBadge`; keep all actions reviewer-controlled; add result-count + freshness line.
- [ ] Virtualize feed + inbox lists (> 50 rows).

---

## 7. Acceptance

- [ ] No institution (or student) list fetches/renders an unbounded set; all paginate or virtualize.
- [ ] `DataTable` columns are typed (no `any`); sort state is in the URL and survives reload.
- [ ] Row selection drives a bulk-action bar; bulk destructive actions confirm via `ConfirmDialog`.
- [ ] Density toggle works and persists; CSV export reflects the current filtered/sorted view.
- [ ] Pipeline Kanban is fully keyboard-operable with `aria-live` move announcements; usable on a phone.
- [ ] Institution surfaces are cobalt-only; AI columns badged; human action never auto-applied; result-count + freshness shown.

---

## 8. Open questions

- **Build vs adopt.** Hand-extend `Table` vs adopt TanStack Table (`@tanstack/react-table`) headless for sort/selection/column model. Recommend TanStack Table headless (pairs with `react-virtual` already chosen in `54`) — proven, keeps our markup/tokens.
- **Saved views storage.** Per-user server-side (durable, cross-device) vs URL-only. Recommend server-side via `56` for institution reviewers who reuse views daily.
- **Mobile institution scope.** Is the institution side expected to be genuinely mobile-usable for v1, or desktop-first with graceful degradation? Recommend desktop-first + the Kanban-collapse fallback so it's not *broken* on mobile, full mobile polish post-launch (`75` §9).
