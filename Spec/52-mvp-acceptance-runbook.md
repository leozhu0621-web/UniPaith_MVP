# 52 · MVP Acceptance & Runbook — "Ready to Use, Front + Back"

> The operational definition of *done* for the MVP. If every gate here passes, a real student and a real institution can complete their full journey end-to-end on the deployed app. Check the build against this before saying "ready." Pairs with `47` (gaps), `48` (build order), `49` (scope), `50` (API), `51` (data).
>
> Status: **draft v1.0** · 2026-05-30 · Build-integration doc. "MVP-ready" = §2 critical paths all green + §5 launch blockers all clear.

---

## 1. What "ready to use" means

Three levels, in order — don't move up until the lower is green:
1. **Boots** — backend serves, frontend builds, DB migrates, auth works, `/openapi.json` lists the routers (`50` §4).
2. **Critical paths pass** — the two end-to-end journeys in §2 complete with real clicks against the real backend (not mocked).
3. **Quality gates pass** — per-surface DoD (§3), front↔back integration (§4), no open launch blocker (§5).

Scope = the MVP set in `49` (student core `08`–`21`, institution core `22`–`37`; Phase-2 `38`–`41` excluded from this gate).

---

## 2. Critical-path smoke tests (the acceptance core)

Each step = a real action on the deployed/staging app. A path is green only if every step works **front and back** (UI action → API call → DB write → UI reflects it). Run with seeded demo accounts (§6).

### 2.1 Student journey (Discover → Apply → Decide)
1. **Sign up** → email verify (or dev bypass) → land on first-run (student → `19` Discover). Token stored, role=student.
2. **Discover chat** (`19`): send a message → assistant replies → an artifact (goal/need/identity) appears in the rail → `discovery_messages` + extracted signal persisted. AI down → rule-based reply still returns (no 5xx, `50` §6).
3. **Profile** (`08`): completion % increases; edit a field → persists → reflected after reload.
4. **Match** (`09`): `/s/explore` shows ranked programs with **fitness + confidence** (DualRing) → "Why this match" opens rationale (cached on 2nd open).
5. **Program detail** (`11`): opens; Costs/Outcomes render from `programs` JSONB; **Save** → appears in Saved (`13`).
6. **Apply** (`15`): start application from Saved → workspace; checklist reflects program requirements; mark an item → persists.
7. **Calendar/Inbox** (`16`/`17`): a deadline shows on the calendar; an institution message appears as a thread with an action label.
8. **Decision** (`18`): when the institution releases a decision (2.2 step 6), it appears in the student's Decisions + Inbox + notification.

### 2.2 Institution journey (Setup → Review → Decide)
1. **Sign in** as `institution_admin` → `/i/dashboard`.
2. **Setup/Profile** (`30`/`22`): institution profile + at least one **published program** (`23`) visible to students (appears in student Match).
3. **Pipeline** (`31`): the student's submitted application (from 2.1) appears in the queue.
4. **Review** (`31`/`32`): open the review packet → AI summary renders (or rule-based fallback) → enter a rubric score → assign reviewer → persists to `application_scores` + `review_assignments`.
5. **Interview** (`33`): schedule an interview → student sees the invite (Inbox + Calendar).
6. **Decide** (`34`): release a decision (+ offer terms) → audit-logged (`admissions_audit_log`) → student notified (closes 2.1 step 8).
7. **Outreach/Analytics** (`25`/`28`): send a campaign to a segment (`26`) → metrics surface; attribution funnel renders.

> **Acceptance bar:** both journeys complete with zero console errors, zero 5xx, and every persisted change surviving a reload. If any step needs a mock to pass, it is **not** green.

---

## 3. Per-surface Definition of Done

A surface is "done" when ALL hold (feature docs add specifics):
- [ ] Renders at its route with the correct role guard (`05`, `50` §2).
- [ ] **Loading, empty, error, and success states** all implemented (`02` rule) — not just the happy path.
- [ ] Reads/writes go through a frontend api-module → real endpoint (`50` §7); types match backend response.
- [ ] Brand-compliant: Europa via Typekit, tokens not hardcoded, no decorative imagery on detail pages, gold rationed (`01`,`02`).
- [ ] Responsive per `03` (usable at 360px for student surfaces).
- [ ] Accessible: 44px targets, focus management, labels, contrast (`03` §9 / WCAG AA).
- [ ] Copy is literal, sentence-case, no marketing voice (`01` §6).
- [ ] Backend: role guard + owner check + 422 validation + the `50` §3 error envelope.
- [ ] AI surfaces honor fallback + flag + consent (`50` §6).

---

## 4. Front ↔ back integration gates

