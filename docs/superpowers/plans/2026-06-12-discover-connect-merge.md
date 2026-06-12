# Discover + Connect Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the Connect surface (`/s/posts`) into Discover (`/s/explore`) as a hub with sub-tabs and a live right rail, shipping six LinkedIn/Handshake-benchmarked integration ideas (follow buttons on cards, feed attribution, badge counts, event chips, saved-search alerts in feed, follow suggestions).

**Architecture:** Frontend-heavy. `/s/explore` gains a `?tab=` param (foryou·updates·events·peers); the existing Connect tab components move in unchanged; a sticky right rail (xl+) shows feed/event/deadline teasers. Backend adds four small read-path features to the existing connect router/service (kinds filter, follow_source, saved-search alert items, unseen-count) plus `institution_id` on the match response. No migrations, no AI-flag changes.

**Tech Stack:** React 19 + TS + TanStack Query + Tailwind (frontend); FastAPI + SQLAlchemy 2 async (backend); vitest + pytest.

**Spec:** `docs/superpowers/specs/2026-06-12-discover-connect-merge-design.md`

**Conventions for every backend test run:**
```bash
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true COGNITO_BYPASS=true S3_LOCAL_MODE=true \
  DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" \  # pragma: allowlist secret
  .venv/bin/pytest tests/<file> -v --tb=short
```
(Memory gotcha: if parallel sessions contend on the shared DB, point DATABASE_URL at an isolated DB, e.g. `unipaith_dcmerge_test`, created with `CREATE DATABASE` outside a txn.)

---

