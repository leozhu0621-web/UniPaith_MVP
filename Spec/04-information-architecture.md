# 04 · Information Architecture

> Complete route map, role-based access, navigation hierarchy, and cross-page navigation rules for the UniPaith app at `app.unipaith.co`. Marketing site at `unipaith.co` is WordPress; not covered here.
>
> Status: **draft v1.0** · 2026-05-29 · Used by every feature spec.

---

## 1. Domain layout

| Domain | Owner | Purpose |
|---|---|---|
| `unipaith.co`, `www.unipaith.co` | WordPress on EC2 (see `App_MVP/CLAUDE.md`) | Marketing landing, blog, public info pages. |
| **`app.unipaith.co`** | React app (this repo) | Authenticated student + institution experience. |
| `api.unipaith.co` | FastAPI on ECS | API. |

This spec covers `app.unipaith.co` only.

---

## 2. Role model

Three role values:
- `student` — paying or trial individual using the journey.
- `institution_admin` — an institution staff member (admissions officer, recruiter, marketing, IT).
- `admin` — placeholder; **no platform admin tier in this MVP** (per the two-sided model decision documented in user memory and the recent removal of platform admin / crawler / NYU seed).

Auth tier and provider (per existing setup): AWS Cognito in production; `COGNITO_BYPASS=true` in dev. Token format in dev: `dev:<user_id>:<role>`.

Google sign-in is **not configured** in Cognito; the broken Google buttons were removed (per user memory). Email + password is the working auth path.

---

## 3. URL grammar

| Prefix | Audience | Auth required | Role guard |
|---|---|---|---|
| `/` | Anyone (redirects to `/login`) | No | — |
| `/login` `/signup` `/auth/*` | Anyone | No | — |
| `/browse` `/school/:id` `/program/:id` | Public | No | — |
| `/onboarding` | First-run student | Yes | `student` (also redirects on completion) |
| `/s/*` | Student app | Yes | `student` |
| `/i/*` | Institution app | Yes | `institution_admin` |

Catch-all → `/login`.

---

## 4. Student app routes (`/s/*`)

### 4.1 Top-level — the four stages

The student app is structured around the journey stages from the Master Paper, not by tool type. Four main pages, each tied to a stage:

| URL | Top-nav label | Stage | Purpose | Spec doc |
|---|---|---|---|---|
| `/s` | **Discover** | 1. Discovery | LLM-led 3-track journey (Profile / Goals / Needs) with chat + live artifact rail | `1B-discovery-stage-conversation.md` |
| `/s/explore` | **Match** | 2. Recommendation | Strategy view (top) + Programs/Schools grid; dual scores (fitness + confidence) | `11-program-match.md`, `12-discovery.md` |
| `/s/manage` | **Apply** | 3b/3c. Preparation + Application Mgmt | Applications · Calendar · Messages · Workshops (feedback-only) | `15`, `16`, `17`, `18`, `19`, `1A` |
| `/s/posts` | **Connect** | 3a. Connection & Outreach | Updates / Events / Peers tabs from followed institutions | `1C-connect.md` |

### 4.2 Avatar-dropdown surfaces

| URL | Label | Purpose | Spec doc |
|---|---|---|---|
| `/s/profile` | **Profile** | 19-section durable profile workspace (see §4.3 for the tab structure inside) | `10-universal-profile.md` |
| `/s/saved` | **Saved** | Saved programs and schools, reach/target/safer grouping, compare, convert to application | `15-saved-list.md` |
| `/s/settings` | **Settings** | Account, notifications, locale, security, account deletion | `1D-settings.md` |

### 4.3 Drill-down routes

| URL | Purpose | Spec doc |
|---|---|---|
| `/s/programs/:programId` | Program detail page (editorial). **Currently routed as `SchoolDetailPage` — the file is mis-named; tracked in `90-current-vs-spec-gap-audit.md`.** | `13-detail-pages-program.md` |
| `/s/schools/:programId` | Alias of `/s/programs/:programId` (same component) | `13` |
| `/s/institutions/:institutionId` | Institution (university) detail page, schools-first IA | `14-detail-pages-school.md` |
| `/s/institutions/:institutionId/schools/:schoolId` | School-within-institution detail (e.g., "School of Engineering" inside the university) | `14` |
| `/s/applications/:appId` | Per-application workspace (status timeline, checklist, documents, essays, resume, interviews, guardrails, offer) | `17-applications.md`, `1A-decisions-offers.md` |

