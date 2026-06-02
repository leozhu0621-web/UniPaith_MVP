# 50 · API Contract — Front ↔ Back Handshake

> The single agreement between the React frontend (`frontend/`) and the FastAPI backend (`unipaith-backend/`). Conventions (envelope, auth, errors, pagination) + the **router map**, all under `/api/v1`. Feature docs own per-endpoint detail; this doc owns the cross-cutting contract.
>
> Status: **draft v1.1** · 2026-06-02 · Build-integration doc. **Machine source of truth = the live OpenAPI at `/api/v1/openapi.json` (Swagger UI at `/docs` when `DEBUG=true`), now also surfaced publicly + grouped at `GET /api/v1/build/api-contract` → the `/goal/api` page (specs 48/49/50 transparency hub), which reads the running route table so the map can never drift.** This doc is the human contract; when they disagree, the running code wins — fix this doc.
>
> **Live count (2026-06-02): 39 router files / ~553 routes under `/api/v1`** — up from the v1.0 draft's 22 / ~285 because specs 39–46 (billing, payments, recruitment, graduate, governance, connect, intake, …) landed afterward. The numbers below are illustrative; `GET /api/v1/build/api-contract` is authoritative.

---

## 1. Base + transport

- **Host:** `api.unipaith.co` (prod) · `http://localhost:8000` (dev).
- **Global prefix: `/api/v1`.** `main.py` mounts the aggregate `api_router` at `/api/v1`; `api/router.py` includes every feature router **without its own prefix**, so each router's `APIRouter(prefix=…)` is appended to `/api/v1`. Example: strategy router `prefix="/students/me/strategy"` → real path `POST /api/v1/students/me/strategy/generate`.
- **Frontend client:** `frontend/src/api/client.ts` — single Axios instance; its `baseURL` carries `/api/v1`. All calls go through it (and through the per-domain modules in `frontend/src/api/*.ts`); never `fetch()` ad-hoc.
- **Content type:** `application/json` except file upload (`multipart/form-data` → documents).

---

## 2. Auth contract

- **Prod:** AWS Cognito. Frontend stores the JWT (Zustand `auth-store`, localStorage); `client.ts` attaches `Authorization: Bearer <token>`.
- **Dev:** `COGNITO_BYPASS=true`. Token format **`dev:<user_id>:<role>`** (e.g. `dev:1111…:student`). Same `Authorization: Bearer` header.
- **Roles:** `student` · `institution_admin` · `admin` (no platform-admin tier in MVP — `05` §2).
- **Guards:** `/students/*` + the student `/me/*` trees → `student`; `/institutions/*` admin actions, `/reviews/*`, `/applications/*` decision/batch, `/interviews/*` → `institution_admin`. Public read: `GET /programs`, `GET /institutions/{id}`, the `/t/{short_code}` redirect, `/health`.
- **401** = missing/expired → frontend redirects `/login?next=…`. **403** = wrong role.
- Login → token → role-home redirect handshake is in `05` §9; this doc fixes only the header + guard contract.

---

## 3. Response & error envelope

### 3.1 Success
Endpoints return the resource (or `{items,total,…}` for lists, §5) directly as JSON. 2xx. No success wrapper — idiomatic FastAPI.

### 3.2 Error
FastAPI shape, read by the `client.ts` interceptor:
```json
{ "detail": "Human-readable message" }
```
422 validation uses FastAPI's structured form (`detail` = array of `{loc,msg,type}`). **Interceptor contract:** surface `detail` (string) as toast/inline; for 422, map `loc`→field for inline form errors (React Hook Form + Zod, `02`).

### 3.3 Status-code taxonomy
| Code | When | Frontend |
|---|---|---|
| 200/201 | ok / created (201 returns the resource → navigate) | proceed |
| 204 | deleted | optimistic remove |
| 400 | semantic bad request | inline `detail` |
| 401 | no/expired token | redirect `/login?next=` |
| 403 | wrong role / not owner | "no access" |
| 404 | not found | not-found state |
| 409 | conflict (dup/state) | inline (e.g. "already applied") |
| 422 | validation | per-field inline |
| 429 | rate limited (AI/bulk) | backoff + retry copy |
| 5xx | server | toast — **but AI endpoints must fall back, not 5xx (§6)** |

---

## 4. Router map (verified against `api/` + `router.py`)

