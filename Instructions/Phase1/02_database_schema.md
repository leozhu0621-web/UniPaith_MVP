# Task 02: Database Schema — All PostgreSQL + pgvector Tables

## Context

You are continuing to build the **UniPaith** backend. Task 01 set up the project scaffolding. Now you need to define all SQLAlchemy ORM models and create the initial Alembic migration.

**This is the most important task in Phase 1** — every subsequent task depends on this schema being correct.

The project structure from Task 01 already has model files at `src/unipaith/models/`. Fill them in with the complete schema below.

## Prerequisites

- Task 01 is complete (project scaffolding exists)
- PostgreSQL + pgvector is running via `docker-compose up -d`
- `pip install -e ".[dev]"` has been run

## What to Build

### models/base.py — Base Class and Mixins

```python
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Adds created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
```

### models/user.py — Users & Authentication (Drawer 1)

**Table: `users`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| email | VARCHAR(255) | UNIQUE, NOT NULL, indexed |
| cognito_sub | VARCHAR(255) | UNIQUE, nullable (set after Cognito signup) |
| role | ENUM('student', 'institution_admin', 'admin') | NOT NULL |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP WITH TZ | DEFAULT now() |
| updated_at | TIMESTAMP WITH TZ | DEFAULT now(), auto-update |

Use a PostgreSQL ENUM type for `role`. Add index on `email` and `cognito_sub`.

Relationships:
- `student_profile` — one-to-one with StudentProfile (if role is student)
- `institution` — one-to-one with Institution (if role is institution_admin)

### models/student.py — Student Domain (Drawers 2-7)

**Table: `student_profiles`** (Drawer 2)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK(users.id), UNIQUE, NOT NULL |
| first_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| date_of_birth | DATE | nullable |
| nationality | VARCHAR(100) | |
| country_of_residence | VARCHAR(100) | |
| bio_text | TEXT | Free-text, sent to LLM for feature extraction |
| goals_text | TEXT | Free-text goals, sent to LLM |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

Relationships: user, academic_records, test_scores, activities, documents, preferences, applications, saved_lists, engagement_signals, onboarding_progress

---

**Table: `academic_records`** (Drawer 3) — one student has many

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| institution_name | VARCHAR(255) | NOT NULL |
| degree_type | VARCHAR(50) | NOT NULL (high_school, bachelors, masters, phd, associate, diploma) |
| field_of_study | VARCHAR(255) | |
| gpa | DECIMAL(4,2) | nullable |
| gpa_scale | VARCHAR(20) | '4.0', 'percentage', 'ib', '10.0', etc. |
| start_date | DATE | |
| end_date | DATE | nullable |
| is_current | BOOLEAN | DEFAULT false |
| honors | VARCHAR(255) | nullable |
| thesis_title | VARCHAR(500) | nullable |
| country | VARCHAR(100) | |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `test_scores`** (Drawer 4)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| test_type | VARCHAR(50) | NOT NULL (SAT, GRE, GMAT, TOEFL, IELTS, AP, IB, ACT, LSAT, MCAT, DUOLINGO) |
| total_score | INTEGER | |
| section_scores | JSONB | e.g., {"verbal": 165, "quantitative": 170} |
| test_date | DATE | |
| is_official | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `activities`** (Drawer 5)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| activity_type | VARCHAR(50) | NOT NULL (work_experience, research, volunteering, extracurricular, leadership, awards, publications) |
| title | VARCHAR(255) | NOT NULL |
| organization | VARCHAR(255) | |
| description | TEXT | Sent to LLM for feature extraction |
| start_date | DATE | |
| end_date | DATE | nullable |
| is_current | BOOLEAN | DEFAULT false |
| hours_per_week | INTEGER | nullable |
| impact_description | TEXT | nullable |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `student_documents`** (Drawer 6)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| document_type | VARCHAR(50) | NOT NULL (transcript, essay, resume, recommendation, portfolio, certificate) |
| file_name | VARCHAR(255) | NOT NULL |
| file_url | VARCHAR(1000) | S3 URL |
| file_size_bytes | INTEGER | |
| mime_type | VARCHAR(100) | |
| extracted_text | TEXT | OCR/PDF-parsed text, nullable |
| uploaded_at | TIMESTAMP WITH TZ | DEFAULT now() |

---