### 4.4 Legacy redirects (still resolve)

All of these resolve to the new IA. Spec'd here so future audits know they're intentional:

| Old route | Redirect target |
|---|---|
| `/s/dashboard` | `/s` |
| `/s/chat` | `/s` |
| `/s/discover` | `/s/explore` (Discover was the legacy name for the search engine; "Match" replaces it in the IA) |
| `/s/match` | `/s` (legacy ProgramMatch — replaced by Discover + Explore) |
| `/s/applications` | `/s/manage` |
| `/s/calendar` | `/s/manage?tab=calendar` |
| `/s/deadlines` | `/s/manage?tab=calendar` |
| `/s/messages` | `/s/manage?tab=messages` |
| `/s/messages/:convId` | `/s/manage?tab=messages` (id discarded — TODO carry through) |
| `/s/financial-aid` | `/s/profile?tab=financial` |
| `/s/recommendations` | `/s/profile?tab=recommenders` |
| `/s/resume-workshop` | `/s/manage?tab=workshops` |
| `/s/essay-workshop` | `/s/manage?tab=workshops` |
| `/s/test-scores` | `/s/profile` |
| `/s/decisions` | `/s/manage` |
| `/s/intake` | `/s` |
| `/s/intelligence` | `/s` |

### 4.5 Onboarding

`/onboarding` is the first-run experience. After completion → `/s` (Discover home). Per audit, the current `OnboardingPage.tsx` is a single-thread chat with a heuristic completion meter; it does NOT seed `discovery_sessions` rows. Spec recommendation: either convert it into a thin shim that creates the first `discovery_sessions` row and routes to `/s?track=profile&layer=basic`, or delete it and route signups directly into `/s` with a first-run banner (see `90` for the gap discussion).

### 4.6 Profile (`/s/profile`) tab structure

Profile is the durable record across all stages. The spec calls for **19 sections** (`10-universal-profile.md`). Current implementation has 7 tabs that cluster sections; this spec reorganizes them per Master Paper structure:

```
/s/profile
  ?tab=overview     ← progress ring + completion map + next-action queue
  ?tab=identity     ← Identity Layer (deepest profile depth — values, worldview, self-awareness)
  ?tab=academics    ← Academics, Test Scores, Languages, Research (a discipline cluster)
  ?tab=experience   ← Activities, Work & Service, Competitions, Portfolio, Online Presence
  ?tab=goals        ← SMART goal stack
  ?tab=needs        ← Maslow-keyed needs map
  ?tab=strategy     ← Active broad strategy + versioned history
  ?tab=preparation  ← Documents, Accommodations, Scheduling, Recommenders
  ?tab=preferences  ← Preferences (location, modality, finances, etc.)
  ?tab=financial    ← Financial aid intent + budget
  ?tab=timeline     ← Profile-progress timeline
  ?tab=analytics    ← Profile analytics view (completion %, activity, peer comparison)
  ?tab=data         ← Data Rights & Export (consent dimensions + portable export)
```

That's 13 tabs covering all 19 sections. Notifications live in `/s/settings`; "Personal" (the first section of the spec — name/email/phone/etc.) lives at the top of the Overview tab as a header block. The grouping rationale is in `10-universal-profile.md` §3.

---

## 5. Institution app routes (`/i/*`)

### 5.1 Top-level — unified surfaces

The institution app uses 4 unified workspaces in the top nav (per the recent "unified pages" reorganization), plus a programs surface for content management. Each top-level surface hosts sub-tabs.

| URL | Top-nav label | Purpose | Sub-tabs | Spec docs |
|---|---|---|---|---|
| `/i/dashboard` | **(home)** | Executive cockpit | — | (covered in `30`) |
| `/i/admissions` | **Admissions** | Pipeline / Interviews / Inquiries / Cohort Compare | `?tab=pipeline\|interviews\|inquiries\|cohort-compare` | `30`, `31`, `32` |
| `/i/outreach` | **Outreach** | Campaigns / Promotions / Events / Posts | `?tab=campaigns\|promotions\|events\|posts` | `23`, `25` |
| `/i/communications` | **Communications** | Templates & AI Drafts / Segments / Inbox | `?tab=templates\|segments\|inbox` | `24`, `27` (inbox) |
| `/i/programs` | **Programs** | Program list + editor | — | `21` |