All paths below are **relative to `/api/v1`**. "n" = route count. Exhaustive paths live in `/docs`.

### Student (role `student`) — note the giant `students.py` monolith
| Router file | prefix (under /api/v1) | n | Feature | Sample routes |
|---|---|---|---|---|
| `students.py` | `/students` | 73 | `08`,`09` | `/me`, `/me/matches`, `/me/matches/{program_id}/explain`, `/me/matches/refresh`, `/me/academics`, `/me/activities`, `/me/test-scores`, `/me/strategy/generate` |
| `discovery.py` | `/students/me/discovery` | 7 | `19` | `/sessions`, `/sessions/{id}`, `/completion` |
| `strategy.py` | `/students/me/strategy` | 6 | `09` | `/active`, `/generate`, `/versions` |
| `goals.py` | `/students/me/goals` | 4 | `08` | `/`, `/{goal_id}` |
| `needs.py` | `/students/me/needs` | 4 | `08` | `/`, `/{need_id}` |
| `identity.py` | `/students/me/identity` | 3 | `08`,`19` | `/`, `/regenerate-summary` |
| `recommendations.py` | `/students/me/recommendations` | 6 | `08` | `/`, `/{rec_id}/send` |
| `documents.py` | `/students/me/documents` | 5 | `08`,`15` | `/`, `/request-upload`, `/{id}` |
| `saved_lists.py` | `/students/me/saved` | 5 | `13` | `/`, `/compare`, `/{program_id}` |
| `workshops.py` | `/students/me` | 14 | `15`,`14` | `/applications/{id}/checklist`, workshop run routes |
| `workshop_feedback.py` | `/students/me/workshops` | 4 | `14` | `/essay/feedback`, `/interview/practice`, `/runs` |
| `ai_feedback.py` | `/students/me/ai-feedback` (inline) | 2 | `37`,`45` | thumbs-up/down on AI turns |

### Institution (role `institution_admin`) — note the giant `institutions.py` monolith
| Router file | prefix (under /api/v1) | n | Feature | Sample routes |
|---|---|---|---|---|
| `institutions.py` | `/institutions` | 81 | `22`–`30` | `/me`, `/me/analytics`, `/inquiries`, + programs/segments/campaigns/posts/promotions/datasets/templates mgmt folded in here |
| `applications.py` | `/applications` | 14 | `31`,`34` | `/`, `/batch/decision`, `/batch/request-items` |
| `reviews.py` | `/reviews` | 16 | `32` | `/applications/{id}/ai-packet`, scoring/assignment |
| `interviews.py` | `/interviews` | 8 | `33` | `/application/{id}`, `/batch/invite` |
| `events.py` | `/events` | 10 | `20`,`27` | `/`, `/manage`, `/manage/{id}` |
| `programs.py` | `/programs` | 6 | `11`,`23` | `/`, `/{id}`, `/search/nlp`, `/search/semantic` |

### Shared / cross-role
| Router file | prefix (under /api/v1) | n | Feature | Routes |
|---|---|---|---|---|
| `auth.py` | `/auth` | 5 | `05` §9 | `/login`, `/me`, `/google-callback` |
| `messaging.py` | `/messages` | 4 | `17`,`29` | `/conversations`, `/conversations/{id}` |
| `notifications.py` | `/notifications` | 6 | `21` | `/`, `/preferences`, `/read-all` |
| `router.py` | (inline) | 2 | infra | `/health`, `/t/{short_code}` (campaign link redirect) |

> **Build reality / drift to note:**
> - **Monoliths.** `students.py` (73) and `institutions.py` (81) carry the bulk of the surface — many feature docs (`22`–`30`) map to one big router, not one router each. When a feature doc names a "segments/campaigns/posts" surface, its endpoints live **inside `institutions.py`** today.
> - **Prefix overlap.** `workshops.py` mounts at `/students/me` (same space as `students.py`) — watch for path collisions when adding routes.
> - **Matching has no own router** — it's `students.py` `/me/matches/*`. There is a separate `strategy.py` AND `/me/strategy/*` inside `students.py`; confirm which is canonical (likely `strategy.py` is the newer split — deprecate the duplicate).
> - Specs `28`/`29`/`35` and Phase-2 `38`–`41` describe surfaces whose endpoints may be partial or absent; treat any endpoint a feature doc names but `/docs` lacks as a **build task**, following the prefix convention here + updating this map.

