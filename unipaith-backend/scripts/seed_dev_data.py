"""
Seed dev data for UniPaith backend.

Usage:
    python -m scripts.seed_dev_data          # seed (skip if already seeded)
    python -m scripts.seed_dev_data --reset   # truncate + re-seed
"""
import argparse
import asyncio
import sys
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import async_session, engine
from unipaith.models import Base
from unipaith.models.application import HistoricalOutcome
from unipaith.models.institution import (
    Institution,
    Program,
    Reviewer,
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
    institutions = [
        Institution(admin_user_id=admin_users[0].id, name="Massachusetts Institute of Technology", type="university",
                    country="United States", region="Northeast", city="Cambridge",
                    ranking_data={"qs": 1, "times_he": 5, "us_news": 2},
                    description_text="MIT is a world-renowned research university known for innovation in science, engineering, and technology.",
                    website_url="https://www.mit.edu", is_verified=True),
        Institution(admin_user_id=admin_users[1].id, name="University of Illinois Urbana-Champaign", type="university",
                    country="United States", region="Midwest", city="Champaign",
                    ranking_data={"qs": 64, "times_he": 48, "us_news": 35},
                    description_text="UIUC is a leading public research university with world-class engineering and computer science programs.",
                    website_url="https://www.illinois.edu", is_verified=True),
        Institution(admin_user_id=admin_users[2].id, name="Northeastern University", type="university",
                    country="United States", region="Northeast", city="Boston",
                    ranking_data={"qs": 375, "times_he": 201, "us_news": 53},
                    description_text="Northeastern is known for its co-op program, integrating professional experience with academic study.",
                    website_url="https://www.northeastern.edu", is_verified=True),
    ]
    db.add_all(institutions)
    await db.flush()
    print(f"  Created {len(institutions)} institutions")

    # ---- Programs ----
    programs = [
        # MIT
        Program(institution_id=institutions[0].id, program_name="MS in Data Science", degree_type="masters",
                department="Institute for Data, Systems, and Society", duration_months=12, tuition=58000,
                acceptance_rate=Decimal("0.0800"), is_published=True, application_deadline=date(2026, 12, 15),
                description_text="Interdisciplinary program combining statistics, machine learning, and domain expertise.",
                who_its_for="Looking for strong quantitative backgrounds with research experience.",
                highlights=["Top-ranked data science program", "Access to MIT research labs", "Strong industry connections"],
                requirements={"min_gpa": 3.5, "gre_required": True, "toefl_min": 100}),
        Program(institution_id=institutions[0].id, program_name="PhD in Computer Science", degree_type="phd",
                department="CSAIL", duration_months=60, tuition=0,
                acceptance_rate=Decimal("0.0500"), is_published=True, application_deadline=date(2026, 12, 1),
                description_text="Fully funded PhD in one of the world's top computer science research labs.",
                who_its_for="Seeking exceptional researchers in AI, systems, and theory.",
                highlights=["Full funding", "World-leading AI research", "Small cohort"],
                requirements={"min_gpa": 3.7, "gre_required": False, "publications_preferred": True}),
        Program(institution_id=institutions[0].id, program_name="MBA", degree_type="masters",
                department="Sloan School of Management", duration_months=24, tuition=82000,
                acceptance_rate=Decimal("0.1200"), is_published=True, application_deadline=date(2027, 1, 15),
                description_text="MIT Sloan MBA combines analytical rigor with entrepreneurial action.",
                highlights=["Innovation-focused", "Strong tech network", "Action learning"],
                requirements={"gmat_min": 700, "work_experience_years": 2}),
        # UIUC
        Program(institution_id=institutions[1].id, program_name="MS in Computer Science", degree_type="masters",
                department="Department of Computer Science", duration_months=24, tuition=38000,
                acceptance_rate=Decimal("0.1500"), is_published=True, application_deadline=date(2026, 12, 15),
                description_text="Flexible MS program with options for thesis or coursework.",
                highlights=["Top-5 CS department", "Research opportunities", "Affordable tuition"],
                requirements={"min_gpa": 3.2, "gre_required": True, "toefl_min": 96}),
        Program(institution_id=institutions[1].id, program_name="MS in Data Science", degree_type="masters",
                department="Department of Statistics", duration_months=18, tuition=32000,
                acceptance_rate=Decimal("0.2000"), is_published=True, application_deadline=date(2027, 1, 15),
                description_text="Applied data science program with industry partnerships.",
                highlights=["Industry capstone projects", "Growing alumni network", "Competitive tuition"],
                requirements={"min_gpa": 3.0, "gre_required": False}),
        Program(institution_id=institutions[1].id, program_name="PhD in Bioengineering", degree_type="phd",
                department="Department of Bioengineering", duration_months=60, tuition=0,
                acceptance_rate=Decimal("0.1000"), is_published=True, application_deadline=date(2026, 12, 1),
                description_text="Interdisciplinary PhD at the intersection of biology and engineering.",
                highlights=["Full funding", "State-of-the-art facilities", "Collaborative culture"],
                requirements={"min_gpa": 3.5, "gre_required": True, "research_required": True}),
        # Northeastern
        Program(institution_id=institutions[2].id, program_name="MS in Data Science (Co-op)", degree_type="masters",
                department="Khoury College of Computer Sciences", duration_months=24, tuition=55000,
                acceptance_rate=Decimal("0.2500"), is_published=True, application_deadline=date(2027, 2, 1),
                description_text="Data science MS with integrated co-op work experience at top companies.",
                highlights=["6-month co-op included", "Boston location", "Industry-ready curriculum"],
                requirements={"min_gpa": 3.0, "toefl_min": 90}),
        Program(institution_id=institutions[2].id, program_name="MS in Computer Science (Co-op)", degree_type="masters",
                department="Khoury College of Computer Sciences", duration_months=24, tuition=55000,
                acceptance_rate=Decimal("0.2200"), is_published=True, application_deadline=date(2027, 2, 1),
                description_text="CS masters with co-op giving real industry experience.",
                highlights=["Co-op at Amazon, Google, Microsoft", "Flexible specializations"],
                requirements={"min_gpa": 3.0, "toefl_min": 90}),
        Program(institution_id=institutions[2].id, program_name="MS in Public Policy", degree_type="masters",
                department="School of Public Policy and Urban Affairs", duration_months=24, tuition=48000,
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