**Table: `student_preferences`** (Drawer 7) — one-to-one with student

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), UNIQUE, NOT NULL |
| preferred_countries | ARRAY(VARCHAR) | PostgreSQL array |
| preferred_regions | ARRAY(VARCHAR) | |
| preferred_city_size | VARCHAR(30) | big_city, college_town, suburban, rural, no_preference |
| preferred_climate | VARCHAR(50) | nullable |
| budget_min | INTEGER | nullable |
| budget_max | INTEGER | nullable |
| funding_requirement | VARCHAR(30) | full_scholarship, partial, self_funded, flexible |
| program_size_preference | VARCHAR(20) | small, large, no_preference |
| career_goals | JSONB | Array of strings |
| values_priorities | JSONB | {"ranking": 3, "location": 5, "cost": 4, ...} rated 1-5 |
| dealbreakers | JSONB | Array: ["no_gre_required", "must_have_coop"] |
| goals_text | TEXT | Free-text for LLM |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `onboarding_progress`** — tracks student intake progress

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), UNIQUE, NOT NULL |
| steps_completed | JSONB | ["account", "basic_profile", "academics", ...] |
| completion_percentage | INTEGER | DEFAULT 0 |
| last_step_at | TIMESTAMP WITH TZ | |
| nudge_sent_at | TIMESTAMP WITH TZ | nullable |

### models/institution.py — Institution Domain (Drawers 8-9 + Supporting)

**Table: `institutions`** (Drawer 8)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| admin_user_id | UUID | FK(users.id), UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| type | VARCHAR(50) | university, college, technical_institute, community_college |
| country | VARCHAR(100) | NOT NULL |
| region | VARCHAR(100) | |
| city | VARCHAR(100) | |
| ranking_data | JSONB | {"qs": 45, "times_he": 52, "us_news": 38} |
| description_text | TEXT | Sent to LLM |
| logo_url | VARCHAR(1000) | nullable |
| website_url | VARCHAR(1000) | nullable |
| is_verified | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

Relationships: programs, segments, campaigns, events, reviewers, conversations

---

**Table: `programs`** (Drawer 9)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| institution_id | UUID | FK(institutions.id), NOT NULL, indexed |
| program_name | VARCHAR(255) | NOT NULL |
| degree_type | VARCHAR(30) | bachelors, masters, phd, certificate, diploma |
| department | VARCHAR(255) | |
| duration_months | INTEGER | |
| tuition | INTEGER | Annual in USD |
| acceptance_rate | DECIMAL(5,4) | 0.0000-1.0000, nullable |
| requirements | JSONB | {"min_gpa": 3.0, "gre_required": false, "toefl_min": 90, ...} |
| description_text | TEXT | |
| current_preferences_text | TEXT | "We want more STEM this year" |
| is_published | BOOLEAN | DEFAULT false |
| application_deadline | DATE | nullable |
| program_start_date | DATE | nullable |
| page_header_image_url | VARCHAR(1000) | nullable |
| highlights | JSONB | Array of key selling points |
| faculty_contacts | JSONB | nullable |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

Add a composite index on `(institution_id, is_published)` for efficient program listing.

---

**Table: `target_segments`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| institution_id | UUID | FK(institutions.id), NOT NULL |
| program_id | UUID | FK(programs.id), nullable |
| segment_name | VARCHAR(255) | NOT NULL |
| criteria | JSONB | {"gpa_min": 3.5, "field": "STEM", "region": ["Southeast Asia"]} |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `campaigns`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| institution_id | UUID | FK(institutions.id), NOT NULL |
| program_id | UUID | FK(programs.id), nullable |
| segment_id | UUID | FK(target_segments.id), nullable |
| campaign_name | VARCHAR(255) | NOT NULL |
| campaign_type | VARCHAR(30) | email, in_platform, event_invite |
| message_subject | VARCHAR(500) | |
| message_body | TEXT | |
| status | VARCHAR(20) | draft, scheduled, active, completed |
| scheduled_send_at | TIMESTAMP WITH TZ | nullable |
| sent_at | TIMESTAMP WITH TZ | nullable |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `campaign_recipients`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| campaign_id | UUID | FK(campaigns.id), NOT NULL |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| delivered_at | TIMESTAMP WITH TZ | nullable |
| opened_at | TIMESTAMP WITH TZ | nullable |
| clicked_at | TIMESTAMP WITH TZ | nullable |
| responded_at | TIMESTAMP WITH TZ | nullable |

Add unique constraint on `(campaign_id, student_id)`.

---

