# 56 · Search, Feed & Recommendations

> The discovery substrate: full-text + semantic search, faceted filters, the ranked Connect feed, recommendations, and saved-search alerts. Powered by the `63` Qwen embeddings + classical ranking on the `55` substrate.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Pairs with `09`/`10` (Match/Discover UI), `20` (Connect feed), `60` (crawled knowledge it searches), `63` (embeddings/rerank), `57` (alert delivery).

---

## 1. Search architecture (staged)

- **Phase A — Postgres**: FTS (`tsvector`) + `pg_trgm` fuzzy for programs/schools/scholarships. Cheap, no new infra.
- **Phase B — hybrid semantic**: pgvector ANN over Qwen embeddings (`63`) **fused with** keyword (reciprocal-rank fusion) → semantic recall + exact precision.
- **Phase C — OpenSearch** if scale/faceting demands it; same hybrid model.
- Query interpretation: `DiscoveryQueryInterpreter` (`45`, Qwen-served per `63`) turns NL → structured filters + constraint chips (`10`).

## 2. Faceted filters

- Facets: degree type, modality, location, cost band, deadline window, test policy, field/CIP, selectivity.
- **Live counts** update as facets toggle (Handshake bar, `53`); filters in URL (`05` §13).
- Server computes facet aggregates alongside results.

## 3. Connect feed ranking (`20`)

- Sources: posts/events/deadline reminders/program-changes from followed institutions (`20`) + crawler `change_events` (`60` §3B).
- **Ranking signal blend**: recency + relevance (to saved/applied/followed + profile embedding) + materiality (`60`) + engagement. Default reverse-chron with a "most relevant" toggle (`20` §4.2).
- Pinned institution posts surface within their items.
- De-dup + "new posts" pill + seen-state.

## 4. Recommendations

- "Programs like this", "students with your goals applied to…", "scholarships you may qualify for" — collaborative-filtering + embedding similarity (`63` L3).
- Always explainable (`07` §2): a one-line "why" on each rec.
- Fairness-gated (`46` §6) — recs never encode protected-class proxies.

## 5. Saved searches + alerts

- Any filter/search set is saveable (named).
- New matches (new program fits filters, new scholarship matches, price/deadline change) → alert via `57` (in-app + digest), consent-gated, per-user caps.
- The proactive payoff that pairs with the crawler's `change_events` (`60` §3B).

## 6. Relevance experimentation

- Ranking variants A/B-tested via the eval/experiment harness (`62` `ab_test_assignments`); measure click/save/apply lift; promote on win.

## 7. Acceptance

- [ ] Search returns keyword + semantic results (hybrid) with typeahead (`53`).
- [ ] Facets with live counts; state in URL.
- [ ] Feed ranked, infinite-scroll, optimistic, "new posts" pill, seen-state.
- [ ] Recs are explainable + fairness-gated.
- [ ] Saved searches fire alerts via `57`, consent + cap respected.
- [ ] Ranking changes A/B-gated.

## 8. Open questions

- OpenSearch trigger threshold (program count / query volume) — stay on Postgres until measured need.
- Cold-start recs (new student, sparse profile) — fall back to popularity + stated intent.
