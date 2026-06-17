# Material Ingest — Complete Extraction + Follow-up Questions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the file-import read every detail of a resume into the correct My Space field, then have Uni ask targeted follow-up questions to fill what the file can't say.

**Architecture:** Widen the existing `MaterialIngestAgent` tool schema + `MaterialIngestService.apply` (Part A); add a deterministic source-agnostic `GapEngine` + a small follow-up LLM agent + an inline `FollowUpCard` (Part B). All flag-gated, best-effort, never 5xx. Builds on shipped v1 (#624/#625).

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy async / anthropic SDK (native PDF+image) ; React 19 / TS / Vite / TanStack Query.

**Spec:** `docs/superpowers/specs/2026-06-16-material-ingest-completeness-followups-design.md`.

**Backend test cmd:** `cd unipaith-backend && DATABASE_URL="postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith" PYTHONPATH=src AI_MOCK_MODE=true COGNITO_BYPASS=true S3_LOCAL_MODE=true .venv/bin/pytest <file> -v --tb=short` <!-- pragma: allowlist secret -->  (local dev DB creds)

**Verified surfaces (use exactly):**
- `StudentService.create_online_presence(student_id, data: CreateOnlinePresenceRequest)` — `platform_type` ∈ `linkedin|github|personal_site|portfolio|wechat|twitter|other`, `url`, `display_name?`.
- `StudentService.create_language(student_id, data: CreateLanguageRequest)` — `language`, `proficiency_level` ∈ `native|fluent|advanced|intermediate|beginner`.
- `StudentService.create_course(student_id, record_id, data: CreateCourseRequest)` — `course_name`, `course_level` ∈ `regular|honors|AP|IB|college`, `subject_area?`. **University coursework → `course_level="college"`.**
- `create_academic_record` returns the record (has `.id`) → pass to `create_course`.
- `StudentProfile` writable via `update_profile(user_id, UpdateProfileRequest)`: `preferred_name`, `secondary_email`, `secondary_phone`, `bio_text`, `country_of_residence`, `first_name`, `last_name`.
- Mappings: proficiency "conversational"→`intermediate`; Tableau/portfolio link→`portfolio`, LinkedIn→`linkedin`, else `other`.

---

## Part A — Complete, correct extraction

### Task 1: Widen the agent tool schema + fix the activity prompt

**Files:**
- Modify: `unipaith-backend/src/unipaith/ai/material_ingest.py` (`SUBMIT_TOOL`, `_SYSTEM`)
- Test: `unipaith-backend/tests/test_material_ingest.py`

- [ ] **Step 1: Add a schema-shape test**

```python
def test_submit_tool_has_complete_coverage():
    from unipaith.ai.material_ingest import SUBMIT_TOOL
    props = SUBMIT_TOOL["input_schema"]["properties"]
    for key in ["profile", "academic_records", "test_scores", "activities",
                "work_experiences", "languages", "online_presence", "goals", "needs", "identity"]:
        assert key in props, key
    assert "preferred_name" in props["profile"]["properties"]
    assert "email" in props["profile"]["properties"]
    assert "skills" in props["profile"]["properties"]
    assert "interests" in props["profile"]["properties"]
    # activity carries a name + optional role (not role-as-title)
    act = props["activities"]["items"]["properties"]
    assert "role" in act and "title" in act
    # academic record carries courses
    assert "courses" in props["academic_records"]["items"]["properties"]
    # languages present
    assert "language" in props["languages"]["items"]["properties"]
```

- [ ] **Step 2: Run → fail** (`-k test_submit_tool_has_complete_coverage`) — KeyError/assert.

- [ ] **Step 3: Widen `SUBMIT_TOOL`**

In `profile.properties` add: `preferred_name {string}`, `email {string}`, `phone {string}`, `skills {array[string]}`, `interests {array[string]}` (keep existing first_name/last_name/bio_text/country_of_residence).

Add top-level array `online_presence`:
```python
"online_presence": {
    "type": "array",
    "items": {"type": "object", "properties": {
        "platform_type": {"type": "string", "enum": ["linkedin","github","personal_site","portfolio","wechat","twitter","other"]},
        "url": {"type": "string"},
        "display_name": {"type": "string"},
    }, "required": ["platform_type", "url"]},
},
"languages": {
    "type": "array",
    "items": {"type": "object", "properties": {
        "language": {"type": "string"},
        "proficiency_level": {"type": "string", "enum": ["native","fluent","advanced","intermediate","beginner"]},
    }, "required": ["language"]},
},
```

In `academic_records.items.properties` add `courses`:
```python
"courses": {"type": "array", "items": {"type": "object", "properties": {
    "course_name": {"type": "string"}, "subject_area": {"type": "string"},
}, "required": ["course_name"]}},
```

In `activities.items.properties`: keep `title` but **redefine its description** to "the activity/club NAME (e.g. 'Electric Formula Club') — NOT the role"; add `"role": {"type": "string", "description": "the student's role, e.g. Member, President"}`.

In `work_experiences.items.properties` add `key_achievements {string}`, `organization_city {string}`, `organization_country {string}`.

Update `_SYSTEM`: append "For an activity/club, `title` is the club's name and `role` is the position (Member/President). Capture relevant coursework under each school's `courses`. Capture languages, links (LinkedIn/portfolio), email/phone, preferred name, skills, and interests when present."

- [ ] **Step 4: Run → pass.**
- [ ] **Step 5: Commit** `feat(materials): widen ingest schema (skills/langs/links/courses/contact) + activity-name fix`

### Task 2: Extend `apply` with the new writers (correct enum mappings)

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/material_ingest_service.py`
- Test: `unipaith-backend/tests/test_material_ingest.py`

- [ ] **Step 1: Test the new writers + activity fix**

```python
@pytest.mark.asyncio
async def test_apply_writes_complete_profile(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    svc = MaterialIngestService(db_session)
    row = await svc.ingest(mock_student_user.id, filename="r.pdf", mime_type="application/pdf", data=b"x")
    sel = {
        "profile": {"preferred_name": "Leo", "email": "leo@bu.edu", "phone": "617",
                    "skills": ["Python", "SQL"], "interests": ["Motorsports"]},
        "online_presence": [{"platform_type": "linkedin", "url": "https://linkedin.com/in/x"}],
        "languages": [{"language": "Chinese", "proficiency_level": "native"},
                      {"language": "French", "proficiency_level": "conversational"}],
        "academic_records": [{"institution_name": "Northeastern", "degree_type": "bachelors",
                              "start_date": "2020-09", "end_date": "2024-12",
                              "courses": [{"course_name": "Data Mining for Business"}]}],
        "activities": [{"title": "Electric Formula Club", "role": "Member", "activity_type": "extracurricular"}],
    }
    out = await svc.apply(mock_student_user.id, row.id, sel)
    c = out["counts"]
    assert c.get("online_presence") == 1
    assert c.get("languages") == 2
    assert c.get("courses") == 1
    assert c.get("activities") == 1
    assert c.get("profile_fields", 0) >= 1
    # activity kept the club name, not "Member"
    from unipaith.models.student import Activity, StudentProfile
    from sqlalchemy import select
    sp = (await db_session.execute(select(StudentProfile).where(StudentProfile.user_id == mock_student_user.id))).scalar_one()
    acts = (await db_session.execute(select(Activity).where(Activity.student_id == sp.id))).scalars().all()
    assert any("Formula" in a.title for a in acts)
    # conversational mapped to intermediate
    from unipaith.models.student import StudentLanguage
    langs = (await db_session.execute(select(StudentLanguage).where(StudentLanguage.student_id == sp.id))).scalars().all()
    assert any(l.language == "French" and l.proficiency_level == "intermediate" for l in langs)
```

- [ ] **Step 2: Run → fail.**

- [ ] **Step 3: Implement the writers.** Add helpers + extend `apply` to call them. Key code:

```python
_PROFICIENCY = {"native": "native", "fluent": "fluent", "advanced": "advanced",
                "conversational": "intermediate", "intermediate": "intermediate",
                "basic": "beginner", "beginner": "beginner"}

# in _apply_profile: extend the allowed set + fold skills/interests into bio_text
allowed = {"first_name", "last_name", "preferred_name", "country_of_residence"}
data = {k: v for k, v in profile.items() if k in allowed and v}
if profile.get("email"): data["secondary_email"] = profile["email"]
if profile.get("phone"): data["secondary_phone"] = profile["phone"]
extras = []
if profile.get("skills"): extras.append("Skills: " + ", ".join(profile["skills"]))
if profile.get("interests"): extras.append("Interests: " + ", ".join(profile["interests"]))
if extras: data["bio_text"] = ((profile.get("bio_text") or "") + "\n" + "\n".join(extras)).strip()
```

New `_apply_online_presence(student_id, items, counts, skipped)` → `create_online_presence(student_id, CreateOnlinePresenceRequest(platform_type=..., url=..., display_name=...))` with `platform_type` validated against the enum (fallback `"other"`).

New `_apply_languages(student_id, items, …)` → `create_language(student_id, CreateLanguageRequest(language=…, proficiency_level=_PROFICIENCY.get(str(x.get("proficiency_level","")).lower(), "intermediate")))`.

In `_apply_academics`: after `rec = await svc.create_academic_record(student_id, req)`, loop `r.get("courses")` → `svc.create_course(student_id, rec.id, CreateCourseRequest(course_name=c["course_name"][:255], subject_area=c.get("subject_area"), course_level="college"))`; count under `"courses"`.

In `_apply_activities`: build `title = a.get("title")`; if a `role` is present, store it in the activity description prefix (`description = f"{role}. {description}"` when role present) — the **title is the name**. `activity_type` fallback `"extracurricular"`.

In `_apply_work`: add `key_achievements=w.get("key_achievements")`, `organization_city=w.get("organization_city")`, `organization_country=w.get("organization_country")` to `CreateWorkExperienceRequest`.

Wire all new `_apply_*` into `apply()` alongside the existing calls.

- [ ] **Step 4: Run → pass** (this test + the existing `test_material_ingest.py` suite).
- [ ] **Step 5: Commit** `feat(materials): apply skills/langs/links/courses/contact + activity-name + work detail`

### Task 3: Widen the review card (frontend)

**Files:**
- Modify: `frontend/src/api/materials.ts` (`ProposedProfile`)
- Modify: `frontend/src/components/student/MaterialReviewCard.tsx`
- Test: `frontend/src/test/material-review-card.test.tsx`

- [ ] **Step 1: Test new sections render**

```tsx
it('renders languages, links, and courses sections', () => {
  const proposed = {
    summary: 's',
    languages: [{ language: 'Chinese', proficiency_level: 'native' }],
    online_presence: [{ platform_type: 'linkedin', url: 'https://x' }],
    academic_records: [{ institution_name: 'NEU', degree_type: 'bachelors', courses: [{ course_name: 'Data Mining' }] }],
  }
  render(<MaterialReviewCard proposed={proposed} onConfirm={() => {}} onCancel={() => {}} />)
  expect(screen.getByText('Languages')).toBeInTheDocument()
  expect(screen.getByText('Links')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run → fail.**

- [ ] **Step 3: Implement.** In `materials.ts` add `online_presence?`, `languages?` to `ProposedProfile`. In `MaterialReviewCard.tsx` add to `SECTIONS`: `{ key: 'online_presence', label: 'Links', preview: i => String(i.platform_type ?? '') }`, `{ key: 'languages', label: 'Languages', preview: i => `${i.language} (${i.proficiency_level ?? ''})` }`. Courses ride inside Education (show count of courses in the Education preview: append `· N courses`). Confirm selection passes `online_presence`/`languages` through (the generic `(sel as Record)[s.key] = proposed[s.key]` path already handles new array keys).

- [ ] **Step 4: Run → pass** (this + existing review-card tests). `npx tsc -p tsconfig.app.json --noEmit`.
- [ ] **Step 5: Commit** `feat(materials): review card shows languages/links/courses`

---

## Part B — Follow-up questions

### Task 4: GapEngine (deterministic, source-agnostic)

**Files:**
- Create: `unipaith-backend/src/unipaith/services/follow_up_service.py`
- Test: `unipaith-backend/tests/test_follow_up.py`

- [ ] **Step 1: Test gap detection + ranking + cap**

```python
@pytest.mark.asyncio
async def test_gap_engine_detects_missing_and_ambiguous(db_session, mock_student_user):
    from unipaith.services.follow_up_service import FollowUpService
    from tests._uni_helpers import ensure_profile
    await ensure_profile(db_session, mock_student_user)
    imp = {"activities": [{"title": "Formula Club"}],  # no role → ambiguous
           "academic_records": [{"institution_name": "NEU", "degree_type": "bachelors"}]}  # no gpa
    gaps = await FollowUpService(db_session).detect(mock_student_user.id, imp)
    cats = {g["category"] for g in gaps}
    assert "missing" in cats          # no GPA / no test scores
    assert len(gaps) <= 5             # capped
    assert all({"id","category","target_field","prompt_hint","kind"} <= set(g) for g in gaps)
    assert sum(1 for g in gaps if g["category"] == "deepen") <= 1
```

- [ ] **Step 2: Run → fail** (ModuleNotFound).

- [ ] **Step 3: Implement `FollowUpService.detect`.** Pure rules over `(import_result, current profile snapshot via StudentService.get_full_snapshot)`. Produce `Gap` dicts:
  - **ambiguous:** for each imported activity missing a `role` → `{category:"ambiguous", target_field:"activity_role", prompt_hint:f"What did you do in {title}?", kind:"text", options:["Member","President","Founder","Volunteer"], ref:{title}}`.
  - **missing:** if snapshot has no test scores → one gap `{category:"missing", target_field:"test_scores", kind:"choice", options:["GRE","GMAT","TOEFL","IELTS","SAT/ACT","None yet"], prompt_hint:"Do you have any test scores to add?"}`; if no GPA on the current record → `{target_field:"gpa", kind:"text", prompt_hint:"What's your GPA?"}`; if no active goal/target degree → `{target_field:"target_degree", kind:"text", prompt_hint:"What program or degree are you aiming for?"}`.
  - **deepen:** exactly one `{category:"deepen", target_field:"goal", kind:"text", prompt_hint:"What's pulling you toward <field>?"}` (use the imported field_of_study if present).
  - Rank ambiguous → missing → deepen; cap at 5. `id` = stable `f"{category}:{target_field}:{i}"`.

- [ ] **Step 4: Run → pass.**
- [ ] **Step 5: Commit** `feat(followup): GapEngine detects ambiguous/missing/deepen gaps`

### Task 5: Follow-up LLM agent (phrase + parse, deterministic fallback)

**Files:**
- Create: `unipaith-backend/src/unipaith/ai/follow_up.py`
- Modify: `unipaith-backend/src/unipaith/services/follow_up_service.py` (`answer`)
- Test: `unipaith-backend/tests/test_follow_up.py`

- [ ] **Step 1: Test answer-applies-to-profile (mock mode → deterministic path)**

```python
@pytest.mark.asyncio
async def test_answer_writes_goal(db_session, mock_student_user):
    from unipaith.services.follow_up_service import FollowUpService
    from tests._uni_helpers import ensure_profile
    await ensure_profile(db_session, mock_student_user)
    svc = FollowUpService(db_session)
    out = await svc.answer(mock_student_user.id,
        {"category":"deepen","target_field":"goal","kind":"text"},
        "I love turning messy data into decisions")
    assert out["applied"] is True
    from unipaith.services.goals_service import GoalsService
    goals = await GoalsService(db_session).list_goals(mock_student_user.id)
    assert any("data" in g.specific.lower() for g in goals)
```

- [ ] **Step 2: Run → fail.**

- [ ] **Step 3: Implement `answer(user_id, gap, raw_answer)`.** Route by `gap["target_field"]`:
  - `goal` → `GoalsService.create_goal(user_id, CreateGoalRequest(category="academic", specific=raw_answer[:2000], source="manual"))`.
  - `gpa` → parse a float from `raw_answer`; if the student has a current `AcademicRecord`, `update_academic_record` its `gpa`; else skip.
  - `test_scores` → if answer ≠ "None yet", `create_test_score(student_id, CreateTestScoreRequest(test_type=<mapped>, total_score=<parsed int if any>))`.
  - `target_degree` → `update_profile(user_id, UpdateProfileRequest(goals_text=raw_answer))` (durable text).
  - `activity_role` → append the role to the matching activity's description (best-effort by `gap["ref"]["title"]`).
  Return `{"applied": bool, "target_field": ...}`. For free-text where structure is needed (gpa/test type), use `ai/follow_up.py::parse_answer(gap, raw)` which, when `settings.ai_material_followups_v2_enabled` and not mock, calls the LLM (workshop_coach slot) to extract `{value}`; on any failure or mock mode, fall back to deterministic regex parsing. `phrase(gap)` similarly returns an LLM one-liner or the deterministic `prompt_hint`.

- [ ] **Step 4: Run → pass.**
- [ ] **Step 5: Commit** `feat(followup): answer applies to My Space + LLM phrase/parse with fallback`

### Task 6: Endpoints + flag

**Files:**
- Modify: `unipaith-backend/src/unipaith/api/materials.py`
- Modify: `unipaith-backend/src/unipaith/config.py` (`ai_material_followups_v2_enabled: bool = False`)
- Modify: `infra/ecs.tf` (`AI_MATERIAL_FOLLOWUPS_V2_ENABLED=true`)
- Test: `unipaith-backend/tests/test_material_ingest.py`

- [ ] **Step 1: Endpoint test**

```python
@pytest.mark.asyncio
async def test_followups_endpoints(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    # create an ingest row to attach followups to
    from unipaith.services.material_ingest_service import MaterialIngestService
    row = await MaterialIngestService(db_session).ingest(mock_student_user.id, filename="r.pdf", mime_type="application/pdf", data=b"x")
    g = await student_client.get(f"/api/v1/students/me/materials/{row.id}/followups")
    assert g.status_code == 200
    assert isinstance(g.json()["questions"], list)
    a = await student_client.post("/api/v1/students/me/followups/answer",
        json={"gap": {"category":"deepen","target_field":"goal","kind":"text"}, "answer": "I love data"})
    assert a.status_code == 200 and a.json()["applied"] in (True, False)
```

- [ ] **Step 2: Run → fail (404).**
- [ ] **Step 3: Implement.** `GET /students/me/materials/{ingest_id}/followups` → load the ingest's `proposed`, `FollowUpService.detect(user.id, proposed)`, return `{"questions": [{**gap, "prompt": phrase(gap)} ...]}`. `POST /students/me/followups/answer` (`ApplyFollowupRequest{gap: dict, answer: str}`) → `FollowUpService.answer(...)`. Add the flag to config + ecs.tf.
- [ ] **Step 4: Run → pass.**
- [ ] **Step 5: Commit** `feat(followup): /materials/{id}/followups + /followups/answer + flag`

### Task 7: FollowUpCard + wiring (frontend)

**Files:**
- Create: `frontend/src/components/student/FollowUpCard.tsx`
- Modify: `frontend/src/api/materials.ts` (`getFollowups`, `answerFollowup`, types)
- Modify: `frontend/src/components/student/MaterialUpload.tsx` (show after apply)
- Test: `frontend/src/test/follow-up-card.test.tsx`

- [ ] **Step 1: Test the card**

```tsx
it('renders questions and answers one', () => {
  const onAnswer = vi.fn()
  const qs = [{ id: 'g1', category: 'missing', target_field: 'gpa', kind: 'text', prompt: "What's your GPA?" }]
  render(<FollowUpCard questions={qs} onAnswer={onAnswer} onDone={() => {}} />)
  expect(screen.getByText(/what's your gpa/i)).toBeInTheDocument()
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '3.8' } })
  fireEvent.click(screen.getByRole('button', { name: /answer|send|add/i }))
  expect(onAnswer).toHaveBeenCalledWith(qs[0], '3.8')
})
```

- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement.** `FollowUpCard({questions, onAnswer, onDone})` — one question at a time (or a short list), each with chips (`kind==='choice'` → options) and/or a text box; a "Skip" per question; advances; calls `onDone` when finished. `api/materials.ts`: `getFollowups(ingestId)`, `answerFollowup(gap, answer)`, `FollowupQuestion` type. In `MaterialUpload.tsx`, after `apply` succeeds, `getFollowups(ingest.id)` → if non-empty, render `FollowUpCard` (each `onAnswer` → `answerFollowup` then refresh queries); `onDone` resets.
- [ ] **Step 4: Run → pass** + `npx tsc -p tsconfig.app.json --noEmit` + `npm run build`.
- [ ] **Step 5: Commit** `feat(followup): FollowUpCard + wire after import (chat + profile)`

### Task 8: Acceptance — live re-run on the real resume + ship

**Files:**
- Create: `unipaith-backend/scripts/verify_material_ingest_live.py` (manual, not CI)

- [ ] **Step 1: Write a manual verify script** that calls `MaterialIngestAgent().read` (non-mock, real key) on a fixture resume PDF and prints the proposed payload; assert clubs-by-name, ≥3 languages, both schools, preferred name, skills line.
- [ ] **Step 2: Run it** with `ANTHROPIC_API_KEY` + `AI_MOCK_MODE=false` against `Leo Resume_1224.pdf`; eyeball every coverage-map row.
- [ ] **Step 3:** Run the full new test set: `pytest tests/test_material_ingest.py tests/test_follow_up.py` + `npx vitest run` (material + follow-up) — all green.
- [ ] **Step 4: Commit + ship** both flags on; merge → deploy (use the direct build+push path if the enrichment fleet cancels CI). Re-probe live; upload the real resume and confirm the review card + follow-ups.

---

## Self-Review

**Spec coverage:** Part A coverage map → Tasks 1–3 (schema, apply, review card). Part B GapEngine → Task 4; LLM phrase/parse + answer → Task 5; endpoints + flag → Task 6; FollowUpCard + wiring → Task 7; acceptance (live Leo re-run) → Task 8. Phasing: GapEngine is `detect(user_id, import|None)` so Phase 2 reuses it. All covered.

**Placeholder scan:** enum mappings are concrete (`college`, `intermediate`, `linkedin/portfolio/other`); each task has real test + impl code. No TBDs.

**Type consistency:** `Gap` dict shape `{id, category, target_field, prompt_hint, kind, options?, ref?}` is consistent across Task 4 (detect), Task 5 (answer), Task 6 (endpoint adds `prompt`), Task 7 (`FollowupQuestion` = Gap + `prompt`). `apply` counts keys (`online_presence`, `languages`, `courses`, `profile_fields`) match the test assertions.
