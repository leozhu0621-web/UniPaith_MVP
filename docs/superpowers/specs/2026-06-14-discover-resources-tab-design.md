# Discover "Resources" tab — Universities · Financial · International

**Date:** 2026-06-14
**Status:** Approved (user-selected forks: search lives under Universities; Financial = authored aid guide; International = authored guide + personalized readiness blend)
**Supersedes:** the unmerged "Browse" tab (PR #816) — this evolves that branch (`claude/discover-browse-tab`); the Browse tab is relabeled Resources and gains sub-tabs.

## Decision

The overloaded "For you" tab already had its program search split out (PR #816). That
split tab is now relabeled **Resources** and given three sub-tabs. The Discover hub tabs
become: **For you · Resources · Updates · Events · Peers**.

`Resources` carries a sub-tab bar driven by a `sub` URL param
(`?tab=resources&sub=universities|financial|international`, default `universities`):

### Sub-tab 1 — Universities (all real data)

The program **search** (search box + outcome/subject tiles + program results, the existing
`DiscoverySearch`) **and** the universities browse grid — i.e. exactly the content the
Browse tab held in #816, now under this sub-tab. Renders inline in `ExplorePage` (it already
owns the search/filter/universities state). Default sub-tab.

### Sub-tab 2 — Financial (authored aid guide)

A general, accurate **reference guide** to how college financial aid works — not
personalized, no invented numbers/deadlines. New component `ResourcesFinancial.tsx` driven
by an authored content array `resources/aidGuide.ts`. Sections:

- **Need-based aid** — FAFSA (federal, US citizens / eligible non-citizens) and the CSS
  Profile (institutional); what they assess (SAI).
- **Merit & external scholarships** — institutional merit awards vs. outside scholarships;
  where to look; that they're competitive and deadline-driven.
- **Grants** — federal (e.g. Pell) and state grants; gift aid vs. loans.
- **Loans** — federal subsidized/unsubsidized vs. private (cosigner often required); borrow
  conservatively.
- **Work-study & assistantships** — on-campus work; for grad study, TA/RA funding.
- **International caveat** — most US federal aid is NOT available to non-citizens; rely on
  institutional aid + external scholarships + (cosigned) private loans. Links to the
  International sub-tab.

Honesty: every section is conceptual; a standing note reads "General guidance — confirm
exact amounts, eligibility, and deadlines with each school." A CTA links to the student's
real cost comparison (`FinancialAidPage`, `/s/applications?tab=costs` or its route) — that
surface holds the actual per-program numbers. No scholarships matching engine is claimed
(none exists).

### Sub-tab 3 — International (blend: guide + personalized readiness)

New component `ResourcesInternational.tsx` = an authored guide + a personalized panel.

**Authored guide** (`resources/intlGuide.ts`): F-1 vs J-1 visas; I-20 / DS-2019 & the SEVIS
fee; the visa interview; maintaining status (full course load, work limits); work
authorization (CPT / OPT / STEM OPT); English-proficiency tests (TOEFL / IELTS / Duolingo)
and common waivers; proof of finances. Conceptual + "confirm current rules with the school's
international office and official sources" note.

**Personalized "Your readiness" panel** — reads ONLY real fields:
- `getVisaInfo()` → `StudentVisaInfo`: `current_immigration_status`, `visa_required`,
  `target_study_country`, `passport_expiration_date`, `financial_proof_available`,
  `work_authorization_needed`.
- `listTestScores()` → an English test (TOEFL / IELTS / DUOLINGO) score if present.
- Render a compact checklist: each known field shown as a ✓ row; each MISSING field shown as
  a muted "Add in Profile →" prompt deep-linking to the relevant Profile tab. NEVER a guessed
  value. If the student isn't international (`visa_required` false / status indicates citizen),
  the panel collapses to a one-line "Not applicable — you don't need a study visa for your
  target country" with the guide still available.

## Architecture / files

```
pages/student/explore/resources/
  ResourcesTabBar.tsx        # the 3 sub-tabs (ARIA tablist, ?sub= param), reused pattern
  ResourcesFinancial.tsx     # renders aidGuide sections + cost-comparison CTA
  ResourcesInternational.tsx # renders intlGuide sections + ReadinessPanel
  ReadinessPanel.tsx         # personalized checklist from getVisaInfo + listTestScores
  aidGuide.ts                # authored financial content (typed section array)
  intlGuide.ts               # authored international content (typed section array)
  GuideSections.tsx          # shared presentational renderer for a section array
ExplorePage.tsx              # Resources panel = ResourcesTabBar + switch(sub):
                             #   universities → existing DiscoverySearch + universities (inline)
                             #   financial → <ResourcesFinancial/>
                             #   international → <ResourcesInternational/>
explore/DiscoverTabBar.tsx   # 'browse' → 'resources' (label "Resources", icon BookOpen/LibraryBig)
```

The authored guides live in typed content arrays (`{ id, heading, body, bullets? }[]`) so the
components are pure renderers and the content is reviewable in one place. `GuideSections`
renders a section array as accessible cards (a shared sub-component, used by both guides).

## URL / IA

- Top tab: `browse` is renamed to `resources` in `DiscoverTab` / `DISCOVER_TABS` /
  `TAB_HEADERS` / the saved-search default (a chips/filters deep-link opens
  `resources&sub=universities`).
- Sub-tab: `sub` param read in `ExplorePage`; `setSub` writes it (replace). Unknown/absent →
  `universities`. Switching the top tab away clears `sub` + the program-search params.
- `/s/explore?tab=browse` (any old links) → resolve `browse`→`resources` in the tab parser
  so the rename never dead-ends.

## Testing

- `aidGuide` / `intlGuide`: non-empty, every section has a heading + body (pure data test).
- `ReadinessPanel`: renders a ✓ row for a present field and an "Add in Profile" prompt for a
  missing one; collapses for a non-international student (mock `getVisaInfo`/`listTestScores`).
- `ResourcesTabBar`: renders the 3 sub-tabs; `sub` defaults to universities; switching fires
  the change.
- `DiscoverTabBar`: the second tab is now "Resources" (update the #816 Browse test);
  `DISCOVER_TABS` contains `resources` not `browse`.
- ExplorePage smoke: `?tab=resources&sub=financial` renders the aid guide; `sub=international`
  renders the guide + readiness; `sub=universities` renders the search.
- tsc 0 · build 0 · full vitest green; ship + verify live (markers: "Resources", the guide
  headings, "Your readiness").

## Honesty guardrails (restated)

- Financial + the International guide are **authored general knowledge** with explicit
  "confirm with the school / official sources" notes — a help center, not personalized claims.
  No dollar amounts, no school-specific deadlines, no fabricated eligibility.
- The readiness panel surfaces **only** real `StudentVisaInfo` + test-score fields; missing →
  prompt, never a guess.

## Out of scope (backlog)

- Per-program English-policy match in the readiness panel ("3 of your saved programs accept
  your IELTS") — needs fetching saved programs' `english_policy`; a follow-up.
- A scholarships matching engine / table (doesn't exist).
- Localizing the guides beyond US-centric + international caveat.