Individually built, must be verified *together*:
- [ ] **api-module parity** — every screen's data call maps to a real router in `50` §4; no orphan frontend call, no unused critical endpoint.
- [ ] **Type parity** — backend Pydantic response fields == frontend TS type fields (build surfaces any missing field — CLAUDE.md "fields invisible otherwise").
- [ ] **Auth round-trip** — login issues a token the guarded routes accept; 401 redirects; role mismatch 403s.
- [ ] **CORS** — app origin allowed; preflight passes from the real frontend host (`50` §8).
- [ ] **AI fallback observed** — force an AI failure and confirm 200 + rule-based result + "showing rule-based" copy.
- [ ] **Notifications loop** — an institution action (decision/message) produces a student notification row + UI surfacing (`21`).
- [ ] **File upload** — `/documents` multipart → S3 (or `S3_LOCAL_MODE`) → parse_status set → appears in profile (`08`/`15`).
- [ ] **Cache invalidation** — edit profile → match rationale recomputes (version bump, `45` §12 / `51` §7).

---

## 5. Launch-blocker checklist (must all clear)

Hard gates — any one open = not launch-ready:
- [ ] **Europa Typekit kit `spe3ioy`** loads on `app.unipaith.co` (domain allow-listed); EB Garamond/Caveat/Kalam removed (`47` G-B1, `01` §3).
- [ ] **Auth works in prod** (Cognito, not bypass); password reset exists or is explicitly deferred.
- [ ] **No secrets in the bundle**; backend secrets via AWS Secrets Manager.
- [ ] **DB migrations apply cleanly** from empty (Alembic head) — no `create_all`.
- [ ] **Consent gate enforced** on AI processing (`46` §2) — even if interim JSONB.
- [ ] **Workshop no-generation contract** green in CI (`14`, `tests/test_workshop_no_generation_contract.py`).
- [ ] **AI never 5xx** to the user (`tests/test_plan2_integration.py` passes).
- [ ] **CloudFront invalidated** after frontend deploy (stale bundle is the #1 deploy footgun).
- [ ] **Both §2 journeys pass on staging** against prod-like data.
- [ ] **Backend + frontend tests green** (`make test-backend`, `make test-frontend`).

---

## 6. Seed / demo data (required to exercise the app)

The app isn't "usable" empty — a clicker needs populated accounts. Provide a seed (`scripts/`, extend `make`):
- **2 students:** one mid-journey (profile ~60%, 1 discovery session, 3 saved programs, 1 submitted application) + one fresh (empty, to test first-run).
- **1 institution** (`institution_admin`): published profile, **3 programs** (varied degree_type/cost so Match + Compare are meaningful), 1 event, 1 post, 1 segment, 1 campaign.
- **Cross-links:** the mid-journey student's application targets one of the institution's programs (so Pipeline is non-empty and the decision loop is testable).
- **Match results + 1 ai_artifact** so Match renders without a live AI call.
- **Idempotent reseed:** `replace=True` / explicit dedup keys (CLAUDE.md) so re-running doesn't collide.
- Demo creds documented in-repo (dev token `dev:<uuid>:<role>`, `50` §2).

---

## 7. Run & verify (local + deploy)

**Local (per `CLAUDE.md` Quick Start):**
```
make dev-db        # Postgres (Docker)
make dev-backend   # migrations + uvicorn :8000  → /docs lists routers
make dev-frontend  # Vite :5173
make test-backend && make test-frontend
```
Run §2 journeys at `localhost:5173` against `localhost:8000`. Pre-work health check first (DB up, build green, tests pass).

**Deploy (per `CLAUDE.md` Deployment Checklist):** frontend → S3 + **CloudFront invalidate**; backend → ECS (confirm task-def env not overwritten); DB password matches Secrets Manager ↔ RDS; RDS in correct VPC/SG. Re-run §2 on the deployed URL.

---

## 8. Acceptance sign-off matrix

"MVP ready" = all `core` rows green.

| Area | Boots | Critical path | DoD | Class |
|---|---|---|---|---|
| Student: Discover/Profile/Match/Detail/Saved | ☐ | ☐ (2.1) | ☐ | core |
| Student: Apply/Calendar/Inbox/Decisions/Connect/Settings | ☐ | ☐ (2.1) | ☐ | core |
| Institution: Setup/Profile/Programs/Data | ☐ | ☐ (2.2) | ☐ | core |
| Institution: Pipeline/Review/Interviews/Decisions | ☐ | ☐ (2.2) | ☐ | core |
| Institution: Outreach/Segments/Campaigns/Posts/Attribution/Messaging | ☐ | ☐ (2.2) | ☐ | core |
| Cross-cutting: Auth, Notifications, AI fallback, Audit, Consent | ☐ | ☐ (§4) | ☐ | core |
| Enrollment/Yield (`35`) | ☐ | ☐ | ☐ | extend |
| Phase-2 (`38`–`41`) | — | — | — | excluded |

---

## 9. Open questions

- **Staging environment.** Mirror prod for §2 sign-off, or run journeys against prod pre-launch? Recommend a staging slice.
- **E2E automation.** §2 is manual today; a Playwright suite for the two journeys makes acceptance repeatable (high ROI post-MVP).
- **Demo-data ownership.** Tie the seed to the migration workflow so it never goes stale.
- **Performance acceptance.** No hard budget yet (`47`/`06` weak); minimal bar: Match p95 < 1.5s cached, page TTI < 3s on 4G, before declaring mobile "ready."