### Task 1: Backend — `kinds` filter on GET /connect/feed

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/connect_service.py` (build_updates_feed, ~line 47)
- Modify: `unipaith-backend/src/unipaith/api/connect.py` (get_feed, ~line 50)
- Test: `unipaith-backend/tests/test_connect_feed.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_connect_feed.py` (reuse the existing `_seed` / `_publish_post` helpers and client fixtures already in that file; mirror the existing tests' fixture signatures exactly):

```python
async def test_feed_kinds_filter_deadline_only(
    db_session, student_client: AsyncClient, student_user, institution_user
):
    """?kinds=deadline returns only deadline items (rail deadline radar)."""
    deadline = date.today() + timedelta(days=30)
    profile, institution, program = await _seed(
        db_session, student_user, institution_user, deadline=deadline
    )
    await _publish_post(db_session, institution.id)
    await _follow_and_save(db_session, profile, institution, program)  # use the file's existing follow/save helper; if it inlines this, copy that block

    res = await student_client.get("/api/v1/connect/feed", params={"kinds": "deadline"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 1
    assert all(it["kind"] == "deadline" for it in items)

    res2 = await student_client.get("/api/v1/connect/feed", params={"kinds": "post"})
    assert all(it["kind"] == "post" for it in res2.json()["items"])
```

Note: read the existing tests in the file first — they show exactly how a follow + saved program is created (there is a passing `test_deadline_item_from_saved_program`); copy its arrangement rather than inventing `_follow_and_save`.

- [ ] **Step 2: Run it to verify it fails** — Expected: FAIL (kinds param ignored, post items present in deadline-only response).

- [ ] **Step 3: Implement.** In `connect_service.py`, change `build_updates_feed`'s signature and assembly:

```python
_ALL_FEED_KINDS = {"post", "deadline", "program_change", "saved_search_alert"}

    async def build_updates_feed(
        self,
        student_id: UUID,
        *,
        rank: str = "recent",
        limit: int = 50,
        cursor: str | None = None,
        kinds: set[str] | None = None,
    ) -> dict:
```

and replace the assembly block (currently `items += await self._post_items(...)` etc.) with:

```python
        want = (kinds & _ALL_FEED_KINDS) if kinds else _ALL_FEED_KINDS

        items: list[dict] = []
        engagement: dict | None = None
        if followed_all:
            inst_names = await self._institution_names(followed_all)
            if "post" in want:
                items += await self._post_items(visible_insts, inst_names)
            if want & {"deadline", "program_change"}:
                engagement = await self._engagement(student_id)
                if "deadline" in want:
                    items += self._deadline_items(engagement, visible_insts, inst_names)
                if "program_change" in want:
                    items += self._program_change_items(engagement, inst_names, muted)

        if rank == "relevant":
            if engagement is None:
                engagement = await self._engagement(student_id)
            items = self._order_relevant(items, engagement)
            items = await self._maybe_ai_rerank(items, engagement, student_id)
        else:
            items = self._order_recent(items)
```

(The old `locals().get("engagement")` trick is replaced by the explicit `engagement` local — keep behavior identical.) In `api/connect.py::get_feed` add the param and parse:

```python
    kinds: str | None = Query(None, description="Comma-list of item kinds to include"),
```
```python
    kind_set = {k.strip() for k in kinds.split(",") if k.strip()} if kinds else None
    return await ConnectService(db).build_updates_feed(
        pid, rank=rank, limit=limit, cursor=cursor, kinds=kind_set
    )
```

- [ ] **Step 4: Run the new test + the whole file** — Expected: PASS, no regressions in `test_connect_feed.py`.
- [ ] **Step 5: Commit** — `feat(connect): kinds filter on the updates feed`

---

### Task 2: Backend — `follow_source` attribution on feed items

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/connect_service.py`
- Test: `unipaith-backend/tests/test_connect_feed.py`

- [ ] **Step 1: Failing test** — the seeded follow in the existing tests has a `source` (check the helper; if it creates the follow with `source="explicit"`, assert that):

```python
async def test_feed_items_carry_follow_source(
    db_session, student_client: AsyncClient, student_user, institution_user
):
    """Each feed item carries the follow row's source for 'because you follow' attribution."""
    profile, institution, program = await _seed(db_session, student_user, institution_user)
    await _publish_post(db_session, institution.id)
    # …create the follow the same way the existing post-feed test does…
    res = await student_client.get("/api/v1/connect/feed")
    items = res.json()["items"]
    assert items, "expected at least one feed item"
    assert items[0]["follow_source"] in ("saved", "application", "explicit")
```

- [ ] **Step 2: Run to verify it fails** (KeyError: follow_source).
- [ ] **Step 3: Implement.** Add to `ConnectService` (near the other data-loading helpers):

```python
    async def _follow_sources(self, student_id: UUID) -> dict[UUID, str]:
        from unipaith.models.follow import InstitutionFollow

        rows = await self.db.execute(
            select(InstitutionFollow.institution_id, InstitutionFollow.source).where(
                InstitutionFollow.student_id == student_id
            )
        )
        return {r[0]: r[1] for r in rows.all()}
```

and in `build_updates_feed`, right after assembly (before ordering):

```python
        if items:
            sources = await self._follow_sources(student_id)
            for it in items:
                iid = it.get("institution_id")
                it["follow_source"] = sources.get(UUID(iid)) if iid else None
```

- [ ] **Step 4: Run test file** — PASS.
- [ ] **Step 5: Commit** — `feat(connect): follow_source attribution on feed items`

---

### Task 3: Backend — saved-search alert items in the feed

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/connect_service.py`
- Modify: `unipaith-backend/src/unipaith/api/connect.py`
- Test: `unipaith-backend/tests/test_connect_feed.py`

- [ ] **Step 1: Failing test:**

```python
async def test_saved_search_alert_items_in_feed(
    db_session, student_client: AsyncClient, student_user, institution_user
):
    """Recently-alerted saved searches surface as feed items; disabled/stale/zero-count don't."""
    from unipaith.models.saved_search import SavedSearch

    profile, institution, program = await _seed(db_session, student_user, institution_user)
    now = datetime.now(UTC)
    db_session.add_all([
        SavedSearch(  # should appear
            user_id=student_user.id, name="CS in California",
            query={"query": "cs", "chips": [], "filters": {}, "sort": "relevance"},
            alert_enabled=True, last_alerted_at=now - timedelta(days=2), last_match_count=5,
        ),
        SavedSearch(  # alert disabled → absent
            user_id=student_user.id, name="No alerts", query={},
            alert_enabled=False, last_alerted_at=now - timedelta(days=2), last_match_count=3,
        ),
        SavedSearch(  # stale (>14d) → absent
            user_id=student_user.id, name="Stale", query={},
            alert_enabled=True, last_alerted_at=now - timedelta(days=30), last_match_count=3,
        ),
        SavedSearch(  # zero matches → absent
            user_id=student_user.id, name="Empty", query={},
            alert_enabled=True, last_alerted_at=now - timedelta(days=1), last_match_count=0,
        ),
    ])
    await db_session.commit()

    res = await student_client.get("/api/v1/connect/feed")
    assert res.status_code == 200
    alerts = [it for it in res.json()["items"] if it["kind"] == "saved_search_alert"]
    assert len(alerts) == 1
    a = alerts[0]
    assert a["search_name"] == "CS in California"
    assert a["match_count"] == 5
    assert a["search_query"]["query"] == "cs"
    assert a["institution_id"] is None
```

- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Implement.** `build_updates_feed` gains `user_id: UUID | None = None` (keyword-only). Add the builder:

```python
# How recently a saved-search alert must have fired to still surface in the feed.
_SAVED_SEARCH_ALERT_WINDOW_DAYS = 14

    async def _saved_search_alert_items(self, user_id: UUID) -> list[dict]:
        """Spec 2026-06-12 §5.4 — alert-enabled saved searches that fired
        recently surface as feed items (LinkedIn job-alerts-in-feed pattern).
        Derived at read time from the Spec 56 bookkeeping columns; no new table."""
        from unipaith.models.saved_search import SavedSearch

        cutoff = datetime.now(UTC) - timedelta(days=_SAVED_SEARCH_ALERT_WINDOW_DAYS)
        rows = await self.db.execute(
            select(SavedSearch).where(
                SavedSearch.user_id == user_id,
                SavedSearch.alert_enabled.is_(True),
                SavedSearch.last_alerted_at.isnot(None),
                SavedSearch.last_alerted_at >= cutoff,
            )
        )
        out: list[dict] = []
        for s in rows.scalars().all():
            if not s.last_match_count:
                continue
            out.append(
                {
                    "kind": "saved_search_alert",
                    "id": f"saved_search_alert:{s.id}",
                    "date": s.last_alerted_at.isoformat(),
                    "institution_id": None,
                    "institution_name": None,
                    "program_id": None,
                    "program_name": None,
                    "muted": False,
                    "saved_search_id": str(s.id),
                    "search_name": s.name,
                    "match_count": int(s.last_match_count),
                    "search_query": s.query or {},
                    "ctas": [],
                }
            )
        return out
```

Wire into assembly (OUTSIDE the `if followed_all:` block — alerts are independent of follows):

```python
        if "saved_search_alert" in want and user_id is not None:
            items += await self._saved_search_alert_items(user_id)
```

In `_order_relevant`'s `weight()`, add after the deadline branch:

```python
            if kind == "saved_search_alert":
                return 600
```

In `api/connect.py::get_feed`, pass `user_id=user.id` to `build_updates_feed`.

- [ ] **Step 4: Run the test file** — PASS (also re-run Tasks 1–2 tests).
- [ ] **Step 5: Commit** — `feat(connect): saved-search alerts surface as feed items`

---

### Task 4: Backend — GET /connect/feed/unseen-count

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/connect_service.py`
- Modify: `unipaith-backend/src/unipaith/api/connect.py`
- Test: `unipaith-backend/tests/test_connect_feed.py`

- [ ] **Step 1: Failing test:**

```python
async def test_unseen_count(
    db_session, student_client: AsyncClient, student_user, institution_user
):
    """Counts posts published after `since` from followed unmuted institutions."""
    profile, institution, program = await _seed(db_session, student_user, institution_user)
    # …create the follow the same way the existing post-feed test does…
    await _publish_post(db_session, institution.id, title="New post")

    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

    res = await student_client.get("/api/v1/connect/feed/unseen-count", params={"since": past})
    assert res.status_code == 200
    assert res.json()["count"] >= 1

    res2 = await student_client.get("/api/v1/connect/feed/unseen-count", params={"since": future})
    assert res2.json()["count"] == 0

    res3 = await student_client.get("/api/v1/connect/feed/unseen-count")
    assert res3.status_code == 422  # since is required
```

- [ ] **Step 2: Run to verify it fails (404).**
- [ ] **Step 3: Implement.** Service method:

```python
    async def count_unseen_posts(self, student_id: UUID, *, since: datetime) -> int:
        """Cheap COUNT for the nav badge (Spec 2026-06-12 §5.3). Posts only:
        deadline items carry future dates by design (urgency mapped onto the
        recency axis), so they would never 'age out' of an unseen count."""
        if since.tzinfo is None:
            since = since.replace(tzinfo=UTC)
        visible = await self.follows.followed_institution_ids(student_id, include_muted=False)
        if not visible:
            return 0
        n = await self.db.execute(
            select(func.count())
            .select_from(InstitutionPost)
            .where(
                InstitutionPost.institution_id.in_(visible),
                InstitutionPost.status == "published",
                InstitutionPost.published_at > since,
            )
        )
        return int(n.scalar() or 0)
```

Route in `api/connect.py` (place directly under `get_feed`; fixed path, no clash with `/feed`):

```python
@router.get("/feed/unseen-count")
async def feed_unseen_count(
    since: datetime = Query(..., description="ISO timestamp of the last Updates visit"),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """New-posts count since the student last opened Updates (nav/tab badge,
    Spec 2026-06-12 §6.3). Deliberately posts-only and assembly-free."""
    pid = await _profile_id(user, db)
    return {"count": await ConnectService(db).count_unseen_posts(pid, since=since)}
```

Add `from datetime import datetime` to the router's imports if absent.

- [ ] **Step 4: Run the test file** — PASS.
- [ ] **Step 5: Run the full connect suite** (`tests/test_connect_feed.py tests/test_connect_events.py tests/test_connect_follows.py tests/test_connect_peers.py`) — all green.
- [ ] **Step 6: Commit** — `feat(connect): unseen-count endpoint for nav badge`

---

### Task 5: Backend — institution_id on the match response

**Files:**
- Modify: `unipaith-backend/src/unipaith/schemas/matching.py:42` (display fields block)
- Modify: `unipaith-backend/src/unipaith/api/students.py` (`_enrich_match_for_student`)
- Test: `unipaith-backend/tests/test_match_explore_api.py` (or wherever /me/matches enrichment is asserted — grep `"/me/matches"` in tests and extend the list test)

- [ ] **Step 1: Failing test** — in the existing /me/matches list test add:

```python
    assert body[0]["institution_id"] is not None
```

- [ ] **Step 2: Run to verify it fails (KeyError).**
- [ ] **Step 3: Implement.** `schemas/matching.py`, with the other display fields:

```python
    program_name: str | None = None
    institution_id: UUID | None = None
    institution_name: str | None = None
```

`api/students.py::_enrich_match_for_student`, inside `if program is not None:`:

```python
        resp.institution_id = getattr(program, "institution_id", None)
```

- [ ] **Step 4: Run that test file** — PASS.
- [ ] **Step 5: Commit** — `feat(matching): institution_id on match responses (Spec 2026-06-12 §6)`

---

### Task 6: Frontend — API layer, types, and shared utils

**Files:**
- Modify: `frontend/src/api/connect.ts`
- Modify: `frontend/src/types/index.ts:2967` (MatchResultDual)
- Create: `frontend/src/utils/connectSeen.ts`
- Create: `frontend/src/pages/student/explore/discovery/searchUrl.ts`
- Modify: `frontend/src/pages/student/saved/SavedSearchesPanel.tsx` (DRY refactor of `openInMatch`)

- [ ] **Step 1: connect.ts.** Update the kind union + item type and feed fn; add unseen count:

```ts
export type FeedItemKind = 'post' | 'deadline' | 'program_change' | 'saved_search_alert'
```

In `ConnectFeedItem`: `institution_id: string | null`, `institution_name: string | null`, and append:

```ts
  // Spec 2026-06-12 §6.2 — follow attribution ("because you follow X").
  follow_source?: 'saved' | 'application' | 'explicit' | null
  // saved_search_alert (Spec 2026-06-12 §5.4)
  saved_search_id?: string
  search_name?: string
  match_count?: number
  search_query?: { query?: string; chips?: unknown[]; filters?: Record<string, unknown>; sort?: string }
```

Replace `getConnectFeed` with an opts-aware version and add `getUnseenCount`:

```ts
export const getConnectFeed = (
  rank: 'recent' | 'relevant' = 'recent',
  cursor?: string | null,
  opts?: { limit?: number; kinds?: string },
) =>
  apiClient
    .get('/connect/feed', {
      params: {
        tab: 'updates',
        rank,
        limit: opts?.limit ?? 50,
        ...(opts?.kinds ? { kinds: opts.kinds } : {}),
        ...(cursor ? { cursor } : {}),
      },
    })
    .then(r => r.data as ConnectFeed)

/** New-posts count since the last Updates visit (nav/tab badge). 0 when never visited. */
export const getUnseenCount = (since: string | null) =>
  since
    ? apiClient
        .get('/connect/feed/unseen-count', { params: { since } })
        .then(r => (r.data as { count: number }).count)
    : Promise.resolve(0)
```

- [ ] **Step 2: types/index.ts** — in `MatchResultDual` next to `institution_name`:

```ts
  institution_id?: string | null
```

- [ ] **Step 3: Create `frontend/src/utils/connectSeen.ts`:**

```ts
// Tracks when the student last opened the Updates tab, for the nav/tab
// "new updates" badge (Spec 2026-06-12 §6.3). Distinct from
// 'unipaith_connect_last_seen' (newest ITEM date, drives the in-feed pill) —
// that key can hold a future deadline date by design, so it can't be the
// `since` for a posts-only server count.
const KEY = 'unipaith_connect_seen_at'

export function getConnectSeenAt(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function markConnectSeen(): void {
  try {
    localStorage.setItem(KEY, new Date().toISOString())
  } catch {
    /* ignore */
  }
}
```

- [ ] **Step 4: Create `frontend/src/pages/student/explore/discovery/searchUrl.ts`** (extracted from SavedSearchesPanel so the feed alert card reuses it):

```ts
import { encodeChipsParam } from './chipUtils'
import { encodeFiltersParam } from './filterUtils'
import type { SavedSearch } from '../../../../api/savedSearches'

/** Rebuild the /s/explore URL that restores a saved search's exact state. */
export function exploreUrlFromSavedQuery(query: SavedSearch['query'] | undefined | null): string {
  const p = new URLSearchParams()
  const q = query?.query
  if (q && q.trim()) p.set('q', q.trim())
  if (query?.chips && query.chips.length) p.set('chips', encodeChipsParam(query.chips))
  if (query?.filters && Object.keys(query.filters).length)
    p.set('filters', encodeFiltersParam(query.filters))
  if (query?.sort && query.sort !== 'relevance') p.set('sort', query.sort)
  const qs = p.toString()
  return qs ? `/s/explore?${qs}` : '/s/explore'
}
```

Check `api/savedSearches.ts` for the exact `SavedSearch['query']` member types — if `chips`/`filters` are typed more loosely there, match the looser type and keep the `encodeChipsParam(query.chips)` call compiling (cast at the call site the same way SavedSearchesPanel does today).

- [ ] **Step 5: Refactor `SavedSearchesPanel.tsx::openInMatch`** to one line:

```ts
  const openInMatch = (s: SavedSearch) => navigate(exploreUrlFromSavedQuery(s.query))
```

(import the helper; remove the now-unused `encodeChipsParam`/`encodeFiltersParam` imports if nothing else uses them).

- [ ] **Step 6: Verify** — `cd frontend && npx tsc -p tsconfig.json --noEmit` → 0 errors (memory: prefer the build-tsc; `npm run build` also fine here).
- [ ] **Step 7: Commit** — `feat(connect-fe): API layer for merged Discover (kinds, unseen, alert items, seen-at)`

---

### Task 7: Frontend — feed cards: attribution + saved-search alert card; UpdatesTab wiring

**Files:**
- Modify: `frontend/src/pages/student/connect/ConnectCards.tsx`
- Modify: `frontend/src/pages/student/connect/UpdatesTab.tsx`

- [ ] **Step 1: ConnectCards.tsx.** (a) Add `onRunSavedSearch?: (item: ConnectFeedItem) => void` to `Props`. (b) Dispatch the new kind in `FeedItemCard`:

```ts
  if (props.item.kind === 'saved_search_alert') return <SavedSearchAlertCard {...props} />
```

(c) Attribution caption — in `InstitutionRow`, under the program name line:

```tsx
const SOURCE_LABEL: Record<string, string> = {
  saved: 'Following · you saved a program here',
  application: 'Following · you applied here',
  explicit: 'You follow this school',
}
```
```tsx
        {item.follow_source && (
          <p className="text-[9px] text-muted-foreground/70 truncate">{SOURCE_LABEL[item.follow_source]}</p>
        )}
```

(d) New card at the bottom of the file (cobalt accents only, consistent with the others):

```tsx
function SavedSearchAlertCard({ item, onRunSavedSearch }: Props) {
  const n = item.match_count ?? 0
  return (
    <CardShell>
      <div className="p-4">
        <div className="flex items-start gap-2">
          <div className="w-7 h-7 rounded-md bg-secondary/10 flex items-center justify-center flex-shrink-0">
            <Bell size={14} className="text-secondary" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-foreground truncate">Saved search alert</p>
            <p className="text-[10px] text-muted-foreground truncate">“{item.search_name}”</p>
          </div>
          <span className="ml-auto text-[10px] text-muted-foreground flex-shrink-0">{relativeTime(item.date)}</span>
        </div>
        <h3 className="text-sm font-semibold text-foreground mt-3">
          New matches for “{item.search_name}” — {n} program{n !== 1 ? 's' : ''} now match{n === 1 ? 'es' : ''}
        </h3>
        {onRunSavedSearch && (
          <button
            onClick={() => onRunSavedSearch(item)}
            className="mt-3 px-3 py-1.5 text-xs font-medium rounded-lg border border-secondary text-secondary hover:bg-secondary/5 transition-colors"
          >
            Run this search
          </button>
        )}
      </div>
    </CardShell>
  )
}
```

Add `Bell` to the lucide import.

- [ ] **Step 2: UpdatesTab.tsx.** (a) Import `markConnectSeen` + `exploreUrlFromSavedQuery`; (b) record the visit + refresh the badge once items load — extend the existing record-visit effect (line ~87):

```ts
  useEffect(() => {
    if (!items.length) return
    const newest = items.reduce((m, it) => (it.date > m ? it.date : m), items[0].date)
    try {
      localStorage.setItem(SEEN_KEY, newest)
    } catch {
      /* ignore */
    }
    markConnectSeen()
    qc.invalidateQueries({ queryKey: ['connect-unseen'] })
  }, [items, qc])
```

(c) Internal link fix (line 59): `const onRsvpEvent = () => navigate('/s/explore?tab=events')`. (d) Empty-state CTA (line 132) stays `navigate('/s/explore')` — now lands on the For-you tab of the same page, which is correct. (e) Pass the new handler to `FeedItemCard`:

```tsx
                onRunSavedSearch={it => navigate(exploreUrlFromSavedQuery(it.search_query))}
```

- [ ] **Step 3: Verify** — `npx tsc --noEmit` → 0; `npx vitest run` (smoke) → green.
- [ ] **Step 4: Commit** — `feat(connect-fe): feed attribution + saved-search alert card`

---

### Task 8: Frontend — Discover hub: tab bar + ExplorePage tabs

**Files:**
- Create: `frontend/src/pages/student/explore/DiscoverTabBar.tsx`
- Modify: `frontend/src/pages/student/ExplorePage.tsx`

- [ ] **Step 1: Create `DiscoverTabBar.tsx`** — the ARIA tablist ported from PostsPage (keyboard nav included) with badge dots and the Manage-following button:

```tsx
// Discover hub sub-tabs (Spec 2026-06-12 §2). For you = the Match surface;
// Updates / Events / Peers are the absorbed Connect tabs. Badges: Updates =
// posts since last visit (server count); Events = recommended upcoming events.
import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, ChevronDown, Newspaper, Sparkles, Users } from 'lucide-react'
import { getConnectEvents, getFollowing, getUnseenCount } from '../../../api/connect'
import { getConnectSeenAt } from '../../../utils/connectSeen'

export type DiscoverTab = 'foryou' | 'updates' | 'events' | 'peers'
export const DISCOVER_TABS: readonly DiscoverTab[] = ['foryou', 'updates', 'events', 'peers'] as const

const TABS: { key: DiscoverTab; label: string; icon: typeof Newspaper }[] = [
  { key: 'foryou', label: 'For you', icon: Sparkles },
  { key: 'updates', label: 'Updates', icon: Newspaper },
  { key: 'events', label: 'Events', icon: Calendar },
  { key: 'peers', label: 'Peers', icon: Users },
]

interface Props {
  tab: DiscoverTab
  onChange: (t: DiscoverTab) => void
  onManageFollowing: () => void
}

export default function DiscoverTabBar({ tab, onChange, onManageFollowing }: Props) {
  const tablistRef = useRef<HTMLDivElement>(null)
  const { data: follows } = useQuery({ queryKey: ['connect-follows'], queryFn: getFollowing, retry: false })
  const { data: unseen = 0 } = useQuery({
    queryKey: ['connect-unseen'],
    queryFn: () => getUnseenCount(getConnectSeenAt()),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: eventsData } = useQuery({
    queryKey: ['connect-events', 'upcoming'],
    queryFn: () => getConnectEvents('upcoming'),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const recommended = (eventsData?.events ?? []).filter(e => e.recommended).length
  const badges: Partial<Record<DiscoverTab, number>> = { updates: unseen, events: recommended }
  const followCount = follows?.length ?? 0

  const handleTabKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, idx: number) => {
    const buttons = tablistRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
    if (!buttons) return
    let next = -1
    if (e.key === 'ArrowRight') next = (idx + 1) % buttons.length
    else if (e.key === 'ArrowLeft') next = (idx - 1 + buttons.length) % buttons.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = buttons.length - 1
    if (next >= 0) {
      e.preventDefault()
      buttons[next].focus()
      onChange(TABS[next].key)
    }
  }

  return (
    <div className="flex items-end justify-between border-b border-border mb-5">
      <div ref={tablistRef} role="tablist" aria-label="Discover sections" className="flex gap-1 overflow-x-auto">
        {TABS.map((t, idx) => {
          const badge = badges[t.key] ?? 0
          return (
            <button
              key={t.key}
              id={`discover-tab-${t.key}`}
              role="tab"
              aria-selected={tab === t.key}
              aria-controls={`discover-panel-${t.key}`}
              tabIndex={tab === t.key ? 0 : -1}
              onClick={() => onChange(t.key)}
              onKeyDown={e => handleTabKeyDown(e, idx)}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
                tab === t.key
                  ? 'border-secondary text-secondary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <t.icon size={14} />
              {t.label}
              {badge > 0 && (
                <span className="min-w-[16px] h-4 px-1 inline-flex items-center justify-center rounded-full bg-secondary text-secondary-foreground text-[9px] font-bold leading-none">
                  {badge > 9 ? '9+' : badge}
                </span>
              )}
            </button>
          )
        })}
      </div>
      <button
        onClick={onManageFollowing}
        className="hidden sm:inline-flex items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors flex-shrink-0"
      >
        Manage following ({followCount}) <ChevronDown size={13} />
      </button>
      <button
        onClick={onManageFollowing}
        className="inline-flex sm:hidden items-center gap-1 px-3 py-1.5 mb-1 text-xs font-medium text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors flex-shrink-0"
      >
        Following ({followCount}) <ChevronDown size={13} />
      </button>
    </div>
  )
}
```

- [ ] **Step 2: ExplorePage.tsx — hub integration.** Imports to add:

```tsx
import { useState, useEffect, useMemo } from 'react'        // (already there)
import DiscoverTabBar, { DISCOVER_TABS, type DiscoverTab } from './explore/DiscoverTabBar'
import UpdatesTab from './connect/UpdatesTab'
import EventsTab from './connect/EventsTab'
import PeersTab from './connect/PeersTab'
import ManageFollowingPanel from './connect/ManageFollowingPanel'
```

Inside the component, after `searchActive`:

```tsx
  // Hub sub-tabs (Spec 2026-06-12 §2). Unknown/absent tab → For you.
  const urlTab = searchParams.get('tab') as DiscoverTab | null
  const tab: DiscoverTab = urlTab && DISCOVER_TABS.includes(urlTab) ? urlTab : 'foryou'
  const setTab = (t: DiscoverTab) =>
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      if (t === 'foryou') next.delete('tab')
      else next.set('tab', t)
      return next
    }, { replace: true })
  const [managing, setManaging] = useState(false)
```

Per-tab header copy:

```tsx
const TAB_HEADERS: Record<DiscoverTab, { title: string; sub: string }> = {
  foryou: { title: 'Your strategy and your matches', sub: 'Ranked for fit, not fame — and every score explains itself.' },
  updates: { title: 'Updates from your schools', sub: 'Posts, deadlines, and changes from the institutions you follow.' },
  events: { title: 'Events from your schools', sub: 'Info sessions, fairs, and open days — RSVP from here.' },
  peers: { title: 'Peers on your path', sub: 'Opt-in: find students applying to the same programs.' },
}
```

(declare it at module scope, above the component). Replace the static `<PageHeader …/>` with:

```tsx
      <PageHeader eyebrow="Discover" title={TAB_HEADERS[tab].title} sub={TAB_HEADERS[tab].sub} />
      <DiscoverTabBar tab={tab} onChange={setTab} onManageFollowing={() => setManaging(true)} />
```

Wrap the EXISTING body (StrategyView → promos → MatchesSection → DiscoverySearch → Browse universities) so it renders only on the For-you tab, and add the connect panels:

```tsx
      {tab === 'foryou' ? (
        <div id="discover-panel-foryou" role="tabpanel" aria-labelledby="discover-tab-foryou">
          {/* …existing For-you body unchanged (rail added in Task 9)… */}
        </div>
      ) : (
        <div
          id={`discover-panel-${tab}`}
          role="tabpanel"
          aria-labelledby={`discover-tab-${tab}`}
          tabIndex={0}
          className="focus-visible:outline-none"
        >
          {tab === 'updates' && <UpdatesTab />}
          {tab === 'events' && <EventsTab />}
          {tab === 'peers' && <PeersTab />}
        </div>
      )}

      {managing && <ManageFollowingPanel onClose={() => setManaging(false)} />}
```

Also gate the For-you data queries off other tabs — change the two `enabled:` options: `enabled: !searchActive && tab === 'foryou'` (universities + featured promos).

NOTE: `?tab=` must not collide with search params — DiscoverySearch uses `q/chips/filters/sort`, browse filters use `country/setting/...`. `tab` is new; `setTab` preserves the rest (param-preserving). CompareTray syncUrl on `/s/explore` is pathname-based, unaffected.

- [ ] **Step 3: Verify** — `npx tsc --noEmit`; `npm run build`; then `npx vitest run` → green. Manually sanity-check no leftover references: `grep -n "connect-panel" src/pages/student/ExplorePage.tsx` (should be none — discover-panel ids).
- [ ] **Step 4: Commit** — `feat(discover): hub sub-tabs absorb Connect (updates/events/peers)`

---

### Task 9: Frontend — the live right rail + follow state

**Files:**
- Create: `frontend/src/pages/student/explore/rail/DiscoverRail.tsx`
- Modify: `frontend/src/pages/student/ExplorePage.tsx`

- [ ] **Step 1: Create `DiscoverRail.tsx`:**

```tsx
// The Discover live rail (Spec 2026-06-12 §2) — ambient Connect context while
// browsing matches: latest updates, next events, deadline radar, following +
// follow suggestions. Rail rows fire NO engagement tracking by design (§2).
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Bell, CalendarClock, CalendarDays, GraduationCap, Newspaper, UserPlus } from 'lucide-react'
import { getConnectEvents, getConnectFeed, getFollowing } from '../../../../api/connect'
import { getMatches } from '../../../../api/matching'
import { listSaved } from '../../../../api/saved-lists'

function relTime(iso: string): string {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function eventDay(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

interface Props {
  followedIds: Set<string>
  onToggleFollow: (institutionId: string) => void
  onOpenTab: (t: 'updates' | 'events') => void
  onManageFollowing: () => void
}

export default function DiscoverRail({ followedIds, onToggleFollow, onOpenTab, onManageFollowing }: Props) {
  const { data: feed } = useQuery({
    queryKey: ['connect-feed-rail'],
    queryFn: () => getConnectFeed('recent', undefined, { limit: 8 }),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: eventsData } = useQuery({
    queryKey: ['connect-events', 'upcoming'],
    queryFn: () => getConnectEvents('upcoming'),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: deadlines } = useQuery({
    queryKey: ['connect-deadline-radar'],
    queryFn: () => getConnectFeed('recent', undefined, { limit: 12, kinds: 'deadline' }),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { data: matches = [] } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches(), retry: 1, staleTime: 60_000 })
  const { data: saved } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })

  const updates = (feed?.items ?? []).filter(it => it.kind === 'post').slice(0, 3)
  const events = (eventsData?.events ?? []).slice(0, 3)
  // Soonest deadlines: items arrive urgency-sorted on the recency axis; sort by days_until to be explicit.
  const radar = [...(deadlines?.items ?? [])]
    .sort((a, b) => (a.days_until ?? 999) - (b.days_until ?? 999))
    .slice(0, 3)

  // Follow suggestions (Spec 2026-06-12 §6.6): institutions from top matches +
  // saved programs the student doesn't follow yet, in match order, top 3.
  const suggestions = useMemo(() => {
    const out: { id: string; name: string }[] = []
    const seen = new Set<string>()
    const push = (id?: string | null, name?: string | null) => {
      if (!id || seen.has(id) || followedIds.has(id)) return
      seen.add(id)
      out.push({ id, name: name || 'Institution' })
    }
    for (const m of matches) push(m.institution_id, m.institution_name)
    for (const s of saved ?? []) push(s.institution_id, s.institution_name)
    return out.slice(0, 3)
  }, [matches, saved, followedIds])

  const followCount = followedIds.size

  return (
    <div className="space-y-4">
      {/* From your schools */}
      <RailCard
        icon={Newspaper}
        title="From your schools"
        action={updates.length > 0 ? { label: 'See all', onClick: () => onOpenTab('updates') } : undefined}
      >
        {updates.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">
            {followCount === 0 ? 'Follow a school to see its updates here.' : 'No updates yet from schools you follow.'}
          </p>
        ) : (
          updates.map(it => (
            <button
              key={it.id}
              onClick={() => onOpenTab('updates')}
              className="w-full text-left px-1 py-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <p className="text-xs font-semibold text-foreground line-clamp-1">{it.title}</p>
              <p className="text-[10px] text-muted-foreground truncate">
                {it.institution_name} · {relTime(it.date)}
              </p>
            </button>
          ))
        )}
      </RailCard>

      {/* Upcoming events */}
      <RailCard
        icon={CalendarDays}
        title="Upcoming events"
        action={events.length > 0 ? { label: 'See all', onClick: () => onOpenTab('events') } : undefined}
      >
        {events.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">No upcoming events from schools you follow.</p>
        ) : (
          events.map(ev => (
            <button
              key={ev.id}
              onClick={() => onOpenTab('events')}
              className="w-full text-left px-1 py-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <p className="text-xs font-semibold text-foreground line-clamp-1">{ev.event_name}</p>
              <p className="text-[10px] text-muted-foreground truncate">
                {ev.institution_name} · {eventDay(ev.start_time)}
                {ev.rsvp_state === 'rsvp' && <span className="text-secondary font-semibold"> · Going</span>}
              </p>
            </button>
          ))
        )}
      </RailCard>

      {/* Deadline radar */}
      <RailCard icon={CalendarClock} title="Deadline radar">
        {radar.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">Save a program to track its deadline here.</p>
        ) : (
          radar.map(it => (
            <button
              key={it.id}
              onClick={() => onOpenTab('updates')}
              className="w-full text-left px-1 py-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <p className="text-xs font-semibold text-foreground line-clamp-1">{it.program_name}</p>
              <p className={`text-[10px] truncate ${(it.days_until ?? 99) <= 7 ? 'text-error font-semibold' : (it.days_until ?? 99) <= 30 ? 'text-warning' : 'text-muted-foreground'}`}>
                {it.days_until === 0 ? 'Due today' : `${it.days_until} day${it.days_until !== 1 ? 's' : ''} left`} · {it.institution_name}
              </p>
            </button>
          ))
        )}
      </RailCard>

      {/* Following + suggestions */}
      <RailCard
        icon={Bell}
        title={`Following · ${followCount}`}
        action={{ label: 'Manage', onClick: onManageFollowing }}
      >
        {suggestions.length === 0 ? (
          <p className="text-xs text-muted-foreground px-1">Updates from schools you follow land in this rail.</p>
        ) : (
          <>
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground px-1 mb-1">Add to your feed</p>
            {suggestions.map(s => (
              <div key={s.id} className="flex items-center gap-2 px-1 py-1.5">
                <div className="w-6 h-6 rounded-md bg-secondary/10 flex items-center justify-center flex-shrink-0">
                  <GraduationCap size={12} className="text-secondary" />
                </div>
                <p className="text-xs font-medium text-foreground truncate flex-1">{s.name}</p>
                <button
                  onClick={() => onToggleFollow(s.id)}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-secondary hover:underline flex-shrink-0"
                >
                  <UserPlus size={11} /> Follow
                </button>
              </div>
            ))}
          </>
        )}
      </RailCard>
    </div>
  )
}

function RailCard({
  icon: Icon,
  title,
  action,
  children,
}: {
  icon: typeof Newspaper
  title: string
  action?: { label: string; onClick: () => void }
  children: React.ReactNode
}) {
  return (
    <section className="bg-card rounded-xl border border-border p-3">
      <div className="flex items-center gap-1.5 mb-2 px-1">
        <Icon size={13} className="text-secondary" />
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground flex-1">{title}</h3>
        {action && (
          <button onClick={action.onClick} className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-secondary hover:underline">
            {action.label} <ArrowRight size={11} />
          </button>
        )}
      </div>
      <div className="space-y-0.5">{children}</div>
    </section>
  )
}
```

- [ ] **Step 2: ExplorePage — follow state + two-column grid.** Add imports `{ getFollowing, followInstitution, unfollowInstitution }` from `../../api/connect` and `DiscoverRail from './explore/rail/DiscoverRail'`. Add follow state (mirrors the savedIds pattern at line 125):

```tsx
  // Followed institutions — drives card follow toggles + rail suggestions.
  const { data: follows, refetch: refetchFollows } = useQuery({
    queryKey: ['connect-follows'],
    queryFn: getFollowing,
    retry: false,
  })
  const [followedIds, setFollowedIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (follows) setFollowedIds(new Set(follows.map(f => String(f.institution_id))))
  }, [follows])

  const toggleFollow = async (institutionId: string) => {
    const was = followedIds.has(institutionId)
    setFollowedIds(prev => {
      const n = new Set(prev)
      if (was) n.delete(institutionId)
      else n.add(institutionId)
      return n
    })
    try {
      if (was) await unfollowInstitution(institutionId)
      else await followInstitution(institutionId)
      queryClient.invalidateQueries({ queryKey: ['connect-follows'] })
      queryClient.invalidateQueries({ queryKey: ['connect-feed-rail'] })
    } catch {
      showToast(`We couldn't ${was ? 'unfollow' : 'follow'} this school. Please try again.`, 'error')
      queryClient.invalidateQueries({ queryKey: ['connect-follows'] })
      refetchFollows()
    }
  }
