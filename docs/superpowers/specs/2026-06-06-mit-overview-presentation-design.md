# MIT Overview — Niche-Style Presentation Redesign (Round 2)

- **Date:** 2026-06-06
- **Status:** Approved design → implementation plan next
- **Surface:** `InstitutionDetail.tsx` → `OverviewTab` (student + public institution detail page)
- **Scope:** Frontend-only presentation refinement. **No data, no schema, no API change** — all data was populated in round 1 (`unipaith/data/mit_profile.py`).

## 1. Context

Round 1 made MIT's data complete and real. Round 2 fixes how the Overview *reads*: today it's a long, monotonous stack of "Card + grid of `Fact` tiles," with duplication and numbers lacking context/visualization. Model the treatment on how Niche presents a college profile, for a mostly student/parent audience (also professionals).

### Current Overview inventory (as built) + issues
| Section (line) | Today | Problem |
|---|---|---|
| Key stats (550) | 4 cards: acceptance · net price · earnings · grad rate | fine — keep |
| Rankings (582) | plain text list "#1 QS World University Rankings · 2025" | flat, unremarkable |
| Distinction (597) | Nobel/MacArthur/**Total enrollment** + funnel **sentence** | mixes accolades with enrollment; funnel buried |
| Quick facts (618) | Type · Setting · **Size "Medium"** · Founded · Undergrads · Schools · Programs | duplicates acceptance(below)/founded(hero); "Medium" vague |
| Admissions (654) | **Acceptance rate (dup)** · SAT · ACT · retention | acceptance duplicated; no funnel |
| First destination (670) | single "Placement 94%" | one bare number; `top_employer_industries` data unused |
| Financial aid (679) | Pell% · loan% · debt (bare) | no net price; no visualization |
| Student body (691) | race % grid (bare) | no visual; no size/gender framing |

## 2. Goals / Non-goals
**Goals:** recompose the Overview into a Niche-style narrative with purpose-built visual primitives; dedupe; surface data we already store but don't show (`top_employer_industries`, Carnegie classification, grad-student count).
**Non-goals:** no data/schema/API change; no hero change (round 1); no other tabs (About/Schools/Programs); **no file split** of `InstitutionDetail.tsx` (concurrent branches are in this file — minimize conflict surface).

## 3. Design

### New section order (narrative)
Key stats → **Rankings** → **Admissions** (incl. funnel) → **Cost & Aid** → **Outcomes ("After MIT")** → **Student body** → **Quick facts** → **Recognition** → Location → Sources.

### Section redesigns
1. **Rankings** → `RankingBadge` rows: ribbon icon + large rank + body & year, 3 across. **#1 = the one earned gold beat** (gold ring/fill); others cobalt-neutral.
2. **Distinction → split:**
   - **Admissions funnel** moves into Admissions: `AdmissionsFunnel` 3-step strip — **29,281 applied → 1,334 admitted → 4.5%** (labeled with `flagship.admissions_cycle`).
   - **Recognition** card keeps the accolades with context: `106 Nobel laureates` · `85 MacArthur Fellows` (subtitle "among faculty & alumni"). Total enrollment removed (moves to Student body).
3. **Quick facts** → dedupe (drop acceptance — it's a key card + funnel; keep founded once here) + enrich: **Carnegie classification**, ownership ("Private, nonprofit" via `ownershipLabel`), accreditor, urban setting; replace size-band "Medium" with the real total. One canonical reference block.
4. **Outcomes ("After MIT")** (was First destination) → `94% employed or continuing ed` + `$143K median earnings (10 yrs)` + **top industries as a `ChipList`** (Technology · Finance · Consulting · Research).
5. **Cost & Aid** (was Financial aid) → lead stat **avg net price $20,111** ("what families pay after aid"); `StatBar` for **Pell 19%** + **federal loans 7%**; **median debt $14,768**.
6. **Student body** → `DiversityBar` (segmented horizontal bar + legend, restrained dark-safe palette) for race/ethnicity; **Women 48%**; size split computed from real data: **Undergraduate 4,535 · Graduate 7,281 (= total − undergrad) · Total 11,816**.

### New primitives (small, in-file, near existing helpers — reused by every school page)
- `RankingBadge({ rank, label, year, peak })` — ribbon medallion; `peak` → gold beat.
- `AdmissionsFunnel({ applicants, admits, rate, cycle })` — 3-step strip with connectors.
- `DiversityBar({ segments })` — segmented bar + legend; segments `{label, pct}`.
- `StatBar({ label, pct, hint? })` — labeled horizontal progress bar.
- `ChipList({ items })` — small rounded tags.
Reuse existing `Card`, `Fact`, `money`, `pct`, `rankingLabel`, `ownershipLabel`.

### System constraints (honor existing rules)
Cream/editorial; **semantic tokens only** (dark-mode safe — no raw charcoal/cobalt/gold literals; use `--secondary`, `--foreground`, `--muted`, `--scrim`); **gold strictly the single earned peak** (#1 ranking) per the design system; cobalt for interactive; content width unchanged (`max-w-5xl`). `DiversityBar` palette uses restrained steps (secondary at descending opacity + muted), not a rainbow.

## 4. Data mapping (all keys already live — verified)
`ranking_data.{qs_world_university_rankings,times_higher_education,us_news_national}` · `school_outcomes.flagship.{applicants,admits,admissions_cycle,nobel_laureates,macarthur_fellows,enrollment_total}` · `school_outcomes.{admit_rate,avg_net_price,median_earnings_10yr,employed_or_continuing_ed,top_employer_industries,financial_aid.*,demographics.*,test_scores.*,retention_rate_first_year}` · `ranking_data.{carnegie_classification,ownership_type,accreditor}` · `student_body_size` (undergrad). Grad = `enrollment_total − student_body_size`. **No new data.**

## 5. Testing
vitest on `InstitutionDetail.test.tsx`: `RankingBadge` marks the #1 as the peak; `AdmissionsFunnel` shows applied/admitted/rate; `DiversityBar` renders a segment per ethnicity; `ChipList` shows industries; **dedupe assertion** — acceptance rate appears once outside the key-stat cards (in the funnel), not as a separate bare Fact. Keep existing Overview tests green.

## 6. Conflicts & rollout
Concurrent branches (`claude/mit-depth-8bf9e6`, `depth-satact`, `discover-uni-redesign`) also touch this file — fetch+merge `origin/main` before push, reconcile keep-both, never force-push. Then ship per the standing rule (tsc/build/tests green → merge `main` → deploy → **verify live + screenshot** app.unipaith.co).
