# Comparability & Normalization Standard

How metrics like salary, employment rate, and acceptance rate become **directly comparable across programs** for students viewing the Discovery / Compare / Detail surfaces. Required because raw published data has wildly different time windows, denominators, and source years.

## The problem

| Metric | Published variation we see in NYU alone |
|---|---|
| Median salary | Scorecard: 1yr / 4yr / 5yr / 10yr; Stern Outcomes: total comp at 6mo; school career reports: starting salary at 6mo or 12mo |
| Employment rate | Scorecard: % employed not enrolled at 1yr; Stern: % full-time within 3mo; Wagner: % at 6mo |
| Acceptance rate | Scorecard: institution-wide; some Stern departments publish program-specific |
| Cost | Scorecard: per-year COA; bulletin: per-credit; some publish 4-year totals |
| Outcome year | Stern 2024 report = Class of 2024; Tisch report = 2022; Wagner = 2023 |

If we render those side-by-side without normalization, students compare apples and oranges. The platform commits to comparable display.

## Schema rule: every numeric metric carries its provenance

Anywhere `outcomes_data`, `cost_data`, or `school_outcomes` holds a numeric metric, the value must be wrapped in an object:

```json
{
  "value": 137804,
  "unit": "USD/yr",
  "window_months": 48,
  "denominator": "graduates with reported salary",
  "denominator_count": 395,
  "source": "College Scorecard",
  "source_url": "https://collegescorecard.ed.gov/...",
  "source_year": 2024,
  "computed_at": "2026-04-19"
}
```

For backward compatibility we accept the bare scalar AND a parallel `<key>_meta` dict with the same fields, OR the wrapped form. New ingest scripts emit the wrapped form. UI prefers wrapped; falls back to scalar with a "(unverified window)" badge if not wrapped.

## Canonical projections (what we display)

| Display metric | Canonical window | How we derive it |
|---|---|---|
| **Median starting salary** | 12 months post-grad, USD | If source is 6mo: project up using BLS national wage-growth curve for the CIP. If 4yr/5yr/10yr: project DOWN using the same curve to the 12mo equivalent. Always show both raw and projected with the basis label. |
| **Employment rate** | 6 months post-grad | If source is 3mo: report as ≤ rate (lower bound). If 12mo: project down using NACE freshly-graduated stabilization curve (typical 12mo - 3pts ≈ 6mo). |
| **Acceptance rate (program)** | Most recent reported cycle | No projection. Show source year explicitly. Distinguish: program-specific vs school-within-university vs institution-wide using a tier badge (program / school / university). |
| **Cost** | Per academic year | Convert per-credit to per-year using program credit count (when known) and standard 30 cr/year. Show 4-year total separately. |
| **Outcome year** | Most recent published | Always show the year as a chip on the metric (e.g. `$84K · Class of 2024`). |

## Reference bands (peer comparison)

For every program with a CIP code we compute three percentiles from College Scorecard's national distribution at the same CIP × degree level:

```json
"peer_band": {
  "cip_4digit": "52.0301",
  "cip_title": "Accounting",
  "degree_level": "bachelors",
  "p25_earnings_12mo_usd": 51000,
  "p50_earnings_12mo_usd": 60000,
  "p75_earnings_12mo_usd": 78000,
  "n_programs_in_band": 832,
  "source": "College Scorecard 2024",
  "computed_at": "2026-04-19"
}
```

UI then renders: `$137,804 · vs national CS Accounting peers $60K (p50)` with a delta indicator. This makes "is NYU Accounting good for the field?" answerable on the card itself.

## Honest empty-state rule (carries over from `INSTITUTION_DATA_STANDARD.md`)

When we cannot project a metric to the canonical window (source data is too old, missing methodology, or otherwise non-projectable), the metric:

1. is NOT displayed in the canonical-window slot
2. IS displayed in a "Raw published values" section under the metric, with the source year and source link
3. carries a small "(not normalized)" tag

We never invent a value to fill the canonical slot.

## Implementation plan

Three new pieces, all stable API surfaces:

1. **`unipaith-backend/src/unipaith/services/normalization_service.py` (NEW).**
   - `normalize_outcomes(outcomes_data, cip_code) → outcomes_canonical`
   - `compute_peer_band(cip, degree_level) → PeerBand`
   - Loaded at request time on `/programs/{id}` (cached per CIP for 1 day).

2. **`scripts/build_peer_bands.py` (NEW).**
   - One-shot Scorecard pull across all CIP × degree-level combos.
   - Writes `data/peer_bands.json` (committed to repo).
   - Re-run yearly when Scorecard updates.

3. **Frontend changes (`SchoolDetailPage.tsx`):**
   - Outcomes / Costs cards use the wrapped form when present.
   - Peer-band chip rendered next to each metric where `peer_band` is set.
   - Empty-state renders "Raw published values" section when normalization failed.

## Migration path for existing rows

Existing rows with bare scalars stay valid (backward compatibility). The normalization service treats a bare scalar as `{value, source: "unknown", source_year: null, window_months: null}` and refuses to project. The UI shows the value with a "(unverified window)" badge so we can see at a glance which rows still need re-ingesting.

The next pass of the enrichment scripts emits wrapped form by default.

## Out of scope (for this doc)

- Multi-language currency conversion (USD assumed today).
- Inflation-adjusted earnings across years (defer until 5+ year time series).
- Cost-of-living adjustment per metro area (separate "cost-of-living" overlay, deferred).

These are tracked as future enhancements; they don't block the normalization layer landing.
