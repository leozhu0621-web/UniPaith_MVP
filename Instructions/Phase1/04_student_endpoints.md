# Task 04: Student CRUD Endpoints

## Context

You are building the student-facing API for **UniPaith**. Tasks 01-03 set up the project, database schema, and authentication. Now build all student profile management endpoints.

**Business logic context:** Students go through an adaptive onboarding process. They fill out their profile in stages — basic info, academics, test scores, activities, preferences. The system tracks their completion percentage and gates AI matching at 80% completion (matching comes in Phase 2).

## What to Build

### 1. services/student_service.py — Business Logic

```python
class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Profile ---
    async def get_profile(self, user_id: UUID) -> StudentProfile:
        """Get student profile with all related data loaded."""

    async def update_profile(self, user_id: UUID, data: UpdateProfileRequest) -> StudentProfile:
        """Update basic profile fields (first_name, last_name, nationality, etc.)."""

    # --- Academic Records ---
    async def list_academic_records(self, student_id: UUID) -> list[AcademicRecord]:
    async def create_academic_record(self, student_id: UUID, data: CreateAcademicRecordRequest) -> AcademicRecord:
    async def update_academic_record(self, student_id: UUID, record_id: UUID, data: UpdateAcademicRecordRequest) -> AcademicRecord:
    async def delete_academic_record(self, student_id: UUID, record_id: UUID) -> None:

    # --- Test Scores ---
    async def list_test_scores(self, student_id: UUID) -> list[TestScore]:
    async def create_test_score(self, student_id: UUID, data: CreateTestScoreRequest) -> TestScore:
    async def update_test_score(self, student_id: UUID, score_id: UUID, data: UpdateTestScoreRequest) -> TestScore:
    async def delete_test_score(self, student_id: UUID, score_id: UUID) -> None:

    # --- Activities ---
    async def list_activities(self, student_id: UUID) -> list[Activity]:
    async def create_activity(self, student_id: UUID, data: CreateActivityRequest) -> Activity:
    async def update_activity(self, student_id: UUID, activity_id: UUID, data: UpdateActivityRequest) -> Activity:
    async def delete_activity(self, student_id: UUID, activity_id: UUID) -> None:

    # --- Preferences ---
    async def get_preferences(self, student_id: UUID) -> StudentPreference | None:
    async def upsert_preferences(self, student_id: UUID, data: UpsertPreferencesRequest) -> StudentPreference:

    # --- Onboarding ---
    async def get_onboarding_status(self, student_id: UUID) -> OnboardingStatus:
        """
        Calculate completion percentage based on what's filled:
        - account created: 10%
        - basic profile (name, nationality): 15%
        - at least 1 academic record: 20%
        - at least 1 test score: 10%
        - at least 1 activity: 10%
        - bio_text filled: 10%
        - goals_text filled: 10%
        - preferences set: 15%
        Total: 100%

        Return current percentage, completed steps, and next recommended step.
        """

    async def get_next_onboarding_step(self, student_id: UUID) -> dict:
        """
        Adaptive intake: returns the next fields/section to fill based on what's missing.
        If student has PhD in academic records → suggest research activities next.
        If student is international → emphasize visa/TOEFL preferences.
        """

    # --- Helpers ---
    async def _get_student_profile(self, user_id: UUID) -> StudentProfile:
        """Get profile by user_id, raise 404 if not found."""

    async def _verify_ownership(self, student_id: UUID, record_owner_id: UUID) -> None:
        """Verify that a sub-record belongs to this student. Raise 403 if not."""

    async def _update_onboarding(self, student_id: UUID) -> None:
        """Recalculate and save onboarding progress. Called after any profile data changes."""
```

**Key business rules:**
- Every create/update/delete should trigger `_update_onboarding()` to recalculate completion %
- Students can only access/modify their OWN data (enforced by `_verify_ownership`)
- Academic records with `is_current=True` should have `end_date=None`
- GPA must be valid for the given scale (e.g., max 4.0 for "4.0" scale)

### 2. api/students.py — Route Handlers

All routes require `require_student` dependency (403 for non-students).

