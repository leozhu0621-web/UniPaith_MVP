# My Space — student personal hub (design)

**Date:** 2026-06-10 · **Status:** Approved by founder (this session) · **Scope:** student app IA restructure + QA

## Summary

"My Space" replaces the Apply surface and absorbs everything personal — Profile and Saved included.
The student app splits into surfaces about *the world* (Uni, Match, Connect) and one surface about
*me* (My Space). Internally My Space uses the **rooms layout ordered by the journey sequence**:
a mission-control Home on top, rooms beneath arranged Plan → Prepare → Apply & decide → Anytime → Record.

Grounding: synthesis of Master Paper, Business Methodology, Feature List V1, Roadmap, To-do list,
Prompt Library, Old Plan, Competition Analysis + a 4-area MVP audit (2026-06-10 workflow run
`wf_a50c342a-129`). The papers' concept is "the student's execution hub for the admissions cycle";
the mission-control Home implements the papers' "next-actions queue + portfolio dashboard".

## Decisions (founder-approved)

1. **Scope: everything personal** — My Space = manage tabs + Profile + Saved + scattered prep pieces.
2. **Primary job: mission control** — Home answers "what do I do next?".
3. **Structure: rooms by workstream, ordered by journey** (combine of the two proposed options).
4. **Name: "My Space"** (working name confirmed; runner-ups Hub / Workspace noted; papers' own
   vocabulary is My Applications / workspace / execution hub — too narrow for this scope).
5. **Delivery: design everything upfront; deployment sequencing delegated to Claude** (4 ships).

## 1. Name and top-level nav

| Position | Label | Route | Stage |
|---|---|---|---|
| 1 | Uni | `/s` | 1 — Discovery |
| 2 | Match | `/s/explore` | 2 — Recommendation |
| 3 | Connect | `/s/posts` | 3a — Outreach |
| 4 | My Space | `/s/space` | Me — spans all stages |

- Nav icon: `Backpack` (lucide); alternate `LayoutDashboard`.
- Avatar dropdown slims to Settings · Feedback inbox (owner) · Sign out. Profile and Saved are
  reachable from the My Space rail (their URLs do not change).
- Mobile bottom tab bar: same 4 items; My Space tab opens Home; rooms via horizontal pill row.

## 2. URL scheme and redirects

Flat URLs; unification comes from a shared shell (`MySpaceLayout`), not nested paths.

| Room | URL | Today |
|---|---|---|
| Home | `/s/space` | new |
| Saved | `/s/saved` | unchanged |
| Prep | `/s/prep` | new (tabs: workshops · prompts · interviews · recommenders · documents) |
| Applications | `/s/applications` | legacy redirect → becomes a real route again |
| Calendar | `/s/calendar` | legacy redirect → becomes a real route again |
| Messages | `/s/messages` | legacy redirect → becomes a real route again |
| Profile | `/s/profile` | unchanged |

`/s/manage` retires with param-preserving redirects:

- bare or `?tab=applications` → `/s/applications`; bare with no tab → `/s/space`
- `?tab=calendar` → `/s/calendar`
- `?tab=messages&thread=X&program=Y` → `/s/messages?thread=X&program=Y` (params preserved — fixes
  the audited param-dropping bug in `ManagementPage.switchTab`)
- `?tab=prompts` → `/s/prep?tab=prompts`; `?tab=workshops` → `/s/prep?tab=workshops`

All entries in `STUDENT_LEGACY_REDIRECTS` (`frontend/src/utils/information-architecture.ts`)
re-point to final destinations — one hop, never chains. The contract test
(`frontend/src/test/information-architecture.test.ts`) updates in lockstep.
`ManagementPage.tsx` dissolves into `MySpaceLayout` + `MySpaceHomePage` + `PrepPage`.

Known rename touchpoints (closed set, from audit): `StudentLayout.tsx` NAV_ITEMS,
`GlobalSearch.tsx` QUICK_LINKS, `ApplicationsPage.tsx` eyebrow, `ApplicationDetailPage.tsx`
breadcrumb, `OnboardingPage.tsx` step title, `MessagesNavButton.tsx`, `connect/UpdatesTab.tsx`
request-info deep link, `inbox/ThreadView.tsx` calendar link, `StudentTitle.tsx` MANAGE_TABS.

## 3. Shell — journey-ordered rooms

Desktop: slim left rail inside existing content width. Rail groups (sentence-case eyebrows):

- (ungrouped) **Home**
- **Plan** — Saved
- **Prepare** — Prep
- **Apply & decide** — Applications
- **Anytime** — Calendar · Messages
- **Record** — Profile

Nav item "My Space" is active for any room route. Every room renders the density layer
(`PageHeader` eyebrow "My Space", `SectionHeader`, `ListRow`, `StatTile`). Eyebrow scheme is
standardized across the app: eyebrow = parent surface name (Connect drops "Stage 3 ·").

## 4. Home — mission control v1

Client-side composition (TanStack Query) of existing endpoints; **zero backend changes for v1**:

| Pane | Content | Source |
|---|---|---|
| Up next | 3–5 most important actions: per-application next steps, overdue checklist items, pending clarifications, interview responses | applications next-step logic + `/students/me/intake/clarifications` |
| Pipeline | Saved → In progress → Submitted → Offers counts linking into rooms | applications + saved lists |
| Deadlines | next 14 days | `GET /me/calendar` |
| Waiting on others | outstanding recommender requests, institution-owned checklist items | recommendations + checklists |
| Latest feedback | recent workshop feedback runs + unread thread count | workshop runs + inbox |

Empty state: brand-new student sees a guided strip pointing at Uni and Match. Panes are shaped to
receive the (deferred) AI readiness layer later. Optional `GET /students/me/home` aggregate endpoint
is a later optimization, not v1.

## 5. Gathering map

| Feature | From | To |
|---|---|---|
| Workshops | `/s/manage?tab=workshops` | Prep › Workshops |
| Prompt Library + Story Bank + major tracks | `/s/manage?tab=prompts` | Prep › Prompts |
| Recommenders | Profile › Preparation | Prep › Recommenders |
| Documents | Profile › Preparation | Prep › Documents |
| Interviews (new consolidated list) | scattered, no list view | Prep › Interviews (contextual panels stay) |
| Scheduling availability | Profile › Preparation | Prep › Interviews |
| Financial aid tools + cost comparison | Profile › Financial | Applications › Costs & aid |
| Scholarship match (orphaned endpoint) | `GET /students/me/scholarships/match`, zero consumers | Applications › Costs & aid |
| Offers overview | per-application only | Applications › Offers |

Applications room views: All · Offers · Costs & aid. Prep tabs: Workshops · Prompts · Interviews ·
Recommenders · Documents. Profile slims 13 → 11 tabs (Preparation, Financial leave; alias
redirects: `?tab=preparation[&section=recommenders]` → `/s/prep?tab=recommenders`,
`?tab=financial` → `/s/applications?tab=costs`).

## 6. QA workstream (ships first, independent)

1. (high) API errors render as "No applications yet" — `ApplicationsPage.tsx:121`
2. (high) StoryEditor drops `stakeholder_type` on edit — `apply/promptlibrary/StoryEditor.tsx`
3. (med) Recommender "send" never emails — `api/recommendations.py:139` (SES provisioned; wire real send)
4. (med) Interview Confirm silently books first slot — `interviews/InterviewRespondPanel.tsx:52`
5. (med) ApplicationDetailPage fixed 240px sidebar, not responsive — `ApplicationDetailPage.tsx:419`
6. (med) Essays tab calls deprecated shim — migrate to workshop-feedback/documents flow, unblocks Phase E
7. (med) Legacy essay feedback gated on wrong flag — `essay_workshop_service.py:179`
8. (med) EnrollmentPanel blank on query error — `apply/enrollment/EnrollmentPanel.tsx:140`
9. (med) Stale workshop run relabeled to newly selected program — `apply/EssayFeedbackPanel.tsx:58` + siblings
10. (med) Null tuition ranks as "Lowest net cost" — `FinancialAidPage.tsx:92`
11. (med) Tab strips lack tablist semantics — `ManagementPage.tsx:56`, `WorkshopsTab.tsx:76`
12. (med) CLAUDE.md IA table stale (Uni rename, 13 profile tabs, Prompts tab) — fix with Ship 2

## 7. Backend touches (no migrations)

- Real SES send for `POST /students/me/recommendations/{id}/send` (+ tests with mocked SES).
- One-line flag fix in `essay_workshop_service.py`.
- Relocate checklist/readiness endpoints out of `api/workshops.py` (paths unchanged) so Phase E
  deletion of that file unblocks; then delete essay/resume shims + orphaned `/messages`
  conversations router once frontend item 6 lands.

## 8. Out of scope (parked follow-ups)

AI readiness layer (deadline-risk bands, submission forecasts, nudge schedules) · workshop
organizational layer (essay versioning, program variants, test-score submission sets) ·
direct-admissions inbound offers · per-application recommender linking (schema change) ·
deeper Profile re-grouping · `match_results.match_score` column drop (Phase E ops).

## 9. Testing

IA contract test updates in lockstep with route changes; redirect param-preservation tests;
room-shell render tests; home-pane tests with mocked queries; backend pytest for SES send (mocked);
tablist a11y verified. Full suites green before every ship.

## 10. Deployment — four ships

1. **Ship 1:** QA fixes (items 1–11).
2. **Ship 2:** shell — nav rename, `/s/space` home, rooms, redirects, CLAUDE.md update (item 12).
3. **Ship 3:** gathering moves (Prep consolidation, Costs & aid, Profile slimming, avatar dropdown).
4. **Ship 4:** polish — eyebrows, breadcrumbs, titles, dead code, backend cleanup (§7 deletions).

Each ship: tsc 0 · build 0 · tests green → merge `main` → auto-deploy → verify live
(app.unipaith.co bundle grep + api smoke), per the standing ship-to-production rule.