**Table: `events`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| institution_id | UUID | FK(institutions.id), NOT NULL |
| program_id | UUID | FK(programs.id), nullable |
| event_name | VARCHAR(255) | NOT NULL |
| event_type | VARCHAR(30) | webinar, campus_visit, info_session, workshop |
| description | TEXT | |
| location | VARCHAR(500) | URL for virtual, address for in-person |
| start_time | TIMESTAMP WITH TZ | NOT NULL |
| end_time | TIMESTAMP WITH TZ | NOT NULL |
| capacity | INTEGER | nullable |
| rsvp_count | INTEGER | DEFAULT 0 |
| status | VARCHAR(20) | draft, published, live, completed, cancelled |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `event_rsvps`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| event_id | UUID | FK(events.id), NOT NULL |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| rsvp_status | VARCHAR(20) | registered, confirmed, attended, no_show |
| registered_at | TIMESTAMP WITH TZ | DEFAULT now() |
| attended_at | TIMESTAMP WITH TZ | nullable |

Add unique constraint on `(event_id, student_id)`.

---

**Table: `reviewers`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| institution_id | UUID | FK(institutions.id), NOT NULL |
| user_id | UUID | FK(users.id), NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| department | VARCHAR(255) | |
| specializations | JSONB | Array |
| current_workload | INTEGER | DEFAULT 0 |
| max_workload | INTEGER | DEFAULT 50 |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

### models/application.py — Application Domain (Drawers 10-11 + Workflow)

**Table: `historical_outcomes`** (Drawer 10)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| program_id | UUID | FK(programs.id), NOT NULL, indexed |
| year | INTEGER | NOT NULL |
| applicant_profile_summary | JSONB | Key features |
| outcome | VARCHAR(20) | admitted, rejected, waitlisted |
| enrolled | BOOLEAN | nullable |
| created_at | TIMESTAMP WITH TZ | |

---

**Table: `applications`** (Drawer 11)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| program_id | UUID | FK(programs.id), NOT NULL, indexed |
| status | VARCHAR(30) | draft, submitted, under_review, interview, decision_made |
| match_score | DECIMAL(5,4) | nullable |
| match_reasoning_text | TEXT | nullable |
| submitted_at | TIMESTAMP WITH TZ | nullable |
| decision | VARCHAR(20) | admitted, rejected, waitlisted, deferred, nullable |
| decision_by | UUID | FK(reviewers.id), nullable |
| decision_at | TIMESTAMP WITH TZ | nullable |
| decision_notes | TEXT | Internal, not shared with student |
| completeness_status | VARCHAR(30) | complete, incomplete, pending_verification |
| missing_items | JSONB | Array of missing requirements |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

Add unique constraint on `(student_id, program_id)` — one application per student per program.

---

**Table: `application_checklists`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| program_id | UUID | FK(programs.id), NOT NULL |
| items | JSONB | Array of {name, status, required} |
| completion_percentage | INTEGER | DEFAULT 0 |
| auto_generated_at | TIMESTAMP WITH TZ | |

---

**Table: `application_submissions`** — immutable snapshot of submitted application

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| application_id | UUID | FK(applications.id), UNIQUE, NOT NULL |
| submitted_documents | JSONB | Snapshot of all materials |
| submission_package_url | VARCHAR(1000) | Compiled package in S3 |
| submitted_at | TIMESTAMP WITH TZ | NOT NULL |
| confirmation_number | VARCHAR(20) | UNIQUE, auto-generated |

---

**Table: `review_assignments`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| application_id | UUID | FK(applications.id), NOT NULL |
| reviewer_id | UUID | FK(reviewers.id), NOT NULL |
| assigned_at | TIMESTAMP WITH TZ | DEFAULT now() |
| due_date | DATE | |
| status | VARCHAR(20) | assigned, in_progress, completed |

---

**Table: `rubrics`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| institution_id | UUID | FK(institutions.id), NOT NULL |
| program_id | UUID | FK(programs.id), nullable |
| rubric_name | VARCHAR(255) | NOT NULL |
| criteria | JSONB | Array of {name, weight, max_score, description} |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `application_scores`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| application_id | UUID | FK(applications.id), NOT NULL |
| reviewer_id | UUID | FK(reviewers.id), NOT NULL |
| rubric_id | UUID | FK(rubrics.id), NOT NULL |
| criterion_scores | JSONB | {criterion_name: score} |
| total_weighted_score | DECIMAL(6,3) | |
| reviewer_notes | TEXT | |
| scored_by_type | VARCHAR(20) | human, ai_suggested |
| scored_at | TIMESTAMP WITH TZ | DEFAULT now() |