```
# Profile
GET  /api/v1/students/me/profile
  Response: Full profile with nested academic_records, test_scores, activities, preferences
  Notes: Eager-load all related data in one query

PUT  /api/v1/students/me/profile
  Body: {first_name?, last_name?, date_of_birth?, nationality?, country_of_residence?, bio_text?, goals_text?}
  Response: Updated profile
  Notes: Partial update — only provided fields are changed

# Onboarding
GET  /api/v1/students/me/onboarding
  Response: {completion_percentage, steps_completed: [...], next_step: {...}}

GET  /api/v1/students/me/onboarding/next-step
  Response: {section, fields: [...], guidance_text}
  Notes: Adaptive — changes based on student context

# Academic Records
GET    /api/v1/students/me/academics
  Response: [AcademicRecord, ...]

POST   /api/v1/students/me/academics
  Body: {institution_name, degree_type, field_of_study, gpa?, gpa_scale?, start_date, end_date?, is_current?, honors?, thesis_title?, country}
  Response: Created record (201)

PUT    /api/v1/students/me/academics/{record_id}
  Body: Same as POST (all fields optional for partial update)
  Response: Updated record

DELETE /api/v1/students/me/academics/{record_id}
  Response: 204 No Content

# Test Scores
GET    /api/v1/students/me/test-scores
POST   /api/v1/students/me/test-scores
PUT    /api/v1/students/me/test-scores/{score_id}
DELETE /api/v1/students/me/test-scores/{score_id}

# Activities
GET    /api/v1/students/me/activities
POST   /api/v1/students/me/activities
PUT    /api/v1/students/me/activities/{activity_id}
DELETE /api/v1/students/me/activities/{activity_id}

# Preferences
GET    /api/v1/students/me/preferences
PUT    /api/v1/students/me/preferences
  Notes: Upsert — creates if not exists, updates if exists
```

### 3. schemas/student.py — Pydantic Schemas

Create request and response schemas. Key patterns:

```python
# Response schemas include id, created_at, updated_at
# Request schemas exclude those (server-generated)
# Update requests make all fields Optional

class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    nationality: str | None
    country_of_residence: str | None
    bio_text: str | None
    goals_text: str | None
    created_at: datetime
    updated_at: datetime
    # Nested
    academic_records: list[AcademicRecordResponse] = []
    test_scores: list[TestScoreResponse] = []
    activities: list[ActivityResponse] = []
    preferences: StudentPreferenceResponse | None = None
    onboarding: OnboardingStatusResponse | None = None

class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    country_of_residence: str | None = None
    bio_text: str | None = None
    goals_text: str | None = None

class CreateAcademicRecordRequest(BaseModel):
    institution_name: str = Field(min_length=1, max_length=255)
    degree_type: Literal["high_school", "bachelors", "masters", "phd", "associate", "diploma"]
    field_of_study: str | None = None
    gpa: Decimal | None = Field(None, ge=0, le=100)  # Validated per scale
    gpa_scale: str | None = None
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    honors: str | None = None
    thesis_title: str | None = None
    country: str | None = None

# ... similar patterns for test scores, activities, preferences
# Use Literal types for enums (degree_type, test_type, activity_type, etc.)

class OnboardingStatusResponse(BaseModel):
    completion_percentage: int
    steps_completed: list[str]
    next_step: NextStepResponse | None

class NextStepResponse(BaseModel):
    section: str          # "academics", "test_scores", "activities", "preferences", etc.
    fields: list[str]     # Specific fields to fill
    guidance_text: str    # Contextual guidance
```

### 4. Tests — test_students.py

Write comprehensive tests:

**Profile tests:**
- GET profile returns full nested data
- PUT profile updates only specified fields (partial update)
- PUT profile doesn't affect unspecified fields
- Profile returns 401 without auth
- Profile returns 403 for institution_admin role

**Academic records tests:**
- POST creates record, returns 201
- GET lists all records for student
- PUT updates specific record
- DELETE removes record, returns 204
- Cannot access another student's records (403)
- Validates degree_type enum
- Current record enforces end_date is null
- GPA validation per scale (4.0 max for "4.0" scale)

**Test scores tests:**
- CRUD operations work correctly
- Validates test_type enum
- Section scores stored as JSONB

**Activities tests:**
- CRUD operations work correctly
- Validates activity_type enum
- Current activities have no end_date

**Preferences tests:**
- GET returns null if not set
- PUT creates preferences on first call
- PUT updates on subsequent calls (upsert)
- Array fields (preferred_countries) store correctly
- JSONB fields (values_priorities, career_goals) store correctly

**Onboarding tests:**
- New student starts at ~10% (account only)
- Adding academic record increases percentage
- Completion percentage updates after each change
- Next step is contextual (PhD student gets research prompt)
- 80% threshold is detectable from response

## Important Notes

- Use **eager loading** (`selectinload` or `joinedload`) for the profile endpoint to avoid N+1 queries
- All list endpoints should eventually support pagination, but for MVP return all records (students won't have thousands of records)
- The `_update_onboarding()` call is critical — it must run after EVERY data change to keep the progress tracker accurate
- Validate that `student_id` in the route always matches the authenticated user's student profile — never trust client-provided IDs for ownership
- `bio_text` and `goals_text` are free-form text that will be sent to the LLM in Phase 2 — no processing needed now, just store them