---

## 5. List / pagination / filter

Collection endpoints: `?limit=` (default 20, max 100) · `?offset=` · `?sort=` · domain filters (`?stage=`, `?status=`, `?q=`). Response `{ "items":[…], "total":int, "limit":int, "offset":int }`. TanStack Query keys on the full param set. High-volume feeds may use `?cursor=` + `next_cursor` instead — pick one per endpoint, record it in the feature doc.

---

## 6. AI-endpoint contract (critical invariant)

AI-backed endpoints — `/students/me/discovery/sessions/{id}/messages`, `/students/me/matches/{id}/explain`, `/students/me/strategy/generate`, `/students/me/workshops/*`, `/students/me/identity/regenerate-summary` — follow `45` + the `CLAUDE.md` invariant:
- **Never 5xx on AI failure.** On timeout/parse-error/guardrail-trip the service **falls back to the rule-based path** and returns 200 with a source indicator (`"source":"rule_based"|"ai"`). Frontend shows "Showing rule-based result" when `source != "ai"`.
- **Feature-flagged:** `ai_discovery_v2_enabled`, `ai_match_rationale_v2_enabled`, `ai_workshops_v2_enabled`, `ai_strategy_v2_enabled`, `ai_identity_v2_enabled` (all on in prod, `infra/ecs.tf`). `AI_MOCK_MODE=true` → deterministic stub.
- **Caching:** rationale cached per `(profile_version, program_version)`; response may carry `cached:true`. The cache + provenance row is `ai_turns` / `match_rationales` (`51`).
- **Consent gate:** `student_data_consent.matching=false` → AI skipped, rule-based/empty returned (`46` §2). Frontend must handle a present-but-non-AI response.
- **Feedback:** `ai_feedback.py` records thumbs-up/down per AI turn (`ai_turn_feedback`) — wire the rationale/summary UIs to it.

---

## 7. Frontend api-module ↔ router parity

Each backend router has a matching `frontend/src/api/*.ts` module (live today: `auth, students, discovery, strategy, goals, needs, identity, recommendations, documents, saved-lists, matching, programs, institutions, applications, applications-admin, reviews, interviews, interviews-admin, events, events-admin, messaging, notifications, workshops-feedback, essays, resumes, normalize`). **Rule:** a screen never calls `client` directly — it calls an api-module function. TS types in `frontend/src/types/` must match the backend Pydantic response field-for-field (CLAUDE.md "fields invisible otherwise" — add the field to the response schema AND the TS type in the same change).

---

## 8. CORS, rate limits, idempotency

- **CORS:** backend allows `app.unipaith.co` + `localhost:5173`; add new frontend hosts to the allowlist.
- **Rate limits:** AI + bulk (`/applications/batch/*`, segment execute, AI runs) → 429 with retry guidance.
- **Idempotency:** money/decision mutations (`39` fees, `/applications/batch/decision`, `35` deposit) accept `Idempotency-Key` so retries don't double-apply.

---

## 9. Build checklist (per endpoint)

- [ ] Router method + Pydantic request/response schema (inline, CLAUDE.md convention).
- [ ] Role guard + owner check on user-scoped resources.
- [ ] Appears in `/api/v1/openapi.json`.
- [ ] Frontend api-module fn + TS type matching the response.
- [ ] Errors use §3 envelope; 422 → inline form errors.
- [ ] AI endpoints honor §6 (fallback, flag, consent, feedback).
- [ ] Feature doc updated; §4 map updated if a new router.

---

## 10. Open questions

- **`students.py`/`institutions.py` decomposition.** 73- and 81-route monoliths are hard to own; consider splitting into the feature-aligned routers the docs assume (segments, campaigns, posts…). Until then, this map is the bridge.
- ~~**Duplicate match/strategy paths** (`students.py` vs `strategy.py`)~~ — **resolved**: `strategy.py` (`/students/me/strategy/*`) is canonical; `students.py` no longer carries `/me/strategy` routes. Match scoring stays in `students.py` `/me/matches/*` by design.
- **Versioning.** `/api/v1` exists — good. Bump policy for v2 when external consumers appear.
- **`messaging.py` conversations vs feature docs' "threads".** Code uses `conversations`; docs `17`/`29` say "threads" — same concept, align the vocabulary (`51` §5).