### 5.2 Drill-down + legacy direct routes

These resolve directly (no redirect — the unified surfaces use sub-tabs but the underlying pages are individually addressable):

| URL | Purpose | Spec doc |
|---|---|---|
| `/i/programs/new` | New program editor | `21` |
| `/i/programs/:id/edit` | Existing program editor | `21` |
| `/i/pipeline` | Pipeline page direct | `30` |
| `/i/pipeline/:studentId` | Per-applicant review packet | `31` |
| `/i/interviews` | Interview management direct | `32` |
| `/i/messages` | Messaging inbox direct | `27-institution-messaging.md` |
| `/i/segments` | Segment builder direct | `24` |
| `/i/campaigns` | Campaign builder direct | `23` |
| `/i/events` | Event manager direct | `25` |
| `/i/posts` | Post manager direct | `25` |
| `/i/inquiries` | Inquiry queue direct | (covered in `30`) |
| `/i/promotions` | Promotions direct | `25` |
| `/i/audit-log` | Audit log direct | `34` |
| `/i/templates` | Templates direct | (covered in `23`) |
| `/i/cohort-compare` | Cohort comparison direct | `31` |
| `/i/intake-rounds` | Intake round management | (covered in `21`) |
| `/i/requirements` | Per-program checklist items | (covered in `21`) |
| `/i/analytics` | Institution analytics | `26` |
| `/i/data` | Data upload workspace | `22` |
| `/i/settings` | Institution profile + rubric + notifications | `1D-settings.md` §3 |
| `/i/setup` | First-run institution wizard | `28-institution-setup.md` |

Both direct + unified routes work — the unified surfaces give a cleaner nav; the direct routes are deep-link targets from emails, audit-log entries, and AI drafts.

---

## 6. Public routes

| URL | Purpose | Notes |
|---|---|---|
| `/browse` | Public program browse | Linked from marketing-site CTAs. No login required. |
| `/school/:institutionId` | Public institution page | The page a search engine indexes. Mirrors `/s/institutions/:institutionId` but without authenticated actions (save, RSVP). |
| `/program/:programId` | Public program detail | Same relationship to `/s/programs/:programId`. |

Anonymized — no engagement logging unless the visitor signs in.

---

## 7. Navigation chrome

### 7.1 Student top nav (logged in)

```
┌────────────────────────────────────────────────────────────────────────┐
│  [Wordmark]    Discover  Match  Apply  Connect              [avatar]   │
└────────────────────────────────────────────────────────────────────────┘
```

- 64px tall, `--bg` background, 1px bottom border `--border`.
- Wordmark left links to `/s` (Discover home).
- Active label gets `--text` color (vs `--text-mut`), weight 600, 2px `--primary` underline.
- Avatar opens dropdown: Profile · Saved · Settings · Sign out.

