# Task 05: Institution & Program CRUD Endpoints

## Context

You are building the institution-facing API for **UniPaith**. Tasks 01-04 set up infrastructure, schema, auth, and student endpoints. Now build institution profile management and program CRUD.

**Business logic context:** Institutions register, set up their profile, then create and publish programs. Programs must be published (`is_published=true`) to appear in student search. Institutions also define target segments for outreach.

## What to Build

### 1. services/institution_service.py — Business Logic

```python
class InstitutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Institution Profile ---
    async def get_institution(self, user_id: UUID) -> Institution:
        """Get institution profile for the authenticated admin user. Raises 404 if not set up."""

    async def create_institution(self, user_id: UUID, data: CreateInstitutionRequest) -> Institution:
        """
        Create institution profile linked to the admin user.
        Only callable once per user (unique constraint on admin_user_id).
        """

    async def update_institution(self, user_id: UUID, data: UpdateInstitutionRequest) -> Institution:
        """Partial update of institution fields."""

    # --- Programs ---
    async def list_programs(self, institution_id: UUID) -> list[Program]:
        """List all programs for this institution (published and drafts)."""

    async def get_program(self, institution_id: UUID, program_id: UUID) -> Program:
        """Get single program. Verify it belongs to this institution."""

    async def create_program(self, institution_id: UUID, data: CreateProgramRequest) -> Program:
        """Create a new program in draft state (is_published=false)."""

    async def update_program(self, institution_id: UUID, program_id: UUID, data: UpdateProgramRequest) -> Program:
        """Update program fields. Partial update."""

    async def publish_program(self, institution_id: UUID, program_id: UUID) -> Program:
        """
        Set is_published=true.
        Validate minimum requirements before publishing:
        - program_name is set
        - degree_type is set
        - description_text is not empty
        - At least one of: tuition, application_deadline
        Raise 400 if requirements not met.
        """

    async def unpublish_program(self, institution_id: UUID, program_id: UUID) -> Program:
        """Set is_published=false. Does NOT delete — just hides from search."""

    async def delete_program(self, institution_id: UUID, program_id: UUID) -> None:
        """
        Soft-delete: only allowed if program has no submitted applications.
        If applications exist, raise 409 Conflict.
        Otherwise, hard delete.
        """

    # --- Target Segments ---
    async def list_segments(self, institution_id: UUID) -> list[TargetSegment]:
    async def create_segment(self, institution_id: UUID, data: CreateSegmentRequest) -> TargetSegment:
    async def update_segment(self, institution_id: UUID, segment_id: UUID, data: UpdateSegmentRequest) -> TargetSegment:
    async def delete_segment(self, institution_id: UUID, segment_id: UUID) -> None:

    # --- Public Program Browsing (no auth required) ---
    async def search_programs(
        self,
        query: str | None = None,
        country: str | None = None,
        degree_type: str | None = None,
        min_tuition: int | None = None,
        max_tuition: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ProgramSummaryResponse]:
        """
        Public search: only returns published programs.
        Full-text search on program_name, description_text, department.
        Filter by country, degree_type, tuition range.
        Paginated results.
        Sort by relevance (if search query) or by institution ranking (default).
        """

    async def get_public_program(self, program_id: UUID) -> Program:
        """Public program detail. Only if published. Includes institution info."""

    # --- Helpers ---
    async def _get_institution_for_user(self, user_id: UUID) -> Institution:
        """Get institution by admin_user_id. Raise 404 if not found."""

    async def _verify_program_ownership(self, institution_id: UUID, program_id: UUID) -> Program:
        """Verify program belongs to institution. Raise 404 if not."""
```

### 2. api/institutions.py — Institution Admin Routes

All routes require `require_institution_admin` dependency.

```
# Institution Profile
GET  /api/v1/institutions/me
  Response: Institution profile with program count

POST /api/v1/institutions/me
  Body: {name, type, country, region?, city?, ranking_data?, description_text?, logo_url?, website_url?}
  Response: Created institution (201)
  Notes: Only callable once per admin user

PUT  /api/v1/institutions/me
  Body: Same as POST (all optional for partial update)
  Response: Updated institution

# Programs (institution admin managing their own)
GET    /api/v1/institutions/me/programs
  Response: [Program, ...] — includes drafts and published

POST   /api/v1/institutions/me/programs
  Body: {program_name, degree_type, department?, duration_months?, tuition?, ...}
  Response: Created program in draft state (201)

GET    /api/v1/institutions/me/programs/{program_id}
  Response: Full program detail

PUT    /api/v1/institutions/me/programs/{program_id}
  Body: Partial update fields
  Response: Updated program

POST   /api/v1/institutions/me/programs/{program_id}/publish
  Response: Published program
  Notes: Validates minimum requirements

POST   /api/v1/institutions/me/programs/{program_id}/unpublish
  Response: Unpublished program

DELETE /api/v1/institutions/me/programs/{program_id}
  Response: 204
  Notes: Fails with 409 if applications exist

# Target Segments
GET    /api/v1/institutions/me/segments
POST   /api/v1/institutions/me/segments
PUT    /api/v1/institutions/me/segments/{segment_id}
DELETE /api/v1/institutions/me/segments/{segment_id}
```