```

Wrap the For-you panel in the two-column grid (page stays full-bleed; rail is density per the app-shell rule):

```tsx
        <div id="discover-panel-foryou" role="tabpanel" aria-labelledby="discover-tab-foryou"
             className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_19rem] gap-6 items-start">
          <div className="min-w-0">
            {/* …existing For-you body… */}
          </div>
          <aside className="hidden xl:block sticky top-4">
            <DiscoverRail
              followedIds={followedIds}
              onToggleFollow={toggleFollow}
              onOpenTab={t => setTab(t)}
              onManageFollowing={() => setManaging(true)}
            />
          </aside>
        </div>
```

Grid-density note: the For-you main column lost ~19rem at xl, so inside it change the three card grids (`featured promos`, `universities loading`, `universities results`) from `xl:grid-cols-4` to `xl:grid-cols-3` — at rail widths 4-up becomes cramped. MatchesSection grids are already `lg:grid-cols-3` (fine).

- [ ] **Step 3: Verify** — tsc 0, build 0, vitest green.
- [ ] **Step 4: Commit** — `feat(discover): live right rail — updates, events, deadline radar, follow suggestions`

---

### Task 10: Frontend — card integrations (follow toggles + event chips)

**Files:**
- Modify: `frontend/src/pages/student/explore/cards/UniversityCard.tsx`
- Modify: `frontend/src/pages/student/explore/cards/ProgramCard.tsx`
- Modify: `frontend/src/pages/student/match/MatchCard.tsx`
- Modify: `frontend/src/pages/student/match/MatchesSection.tsx`
- Modify: `frontend/src/pages/student/explore/discovery/DiscoverySearch.tsx`
- Modify: `frontend/src/pages/student/ExplorePage.tsx`

- [ ] **Step 1: UniversityCard follow toggle.** Props gain:

```ts
interface Props {
  institution: UniversityData
  onClick: () => void
  following?: boolean
  onToggleFollow?: () => void
}
```

Footer (replace the existing footer div content):

```tsx
      <div className="flex items-center border-t border-border mt-auto px-5 py-2.5">
        <span className="text-xs font-semibold text-secondary flex-1">View university</span>
        {onToggleFollow && (
          <button
            onClick={e => { e.stopPropagation(); onToggleFollow() }}
            aria-pressed={!!following}
            className={`mr-3 inline-flex items-center gap-1 text-xs font-semibold transition-colors ${
              following ? 'text-muted-foreground hover:text-foreground' : 'text-secondary hover:underline'
            }`}
          >
            {following ? <><BellRing size={12} /> Following</> : <><BellPlus size={12} /> Follow</>}
          </button>
        )}
        <ChevronRight size={16} className="text-secondary group-hover/card:translate-x-0.5 transition-transform" />
      </div>
