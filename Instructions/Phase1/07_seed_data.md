# Task 07: Seed Data & Dev Bootstrap

## Context

You are completing Phase 1 of the **UniPaith** backend. Tasks 01-06 built the full foundation — schema, auth, CRUD endpoints, document upload. Now create realistic seed data so the system is demo-ready and developers can test against meaningful data.

## What to Build

### 1. scripts/seed_dev_data.py — Main Seed Script

An async Python script that populates the database with representative data for development and demos. Run it with:

```bash
python -m scripts.seed_dev_data
```

The script should:
1. Check if data already exists (idempotent — skip if already seeded)
2. Create data in dependency order
3. Print progress as it goes
4. Be re-runnable (truncate + re-seed option via `--reset` flag)

### 2. Seed Data Specification

#### Users (10 total)

**5 Student users:**

| Name | Email | Nationality | Background |
|------|-------|-------------|------------|
| Maria Santos | maria.santos@example.com | Brazilian | CS undergrad from USP, wants US masters in Data Science. Strong GPA (3.7/4.0), GRE 325, TOEFL 105. Research experience in NLP. Budget-conscious, needs partial scholarship. |
| Wei Chen | wei.chen@example.com | Chinese | Finance major from Fudan, wants MBA in US or UK. GMAT 720, IELTS 7.5. 3 years work experience at Deloitte Shanghai. Flexible budget, values ranking highly. |
| Priya Sharma | priya.sharma@example.com | Indian | Biomedical engineering from IIT Bombay. Wants PhD in bioengineering. GRE 332, TOEFL 112. Published 2 papers. Needs full funding (PhD). Strong research profile. |
| James Wilson | james.wilson@example.com | American | Liberal arts from small college. 3.2 GPA. Wants masters in public policy. No GRE yet. AmeriCorps experience. Budget is primary concern — needs full scholarship. |
| Fatima Al-Rashid | fatima.alrashid@example.com | Saudi Arabian | Computer engineering from KAUST. Wants masters in AI/ML. GRE 328, IELTS 8.0. Internship at Google. Government scholarship available, prefers top-ranked programs. |

**3 Institution admin users:**

| Name | Institution |
|------|-------------|
| admin@mit-demo.edu | MIT (top research university) |
| admin@uiuc-demo.edu | UIUC (large public research university) |
| admin@northeastern-demo.edu | Northeastern (co-op focused) |

**2 Reviewer users** (linked to institutions):
- reviewer1@mit-demo.edu → MIT
- reviewer2@uiuc-demo.edu → UIUC

#### Student Profiles (5)

For each student, create:
- Full `student_profiles` record with bio_text and goals_text
- 1-3 `academic_records` (vary by background)
- 1-3 `test_scores` (appropriate for their target)
- 2-5 `activities` (mix of work, research, extracurricular)
- `student_preferences` (realistic for their situation)
- `onboarding_progress` (most at 80-100%, one at 50%)

**Example — Maria Santos:**
```python
# Profile
bio_text = "I'm a computer science student from São Paulo with a passion for using data to solve real-world problems. My research in NLP at USP's AI lab sparked my interest in pursuing advanced study in data science. I want to bridge the gap between academic research and practical applications, especially in healthcare and sustainability."

goals_text = "I want to earn a masters in data science or machine learning from a top US program, gain industry experience through internships or co-ops, and eventually work at the intersection of AI and healthcare. Long-term, I'd like to return to Brazil and contribute to the growing tech ecosystem."

# Academic Record
institution_name = "Universidade de São Paulo (USP)"
degree_type = "bachelors"
field_of_study = "Computer Science"
gpa = 3.7
gpa_scale = "4.0"
start_date = "2021-02-01"
end_date = "2024-12-15"
country = "Brazil"

# Test Scores
[GRE: total 325, {"verbal": 158, "quantitative": 167}],
[TOEFL: total 105, {"reading": 28, "listening": 26, "speaking": 24, "writing": 27}]

# Activities
- Research Assistant, USP AI Lab, NLP research, 2023-2024
- Data Science Intern, Nubank, 2024 summer
- Teaching Assistant, Intro to Programming, USP, 2023
- Hackathon Winner, HackBrazil 2023

# Preferences
preferred_countries = ["United States"]
preferred_regions = ["Northeast", "West Coast"]
preferred_city_size = "big_city"
budget_max = 60000
funding_requirement = "partial"
career_goals = ["data scientist", "ml engineer", "research scientist"]
values_priorities = {"ranking": 4, "location": 3, "cost": 5, "research": 4, "industry_connections": 5}
dealbreakers = ["must_accept_toefl"]
```

Create similarly detailed and realistic profiles for all 5 students. Each should have a distinct story, different strengths, and different priorities.

#### Institutions (3)

**MIT:**
```python
name = "Massachusetts Institute of Technology"
type = "university"
country = "United States"
region = "Northeast"
city = "Cambridge"
ranking_data = {"qs": 1, "times_he": 5, "us_news": 2}
description_text = "MIT is a world-renowned research university..."
```

**UIUC:**
```python
name = "University of Illinois Urbana-Champaign"
type = "university"
country = "United States"
region = "Midwest"
city = "Champaign"
ranking_data = {"qs": 64, "times_he": 48, "us_news": 35}
```