---

**Table: `interviews`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| application_id | UUID | FK(applications.id), NOT NULL |
| interviewer_id | UUID | FK(reviewers.id), NOT NULL |
| interview_type | VARCHAR(20) | video, in_person, phone, group |
| proposed_times | JSONB | Array of ISO datetime strings |
| confirmed_time | TIMESTAMP WITH TZ | nullable |
| location_or_link | VARCHAR(500) | |
| status | VARCHAR(20) | invited, scheduling, confirmed, completed, cancelled, no_show |
| duration_minutes | INTEGER | DEFAULT 30 |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `interview_scores`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| interview_id | UUID | FK(interviews.id), NOT NULL |
| interviewer_id | UUID | FK(reviewers.id), NOT NULL |
| rubric_id | UUID | FK(rubrics.id), nullable |
| criterion_scores | JSONB | |
| total_weighted_score | DECIMAL(6,3) | |
| interviewer_notes | TEXT | |
| recommendation | VARCHAR(20) | strong_admit, admit, borderline, reject |

---

**Table: `offer_letters`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| application_id | UUID | FK(applications.id), UNIQUE, NOT NULL |
| offer_type | VARCHAR(30) | full_admission, conditional, waitlist_offer |
| tuition_amount | INTEGER | |
| scholarship_amount | INTEGER | DEFAULT 0 |
| assistantship_details | JSONB | nullable |
| financial_package_total | INTEGER | |
| conditions | JSONB | For conditional offers |
| response_deadline | DATE | |
| generated_letter_url | VARCHAR(1000) | |
| status | VARCHAR(20) | draft, approved, sent, accepted, declined, expired |
| student_response | VARCHAR(20) | accepted, declined, nullable |
| response_at | TIMESTAMP WITH TZ | nullable |
| decline_reason | TEXT | nullable, feeds back to system |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `enrollment_records`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| application_id | UUID | FK(applications.id), UNIQUE, NOT NULL |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| program_id | UUID | FK(programs.id), NOT NULL |
| enrolled_at | TIMESTAMP WITH TZ | DEFAULT now() |
| enrollment_status | VARCHAR(20) | confirmed, deferred, withdrawn |
| start_term | VARCHAR(20) | e.g., "Fall 2026" |

### models/engagement.py — Engagement & Communication

**Table: `student_engagement_signals`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| program_id | UUID | FK(programs.id), NOT NULL, indexed |
| signal_type | VARCHAR(30) | viewed_program, time_spent, saved, compared, unsaved, dismissed, clicked_apply |
| signal_value | INTEGER | Seconds for time_spent, 1/0 for boolean |
| created_at | TIMESTAMP WITH TZ | DEFAULT now() |

Add index on `(student_id, program_id, signal_type)` for efficient querying.

---

**Table: `saved_lists`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| list_name | VARCHAR(100) | NOT NULL, DEFAULT "My List" |
| created_at | TIMESTAMP WITH TZ | |

---

**Table: `saved_list_items`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| list_id | UUID | FK(saved_lists.id), NOT NULL |
| program_id | UUID | FK(programs.id), NOT NULL |
| added_at | TIMESTAMP WITH TZ | DEFAULT now() |
| notes | TEXT | nullable |

Add unique constraint on `(list_id, program_id)`.

---

**Table: `student_calendar`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| entry_type | VARCHAR(20) | event, deadline, interview, custom |
| reference_id | UUID | Points to event_id, application deadline, etc. |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| start_time | TIMESTAMP WITH TZ | NOT NULL |
| end_time | TIMESTAMP WITH TZ | nullable |
| reminder_at | TIMESTAMP WITH TZ | nullable |
| created_at | TIMESTAMP WITH TZ | |

---

**Table: `crm_records`** — append-only touchpoint log

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| institution_id | UUID | FK(institutions.id), NOT NULL, indexed |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| touchpoint_type | VARCHAR(50) | event_rsvp, inquiry_sent, campaign_opened, application_submitted, etc. |
| touchpoint_detail | JSONB | |
| occurred_at | TIMESTAMP WITH TZ | DEFAULT now() |

Add index on `(institution_id, student_id)`.

---

