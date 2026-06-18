# Profile refinement v2 — demographics, tab restructure, Enrich-with-Uni (design)

**Date:** 2026-06-18 · **Status:** Approved by founder (design + mockup approved) · **Scope:** two ships

Founder direction: Basic info should be a comprehensive demographic surface (like other apps — currently missing fields); rename Identity → Personality; merge Academics + Experience into one tab and fix its UI; drop the Analytics tab; and every non-Basic-info tab gets an "Enrich with Uni" surface (guided question cards + a talk-to-Uni escape) that helps the chatbot update the profile, per the AI-Structure Spec 1 enrichment loop. Verify with a mock user.

## Ship 1 — Profile structure (frontend-mostly)

### 1.1 Basic info → Demographics (Common-App level)
All target columns already exist on `StudentProfile` AND in `StudentProfileResponse` / the update schema (`preferred_name`, `legal_sex`, `place_of_birth`, `nationality`, `passport_issuing_country`, `country_of_residence`, `secondary_phone`, `addresses`) — so this is **frontend-only**. Reorganize `BasicInfoForm` (`components/ProfileForms.tsx`) + `OverviewTab` into grouped sections in the wide centered grid:
- **Identity:** first_name · last_name · preferred_name · gender_identity (Select + existing 90-day lock) · legal_sex (Select: Female / Male / Intersex / Prefer not to say) · date_of_birth · preferred_pronouns
- **Citizenship & origin:** nationality (label "Citizenship / nationality") · place_of_birth ("Place of birth") · passport_issuing_country ("Passport issuing country") · country_of_residence
- **Contact:** secondary_phone ("Phone") · mailing address → `addresses.current` `{line1, city, state, postal_code, country}`. The form MUST read existing `addresses`, update only `.current`, and send the merged dict back (PUT replaces the whole JSONB — never wipe `permanent`/`billing`).
- **About you:** bio_text. **Drop the Goals box** (it lives in Planning › Goals; do not send `goals_text`, leaving the stored value untouched).
Group headers are small density `SectionHeader`s. Gender lock UI unchanged.

### 1.2 Identity → "Personality"
Rename the visible label only — `ProfilePage` TABS `identity` label → "Personality", the My Space rail child label → "Personality", and the IdentityTab heading copy if it says "Identity". Keep the route key `identity` (stable; add a `personality` → `identity` alias in `PROFILE_TAB_ALIASES`). Content (Who you are · Core values · Worldview · Self-awareness) unchanged.

### 1.3 Academics + Experience → one tab "Academics & experience"
Merge `AcademicsTab` + `ExperienceTab` into a single tab rendered under the `academics` key (alias `experience` → `academics`). Sections in order: Institutions & GPA · Courses · Test scores · Activities · Work & service · Competitions · Portfolio · Online presence. **UI fix:** the current `profile/shared` `SectionHeader` renders an oversized `text-h3` and `ExperienceTab` uses `space-y-10` — switch the merged tab to the dense density `SectionHeader` (small utilitarian header) with `space-y-6/8` rhythm and consistent compact cards; warm one-line empty states. Rail: one item "Academics & experience"; ProfilePage TABS collapses the two into one.

### 1.4 Drop Analytics
Remove `analytics` from `ProfilePage` TABS + `PROFILE_TABS_SPEC` + the rail; delete `AnalyticsTab.tsx`; `analytics` → redirect to the record tab via `PROFILE_TAB_ALIASES`. Backend analytics endpoints untouched.

**Resulting Profile tabs:** Basic info · Personality · Academics & experience. (Planning cluster — Strategy/Goals/Needs/Preferences — unchanged.)

## Ship 2 — Enrich with Uni (full-stack)
A reusable **`EnrichPanel`** at the top of each non-Basic-info tab (Personality · Academics & experience · Goals · Needs · Preferences · Strategy): the existing `EnrichWidget` guided cards **scoped to that section** + a **"Talk to Uni"** link that opens Uni focused on the section (reuses the `/s?prefill=…` opener path; one prefill per section).
- **Backend:** add an optional `section` filter to the enrich planner + `GET /me/enrichment/next?section=…` and `EnrichmentService.next_signals(section=…)`. Map each tab → its Spec-1 field group (Personality→identity; Academics&experience→gpa/test scores/activities/work/languages/field; Goals→goals; Needs→needs; Preferences→weights/budget/funding/preferred countries; Strategy→target degree/field). The implementer maps to the planner's ACTUAL field keys (read `enrichment_planner`/the field catalog first). When `section` is absent, behavior is unchanged (global next).
- **Frontend:** `getEnrichNext(section?)` passes the param; `EnrichPanel` wraps `EnrichWidget` (passing the section) + the Talk-to-Uni link; render it at the top of each tab. Cards write via the existing stamped `setEnrichValue`; on submit, invalidate the tab's queries so the section reflects the new value. Panel hides when the section has no pending signals.

## Verification (mock user) — both ships
Seed a mock student via the local auth-preview recipe; drive each surface:
- Demographics: every new field saves + round-trips; address merge preserves other address keys; gender lock still holds.
- Personality label shows; `?tab=identity` and `?tab=personality` both resolve.
- Academics & experience: all sections render, CRUD works, headers are dense; `?tab=experience` redirects.
- Analytics tab gone; `?tab=analytics` redirects.
- Each tab's EnrichPanel surfaces THAT section's next signal; submitting a card updates the profile; Talk-to-Uni opens Uni with the section prefill. (The Uni conversation itself runs on the live managed agent; verify the wiring + the deterministic structured-enrich path end-to-end.)

## Out of scope
No change to the match engine, the Uni agent persona, or the analytics backend. No new demographic columns (all exist). The enrichment write/confidence model is reused as-is.

## Verification gate (each ship)
tsc 0 · vite build 0 · eslint 0 errors · vitest green · backend ruff + tests (Ship 2) · single alembic head if a migration is added (none expected) · ship via `/ship` and confirm live.