```

Add `BellPlus, BellRing` to the lucide import. In **ExplorePage**, pass to the browse grid:

```tsx
                  <UniversityCard
                    key={inst.id}
                    institution={inst}
                    onClick={() => navigate(`/s/institutions/${inst.id}`)}
                    following={followedIds.has(String(inst.id))}
                    onToggleFollow={() => toggleFollow(String(inst.id))}
                  />
```

- [ ] **Step 2: Event map in ExplorePage.** Below the follow state:

```tsx
  // Next upcoming event per institution — for the Handshake-style event chips
  // on cards (Spec 2026-06-12 §6.4). Events arrive start_time-asc.
  const { data: upcomingEvents } = useQuery({
    queryKey: ['connect-events', 'upcoming'],
    queryFn: () => getConnectEvents('upcoming'),
    staleTime: 5 * 60 * 1000,
    retry: false,
    enabled: tab === 'foryou',
  })
  const nextEventByInst = useMemo(() => {
    const m = new Map<string, { event_name: string; start_time: string }>()
    for (const e of upcomingEvents?.events ?? []) {
      if (!m.has(e.institution_id)) m.set(e.institution_id, { event_name: e.event_name, start_time: e.start_time })
    }
    return m
  }, [upcomingEvents])
```

(import `getConnectEvents`).

- [ ] **Step 3: MatchCard event chip.** Props gain:

```ts
  nextEvent?: { event_name: string; start_time: string } | null
  onEventClick?: () => void
