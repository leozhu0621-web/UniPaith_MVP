# 56 · Search, Feed & Recommendations — Build Spec

> Buildable spec for the discovery substrate: full-text + semantic search, faceted filters, the ranked Connect feed, recommendations, and saved-search alerts. Grounded in the real backend modules that already exist (`services/search_service.py`, `query_parser.py`, `reranker.py`, `ai/connect_ranker.py`, `ai/query_interpreter.py`, `ai/event_recommender.py`) and the FE `api/search.ts`/`api/connect.ts`. Companion to `09`/`10` (Match/Discover UI), `20` (Connect feed), `60` (crawled knowledge), `63` (embeddings/rerank), `57` (alert delivery), `55` (substrate).
>
> Status: **draft v2.0** · 2026-05-30 · v2 converts standards → build tasks against real modules.

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Search service | `services/search_service.py` | exists — confirm FTS/trgm impl; extend to hybrid |
| NL query → filters | `services/query_parser.py` + `ai/query_interpreter.py` | exists (interpreter is Qwen-served per `63`) |
| Reranking | `services/reranker.py` | exists — wire to Qwen3-Reranker (`63`) |
| Feed ranking | `ai/connect_ranker.py` + `services/connect_service.py` | exists |
| Event recs | `ai/event_recommender.py` | exists |
| Net-price (a rec input) | `services/net_price_service.py` | exists |
| Match banding | `services/match_banding.py` | exists |
| FE | `api/search.ts`, `api/connect.ts` | exist |
| Saved-search + alerts | — | **NEW (build)** |
| Hybrid semantic fusion | — | **NEW (build on pgvector `63`)** |
| Faceted live counts | — | **verify/build in search_service** |

So this is mostly **wiring + extending real modules**, plus building saved-searches.

---

## 2. Search architecture (staged, in `services/search_service.py`)

- **Phase A — Postgres** (cheap, no new infra): `tsvector` FTS + `pg_trgm` fuzzy over `programs`/`schools`/`scholarships`. Confirm `search_service.py` already does this; add GIN indexes (`55` §7).
- **Phase B — hybrid semantic:** pgvector ANN over Qwen embeddings (`63` §8, `embeddings` table) **fused with** keyword via **reciprocal-rank fusion** in `search_service`; `reranker.py` (Qwen3-Reranker) does the final precision pass. Result: semantic recall + exact precision.
- **Phase C — OpenSearch** only if program count / query volume demands faceting at scale; same hybrid model.
- **NL interpretation:** `ai/query_interpreter.py` (Qwen, `63`) turns NL → structured filters + constraint chips rendered by `10`. Falls back to `query_parser.py` (rule-based) on AI failure (`50` §6).

Endpoints (under `/api/v1`, confirm against `50`): `GET /programs/search` (keyword+facets), `POST /programs/search/semantic` or `…/nlp` (NL → hybrid). Response: `{items, total, facets, next_cursor}`.

---

## 3. Faceted filters (build into the search response)

- Facets: degree type, modality, location, cost band, deadline window, test policy, field/CIP, selectivity.
- **Live counts:** `search_service` returns `facets: {facet: [{value, count}]}` computed alongside results (one query with aggregates) so toggling updates counts (`53` Handshake bar).
- Filter state in URL (`05` §13, `54` §2); FE sends the full filter object as the query key (`54` §3).

---

## 4. Connect feed ranking (`ai/connect_ranker.py` + `services/connect_service.py`)

- **Sources:** posts/events/deadline-reminders/program-changes from followed institutions (`20`) + crawler `change_events` (`60` §3B).
- **Ranking blend (formalize in `connect_ranker`):** `score = w_recency·recency + w_rel·relevance(profile_embedding · item_embedding, saved/applied/followed) + w_mat·materiality(60) + w_eng·engagement`. Default reverse-chron; "most relevant" toggle applies the blend (`20` §4.2). Weights config-tunable + A/B'd (§6).
- Pinned institution posts surface within their institution's items; de-dup; "new posts" pill (seen-state via `interaction_signals`).
- Endpoint: `GET /feed?cursor=…&rank=recent|relevant` → `{items, next_cursor}` (cursor paginated, `50` §5).

---

## 5. Recommendations (`63` L3 + `ai/event_recommender.py`)

- "Programs like this" (embedding similarity), "students with your goals applied to…" (collaborative filtering, `matching.py`), "scholarships you may qualify for" (eligibility match on `scholarships` `60` §5.1 + `net_price_service`).
- **Explainable** (`07` §2): each rec carries a one-line `why` (cited signal) — Qwen synthesizes the data, the *student-facing* phrasing on a rec card is short factual text (a full conversational "why" is Claude, `63` §3).
- **Fairness-gated** (`46` §6): recs never encode protected-class proxies; the `fairness_reports` check gates the ranker.

---

## 6. Saved searches + alerts (NEW — build)

- **New table `saved_searches`:** `id, user_id, name, query{json}(filters+q), entity_type(program|scholarship|school), alert_enabled, last_run_at, created_at`. Migration + model + `services/saved_search_service.py`.
- Any filter/search set is saveable (named) from `10`/Match UI.
- **Alert loop:** a scheduled job (`55` §4 / `core/scheduler.py`) re-runs each `alert_enabled` saved search against the (crawler-freshened) index; new matches / new scholarship / price-or-deadline change → emit a `change_event`-style alert through `57` (in-app + digest), **consent-gated** (`46`) + per-user caps (§ below). This is the proactive payoff pairing with `60` §3B.
- Endpoints: `GET/POST /me/saved-searches`, `PATCH /me/saved-searches/{id}` (toggle alert), `DELETE`.
- **Caps:** max alerts/user/day (config `alert_cap_per_day`); batch low-urgency into the `57` digest.

---

## 7. Relevance experimentation (`62` harness)

- Ranking variants (feed weights, search fusion params, rec models) A/B-tested via `62`'s `ab_test_assignments`; measure click/save/apply lift; promote on win. Variants behind a config so no redeploy to flip.

---

## 8. Build tasks (checklist)

- [ ] Confirm/extend `search_service.py` to FTS+trgm with facet aggregates + GIN indexes.
- [ ] Hybrid fusion (pgvector + keyword RRF) + `reranker.py` → Qwen3-Reranker wiring.
- [ ] `query_interpreter` (Qwen) → chips, with `query_parser` rule-based fallback.
- [ ] Formalize `connect_ranker` blended score + config weights; cursor feed endpoint.
- [ ] Rec endpoints with explainable `why` + fairness gate.
- [ ] `saved_searches` table/model/service + alert job + endpoints + caps.
- [ ] A/B hooks for ranking variants via `62`.

---

## 9. Acceptance

- [ ] Search returns hybrid (keyword+semantic) results with typeahead (`53`) + faceted live counts; state in URL.
- [ ] Feed ranked, infinite-scroll, optimistic react/RSVP, "new posts" pill, seen-state.
- [ ] Recs explainable + fairness-gated (`46`).
- [ ] Saved searches fire alerts via `57`, consent + cap respected.
- [ ] Ranking changes A/B-gated via `62`; no redeploy to flip a variant.

---

## 10. Open questions

- OpenSearch trigger threshold (program count / query volume) — stay on Postgres until measured need.
- Cold-start recs (sparse new profile) — fall back to popularity + stated intent (`42` intent signals).
- Does `search_service.py` already compute facet counts? — verify before building; extend if not.