### 7.2 Institution top nav (logged in)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Wordmark]   Admissions  Outreach  Communications  Programs      ⌥  [avatar] │
└──────────────────────────────────────────────────────────────────────────────┘
```

- Same chrome.
- 4 unified labels.
- `⌥` shows a "switch view" if the user belongs to multiple institutions (future).
- Avatar dropdown: Institution settings · Switch institution (future) · Account · Sign out.

### 7.3 Public top nav

```
┌────────────────────────────────────────────────────────────────────────┐
│ [Wordmark]   Browse                       Sign in   [ Get started ]    │
└────────────────────────────────────────────────────────────────────────┘
```

`Get started` is the primary CTA (gold).

### 7.4 Side nav

Reserved for the institution Admissions queue (filters/saved views — see `30-admissions-intake.md`). All other workspaces are top-nav only.

### 7.5 Breadcrumbs

Present on every drill-down page. Example, student program detail:
```
Match · Search results · Computer Science MS  ·  ◾  University of Foo
```
Separators `·` (middle dot). Last item not a link. `--text-mut` color.

---

## 8. Cross-page navigation rules

The single biggest IA invariant: **any item, anywhere, can navigate to its canonical workspace.** Examples:

| Trigger | Lands at | Notes |
|---|---|---|
| Saved-list row "Start application" | `/s/applications/:newAppId` | App created server-side; navigate after the 201. |
| Calendar item linked to an application | `/s/applications/:appId?tab=checklist` | Calendar item carries `application_id` in its payload. |
| Inbox thread "Open application" | `/s/applications/:appId` | Thread carries `application_id`. |
| Program card "Save" → toast "Saved" | `/s/saved` | Inline action; toast offers "Open Saved" link. |
| Discover artifact rail "Generate strategy" | Strategy generated server-side; navigate to `/s/explore?showStrategy=open` | `?showStrategy=open` auto-opens the StrategyView. |
| Discover chat suggests "I think you should add a recommender" | `/s/profile?tab=preparation&section=recommenders` | Deep-link with section param. |
| Saved-list row "Open program detail" | `/s/programs/:programId` | Carries program context. |
| Match search result "Add to compare" | adds to compare tray; "Open compare" → `/s/explore?compare=open` | Compare tray is global; opening compare is in-place. |
| Institution PipelinePage applicant click | `/i/pipeline/:studentId` | Full applicant review packet. |
| Institution Templates "Use in new campaign" | `/i/campaigns?from_template=:templateId` | Pre-fills campaign body from template. |
| Institution AuditLog row "Open application" | `/i/pipeline/:studentId?focus=:application_id` | Cross-reference. |

### Query param conventions
- `?tab=` — selects a sub-tab on a multi-tab page.
- `?section=` — scrolls/expands a specific section inside a page.
- `?focus=` — highlights a specific record on a list page.
- `?from_template=` `?from_segment=` `?from_program=` — pre-fills a creation form from another object.
- `?showX=open` — auto-opens a normally-collapsed widget.

---

## 9. Auth flow

```
/login  → submit creds → POST /auth/login
                     ├─ 200 with student token → /s
                     ├─ 200 with institution token → /i/dashboard
                     ├─ 200 with onboarding_pending → /onboarding
                     └─ 4xx → inline error