```

In the badge row (after the acceptPct span):

```tsx
            {nextEvent && (
              <button
                onClick={e => { e.stopPropagation(); onEventClick?.() }}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-md bg-secondary/10 text-secondary hover:bg-secondary/20 transition-colors"
                title={`Upcoming: ${nextEvent.event_name}`}
              >
                <CalendarDays size={10} />
                {nextEvent.event_name.length > 18 ? nextEvent.event_name.slice(0, 18) + '…' : nextEvent.event_name} ·{' '}
                {new Date(nextEvent.start_time).toLocaleDateString('en-US', { weekday: 'short' })}
              </button>
            )}
```

Add `CalendarDays` to the lucide import; destructure the new props in the component signature.

- [ ] **Step 4: MatchesSection threading.** Props gain:

```ts
interface MatchesSectionProps {
  savedIds: Set<string>
  onToggleSave: (programId: string) => void
  nextEventByInstitution?: Map<string, { event_name: string; start_time: string }>
  onEventClick?: () => void
}
```

In `renderCard`, pass:

```tsx
        nextEvent={m.institution_id ? nextEventByInstitution?.get(m.institution_id) ?? null : null}
        onEventClick={onEventClick}
```

In **ExplorePage**:

```tsx
          <MatchesSection
            savedIds={savedIds}
            onToggleSave={toggleSave}
            nextEventByInstitution={nextEventByInst}
            onEventClick={() => setTab('events')}
          />