**Northeastern:**
```python
name = "Northeastern University"
type = "university"
country = "United States"
region = "Northeast"
city = "Boston"
ranking_data = {"qs": 375, "times_he": 201, "us_news": 53}
```

#### Programs (8-10 across institutions)

Create realistic programs. Examples:

**MIT programs:**
- MS in Data Science (IDSS) — tuition $58,000, 12 months, acceptance rate 8%
- PhD in Computer Science (CSAIL) — tuition $0 (funded), 60 months, acceptance rate 5%
- MBA (Sloan) — tuition $82,000, 24 months, acceptance rate 12%

**UIUC programs:**
- MS in Computer Science — tuition $38,000, 24 months, acceptance rate 15%
- MS in Data Science — tuition $32,000, 18 months, acceptance rate 20%
- PhD in Bioengineering — tuition $0 (funded), 60 months, acceptance rate 10%

**Northeastern programs:**
- MS in Data Science (with co-op) — tuition $55,000, 24 months, acceptance rate 25%
- MS in Computer Science (with co-op) — tuition $55,000, 24 months, acceptance rate 22%
- MS in Public Policy — tuition $48,000, 24 months, acceptance rate 35%

Each program should have:
- Realistic `requirements` JSON (min GPA, test requirements, etc.)
- `description_text` (2-3 sentences)
- `current_preferences_text` (what the program is looking for this cycle)
- `highlights` (3-5 selling points)
- `application_deadline` (set in the future, e.g., December 2026 or January 2027)
- `is_published = true`

#### Target Segments (3-5)

Create segments for institutions, e.g.:
- MIT: "High-achieving international STEM" — criteria: gpa_min 3.5, field STEM, international
- UIUC: "Experienced professionals" — criteria: work_experience_years >= 2
- Northeastern: "Co-op interested" — criteria: values co-op/industry experience

#### Historical Outcomes (20-30)

Create realistic historical admission outcomes for the programs. These will be used by the ML engine in Phase 2. Vary by:
- Admitted students (strong profiles)
- Rejected students (weaker profiles or mismatches)
- Waitlisted students (borderline)
- Mix of enrolled=True/False for admitted students

#### Reviewers (2)

Link to MIT and UIUC institutions with specializations.

### 3. Data Consistency

Ensure:
- All foreign keys are valid
- User IDs match between users table and student_profiles/institutions
- Programs reference valid institutions
- Historical outcomes reference valid programs
- Onboarding completion percentages match actual data presence
- All Cognito-related fields (cognito_sub) use placeholder values for dev (e.g., "dev-sub-maria-santos")

### 4. Alembic Seed Migration (Optional)

Alternatively (or additionally), create a seed data Alembic migration that can be applied:
```bash
alembic revision -m "seed_dev_data"
```
This approach makes seeding part of the migration chain, which is useful for CI/CD.

### 5. Tests — test_seed.py

- Run seed script → verify expected record counts
- Verify all relationships load correctly (no broken FKs)
- Verify onboarding percentages match actual data
- Verify published programs appear in public search
- Run seed script twice → verify idempotent (no duplicates)

### 6. scripts/reset_dev.py — Dev Reset Script

Quick script that:
1. Drops all tables
2. Runs all migrations
3. Runs seed script

```bash
python -m scripts.reset_dev
```

Useful when schema changes and you need a clean slate.

## Verification — Phase 1 Complete Checklist

After this task, verify the entire Phase 1 works end-to-end:

1. **Infrastructure:** `docker-compose up -d` starts PostgreSQL + pgvector
2. **Migrations:** `alembic upgrade head` creates all tables
3. **Seed:** `python -m scripts.seed_dev_data` populates data
4. **Server:** `uvicorn unipaith.main:app --reload` starts without errors
5. **Health:** `GET /api/v1/health` → 200
6. **Auth:** `POST /api/v1/auth/login` with dev bypass → token returned
7. **Student profile:** `GET /api/v1/students/me/profile` → full nested profile
8. **Student CRUD:** Create/update/delete academic record → works
9. **Onboarding:** `GET /api/v1/students/me/onboarding` → correct percentage
10. **Programs search:** `GET /api/v1/programs?q=data+science` → published programs
11. **Institution admin:** `GET /api/v1/institutions/me/programs` → program list
12. **Document upload:** `POST /api/v1/students/me/documents/request-upload` → presigned URL
13. **Tests:** `pytest` → all pass

If all 13 checks pass, **Phase 1: Foundation is complete.** The system has:
- Working auth with role-based access
- Full student profile management with adaptive onboarding
- Institution and program management with publishing flow
- Document upload via S3
- Realistic seed data for demo
- Test coverage across all endpoints

**Next: Phase 2 (AI Core)** — GPU setup, LLM serving, feature extraction, embedding generation, and the matching pipeline.

## Important Notes

- Seed data should be realistic enough for demos but clearly fake (use example.com emails)
- Use the COGNITO_BYPASS=true mode for all seed data (dev tokens, not real Cognito)
- The historical outcomes data is crucial — Phase 2's ML engine trains on this
- Keep the seed script maintainable — use helper functions, not a giant monolith
- Consider using factory-boy for test data generation patterns
