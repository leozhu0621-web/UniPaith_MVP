"""
Seed dev data for UniPaith backend.

Usage:
    python -m scripts.seed_dev_data          # seed (skip if already seeded)
    python -m scripts.seed_dev_data --reset   # truncate + re-seed
"""
import argparse
import asyncio
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import async_session, engine
from unipaith.models import Base
from unipaith.models.application import (
    Application,
    ApplicationChecklist,
    HistoricalOutcome,
)
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import (
    Institution,
    Program,
    Reviewer,
    School,
    TargetSegment,
)
from unipaith.models.student import (
    AcademicRecord,
    Activity,
    OnboardingProgress,
    StudentPreference,
    StudentProfile,
    TestScore,
)
from unipaith.models.user import User, UserRole


async def _already_seeded(db: AsyncSession) -> bool:
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none() is not None


async def _reset(db: AsyncSession) -> None:
    print("Resetting database ...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tables recreated.")


async def seed(db: AsyncSession) -> None:
    # ---- Student Users ----
    # cognito_sub must be a valid UUID so dev tokens (dev:<sub>:<role>) work
    student_users = [
        User(email="maria.santos@example.com", cognito_sub="aaaa0001-0000-0000-0000-000000000001", role=UserRole.student),
        User(email="wei.chen@example.com", cognito_sub="aaaa0002-0000-0000-0000-000000000002", role=UserRole.student),
        User(email="priya.sharma@example.com", cognito_sub="aaaa0003-0000-0000-0000-000000000003", role=UserRole.student),
        User(email="james.wilson@example.com", cognito_sub="aaaa0004-0000-0000-0000-000000000004", role=UserRole.student),
        User(email="fatima.alrashid@example.com", cognito_sub="aaaa0005-0000-0000-0000-000000000005", role=UserRole.student),
    ]
    db.add_all(student_users)
    await db.flush()
    print(f"  Created {len(student_users)} student users")

    # ---- Institution Admin Users ----
    admin_users = [
        User(email="admin@mit-demo.edu", cognito_sub="bbbb0001-0000-0000-0000-000000000001", role=UserRole.institution_admin),
        User(email="admin@uiuc-demo.edu", cognito_sub="bbbb0002-0000-0000-0000-000000000002", role=UserRole.institution_admin),
        User(email="admin@northeastern-demo.edu", cognito_sub="bbbb0003-0000-0000-0000-000000000003", role=UserRole.institution_admin),
    ]
    db.add_all(admin_users)
    await db.flush()

    # ---- Reviewer Users ----
    reviewer_users = [
        User(email="reviewer1@mit-demo.edu", cognito_sub="cccc0001-0000-0000-0000-000000000001", role=UserRole.institution_admin),
        User(email="reviewer2@uiuc-demo.edu", cognito_sub="cccc0002-0000-0000-0000-000000000002", role=UserRole.institution_admin),
    ]
    db.add_all(reviewer_users)
    await db.flush()
    print(f"  Created {len(admin_users)} admin + {len(reviewer_users)} reviewer users")

    # ---- Student Profiles ----
    profiles_data = [
        dict(user_id=student_users[0].id, first_name="Maria", last_name="Santos",
             nationality="Brazilian", country_of_residence="Brazil", date_of_birth=date(2002, 5, 14),
             bio_text="I'm a computer science student from São Paulo with a passion for using data to solve real-world problems. My research in NLP at USP's AI lab sparked my interest in pursuing advanced study in data science.",
             goals_text="I want to earn a masters in data science from a top US program, gain industry experience, and eventually work at the intersection of AI and healthcare."),
        dict(user_id=student_users[1].id, first_name="Wei", last_name="Chen",
             nationality="Chinese", country_of_residence="China", date_of_birth=date(1998, 11, 3),
             bio_text="Finance professional from Shanghai with 3 years at Deloitte. Looking to transition into strategic leadership through an MBA program.",
             goals_text="Earn an MBA from a top-ranked US or UK program and move into management consulting or corporate strategy."),
        dict(user_id=student_users[2].id, first_name="Priya", last_name="Sharma",
             nationality="Indian", country_of_residence="India", date_of_birth=date(2000, 7, 22),
             bio_text="Biomedical engineering researcher from IIT Bombay with published work in tissue engineering and drug delivery systems.",
             goals_text="Pursue a PhD in bioengineering at a top research university with full funding. Long-term goal: lead a research lab."),
        dict(user_id=student_users[3].id, first_name="James", last_name="Wilson",
             nationality="American", country_of_residence="United States", date_of_birth=date(2001, 3, 8),
             bio_text="Liberal arts graduate with AmeriCorps service experience. Passionate about education policy and social equity.",
             goals_text="Earn a masters in public policy with full scholarship. Work in education policy at the state or federal level."),
        dict(user_id=student_users[4].id, first_name="Fatima", last_name="Al-Rashid",
             nationality="Saudi Arabian", country_of_residence="Saudi Arabia", date_of_birth=date(2001, 9, 15),
             bio_text="Computer engineering graduate from KAUST with internship experience at Google. Interested in advancing AI/ML research.",
             goals_text="Masters in AI/ML at a top-ranked program. Government scholarship available. Career in AI research or tech leadership."),
    ]
    profiles = [StudentProfile(**d) for d in profiles_data]
    db.add_all(profiles)
    await db.flush()
    print(f"  Created {len(profiles)} student profiles")

    # ---- Academic Records ----
    academics = [
        AcademicRecord(student_id=profiles[0].id, institution_name="Universidade de São Paulo (USP)",
                       degree_type="bachelors", field_of_study="Computer Science",
                       gpa=Decimal("3.70"), gpa_scale="4.0",
                       start_date=date(2021, 2, 1), end_date=date(2024, 12, 15), country="Brazil"),
        AcademicRecord(student_id=profiles[1].id, institution_name="Fudan University",
                       degree_type="bachelors", field_of_study="Finance",
                       gpa=Decimal("3.60"), gpa_scale="4.0",
                       start_date=date(2016, 9, 1), end_date=date(2020, 6, 30), country="China"),
        AcademicRecord(student_id=profiles[2].id, institution_name="Indian Institute of Technology Bombay",
                       degree_type="bachelors", field_of_study="Biomedical Engineering",
                       gpa=Decimal("9.20"), gpa_scale="10.0",
                       start_date=date(2018, 7, 1), end_date=date(2022, 5, 30), country="India"),
        AcademicRecord(student_id=profiles[3].id, institution_name="Grinnell College",
                       degree_type="bachelors", field_of_study="Political Science",
                       gpa=Decimal("3.20"), gpa_scale="4.0",
                       start_date=date(2019, 8, 15), end_date=date(2023, 5, 20), country="United States"),
        AcademicRecord(student_id=profiles[4].id, institution_name="King Abdullah University of Science and Technology",
                       degree_type="bachelors", field_of_study="Computer Engineering",
                       gpa=Decimal("3.90"), gpa_scale="4.0",
                       start_date=date(2019, 9, 1), end_date=date(2023, 6, 15), country="Saudi Arabia"),
    ]
    db.add_all(academics)
    await db.flush()

    # ---- Test Scores ----
    scores = [
        TestScore(student_id=profiles[0].id, test_type="GRE", total_score=325,
                  section_scores={"verbal": 158, "quantitative": 167}, test_date=date(2024, 6, 15)),
        TestScore(student_id=profiles[0].id, test_type="TOEFL", total_score=105,
                  section_scores={"reading": 28, "listening": 26, "speaking": 24, "writing": 27}, test_date=date(2024, 5, 10)),
        TestScore(student_id=profiles[1].id, test_type="GMAT", total_score=720,
                  section_scores={"verbal": 38, "quantitative": 50, "integrated_reasoning": 7}, test_date=date(2024, 3, 20)),
        TestScore(student_id=profiles[1].id, test_type="IELTS", total_score=75,
                  section_scores={"listening": 8.0, "reading": 7.5, "writing": 7.0, "speaking": 7.5}, test_date=date(2024, 4, 5)),
        TestScore(student_id=profiles[2].id, test_type="GRE", total_score=332,
                  section_scores={"verbal": 162, "quantitative": 170}, test_date=date(2024, 2, 10)),
        TestScore(student_id=profiles[2].id, test_type="TOEFL", total_score=112,
                  section_scores={"reading": 29, "listening": 28, "speaking": 27, "writing": 28}, test_date=date(2024, 1, 20)),
        TestScore(student_id=profiles[4].id, test_type="GRE", total_score=328,
                  section_scores={"verbal": 160, "quantitative": 168}, test_date=date(2024, 7, 1)),
        TestScore(student_id=profiles[4].id, test_type="IELTS", total_score=80,
                  section_scores={"listening": 8.5, "reading": 8.0, "writing": 7.5, "speaking": 8.0}, test_date=date(2024, 6, 1)),
    ]
    db.add_all(scores)
    await db.flush()

    # ---- Activities ----
    acts = [
        Activity(student_id=profiles[0].id, activity_type="research", title="Research Assistant",
                 organization="USP AI Lab", description="NLP research on sentiment analysis for Portuguese text.",
                 start_date=date(2023, 3, 1), end_date=date(2024, 8, 1)),
        Activity(student_id=profiles[0].id, activity_type="work_experience", title="Data Science Intern",
                 organization="Nubank", description="Built ML models for credit risk assessment.",
                 start_date=date(2024, 1, 15), end_date=date(2024, 7, 15)),
        Activity(student_id=profiles[0].id, activity_type="extracurricular", title="Teaching Assistant",
                 organization="USP", description="TA for Intro to Programming course.",
                 start_date=date(2023, 2, 1), end_date=date(2023, 12, 15)),
        Activity(student_id=profiles[0].id, activity_type="awards", title="Hackathon Winner",
                 organization="HackBrazil 2023", description="First place in data science track."),
        Activity(student_id=profiles[1].id, activity_type="work_experience", title="Audit Associate",
                 organization="Deloitte Shanghai", description="Financial audit and advisory for Fortune 500 clients.",
                 start_date=date(2020, 7, 1), end_date=date(2023, 6, 30)),
        Activity(student_id=profiles[1].id, activity_type="leadership", title="VP Finance Club",
                 organization="Fudan University", description="Led 50-member finance club."),
        Activity(student_id=profiles[2].id, activity_type="research", title="Research Fellow",
                 organization="IIT Bombay Bioengineering Lab", description="Published 2 papers on drug delivery nanoparticles.",
                 start_date=date(2021, 6, 1), end_date=date(2022, 5, 30)),
        Activity(student_id=profiles[2].id, activity_type="publications", title="First-author publication",
                 organization="Journal of Biomedical Materials", description="Nanoparticle-based targeted drug delivery systems."),
        Activity(student_id=profiles[3].id, activity_type="volunteering", title="AmeriCorps Service Member",
                 organization="City Year", description="Served as tutor and mentor in underserved schools.",
                 start_date=date(2023, 8, 1), end_date=date(2024, 6, 30)),
        Activity(student_id=profiles[3].id, activity_type="extracurricular", title="Debate Team Captain",
                 organization="Grinnell College"),
        Activity(student_id=profiles[4].id, activity_type="work_experience", title="Software Engineering Intern",
                 organization="Google", description="Worked on TensorFlow model optimization.",
                 start_date=date(2023, 6, 1), end_date=date(2023, 9, 1)),
        Activity(student_id=profiles[4].id, activity_type="research", title="Undergraduate Researcher",
                 organization="KAUST AI Lab", description="Computer vision research for autonomous systems.",
                 start_date=date(2022, 1, 1), end_date=date(2023, 5, 30)),
    ]
    db.add_all(acts)
    await db.flush()

    # ---- Preferences ----
    prefs = [
        StudentPreference(student_id=profiles[0].id, preferred_countries=["United States"],
                          preferred_regions=["Northeast", "West Coast"], preferred_city_size="big_city",
                          budget_max=60000, funding_requirement="partial",
                          career_goals=["data scientist", "ml engineer", "research scientist"],
                          values_priorities={"ranking": 4, "location": 3, "cost": 5, "research": 4, "industry_connections": 5},
                          dealbreakers=["must_accept_toefl"]),
        StudentPreference(student_id=profiles[1].id, preferred_countries=["United States", "United Kingdom"],
                          preferred_city_size="big_city", budget_max=100000, funding_requirement="self_funded",
                          career_goals=["management consultant", "corporate strategist"],
                          values_priorities={"ranking": 5, "location": 4, "cost": 2, "alumni_network": 5}),
        StudentPreference(student_id=profiles[2].id, preferred_countries=["United States"],
                          preferred_city_size="college_town", funding_requirement="full_scholarship",
                          career_goals=["professor", "research scientist", "biotech founder"],
                          values_priorities={"ranking": 3, "research": 5, "faculty": 5, "funding": 5}),
        StudentPreference(student_id=profiles[3].id, preferred_countries=["United States"],
                          preferred_city_size="big_city", budget_max=30000, funding_requirement="full_scholarship",
                          career_goals=["policy analyst", "education director"],
                          values_priorities={"ranking": 2, "cost": 5, "location": 3, "practical_experience": 4}),
        StudentPreference(student_id=profiles[4].id, preferred_countries=["United States"],
                          preferred_regions=["West Coast", "Northeast"], preferred_city_size="big_city",
                          funding_requirement="flexible",
                          career_goals=["ai researcher", "tech lead", "startup founder"],
                          values_priorities={"ranking": 5, "research": 5, "location": 3, "industry_connections": 4}),
    ]
    db.add_all(prefs)
    await db.flush()

    # ---- Onboarding Progress ----
    onboarding = [
        OnboardingProgress(student_id=profiles[0].id, steps_completed=["account", "basic_profile", "academics", "test_scores", "activities", "bio", "goals", "preferences"], completion_percentage=100),
        OnboardingProgress(student_id=profiles[1].id, steps_completed=["account", "basic_profile", "academics", "test_scores", "activities", "bio", "goals", "preferences"], completion_percentage=100),
        OnboardingProgress(student_id=profiles[2].id, steps_completed=["account", "basic_profile", "academics", "test_scores", "activities", "bio", "goals", "preferences"], completion_percentage=100),
        OnboardingProgress(student_id=profiles[3].id, steps_completed=["account", "basic_profile", "academics", "activities"], completion_percentage=55),
        OnboardingProgress(student_id=profiles[4].id, steps_completed=["account", "basic_profile", "academics", "test_scores", "activities", "bio", "goals", "preferences"], completion_percentage=100),
    ]
    db.add_all(onboarding)
    await db.flush()
    print("  Created academics, test scores, activities, preferences, onboarding")

    # ---- Institutions ----
    # Structured fields (campus_setting, founded_year, support_services, policies,
    # international_info, school_outcomes) populate the Spec-12 School Detail page
    # Overview + About tabs with real editorial content.
    institutions = [
        Institution(admin_user_id=admin_users[0].id, name="Massachusetts Institute of Technology", type="university",
                    country="United States", region="Northeast", city="Cambridge",
                    campus_setting="urban", student_body_size=11858, founded_year=1861,
                    contact_email="admissions@mit.edu",
                    ranking_data={"qs": 1, "times_he": 5, "us_news": 2,
                                  "ownership_type": "private_nonprofit", "accreditor": "NECHE",
                                  "median_earnings": 124200, "graduation_rate": 0.96, "retention_rate": 0.99,
                                  "carnegie_classification": "Doctoral Universities: Very High Research Activity"},
                    description_text="MIT is a world-renowned research university known for innovation in science, engineering, and technology.",
                    campus_description="An urban campus along the Charles River in Cambridge, steps from Boston. Dense, walkable, and built around maker spaces, research labs, and a culture of hands-on problem solving.",
                    support_services={
                        "tutoring": {"name": "Tutoring & academic support", "url": "https://uaap.mit.edu"},
                        "career": {"name": "Career Advising & Professional Development", "url": "https://capd.mit.edu"},
                        "counseling": {"name": "Student Mental Health & Counseling"},
                        "disability": {"name": "Disability & Access Services"},
                    },
                    policies={
                        "transfer_credit": {"summary": "Transfer credit evaluated by department; AP and prior college coursework considered."},
                        "test_optional": {"summary": "Standardized tests required for first-year applicants."},
                    },
                    international_info={
                        "supported_visas": ["F-1", "J-1"],
                        "english_proficiency": {"summary": "TOEFL or IELTS required for non-native English speakers; minimum TOEFL iBT 100."},
                        "international_student_count": 3900,
                    },
                    school_outcomes={
                        "employed_or_continuing_ed": 0.94, "graduation_rate_6yr": 0.96,
                        "top_employer_industries": ["Technology", "Finance", "Consulting", "Research"]},
                    website_url="https://www.mit.edu", is_verified=True),
        Institution(admin_user_id=admin_users[1].id, name="University of Illinois Urbana-Champaign", type="university",
                    country="United States", region="Midwest", city="Champaign",
                    campus_setting="suburban", student_body_size=56607, founded_year=1867,
                    contact_email="admissions@illinois.edu",
                    ranking_data={"qs": 64, "times_he": 48, "us_news": 35,
                                  "ownership_type": "public", "accreditor": "HLC",
                                  "median_earnings": 78600, "graduation_rate": 0.85, "retention_rate": 0.93},
                    description_text="UIUC is a leading public research university with world-class engineering and computer science programs.",
                    campus_description="A classic Big Ten college town spanning the twin cities of Urbana and Champaign — large, green, and self-contained, with a quad at its heart.",
                    support_services={
                        "tutoring": {"name": "Academic Resources & Tutoring"},
                        "career": {"name": "The Career Center", "url": "https://careercenter.illinois.edu"},
                        "counseling": {"name": "Counseling Center"},
                        "financial_literacy": {"name": "Student Money Management Center"},
                    },
                    policies={
                        "transfer_credit": {"summary": "Generous transfer credit for accredited coursework and approved AP/IB scores."},
                        "test_optional": {"summary": "Test-optional for most first-year applicants."},
                    },
                    international_info={
                        "supported_visas": ["F-1", "J-1"],
                        "english_proficiency": {"summary": "TOEFL iBT 79+ or IELTS 6.5+ for graduate admission."},
                        "international_student_count": 10800,
                    },
                    school_outcomes={
                        "employed_or_continuing_ed": 0.91, "graduation_rate_6yr": 0.85,
                        "top_employer_industries": ["Engineering", "Technology", "Agriculture", "Finance"]},
                    website_url="https://www.illinois.edu", is_verified=True),
        Institution(admin_user_id=admin_users[2].id, name="Northeastern University", type="university",
                    country="United States", region="Northeast", city="Boston",
                    campus_setting="urban", student_body_size=30013, founded_year=1898,
                    contact_email="admissions@northeastern.edu",
                    ranking_data={"qs": 375, "times_he": 201, "us_news": 53,
                                  "ownership_type": "private_nonprofit", "accreditor": "NECHE",
                                  "median_earnings": 84300, "graduation_rate": 0.89, "retention_rate": 0.97},
                    description_text="Northeastern is known for its co-op program, integrating professional experience with academic study.",
                    campus_description="An urban campus in Boston's Fenway neighborhood, built around experiential learning and a signature co-op program that places students with employers worldwide.",
                    support_services={
                        "tutoring": {"name": "Peer Tutoring & Writing Center"},
                        "career": {"name": "Co-op & Career Design", "url": "https://careers.northeastern.edu"},
                        "counseling": {"name": "University Health & Counseling Services"},
                        "disability": {"name": "Disability Resource Center"},
                    },
                    policies={
                        "transfer_credit": {"summary": "Transfer credit and co-op experience recognized toward degree progress."},
                        "test_optional": {"summary": "Test-optional admissions policy."},
                    },
                    international_info={
                        "supported_visas": ["F-1", "J-1"],
                        "english_proficiency": {"summary": "TOEFL iBT 92+ or IELTS 6.5+; conditional pathways available."},
                        "international_student_count": 9400,
                        "scholarship_eligibility": "International students are considered for merit scholarships at the time of admission.",
                    },
                    school_outcomes={
                        "employed_or_continuing_ed": 0.93, "graduation_rate_6yr": 0.89,
                        "top_employer_industries": ["Technology", "Healthcare", "Finance", "Consulting"]},
                    website_url="https://www.northeastern.edu", is_verified=True),
    ]
    db.add_all(institutions)
    await db.flush()
    print(f"  Created {len(institutions)} institutions")

    # ---- Schools (within-institution units) ----
    # Gives the Spec-12 Schools tab (the default tab) real content to drill into.
    schools = [
        # MIT
        School(institution_id=institutions[0].id, name="Schwarzman College of Computing",
               description_text="MIT's hub for computer science, artificial intelligence, and data systems, connecting computing with every discipline.",
               sort_order=1),
        School(institution_id=institutions[0].id, name="Sloan School of Management",
               description_text="MIT's business school, pairing analytical rigor with entrepreneurship and innovation.",
               sort_order=2),
        # UIUC
        School(institution_id=institutions[1].id, name="Grainger College of Engineering",
               description_text="One of the top engineering colleges in the U.S., home to nationally ranked computer science and bioengineering programs.",
               sort_order=1),
        # Northeastern
        School(institution_id=institutions[2].id, name="Khoury College of Computer Sciences",
               description_text="The first college of computer science in the U.S., known for its co-op-integrated graduate programs.",
               sort_order=1),
        School(institution_id=institutions[2].id, name="School of Public Policy and Urban Affairs",
               description_text="Policy education grounded in experiential learning across government, nonprofits, and industry.",
               sort_order=2),
    ]
    db.add_all(schools)
    await db.flush()
    print(f"  Created {len(schools)} schools")

    # ---- Programs ----
    # school_id links each program to its within-institution School so the
    # Spec-12 Schools tab and school sub-page render the right program lists.
    programs = [
        # MIT — Schwarzman College of Computing
        Program(institution_id=institutions[0].id, school_id=schools[0].id, program_name="MS in Data Science", degree_type="masters",
                department="Institute for Data, Systems, and Society", duration_months=12, tuition=58000, delivery_format="in_person",
                acceptance_rate=Decimal("0.0800"), is_published=True, application_deadline=date(2026, 12, 15),
                description_text="Interdisciplinary program combining statistics, machine learning, and domain expertise.",
                who_its_for="Looking for strong quantitative backgrounds with research experience.",
                highlights=["Top-ranked data science program", "Access to MIT research labs", "Strong industry connections"],
                requirements={"min_gpa": 3.5, "gre_required": True, "toefl_min": 100}),
        Program(institution_id=institutions[0].id, school_id=schools[0].id, program_name="PhD in Computer Science", degree_type="phd",
                department="CSAIL", duration_months=60, tuition=0, delivery_format="in_person",
                acceptance_rate=Decimal("0.0500"), is_published=True, application_deadline=date(2026, 12, 1),
                description_text="Fully funded PhD in one of the world's top computer science research labs.",
                who_its_for="Seeking exceptional researchers in AI, systems, and theory.",
                highlights=["Full funding", "World-leading AI research", "Small cohort"],
                requirements={"min_gpa": 3.7, "gre_required": False, "publications_preferred": True}),
        # MIT — Sloan School of Management
        Program(institution_id=institutions[0].id, school_id=schools[1].id, program_name="MBA", degree_type="masters",
                department="Sloan School of Management", duration_months=24, tuition=82000, delivery_format="in_person",
                acceptance_rate=Decimal("0.1200"), is_published=True, application_deadline=date(2027, 1, 15),
                description_text="MIT Sloan MBA combines analytical rigor with entrepreneurial action.",
                highlights=["Innovation-focused", "Strong tech network", "Action learning"],
                requirements={"gmat_min": 700, "work_experience_years": 2}),
        # UIUC — Grainger College of Engineering
        Program(institution_id=institutions[1].id, school_id=schools[2].id, program_name="MS in Computer Science", degree_type="masters",
                department="Department of Computer Science", duration_months=24, tuition=38000, delivery_format="in_person",
                acceptance_rate=Decimal("0.1500"), is_published=True, application_deadline=date(2026, 12, 15),
                description_text="Flexible MS program with options for thesis or coursework.",
                highlights=["Top-5 CS department", "Research opportunities", "Affordable tuition"],
                requirements={"min_gpa": 3.2, "gre_required": True, "toefl_min": 96}),
        Program(institution_id=institutions[1].id, school_id=schools[2].id, program_name="MS in Data Science", degree_type="masters",
                department="Department of Statistics", duration_months=18, tuition=32000, delivery_format="hybrid",
                acceptance_rate=Decimal("0.2000"), is_published=True, application_deadline=date(2027, 1, 15),
                description_text="Applied data science program with industry partnerships.",
                highlights=["Industry capstone projects", "Growing alumni network", "Competitive tuition"],
                requirements={"min_gpa": 3.0, "gre_required": False}),
        Program(institution_id=institutions[1].id, school_id=schools[2].id, program_name="PhD in Bioengineering", degree_type="phd",
                department="Department of Bioengineering", duration_months=60, tuition=0, delivery_format="in_person",
                acceptance_rate=Decimal("0.1000"), is_published=True, application_deadline=date(2026, 12, 1),
                description_text="Interdisciplinary PhD at the intersection of biology and engineering.",
                highlights=["Full funding", "State-of-the-art facilities", "Collaborative culture"],
                requirements={"min_gpa": 3.5, "gre_required": True, "research_required": True}),
        # Northeastern — Khoury College of Computer Sciences
        Program(institution_id=institutions[2].id, school_id=schools[3].id, program_name="MS in Data Science (Co-op)", degree_type="masters",
                department="Khoury College of Computer Sciences", duration_months=24, tuition=55000, delivery_format="in_person",
                acceptance_rate=Decimal("0.2500"), is_published=True, application_deadline=date(2027, 2, 1),
                description_text="Data science MS with integrated co-op work experience at top companies.",
                highlights=["6-month co-op included", "Boston location", "Industry-ready curriculum"],
                requirements={"min_gpa": 3.0, "toefl_min": 90}),
        Program(institution_id=institutions[2].id, school_id=schools[3].id, program_name="MS in Computer Science (Co-op)", degree_type="masters",
                department="Khoury College of Computer Sciences", duration_months=24, tuition=55000, delivery_format="in_person",
                acceptance_rate=Decimal("0.2200"), is_published=True, application_deadline=date(2027, 2, 1),
                description_text="CS masters with co-op giving real industry experience.",
                highlights=["Co-op at Amazon, Google, Microsoft", "Flexible specializations"],
                requirements={"min_gpa": 3.0, "toefl_min": 90}),
        # Northeastern — School of Public Policy and Urban Affairs
        Program(institution_id=institutions[2].id, school_id=schools[4].id, program_name="MS in Public Policy", degree_type="masters",
                department="School of Public Policy and Urban Affairs", duration_months=24, tuition=48000, delivery_format="hybrid",
                acceptance_rate=Decimal("0.3500"), is_published=True, application_deadline=date(2027, 3, 1),
                description_text="Policy program with experiential learning in government and nonprofits.",
                highlights=["DC semester option", "Policy co-op", "Diverse cohort"],
                requirements={"min_gpa": 3.0, "gre_required": False}),
    ]
    db.add_all(programs)
    await db.flush()
    print(f"  Created {len(programs)} programs")

    # ---- Target Segments ----
    segments = [
        TargetSegment(institution_id=institutions[0].id, segment_name="High-achieving international STEM",
                      criteria={"gpa_min": 3.5, "field": "STEM", "international": True}),
        TargetSegment(institution_id=institutions[1].id, segment_name="Experienced professionals",
                      criteria={"work_experience_years_min": 2}),
        TargetSegment(institution_id=institutions[2].id, segment_name="Co-op interested students",
                      criteria={"values": ["industry_experience", "co_op"]}),
    ]
    db.add_all(segments)
    await db.flush()

    # ---- Reviewers ----
    reviewers = [
        Reviewer(institution_id=institutions[0].id, user_id=reviewer_users[0].id,
                 name="Dr. Sarah Chen", department="CSAIL",
                 specializations=["machine learning", "natural language processing"]),
        Reviewer(institution_id=institutions[1].id, user_id=reviewer_users[1].id,
                 name="Prof. Michael Brown", department="Bioengineering",
                 specializations=["tissue engineering", "biomaterials"]),
    ]
    db.add_all(reviewers)
    await db.flush()

    # ---- Historical Outcomes ----
    outcomes = []
    for prog_idx, prog in enumerate(programs[:6]):
        for year in [2024, 2025]:
            outcomes.append(HistoricalOutcome(
                program_id=prog.id, year=year, outcome="admitted", enrolled=True,
                applicant_profile_summary={"gpa": 3.8, "gre": 330, "research": True}))
            outcomes.append(HistoricalOutcome(
                program_id=prog.id, year=year, outcome="admitted", enrolled=False,
                applicant_profile_summary={"gpa": 3.7, "gre": 325, "research": True}))
            outcomes.append(HistoricalOutcome(
                program_id=prog.id, year=year, outcome="rejected",
                applicant_profile_summary={"gpa": 3.0, "gre": 300, "research": False}))
            if prog_idx % 2 == 0:
                outcomes.append(HistoricalOutcome(
                    program_id=prog.id, year=year, outcome="waitlisted",
                    applicant_profile_summary={"gpa": 3.4, "gre": 315, "research": True}))

    db.add_all(outcomes)
    await db.flush()
    print(f"  Created {len(outcomes)} historical outcomes")

    # ── Inbox (Spec 17) — application-threaded conversations + system notices ──
    demo = profiles[0]  # Maria Santos
    mit, uiuc = institutions[0], institutions[1]
    prog_mit, prog_uiuc = programs[0], programs[3]

    app_mit = Application(student_id=demo.id, program_id=prog_mit.id, status="in_progress")
    app_uiuc = Application(student_id=demo.id, program_id=prog_uiuc.id, status="submitted")
    db.add_all([app_mit, app_uiuc])
    await db.flush()

    # A checklist for the MIT app so the inbox "Mark complete" has a real item
    # to flip (recommendation_letters).
    db.add(
        ApplicationChecklist(
            student_id=demo.id,
            program_id=prog_mit.id,
            items=[
                {"name": "Personal Information", "category": "personal_info", "required": True, "completed": True, "description": "Full name, nationality, residence."},
                {"name": "Recommendation Letters", "category": "recommendation_letters", "required": True, "completed": False, "description": "2 recommendation letter(s) required."},
                {"name": "Statement of Purpose", "category": "essays", "required": True, "completed": False, "description": "A statement of purpose."},
            ],
            manual_overrides={},
            completion_percentage=33,
        )
    )

    now = datetime.now(timezone.utc)

    def _thread(**kw) -> Conversation:
        return Conversation(student_id=demo.id, status="active", started_at=now, last_message_at=now, **kw)

    t_reply = _thread(institution_id=mit.id, program_id=prog_mit.id, application_id=app_mit.id, thread_type="human", subject="Your second recommender", action_label="needs_reply", waiting_on="student", due_date=now + timedelta(days=5), linked_checklist_item_category="recommendation_letters")
    t_doc = _thread(institution_id=None, program_id=prog_mit.id, application_id=app_mit.id, thread_type="system", subject="Missing item: official transcript", action_label="document_requested", waiting_on="student", due_date=now + timedelta(days=10), linked_checklist_item_category="documents")
    t_interview = _thread(institution_id=uiuc.id, program_id=prog_uiuc.id, application_id=app_uiuc.id, thread_type="human", subject="Interview invitation", action_label="interview_invite", waiting_on="student", due_date=now + timedelta(days=8))
    t_clarify = _thread(institution_id=uiuc.id, program_id=prog_uiuc.id, application_id=app_uiuc.id, thread_type="human", subject="Quick question about your background", action_label="clarification_required", waiting_on="student", due_date=now + timedelta(days=3))
    t_status = _thread(institution_id=None, program_id=prog_mit.id, application_id=app_mit.id, thread_type="system", subject="Your match scores updated", action_label="status_update_only", waiting_on="none")
    t_done = _thread(institution_id=uiuc.id, program_id=prog_uiuc.id, application_id=app_uiuc.id, thread_type="human", subject="Application received", action_label="completed", waiting_on="none")
    threads = [t_reply, t_doc, t_interview, t_clarify, t_status, t_done]
    db.add_all(threads)
    await db.flush()

    def _msg(conv: Conversation, sender_type: str, body: str, *, sender_id=None, mins_ago: int = 0) -> Message:
        return Message(conversation_id=conv.id, sender_type=sender_type, sender_id=sender_id, message_body=body, status="sent", sent_at=now - timedelta(minutes=mins_ago))

    db.add_all([
        _msg(t_reply, "admissions_officer", "Hi Maria, please send a clarification by Wednesday about your second recommender. We spoke yesterday but didn't receive the form.", sender_id=mit.admin_user_id, mins_ago=120),
        _msg(t_doc, "system", "We're still missing your official transcript. Upload it to complete your application.", mins_ago=200),
        _msg(t_interview, "admissions_officer", "We'd like to invite you to an interview. Please pick a time that works for you.", sender_id=uiuc.admin_user_id, mins_ago=60),
        _msg(t_clarify, "admissions_officer", "Quick question: could you tell us more about your tissue-engineering research at IIT Bombay?", sender_id=uiuc.admin_user_id, mins_ago=90),
        _msg(t_status, "system", "Your match scores updated after your recent profile edit. Two new programs entered your Target band.", mins_ago=30),
        _msg(t_done, "admissions_officer", "Thank you — we've received your complete application and it's now under review.", sender_id=uiuc.admin_user_id, mins_ago=1440),
    ])

    # Calendar deadlines linked to threads via reference_id (so inbox
    # "Mark complete" sets completed_at on the matching entry).
    db.add_all([
        StudentCalendar(student_id=demo.id, entry_type="inbox_deadline", reference_id=t_reply.id, title="Recommender clarification due — MIT", start_time=now + timedelta(days=5)),
        StudentCalendar(student_id=demo.id, entry_type="interview", reference_id=t_interview.id, title="Interview — UIUC MS CS", start_time=now + timedelta(days=8)),
    ])
    await db.flush()
    print(f"  Created 2 applications, {len(threads)} inbox threads, checklist + calendar links")

    await db.commit()
    print("\nSeed data complete!")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    async with async_session() as db:
        if args.reset:
            await _reset(db)

        if await _already_seeded(db):
            print("Database already seeded. Use --reset to re-seed.")
            return

        print("Seeding dev data ...")
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