```

- [ ] **Step 5: ProgramCard follow toggle + event chip.** Props gain:

```ts
  following?: boolean
  onToggleFollow?: () => void
  nextEvent?: { event_name: string; start_time: string } | null
  onEventClick?: () => void
```

Header: second icon button left of the save button (save is `top-3 right-3`):

```tsx
        {onToggleFollow && (
          <button
            onClick={e => { e.stopPropagation(); onToggleFollow() }}
            className={`absolute top-3 right-12 p-2 rounded-full transition-colors ${
              following ? 'text-secondary bg-secondary/10' : 'text-muted-foreground hover:bg-muted'
            }`}
            aria-label={following ? `Unfollow ${program.institution_name}` : `Follow ${program.institution_name} for updates`}
            title={following ? `Following ${program.institution_name}` : `Follow ${program.institution_name}`}
          >
            {following ? <BellRing size={15} /> : <BellPlus size={15} />}
          </button>
        )}
```

(widen the title padding `pr-9` → `pr-[4.5rem]` when `onToggleFollow` is provided: `className={...(onToggleFollow ? 'pr-[4.5rem]' : 'pr-9')}` on the flex row). Event chip — in the band/ring row (the `{(bandLabel || hasDual) && …}` block), extend the condition to `{(bandLabel || hasDual || nextEvent) && …}` and add the same chip button as MatchCard before the DualRing span. Add `BellPlus, BellRing, CalendarDays` to the lucide import.

- [ ] **Step 6: DiscoverySearch threading.** Props (new optional interface — component currently takes none):

```ts
interface DiscoverySearchProps {
  followedIds?: Set<string>
  onToggleFollow?: (institutionId: string) => void
  nextEventByInstitution?: Map<string, { event_name: string; start_time: string }>
  onEventClick?: () => void
}
```

At the `ProgramCard` render site inside DiscoverySearch (find `<ProgramCard`), add:

```tsx
                following={followedIds?.has(p.institution_id)}
                onToggleFollow={onToggleFollow ? () => onToggleFollow(p.institution_id) : undefined}
                nextEvent={nextEventByInstitution?.get(p.institution_id) ?? null}
                onEventClick={onEventClick}