**Table: `conversations`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| institution_id | UUID | FK(institutions.id), NOT NULL |
| program_id | UUID | FK(programs.id), nullable |
| subject | VARCHAR(500) | |
| status | VARCHAR(20) | open, awaiting_response, resolved, closed |
| started_at | TIMESTAMP WITH TZ | DEFAULT now() |
| last_message_at | TIMESTAMP WITH TZ | |

---

**Table: `messages`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| conversation_id | UUID | FK(conversations.id), NOT NULL, indexed |
| sender_type | VARCHAR(20) | student, institution |
| sender_id | UUID | FK(users.id), NOT NULL |
| message_body | TEXT | NOT NULL |
| sent_at | TIMESTAMP WITH TZ | DEFAULT now() |
| read_at | TIMESTAMP WITH TZ | nullable |

---

**Table: `student_resumes`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| resume_version | INTEGER | DEFAULT 1 |
| content | JSONB | Structured resume data |
| rendered_pdf_url | VARCHAR(1000) | nullable |
| ai_suggestions | JSONB | LLM feedback, nullable |
| target_program_id | UUID | FK(programs.id), nullable |
| status | VARCHAR(20) | draft, reviewed, finalized |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `student_essays`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| program_id | UUID | FK(programs.id), NOT NULL |
| prompt_text | TEXT | Essay question |
| essay_version | INTEGER | DEFAULT 1 |
| content | TEXT | |
| word_count | INTEGER | |
| ai_feedback | JSONB | LLM analysis, nullable |
| status | VARCHAR(20) | draft, reviewed, revised, finalized |
| created_at | TIMESTAMP WITH TZ | |
| updated_at | TIMESTAMP WITH TZ | |

### models/matching.py — AI/ML Tables

**Table: `match_results`** — cached AI predictions

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL, indexed |
| program_id | UUID | FK(programs.id), NOT NULL, indexed |
| match_score | DECIMAL(5,4) | 0.0000 to 1.0000 |
| match_tier | INTEGER | 1, 2, or 3 |
| score_breakdown | JSONB | {"academic_fit": 0.85, "preference_alignment": 0.78, ...} |
| reasoning_text | TEXT | LLM-generated explanation |
| model_version | VARCHAR(50) | |
| computed_at | TIMESTAMP WITH TZ | DEFAULT now() |
| is_stale | BOOLEAN | DEFAULT false |

Add unique constraint on `(student_id, program_id)`.

---

**Table: `student_features`** — pre-computed feature vectors

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), UNIQUE, NOT NULL |
| feature_data | JSONB | LLM-extracted flexible features |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `institution_features`** — pre-computed per program

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| program_id | UUID | FK(programs.id), UNIQUE, NOT NULL |
| feature_data | JSONB | LLM-extracted flexible features |
| updated_at | TIMESTAMP WITH TZ | |

---

**Table: `embeddings`** — pgvector embeddings

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| entity_type | VARCHAR(20) | 'student' or 'program' |
| entity_id | UUID | NOT NULL |
| embedding | VECTOR(768) | pgvector column |
| updated_at | TIMESTAMP WITH TZ | |

Add unique constraint on `(entity_type, entity_id)`.
Add an IVFFlat or HNSW index on the `embedding` column for approximate nearest neighbor search:
```sql
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
```

---

**Table: `prediction_logs`** — heartbeat of self-improvement

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| program_id | UUID | FK(programs.id), NOT NULL |
| predicted_score | DECIMAL(5,4) | |
| predicted_tier | INTEGER | |
| model_version | VARCHAR(50) | |
| features_used | JSONB | Snapshot of input features |
| predicted_at | TIMESTAMP WITH TZ | DEFAULT now() |
| actual_outcome | VARCHAR(20) | admitted, rejected, waitlisted, null |
| outcome_recorded_at | TIMESTAMP WITH TZ | nullable |

---

**Table: `model_registry`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| model_version | VARCHAR(50) | UNIQUE, NOT NULL |
| architecture | TEXT | Description of model structure |
| hyperparameters | JSONB | |
| training_data_snapshot | VARCHAR(255) | Reference to training data |
| performance_metrics | JSONB | {"accuracy": 0.74, "bias_gap": 0.08, ...} |
| is_active | BOOLEAN | DEFAULT false |
| trained_at | TIMESTAMP WITH TZ | |
| promoted_at | TIMESTAMP WITH TZ | nullable |
| retired_at | TIMESTAMP WITH TZ | nullable |
| created_at | TIMESTAMP WITH TZ | |

---