### 3. api/programs.py — Public Program Browsing Routes

These routes are public — no auth required.

```
GET /api/v1/programs
  Query params: q (search), country, degree_type, min_tuition, max_tuition, page, page_size
  Response: Paginated list of published programs with institution summary
  Notes: Only published programs appear here

GET /api/v1/programs/{program_id}
  Response: Full program detail with institution info
  Notes: Only if published. Returns 404 for unpublished.
```

### 4. schemas/institution.py — Pydantic Schemas

```python
# Institution
class CreateInstitutionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: Literal["university", "college", "technical_institute", "community_college"]
    country: str = Field(min_length=1, max_length=100)
    region: str | None = None
    city: str | None = None
    ranking_data: dict | None = None
    description_text: str | None = None
    logo_url: HttpUrl | None = None
    website_url: HttpUrl | None = None

class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    type: str
    country: str
    region: str | None
    city: str | None
    ranking_data: dict | None
    description_text: str | None
    logo_url: str | None
    website_url: str | None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    program_count: int | None = None  # Computed field

# Program
class CreateProgramRequest(BaseModel):
    program_name: str = Field(min_length=1, max_length=255)
    degree_type: Literal["bachelors", "masters", "phd", "certificate", "diploma"]
    department: str | None = None
    duration_months: int | None = Field(None, ge=1, le=120)
    tuition: int | None = Field(None, ge=0)
    acceptance_rate: Decimal | None = Field(None, ge=0, le=1)
    requirements: dict | None = None
    description_text: str | None = None
    current_preferences_text: str | None = None
    application_deadline: date | None = None
    program_start_date: date | None = None
    page_header_image_url: str | None = None
    highlights: list[str] | None = None
    faculty_contacts: list[dict] | None = None

class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_name: str
    degree_type: str
    department: str | None
    duration_months: int | None
    tuition: int | None
    acceptance_rate: Decimal | None
    requirements: dict | None
    description_text: str | None
    current_preferences_text: str | None
    is_published: bool
    application_deadline: date | None
    program_start_date: date | None
    highlights: list | None
    created_at: datetime
    updated_at: datetime

class ProgramSummaryResponse(BaseModel):
    """Lighter response for search results."""
    id: UUID
    program_name: str
    degree_type: str
    department: str | None
    tuition: int | None
    application_deadline: date | None
    institution_name: str
    institution_country: str

# Pagination
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# Target Segments
class CreateSegmentRequest(BaseModel):
    segment_name: str = Field(min_length=1, max_length=255)
    program_id: UUID | None = None
    criteria: dict  # {"gpa_min": 3.5, "field": "STEM", "region": ["Southeast Asia"]}
    is_active: bool = True
```

### 5. schemas/common.py — Shared Schemas

```python
class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None

class MessageResponse(BaseModel):
    message: str

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
```

### 6. Tests — test_institutions.py

**Institution profile tests:**
- POST creates institution for admin user → 201
- POST second time for same user → 409 Conflict
- GET returns institution with program count
- PUT updates only specified fields
- Student cannot access institution endpoints → 403

**Program tests:**
- POST creates program in draft state
- GET lists all programs (published + drafts) for own institution
- PUT updates program fields
- Publish validates minimum requirements → 400 if missing
- Publish succeeds when requirements met → program appears in public search
- Unpublish removes from public search
- DELETE succeeds for program with no applications
- DELETE fails for program with applications → 409

**Public search tests:**
- GET /programs returns only published programs
- Search by query filters correctly
- Filter by country works
- Filter by degree_type works
- Pagination returns correct page/total
- GET /programs/{id} for unpublished → 404
- GET /programs/{id} for published → 200 with institution info

**Segment tests:**
- CRUD operations work
- Segments are scoped to institution

## Important Notes

- Institution admin sees ALL their programs (drafts + published). Public API only sees published.
- The `program_count` on InstitutionResponse is a computed field — count published programs.
- `search_programs` should use PostgreSQL full-text search (`to_tsvector` / `to_tsquery`) for the `q` parameter. For MVP, `ILIKE` is acceptable but add a TODO comment for full-text search upgrade.
- The `requirements` JSON on programs is flexible by design — different programs have different requirements. No rigid schema.
- `current_preferences_text` is institution-facing only (not shown to students). It feeds into the AI matching in Phase 2.