```

(adjust `p` to the actual loop variable name). In **ExplorePage**:

```tsx
          <DiscoverySearch
            followedIds={followedIds}
            onToggleFollow={toggleFollow}
            nextEventByInstitution={nextEventByInst}
            onEventClick={() => setTab('events')}
          />
```

- [ ] **Step 7: Verify** — tsc 0, build 0, vitest green.
- [ ] **Step 8: Commit** — `feat(discover): follow toggles + event chips on cards`

---

### Task 11: Frontend — nav, redirects, IA contract, cleanup

**Files:**
- Modify: `frontend/src/utils/information-architecture.ts`
- Test: `frontend/src/test/information-architecture.test.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/StudentLayout.tsx`
- Modify: `frontend/src/components/layout/StudentTitle.tsx`
- Modify: `frontend/src/components/student/GlobalSearch.tsx`
- Delete: `frontend/src/pages/student/PostsPage.tsx`

- [ ] **Step 1: Failing IA test** — add to `information-architecture.test.ts`:

```ts
  // Discover + Connect merge (Spec 2026-06-12) — /s/posts retired into /s/explore tabs.
  it('retires /s/posts into Discover hub tabs', () => {
    expect(STUDENT_LEGACY_REDIRECTS['/s/posts']).toBe('/s/explore?tab=updates')
    expect(POSTS_TAB_REDIRECTS.updates).toBe('/s/explore?tab=updates')
    expect(POSTS_TAB_REDIRECTS.events).toBe('/s/explore?tab=events')
    expect(POSTS_TAB_REDIRECTS.peers).toBe('/s/explore?tab=peers')
    // One hop — no redirect target is itself a legacy path.
    for (const target of Object.values(POSTS_TAB_REDIRECTS)) {
      expect(Object.keys(STUDENT_LEGACY_REDIRECTS)).not.toContain(target.split('?')[0])
    }
  })
