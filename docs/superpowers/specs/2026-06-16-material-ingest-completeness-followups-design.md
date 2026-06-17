# Material Ingest — Complete Extraction + Uni Follow-up Questions

**Date:** 2026-06-16
**Status:** Design (approved in brainstorm; pending spec review)
**Builds on:** the shipped material-ingest v1 (#624 backend, #625 frontend) — upload a file → Claude reads it → review → confirm into My Space.

## Problem

A real resume import (`Leo Resume_1224.pdf`) revealed two failures:

1. **Incomplete + incorrect extraction.** The v1 schema only covered profile basics, education, test scores, activities, work, goals, needs, identity. It dropped **skills, languages, interests, preferred name, contact (email/phone/links), honors/scholarships, relevant coursework, and the achievement bullets**, and it **mis-mapped activities** (three clubs all became "Member" because the agent put the *role* in the `title`).
2. **No way to fill what a resume can't say.** A resume omits GPA, test scores, intended program, and any *why* — the admissions-critical signal. The student should be able to answer a few targeted questions instead of hunting through forms.

## Goal

**Uni catches every detail in an uploaded file and lands each one in the correct profile field — and then asks targeted follow-up questions to fill what the file couldn't say.** Review-and-confirm stays: nothing is written until the student approves.

### Acceptance bar (the "correctly" guarantee)

A live re-run against `Leo Resume_1224.pdf` must land **every** item below in the named field. This is the headline acceptance test.

## Part A — Complete, correct extraction

### Exhaustive coverage map (resume element → agent field → My Space target)

| Resume element | Agent schema field | Target entity / field | Writer |
|---|---|---|---|
| "Juncheng (Leo) Zhu" | `profile.first_name`, `.last_name`, `.preferred_name` | `StudentProfile` | `update_profile` |
| `junczhu@bu.edu` | `profile.email` | `StudentProfile.secondary_email` | `update_profile` |
| `617-992-0511` | `profile.phone` | `StudentProfile.secondary_phone` | `update_profile` |
| LinkedIn, Tableau URLs | `online_presence[]` `{platform_type, url, display_name}` | `StudentOnlinePresence` | `create_online_presence` |
| 2 schools | `academic_records[]` `{institution_name, degree_type, field_of_study, gpa, gpa_scale, honors, start_date, end_date, is_current}` | `AcademicRecord` | `create_academic_record` |
| Concentration "Business Analytics & Marketing" | `academic_records[].field_of_study` | `AcademicRecord.field_of_study` | ″ |
| "Hup Fong Scholarship", "Dean's List Fall 2023" | `academic_records[].honors` | `AcademicRecord.honors` | ″ |
| Relevant courses (per school) | `academic_records[].courses[]` `{course_name, subject_area}` | `StudentCourse` (`course_level` derived from degree_type) | `create_course` |
| Clubs (Formula, CSU, ASU) | `activities[]` `{title = club NAME, role, activity_type}` | `Activity` | `create_activity` |
| 3 roles (work + internships) | `work_experiences[]` `{experience_type, organization, role_title, description, key_achievements, start_date, end_date, is_current, organization_city, organization_country}` | `StudentWorkExperience` | `create_work_experience` |
| Languages (Chinese/English/French) | `languages[]` `{language, proficiency_level}` | `StudentLanguage` | `create_language` |
| Skills (Excel, Python, …) | `profile.skills[]` | `StudentProfile.bio_text` (v1 — no skills table yet) | `update_profile` |
| Interests (Motorsports, …) | `profile.interests[]` | `StudentProfile.bio_text` (v1) | `update_profile` |
| Goals/needs/identity | only if explicitly stated; else → follow-ups | as v1 | as v1 |

### Key corrections
- **Activity mapping fix** — `title` is the activity/club *name*; the role ("Member", "President") is a separate optional field. The agent prompt states this explicitly. (Root cause of "Member · Member · Member".)
- **`proficiency_level`** is required on `StudentLanguage` — map "Native"→`native`, "Fluent"→`fluent`, "Conversational"→`conversational` (lenient fallback `other`).
- **`course_level`** is required on `StudentCourse` — derive from the parent record's `degree_type` (`bachelors`/`associate`/`high_school` → `undergraduate`; `masters`/`phd` → `graduate`).
- **Skills/interests** have no structured home yet → folded into `bio_text` as labeled lines in v1; a dedicated skills entity is an explicit out-of-scope follow-up.
- **Apply stays best-effort per item** (one bad item never aborts the rest) and returns the `{counts, skipped}` summary.

## Part B — The follow-up loop ("Uni has a few questions")

### GapEngine (deterministic, source-agnostic)
`detect(profile_snapshot, import_result | None) -> list[Gap]`. Each `Gap` = `{id, category, target_field, prompt_hint, kind, options[]}`. Three categories, ranked in this order, capped at **5**:

1. **Ambiguous** (extracted but thin) — an activity with no role/detail ("What did you do in the Electric Formula Club?"); a work item with a weak description.
2. **Missing high-value** — fields a resume omits that matter for matching: GPA, test scores, intended degree/program, intake term, budget band, target geographies.
3. **Deepen** (seed discovery) — exactly **one** reflective question routed to goals/needs/identity ("What's pulling you toward Business Analytics?"), since resumes don't state motivation.

Source-agnostic by construction: with `import_result=None` it scans the whole profile for gaps — this is the Phase-2 hook (general profile follow-ups, no upload).

### LLM phrasing + parse (Uni's voice)
`ai/follow_up.py` — one small agent (consent-free `workshop_coach` slot, like the ingest agent) does two jobs: (a) phrase each `Gap.prompt_hint` into a warm, first-person one-liner; (b) parse a free-text answer back into the structured `target_field`. On LLM failure → fall back to the deterministic `prompt_hint` and store the raw answer (never a 5xx).

### Inline "Uni has a few questions" card
A new `FollowUpCard` rendered **after "Add to My Space"**, in the same place the import happened (chat and Profile). Each question is answerable by **tap-chips and/or a free-text box**, individually **skippable**, with a small progress count. Answers write to My Space via the same `create_*`/`update_profile` writers. Reuses the existing chip/`AnswerChoices` styling.

## Architecture / files

**Backend**
- `ai/material_ingest.py` — widen `SUBMIT_TOOL` schema (Part A fields), fix the activity-title prompt.
- `services/material_ingest_service.py` — extend `apply` with the new writers (online presence, languages, courses, contact, skills/interests→bio_text); fix activity mapping.
- `services/follow_up_service.py` *(new)* — `GapEngine.detect` + `answer`. **Stateless:** `GET …/followups` generates gaps fresh from (import + current profile); each `Gap` it returns carries its own `target_field`/`kind`/`options`, so the `answer` POST echoes that descriptor + the value and applies it directly — no question-store table.
- `ai/follow_up.py` *(new)* — phrasing + free-text parse.
- `api/materials.py` — `GET /me/materials/{id}/followups`, `POST /me/followups/answer`.
- Flag `ai_material_followups_v2_enabled` (config + ecs.tf).

**Frontend**
- `components/student/MaterialReviewCard.tsx` — render the new sections (skills, languages, links, courses, contact).
- `components/student/FollowUpCard.tsx` *(new)* — the question loop.
- `components/student/MaterialUpload.tsx` — after apply, fetch + show `FollowUpCard`.
- `api/materials.ts` — `getFollowups`, `answerFollowup` + widened `ProposedProfile` type.

## Data flow

upload → parse (widened agent) → review card (all sections) → **Add to My Space** (best-effort writes) → `GET …/followups` (GapEngine on import + profile) → FollowUpCard → per-answer `POST …/answer` (LLM parse → write) → profile complete.

## Error handling
- Parse / apply / follow-up answer all **best-effort, never 5xx** (consistent with v1 + the codebase invariant). LLM phrasing/parse failure → deterministic fallback.
- Flag off → no follow-ups; extraction still works (Part A is independent of the flag).

## Testing
- **Acceptance (headline):** a live (non-mock) re-run against `Leo Resume_1224.pdf` asserting each coverage-map row lands in the right field — clubs by name, 3 languages, both schools' honors + courses, links, preferred name "Leo", skills line in bio.
- Backend units: activity-title fix; new-field apply (online presence / language / course / contact); `GapEngine.detect` categories + ranking + cap; `answer` parse-and-write; best-effort skip.
- Frontend vitest: `FollowUpCard` render / tap-answer / free-text / skip; `MaterialReviewCard` new sections.

## Phasing
- **Phase 1 (this spec):** Part A (complete extraction) + Part B import-triggered follow-ups.
- **Phase 2 (future spec):** general profile-gap follow-ups — reuse `GapEngine.detect(profile, None)` + `FollowUpCard`, surfaced from My Space / readiness. (Builds on the existing Spec-44 clarification scaffold.)

## Out of scope
- A dedicated structured **skills** entity (v1 uses `bio_text`).
- Retaining the raw uploaded file (still parsed in-memory; durable storage is the `documents` feature).
- Phase 2 general follow-ups (separate spec).