**Table: `data_sources`** — crawler registry

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| source_name | VARCHAR(255) | NOT NULL |
| source_url | VARCHAR(1000) | |
| source_type | VARCHAR(20) | web_scrape, api, rss, csv_download |
| crawl_frequency | VARCHAR(20) | daily, weekly, monthly, yearly |
| data_category | VARCHAR(50) | rankings, program_info, admissions_stats, scholarship, visa_policy |
| last_crawled_at | TIMESTAMP WITH TZ | nullable |
| reliability_score | DECIMAL(3,2) | 0.00 to 1.00 |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP WITH TZ | |

---

**Table: `raw_ingested_data`** — staging area

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| source_id | UUID | FK(data_sources.id), NOT NULL |
| raw_content | TEXT | HTML, JSON, CSV, etc. |
| content_hash | VARCHAR(64) | SHA-256 for change detection |
| ingested_at | TIMESTAMP WITH TZ | DEFAULT now() |
| processed | BOOLEAN | DEFAULT false |
| processing_result | JSONB | What was extracted, confidence, flags |

---

**Table: `offer_comparisons`**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| student_id | UUID | FK(student_profiles.id), NOT NULL |
| offer_ids | JSONB | Array of offer letter IDs |
| ai_analysis | JSONB | LLM comparison |
| created_at | TIMESTAMP WITH TZ | DEFAULT now() |

### models/__init__.py — Import All Models

```python
# Import all models so Alembic can detect them
from unipaith.models.base import Base
from unipaith.models.user import User
from unipaith.models.student import (
    StudentProfile, AcademicRecord, TestScore, Activity,
    StudentDocument, StudentPreference, OnboardingProgress,
)
from unipaith.models.institution import (
    Institution, Program, TargetSegment, Campaign, CampaignRecipient,
    Event, EventRSVP, Reviewer,
)
from unipaith.models.application import (
    HistoricalOutcome, Application, ApplicationChecklist,
    ApplicationSubmission, ReviewAssignment, Rubric,
    ApplicationScore, Interview, InterviewScore,
    OfferLetter, EnrollmentRecord,
)
from unipaith.models.engagement import (
    StudentEngagementSignal, SavedList, SavedListItem,
    StudentCalendar, CRMRecord, Conversation, Message,
    StudentResume, StudentEssay,
)
from unipaith.models.matching import (
    MatchResult, StudentFeature, InstitutionFeature,
    Embedding, PredictionLog, ModelRegistry,
    DataSource, RawIngestedData, OfferComparison,
)

__all__ = [
    "Base",
    "User",
    "StudentProfile", "AcademicRecord", "TestScore", "Activity",
    "StudentDocument", "StudentPreference", "OnboardingProgress",
    "Institution", "Program", "TargetSegment", "Campaign", "CampaignRecipient",
    "Event", "EventRSVP", "Reviewer",
    "HistoricalOutcome", "Application", "ApplicationChecklist",
    "ApplicationSubmission", "ReviewAssignment", "Rubric",
    "ApplicationScore", "Interview", "InterviewScore",
    "OfferLetter", "EnrollmentRecord",
    "StudentEngagementSignal", "SavedList", "SavedListItem",
    "StudentCalendar", "CRMRecord", "Conversation", "Message",
    "StudentResume", "StudentEssay",
    "MatchResult", "StudentFeature", "InstitutionFeature",
    "Embedding", "PredictionLog", "ModelRegistry",
    "DataSource", "RawIngestedData", "OfferComparison",
]
```

## After Code Generation

1. Run `alembic revision --autogenerate -m "create_all_tables"` to generate the migration
2. Run `alembic upgrade head` to apply it
3. Connect to the database and verify all tables exist:
   ```sql
   \dt
   ```
4. Verify pgvector extension is installed:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
5. Verify the HNSW index on embeddings was created

## Important Notes

- Use `JSONB` (not `JSON`) for all JSON columns — it's indexable and more performant in PostgreSQL
- Use `TIMESTAMP WITH TIME ZONE` for all timestamps (not naive timestamps)
- All foreign keys should have `ondelete="CASCADE"` where the child makes no sense without the parent (e.g., academic_records -> student_profiles), and `ondelete="SET NULL"` where the reference is optional
- Use `ARRAY` type for simple arrays (preferred_countries) and `JSONB` for structured arrays (career_goals with nested objects)
- Define all `relationship()` mappings on both sides with proper `back_populates`
- The `pgvector` column type is `Vector(768)` from the `pgvector` SQLAlchemy integration