```

(import `POSTS_TAB_REDIRECTS`). Run → FAIL.

- [ ] **Step 2: IA contract** — in `utils/information-architecture.ts` add `'/s/posts': '/s/explore?tab=updates',` to `STUDENT_LEGACY_REDIRECTS` and:

```ts
/** /s/posts?tab=… → Discover hub tab targets (App.tsx PostsRedirect contract,
 *  Spec 2026-06-12 — Connect merged into Discover). */
export const POSTS_TAB_REDIRECTS: Record<string, string> = {
  updates: '/s/explore?tab=updates',
  events: '/s/explore?tab=events',
  peers: '/s/explore?tab=peers',
}
```

Run the IA test → PASS.

- [ ] **Step 3: App.tsx.** Add next to `ManageRedirect`:

```tsx
// /s/posts retired (Spec 2026-06-12) — Connect merged into the Discover hub.
// One hop, tab-mapping per POSTS_TAB_REDIRECTS.
function PostsRedirect() {
  const [params] = useSearchParams()
  const tab = params.get('tab')
  const target = (tab && POSTS_TAB_REDIRECTS[tab]) || '/s/explore?tab=updates'
  return <Navigate to={target} replace />
}
```

(import `POSTS_TAB_REDIRECTS` from `./utils/information-architecture` — check the existing import path style in App.tsx). Replace the route at line 207: `{ path: 'posts', element: <PostsRedirect /> },` and delete the `StudentPostsPage` import. CAREFUL: `/i` routes also have a `posts` path (institution PostsPage) — leave that untouched.

- [ ] **Step 4: StudentLayout.** NAV_ITEMS → 3 entries (drop the Connectors line, drop the `Newspaper` import):

```tsx
const NAV_ITEMS = [
  { to: '/s', icon: Compass, label: 'Uni', end: true },
  { to: '/s/explore', icon: Target, label: 'Discover', end: false },
  { to: '/s/space', icon: Backpack, label: 'My Space', end: false },
]
```

Nav dot — add the query inside the component:

```tsx
  // "New updates" dot on Discover (Spec 2026-06-12 §6.3).
  const { data: unseenCount = 0 } = useQuery({
    queryKey: ['connect-unseen'],
    queryFn: () => getUnseenCount(getConnectSeenAt()),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
```

(imports: `useQuery` from @tanstack/react-query, `getUnseenCount` from `../../api/connect`, `getConnectSeenAt` from `../../utils/connectSeen`). Desktop NavLink children — after `{item.label}`:

```tsx
                      {item.to === '/s/explore' && unseenCount > 0 && (
                        <span className="absolute top-4 right-1 w-1.5 h-1.5 rounded-full bg-secondary" aria-hidden="true" />
                      )}
```

Mobile tab bar — inside the NavLink, wrap the icon:

```tsx
            <span className="relative">
              <item.icon size={20} strokeWidth={1.75} />
              {item.to === '/s/explore' && unseenCount > 0 && (
                <span className="absolute -top-0.5 -right-1 w-1.5 h-1.5 rounded-full bg-secondary" aria-hidden="true" />
              )}
            </span>
```

- [ ] **Step 5: StudentTitle.tsx** — remove the `'/s/posts': 'Connectors',` entry (the `/s/explore` entry already exists; verify its label reads 'Discover'). **GlobalSearch.tsx:42** — repoint the quick link:

```tsx
  { label: 'Updates from your schools', sub: 'Posts, events, and peers — now in Discover', to: '/s/explore?tab=updates', icon: Newspaper },
```

- [ ] **Step 6: Delete `frontend/src/pages/student/PostsPage.tsx`** (`git rm`). Grep for stragglers: `grep -rn "PostsPage\|/s/posts" frontend/src --include=*.ts*` → only the institution `pages/institution/PostsPage` import in App.tsx and the IA contract/test/redirect references should remain.

- [ ] **Step 7: Verify** — `npx tsc --noEmit` 0; `npm run build` 0; `npx vitest run` green.
- [ ] **Step 8: Commit** — `feat(discover)!: retire /s/posts — 3-tab nav, redirects, nav badge`

---

### Task 12: Full verification

- [ ] Frontend: `cd frontend && npx tsc --noEmit && npm run build && npx vitest run` — all green, 0 errors.
- [ ] Backend: full connect + matching suites, then the whole backend suite if time allows (CI is the full gate):

```bash
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true COGNITO_BYPASS=true S3_LOCAL_MODE=true \
  .venv/bin/pytest tests/test_connect_feed.py tests/test_connect_events.py tests/test_connect_follows.py \
  tests/test_connect_peers.py tests/test_match_explore_api.py -v --tb=short ; echo EXIT=$?
```

- [ ] Lint: `cd unipaith-backend && .venv/bin/ruff check src tests ; echo EXIT=$?` and `cd frontend && npx eslint src --max-warnings=0` (match the repo's lint command in Makefile).
- [ ] iCloud-dup purge before committing (memory gotcha): `git ls-files | grep ' 2\.' ` must be empty; `find . -name "* 2.*" -not -path "./node_modules/*" -delete` if disk pollution appeared.
- [ ] Commit anything outstanding.

### Task 13: Ship (standing rule — same session)

- [ ] Push branch, open PR against `main` with a summary referencing the spec; merge (squash) once CI is green (repo merges immediately; checks are non-blocking — but wait for backend CI green per the standing verify rule when feasible).
- [ ] Confirm auto-deploy: frontend bundle (S3+CloudFront) and backend (ECS) — backend deploy is the ~12-min gated workflow.
- [ ] Verify live: `curl -s https://app.unipaith.co/assets/index-*.js | grep -o "Deadline radar"` (marker string from the rail) and `curl -s -H "Authorization: Bearer dev:..." https://api.unipaith.co/api/v1/connect/feed/unseen-count` → 422 (route exists, since required) not 404.
- [ ] Confirm worktree clean, `main` at the new commit.

---

## Self-review notes

- Spec coverage: §1 routing → Task 11; §2 hub/rail → Tasks 8–9; §3 tabs → Task 8; §4 naming → Task 8 (TAB_HEADERS); §5.1 kinds → Task 1; §5.2 follow_source → Task 2; §5.3 unseen → Task 4; §5.4 alerts → Task 3; §6.1 follow buttons → Tasks 9–10; §6.2 attribution → Task 7; §6.3 badges → Tasks 8+11; §6.4 event chips → Task 10; §6.5 alert card → Task 7; §6.6 suggestions → Task 9; §8 testing → Tasks 1–5, 11, 12; §9 cleanup → Task 11.
- Type consistency: `DiscoverTab` defined once in DiscoverTabBar and imported by ExplorePage; `nextEvent` chip shape `{ event_name, start_time }` consistent across MatchCard/ProgramCard/MatchesSection/ExplorePage; `['connect-unseen']` query key shared by StudentLayout + DiscoverTabBar + UpdatesTab invalidation.
- Known judgment calls encoded: unseen-count is posts-only (future-dated deadline items would never age out); saved-search alert phrasing uses the persisted total (`last_match_count`), not an unpersisted delta; rail hidden < xl with badges carrying the signal.
