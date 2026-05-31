# 56 · Search, Feed & Recommendations

> The discovery engines that make the platform feel alive and personalized — at Handshake/LinkedIn grade. Three related systems: **search** (find programs/schools/institutions fast), **feed ranking** (the Connect feed, `20`), and **recommendations + saved-search alerts** (the retention loop). Feature docs `09`/`10`/`20` own the surfaces; this owns the relevance + retrieval architecture behind them.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Builds on `06` (3-layer AI/ML), `42`–`45` (signals + agents), `55` (caching/jobs), `57` (alert delivery).

---

## 1. Search architecture (staged, don't over-build)

Match the speed users expect from Handshake's job search ([Handshake search](https://support.joinhandshake.com/hc/en-us/articles/218693388-Saving-Job-Searches-and-Receiving-Job-Alerts)) with a staged approach:

### Stage 1 — Postgres-native (MVP)
- **Full-text search** (`tsvector` + GIN) on programs/schools/institutions (name, description, field, keywords).
- **Trigram** (`pg_trgm`) for fuzzy/typo-tolerant typeahead.
- Faceted filters as indexed WHERE clauses (degree, modality, cost band, location, deadline).
- Already partially present: `programs.py` has `/search/nlp` + `/search/semantic` (`50` §4).

### Stage 2 — Dedicated search (scale)
- Move to **OpenSearch/Elasticsearch** when result quality/latency/volume outgrows Postgres (faceting + relevance scoring + synonyms + highlighting).
- Index kept fresh via the task queue (`55` §3) on program/institution writes.
- Don't do this until Stage-1 latency or relevance is a real problem — premature.

### Hybrid keyword + semantic
- Combine lexical (FTS/BM25) with **semantic** (pgvector embedding similarity, `06` §4 / `51` `embeddings`) → re-rank by a weighted blend. This is what makes "find me programs like X" work beyond keyword match.
- The `/search/semantic` route is the seam; `45` provides the query→embedding step.

---

## 2. Typeahead / instant search (`53` §3.6)

- Debounced 150–250ms; serve from a cached, denormalized index (Redis, `55` §2) for sub-100ms.
- Returns mixed entity types (programs, schools, institutions) grouped, with matched-substring highlight.
- Recent + suggested queries on focus.
- Backend endpoint returns minimal payload (id, name, type, one stat) — full detail loads on select.

---

## 3. Faceted filtering (Match/Explore, `09`/`10`)

- Filters update results **live** (no "apply" button) — debounced, optimistic count.
- Show result counts per facet value before selection ("Master's (142)").
- Filter state in the URL (`05` §13) so a search is shareable/bookmarkable — prerequisite for saved searches (§5).
- Combine with the dual-score sort (fitness/confidence) + "best fit / stretch / safer" banding (`09`).

---

## 4. Feed ranking — the Connect feed (`20`)

LinkedIn proves a **ranked** feed drives engagement far past chrono ([feed ranking](https://gouravdigitalclub.com/blog/linkedin-profile-optimization/)). Connect feed ranking:

### Inputs
- Recency (decay).
- Affinity: how related the post's institution/program is to the student's saved/applied/followed set + match scores.
- Relevance: deadline proximity, program-change importance (a requirement change on an applied program ranks top — never suppressed, `20` §4.3).
- Engagement signal: post type the student tends to interact with.

### Model
- MVP: a **transparent weighted score** (recency × affinity × relevance × type-weight) — explainable, tunable, no black box.
- Later: a learned re-ranker (`06` L3) trained on engagement, gated by the fairness harness (`46` §6) so the feed doesn't amplify bias.
- **"Why am I seeing this"** affordance (`53` §10 open question) — students distrust opaque feeds; transparency is a UniPaith value (`07` §2 "explain everything").
- A **chrono toggle** as the escape hatch.

### Serving
- Precompute per-user feed candidates in a job (`55` §3) + cache (Redis); merge live items at read. Pull vs push hybrid — push for high-fanout institutions, pull for the long tail ([fan-out](https://codelit.io/blog/notification-system-architecture)).

---

## 5. Saved searches & alerts (Handshake's retention engine)

The single highest-retention feature Handshake has; spec'd in `53` §7, engineered here:
- Persist a saved search = the **criteria** (filters + query), not results.
- A scheduled job (`55` §3) re-runs each active saved search on its cadence (instant/daily/weekly) → diffs against last-seen → new matches.
- New matches → notification (`57`) + Connect feed item (`20`) + optional email digest.
- **Deadline-closing alerts**: job scans followed/saved programs for approaching `application_deadline` → alert (Handshake's "application window closing" — [source](https://support.joinhandshake.com/hc/en-us/articles/218693388-Saving-Job-Searches-and-Receiving-Job-Alerts)).
- Managed in `21` Settings → Alerts; pausable/deletable per Handshake's pattern.
- Frequency + dedup so a student isn't alerted twice for the same program.

---

## 6. Recommendations (explainable)

Handshake recommends from interests + activity; we add explainability ([Handshake recs](https://www.collegeraptor.com/explore-careers/articles/careers-internships/handshake-platform/)):
- **Program recommendations** (`09`): the match engine output, surfaced with "recommended because…" (fitness drivers, `42` §4).
- **"Students like you also considered"** (collaborative filtering, `06` L3) — clearly labeled, privacy-safe (aggregate, never naming peers).
- **Event/post recommendations** in Connect (`20`) from followed + affinity.
- **Next-best-action** nudges (`44` §8 engagement outputs): "add a recommender," "3 saved programs close this week."
- All recs respect `consent.matching` (`46` §2) — no AI personalization without consent; fall back to popularity/recency.

---

## 7. Relevance tuning & experimentation

A marketed app tunes relevance continuously:
- **A/B testing** harness (the `ml_loop` `ab_test_assignments` table exists, `51`) — test ranking weights, alert cadences, rec algorithms.
- Offline eval: hold-out + metrics (precision@k for search, CTR/engagement for feed, apply-rate for recs).
- **Guardrail metrics** so an engagement win that hurts fairness (`46` §6) or apply-quality is caught.
- Log every search/feed/rec impression + outcome (`44` §8) to power tuning + the learned models.

---

## 8. Performance

- Search/typeahead p95 < 200ms (cached); feed first-page < 300ms; honor `55` budgets.
- Virtualized infinite scroll on results/feed (`54` §6).
- Cache hot searches + precomputed feeds (Redis, `55` §2); invalidate on relevant writes.

---

## 9. Open questions

- **OpenSearch trigger** — define the latency/volume threshold that promotes search from Postgres to a dedicated engine (don't pre-build).
- **Feed ranked-vs-chrono default** — ranked-with-why + chrono toggle recommended (`53` §10); confirm.
- **Collaborative filtering cold-start** — until enough data, recs fall back to fitness + popularity; define the switchover.
- **Alert volume governance** — global cap on alerts/user/day so the retention feature doesn't become noise (ties `57` digest/batching).

Sources: [Handshake saved searches & alerts](https://support.joinhandshake.com/hc/en-us/articles/218693388-Saving-Job-Searches-and-Receiving-Job-Alerts) · [Handshake as "LinkedIn for students"](https://www.collegeraptor.com/explore-careers/articles/careers-internships/handshake-platform/) · [LinkedIn feed/ranking](https://gouravdigitalclub.com/blog/linkedin-profile-optimization/) · [fan-out architecture](https://codelit.io/blog/notification-system-architecture).