```

- Token stored in localStorage by `auth-store` (Zustand).
- `RequireAuth` guard wraps `/s` and `/i` route trees; redirects to `/login?next=<original>` on miss.
- After `/login` success, redirect to `next` if present, else role-default.
- `AuthCallbackPage` at `/auth/callback` handles Cognito-Hosted-UI callback for SSO (currently no Google IdP per user memory; route exists for future).

---

## 10. Settings architecture

> Full settings spec is now `1D-settings.md`. This table is the at-a-glance role matrix; `1D` is the build contract.

Both roles have a settings page. Sections common to both:

| Section | Student | Institution | Notes |
|---|---|---|---|
| Account info | ✓ | ✓ | Email, role, member-since. |
| Password change | TODO | TODO | Cognito API. |
| MFA / 2FA | TODO | TODO | Cognito MFA. |
| Locale + timezone | TODO | TODO | Per-user preference. |
| Notification preferences | ✓ | ✓ | Email + per-type toggles. |
| Data rights / portable export | (lives on Profile) | (institution version: dataset export — `22-data-upload.md`) | Student per Appendix A consent dimensions. |
| Account deletion | TODO | (institution: contact support) | Student soft-delete + 30-day grace. |
| Sign out | ✓ | ✓ | |
| Institution-only: profile, rubric, integration credentials, billing | — | ✓ | Existing `/i/settings`. |

The "Notifications" Universal Profile section from the Master Paper lives here in Settings, not on the Profile page (one-place-for-notification-preferences principle).

---

## 11. First-run / setup

### Student first run
1. Sign up at `/signup`.
2. Email verification (if Cognito policy requires).
3. Land on `/onboarding` (or `/s` if the onboarding shim is removed).
4. Initial Discovery session created server-side for `track=profile&layer=basic`.
5. After ~10–15 min of chat (heuristic: when basic-layer completeness ≥ 60%), CTA appears: "Continue exploring on Discover" → `/s?track=profile&layer=basic`.

### Institution first run
1. Invitation email → `/signup?invite=<token>`.
2. Land on `/i/setup` (4-step wizard).
3. After completing wizard → `/i/dashboard`.
4. Empty-state dashboard nudges to "Add your first program" (already wired).

---

## 12. Notification destinations

Where notifications fire and where they land:

| Trigger | Student notification (where they see it) | Email |
|---|---|---|
| Match score updated | Discover artifact rail badge + Match page banner | weekly digest |
| Application missing item | Inbox (system message) + Applications dashboard | per event (if pref on) |
| Interview invite received | Inbox (human message) + Calendar | per event |
| Deadline approaching | Calendar agenda + Apply dashboard | per event |
| Decision released | Inbox + Applications dashboard + Decisions banner | per event |
| Saved program edited by institution | Inbox (system message) | per event (if pref on) |
| Institution post on a saved program | Connect feed | weekly digest |

| Trigger | Institution notification |
|---|---|
| New inquiry | Inquiries queue + Dashboard alert |
| New application submitted | Pipeline + Dashboard |
| Reviewer assignment overdue | Dashboard alert |
| Yield-risk threshold breached | Dashboard alert |
| Disparate-impact threshold approaching | Dashboard alert (`43-data-rights-privacy.md` §6) |

---

## 13. URL state vs UI state vs server state

Default rule:
- **In URL:** anything a user might want to share or bookmark — page, tab, filter chips, search query, sort, compare set.
- **In UI state only:** transient toggles (a modal open/closed), hover states, drag-in-flight state.
- **On server:** the canonical record. UI mirrors what's saved.

Specifically:
- Discovery filter chips → URL query params.
- Saved-list priority → server (currently in UI only — `90`).
- Compare tray contents → URL on `/s/explore` (so a deep link reproduces the comparison).
- Profile tab → URL `?tab=`.
- Application tab → URL `?tab=`.
- Inbox open thread → URL `/s/manage?tab=messages&thread=:id`.

---

## 14. Mobile breakpoints

| Breakpoint | Width | Behavior |
|---|---|---|
| `sm` | 640px | Top nav collapses to hamburger; avatar stays. Side rails collapse to bottom sheets. |
| `md` | 768px | Two-column layouts collapse to single. Compare and artifact rails open as sheets. |
| `lg` | 1024px | Desktop layout. |
| `xl` | 1280px | Discovery artifact rail unfolds permanently. |
| `2xl` | 1440px | Pipeline / Applications list go full-width. |

A dedicated mobile spec doc (`02b-design-system-mobile.md`) is recommended.

---

## 15. Compliance checklist (per route)

- [ ] Authenticated routes guarded by `RequireAuth`.
- [ ] Role guard matches the audience (`/s` → student; `/i` → institution_admin).
- [ ] No protected data leaks via URL params (use ids, not PII).
- [ ] Legacy redirect targets unchanged unless explicitly migrating (the redirects above are the contract).
- [ ] Breadcrumbs present on every drill-down.
- [ ] Deep links carry the context that lets the destination open in the right state (`?tab=`, `?section=`, `?focus=`).
- [ ] Active nav label visually distinct (color + weight + underline).
- [ ] Page title in `<title>` matches the route purpose.

---

## 16. Open questions / known gaps

- **`/s/messages/:convId` redirect drops the id.** Should carry through to `/s/manage?tab=messages&thread=:convId`.
- **Onboarding's relationship to Discover.** Two paths exist — the spec recommendation (shim into Discovery) is not yet implemented. Decision needed before authoring `1B-discovery-stage-conversation.md` fully.
- **Public program detail (`/program/:programId`) vs authenticated (`/s/programs/:programId`).** Two implementations exist; the public one should be a thin wrapper around the same components with auth-gated CTAs replaced by "Sign in to save" buttons. To capture in `13-detail-pages-program.md`.
- **Multi-institution staff users.** Not in MVP. The avatar's `⌥` "switch institution" is a placeholder.
- **Account deletion / portable export UI for students.** Currently only the export exists (Profile Data tab). Deletion flow needs UX + backend `delete_account` + 30-day grace.
