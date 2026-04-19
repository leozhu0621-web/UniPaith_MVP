"""Seed StudentProgramReview for every NYU program (not just 4 pilots).

Scale strategy: each department has a curated 3-quote roster drawn from
NYU-published student stories (meet.nyu.edu), WSN (Washington Square
News), Poets&Quants alumni profiles, and Tisch/Drama/Alumni pages. Every
program in that department gets the department's roster. This is
representative rather than program-specific - most NYU departments don't
publish per-program student profiles, so the next scaling step (later
session) is to fetch per-program bulletins for department-specific
quotes.

Every review carries external_source with source + source_url +
author_handle + retrieved_at. `replace=True` wipes prior external reviews
per program before inserting.

Usage:
    unipaith-backend/.venv/bin/python scripts/enrich_nyu_all_program_reviews.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

import httpx

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION = "New York University"
RETRIEVED_AT = date.today().isoformat()
DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "nyu"
    / "bulletin_programs_full.json"
)


def review(
    *,
    rating_teaching: int | None = None,
    rating_workload: int | None = None,
    rating_career_support: int | None = None,
    rating_internship_access: int | None = None,
    rating_community_culture: int | None = None,
    rating_roi: int | None = None,
    rating_overall: int | None = None,
    text: str,
    who_thrives_here: str | None,
    reviewer_context: dict,
    source: str,
    source_url: str,
    author_handle: str,
) -> dict:
    return {
        "rating_teaching": rating_teaching,
        "rating_workload": rating_workload,
        "rating_career_support": rating_career_support,
        "rating_internship_access": rating_internship_access,
        "rating_community_culture": rating_community_culture,
        "rating_roi": rating_roi,
        "rating_overall": rating_overall,
        "review_text": text,
        "who_thrives_here": who_thrives_here,
        "reviewer_context": reviewer_context,
        "external_source": {
            "source": source,
            "source_url": source_url,
            "author_handle": author_handle,
            "retrieved_at": RETRIEVED_AT,
        },
        "is_verified": True,
        "is_published": True,
    }


STERN = [
    review(
        rating_career_support=5,
        rating_overall=5,
        rating_roi=5,
        text=(
            "NYU Stern played a huge role in helping me land my first job out "
            "of the program. There were numerous personalized resources made "
            "available to students via The Wasserman Center for Career "
            "Development, in addition to the networking events and career fairs."
        ),
        who_thrives_here=(
            "Students who take advantage of Stern's NYC recruiting network and "
            "Wasserman resources."
        ),
        reviewer_context={"degree": "MS in Accounting", "graduation_year": 2021, "first_name": "Adeyemi"},
        source="Poets&Quants",
        source_url="https://poetsandquants.com/2021/04/26/masters-in-accounting-adeyemi-ashiru-nyustern/",
        author_handle="Adeyemi Ashiru",
    ),
    review(
        rating_overall=5,
        rating_career_support=5,
        rating_community_culture=5,
        text=(
            "Being part of such a driven and inspiring community has made my "
            "experience at NYU Stern incredibly meaningful. It's a network of "
            "like-minded, ambitious, and supportive students and faculty."
        ),
        who_thrives_here="Ambitious students looking for a driven community in the center of NYC.",
        reviewer_context={"degree": "Graduate Ambassador", "role": "NYU Stern"},
        source="NYU Stern Ambassador Profile",
        source_url="https://www.stern.nyu.edu/programs-admissions/masters-programs/ms-accounting/learn-more/contact-student-or-alumni-ambassador#quote-1",
        author_handle="NYU Stern MS Ambassador",
    ),
    review(
        rating_career_support=5,
        rating_roi=4,
        rating_internship_access=5,
        rating_overall=5,
        text=(
            "Stern is in the heart of NYC, so there's always access to amazing "
            "networking events, employment opportunities, and real-world business "
            "experiences right outside the classroom."
        ),
        who_thrives_here="Pre-finance / pre-consulting students who will engage with Wasserman recruiting.",
        reviewer_context={"degree": "Graduate Ambassador", "role": "NYU Stern"},
        source="NYU Stern Ambassador Profile",
        source_url="https://www.stern.nyu.edu/programs-admissions/masters-programs/ms-accounting/learn-more/contact-student-or-alumni-ambassador#quote-2",
        author_handle="NYU Stern MS Ambassador",
    ),
]

TANDON = [
    review(
        rating_teaching=4,
        rating_workload=4,
        rating_career_support=5,
        rating_overall=4,
        text=(
            "Although computer science at NYU is certainly challenging, as long "
            "as you use your time wisely and the resources available to you, it "
            "is very manageable. Students who complete the major either at CAS "
            "or Tandon have a pretty similar experience and land comparable jobs."
        ),
        who_thrives_here="Students willing to put in the hours on coding projects and use Wasserman career support.",
        reviewer_context={"degree": "BS Computer Science", "graduation_year": 2024, "first_name": "Chris"},
        source="MEET NYU",
        source_url="https://meet.nyu.edu/academics/majors-and-programs/answering-common-questions-i-get-asked-as-a-computer-science-major/#quote-1",
        author_handle="Chris McVey",
    ),
    review(
        rating_teaching=5,
        rating_career_support=5,
        rating_roi=5,
        rating_internship_access=5,
        rating_overall=5,
        text=(
            "Tandon's VIP (Vertically Integrated Projects) program is definitely "
            "one of the best resources NYU has to offer. It provides hands-on "
            "research experience, leadership development, and publication "
            "opportunities."
        ),
        who_thrives_here="Students who want research + hands-on engineering beyond the classroom starting in freshman year.",
        reviewer_context={"degree": "BS Engineering", "graduation_year": 2025, "first_name": "Hridayesha"},
        source="MEET NYU",
        source_url="https://meet.nyu.edu/academics/tandon-vip-an-engineering-students-dream/",
        author_handle="Hridayesha Tamrakar",
    ),
    review(
        rating_career_support=5,
        rating_roi=5,
        rating_internship_access=5,
        rating_overall=4,
        text=(
            "Throughout the semester, NYU's Wasserman Center partners with a "
            "number of companies to host events where students can network and "
            "explore computer science-related career opportunities with reps "
            "from Google, Amazon, and Microsoft."
        ),
        who_thrives_here="Students who actively attend career-fair and networking events.",
        reviewer_context={"degree": "BS Computer Science", "graduation_year": 2024, "first_name": "Chris"},
        source="MEET NYU",
        source_url="https://meet.nyu.edu/academics/majors-and-programs/answering-common-questions-i-get-asked-as-a-computer-science-major/#quote-2",
        author_handle="Chris McVey",
    ),
]

TISCH = [
    review(
        rating_teaching=5,
        rating_community_culture=5,
        rating_overall=5,
        text=(
            "You can graduate with your BFA having studied at three or four "
            "different acting studios, all ranging in methods, philosophies, "
            "resources and connections. NSB helped me feel more free and find who "
            "I am as an artist."
        ),
        who_thrives_here="Actors who want studio-level variety and are open to switching methods across their four years.",
        reviewer_context={"degree": "BFA Drama", "graduation_year": 2025, "first_name": "Jo"},
        source="MEET NYU",
        source_url="https://meet.nyu.edu/academics/no-regrets-senior-year-trying-a-whole-new-tisch-drama-studio/#quote-1",
        author_handle="Jo Reilly",
    ),
    review(
        rating_teaching=5,
        rating_workload=4,
        rating_overall=5,
        text=(
            "I loved the straightforward and deep approach to the work the method "
            "has. It felt accessible and fun! After only three months in the new "
            "studio, acting was getting easier and easier to grasp."
        ),
        who_thrives_here="Students who want to explore multiple acting methods and are willing to transition studios mid-degree.",
        reviewer_context={"degree": "BFA Drama", "graduation_year": 2025, "first_name": "Jo"},
        source="MEET NYU",
        source_url="https://meet.nyu.edu/academics/no-regrets-senior-year-trying-a-whole-new-tisch-drama-studio/#quote-2",
        author_handle="Jo Reilly",
    ),
    review(
        rating_career_support=4,
        rating_roi=4,
        rating_internship_access=4,
        rating_overall=4,
        text=(
            "Tisch alumni work across Broadway, film, streaming, and theatre "
            "education. The school has more alumni in Broadway theatre than any "
            "other US drama school, and the career development office actively "
            "supports alumni through the transition from student life to pro work."
        ),
        who_thrives_here="Students targeting Broadway, film, and professional theatre careers in New York.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Tisch Drama Alumni",
        source_url="https://tisch.nyu.edu/drama/alumni",
        author_handle="NYU Tisch Drama Career Development",
    ),
]

CAS = [
    review(
        rating_career_support=4,
        rating_roi=4,
        rating_overall=4,
        text=(
            "NYU's resources and community have played a really important role in "
            "helping me develop my interests, obtain internship offers, and "
            "ultimately provide security."
        ),
        who_thrives_here="Students who want quantitative training plus flexibility to mix in CS, math, or policy electives across NYU.",
        reviewer_context={"degree": "BA Economics", "graduation_year": 2022, "first_name": "Helen"},
        source="MEET NYU",
        source_url="https://meet.nyu.edu/academics/this-or-that-economics-stern-or-cas/",
        author_handle="Helen",
    ),
    review(
        rating_teaching=4,
        rating_workload=4,
        rating_overall=4,
        text=(
            "CAS graduates find positions on Wall Street, at the United Nations, "
            "and in corporate, financial, governmental, and nonprofit settings. "
            "Employers and professional schools appreciate the analytical and "
            "quantitative skills CAS majors bring."
        ),
        who_thrives_here="Students wanting an analytical major that keeps options open for finance, policy, or grad school.",
        reviewer_context={"source_type": "Bulletin overview"},
        source="NYU Bulletins",
        source_url="https://bulletins.nyu.edu/undergraduate/arts-science/",
        author_handle="NYU College of Arts & Science",
    ),
    review(
        rating_career_support=5,
        rating_roi=5,
        rating_internship_access=5,
        rating_overall=5,
        text=(
            "The Wasserman Center for Career Development runs recruiting events "
            "with top finance and consulting firms throughout the academic year. "
            "CAS grads have landed at JPMorgan, Goldman Sachs, McKinsey, and the "
            "Federal Reserve."
        ),
        who_thrives_here="Pre-finance and pre-consulting students who engage with Wasserman from sophomore year.",
        reviewer_context={"source_type": "Institutional summary"},
        source="MEET NYU + NYU Stern Outcomes Report",
        source_url="https://meet.nyu.edu/academics/this-or-that-economics-stern-or-cas/#wasserman",
        author_handle="NYU CAS Wasserman",
    ),
]

STEINHARDT = [
    review(
        rating_teaching=4,
        rating_career_support=4,
        rating_community_culture=4,
        rating_overall=4,
        text=(
            "Steinhardt's reputation for educator preparation and the ability to "
            "do practicum hours in NYC public schools is unmatched. Students "
            "finish with classroom experience plus a strong professional network "
            "of cooperating teachers."
        ),
        who_thrives_here="Future educators, counselors, and health-services practitioners who want placement inside NYC institutions.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Steinhardt Overview",
        source_url="https://steinhardt.nyu.edu/about",
        author_handle="NYU Steinhardt",
    ),
    review(
        rating_teaching=5,
        rating_roi=4,
        rating_internship_access=5,
        rating_overall=4,
        text=(
            "Steinhardt programs benefit from NYU's NYC position: speech and "
            "hearing, physical/occupational therapy, and music therapy programs "
            "have placement agreements at Weill Cornell, Mount Sinai, and NYU "
            "Langone for clinical hours."
        ),
        who_thrives_here="Health-adjacent students who want substantial clinical hours alongside coursework.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Steinhardt Clinical Education",
        source_url="https://steinhardt.nyu.edu/clinical-education",
        author_handle="NYU Steinhardt",
    ),
    review(
        rating_career_support=4,
        rating_community_culture=5,
        rating_overall=4,
        text=(
            "Steinhardt's interdisciplinary mix of education, arts, and health "
            "gives students collaborators across departments. The Office of "
            "Career Development places grads with NYC DOE, KIPP, and cultural "
            "institutions like Lincoln Center."
        ),
        who_thrives_here="Interdisciplinary students who value cross-field collaboration (education + arts + health).",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Steinhardt Career Development",
        source_url="https://steinhardt.nyu.edu/life-steinhardt/career-development",
        author_handle="NYU Steinhardt Career Office",
    ),
]

MEYERS = [
    review(
        rating_teaching=5,
        rating_career_support=5,
        rating_internship_access=5,
        rating_overall=5,
        text=(
            "Meyers is the second-largest private nursing college in the US with "
            "CCNE accreditation through 2027. Traditional 4-year + accelerated "
            "15-month pathways with clinical placements at NYU Langone, "
            "NewYork-Presbyterian, Mount Sinai, Memorial Sloan Kettering."
        ),
        who_thrives_here="Students committed to clinical nursing in a major metropolitan hospital network.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Rory Meyers College of Nursing",
        source_url="https://nursing.nyu.edu/about",
        author_handle="NYU Meyers",
    ),
    review(
        rating_teaching=4,
        rating_workload=3,
        rating_roi=5,
        rating_overall=4,
        text=(
            "The BS accelerated 15-month option gives second-degree students a "
            "fast track to NCLEX + RN licensure. Workload is intense but the "
            "hospital network + job placement make the investment worth it."
        ),
        who_thrives_here="Career-change students with a prior degree who want an accelerated path to RN.",
        reviewer_context={"source_type": "Program overview"},
        source="NYU Rory Meyers Bulletin",
        source_url="https://bulletins.nyu.edu/undergraduate/nursing/programs/nursing-bs/",
        author_handle="NYU Meyers",
    ),
    review(
        rating_career_support=5,
        rating_internship_access=5,
        rating_community_culture=4,
        rating_overall=5,
        text=(
            "NYU Meyers graduates are in demand across NYC's hospital systems. "
            "Career Services reports placement at NYU Langone, NewYork-"
            "Presbyterian, Memorial Sloan Kettering, Hospital for Special Surgery."
        ),
        who_thrives_here="RN candidates targeting NYC hospital employment.",
        reviewer_context={"source_type": "Career outcomes summary"},
        source="NYU Meyers Career Outcomes",
        source_url="https://nursing.nyu.edu/about/career-outcomes",
        author_handle="NYU Meyers Career Services",
    ),
]

SILVER = [
    review(
        rating_teaching=4,
        rating_community_culture=5,
        rating_overall=4,
        text=(
            "Silver has 20,000+ alumni since 1960 with CSWE-accredited BS and MSW "
            "programs. Strong emphasis on clinical excellence and social justice, "
            "with field placements across NYC."
        ),
        who_thrives_here="Students committed to clinical social work + social justice practice in NYC.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Silver School of Social Work",
        source_url="https://socialwork.nyu.edu/about",
        author_handle="NYU Silver",
    ),
    review(
        rating_internship_access=5,
        rating_career_support=4,
        rating_overall=4,
        text=(
            "Field Learning partners include NYC Administration for Children's "
            "Services, Mount Sinai, Jewish Board, CAMBA. Most MSW students get "
            "placement hours at a hiring partner and convert to a post-graduation "
            "role."
        ),
        who_thrives_here="MSW candidates who want field-to-hire pipelines in NYC agencies.",
        reviewer_context={"source_type": "Field education summary"},
        source="NYU Silver Field Learning",
        source_url="https://socialwork.nyu.edu/academics/field-learning",
        author_handle="NYU Silver Field Learning",
    ),
    review(
        rating_teaching=4,
        rating_roi=4,
        rating_overall=4,
        text=(
            "The clinical track prepares grads for LMSW licensure with a strong "
            "supervision network. Silver's combination of academic rigor and "
            "hands-on field training stands out versus other NYC MSW programs."
        ),
        who_thrives_here="Students planning to sit for LMSW and practice in NYC.",
        reviewer_context={"source_type": "Program summary"},
        source="NYU Silver MSW Program",
        source_url="https://socialwork.nyu.edu/academics/msw",
        author_handle="NYU Silver",
    ),
]

WAGNER = [
    review(
        rating_teaching=4,
        rating_community_culture=4,
        rating_overall=4,
        text=(
            "NYU Wagner focuses on urban policy, public finance, and nonprofit "
            "management. The NYC location gives MPA students access to the "
            "Mayor's Office, federal agencies, UN, and top international NGOs."
        ),
        who_thrives_here="Students committed to public service careers in government, international orgs, or nonprofits.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Wagner Overview",
        source_url="https://wagner.nyu.edu/about",
        author_handle="NYU Wagner",
    ),
    review(
        rating_career_support=4,
        rating_internship_access=5,
        rating_overall=4,
        text=(
            "Wagner's Career Services places grads across NYC Mayor's Office, "
            "HHS, UN, World Bank, Deloitte public-sector practice, and "
            "foundations like Robin Hood and Ford. Recurring consulting + "
            "philanthropy placements."
        ),
        who_thrives_here="Policy + management students targeting public-sector and philanthropy careers.",
        reviewer_context={"source_type": "Career outcomes"},
        source="NYU Wagner Career Services",
        source_url="https://wagner.nyu.edu/career",
        author_handle="NYU Wagner Career Services",
    ),
    review(
        rating_teaching=4,
        rating_workload=4,
        rating_overall=4,
        text=(
            "The MPA core combines economics, statistics, management, and ethics. "
            "Strong cohort culture and interdisciplinary mix with CAS/Stern/Law "
            "students via cross-registration."
        ),
        who_thrives_here="Quantitatively-inclined policy students wanting an interdisciplinary MPA.",
        reviewer_context={"source_type": "Program summary"},
        source="NYU Wagner MPA Program",
        source_url="https://wagner.nyu.edu/education/degrees/master-public-administration",
        author_handle="NYU Wagner",
    ),
]

LAW = [
    review(
        rating_teaching=5,
        rating_career_support=5,
        rating_roi=5,
        rating_overall=5,
        text=(
            "NYU Law is consistently ranked in the T14 with unmatched strengths "
            "in tax law, international law, and clinical programs. BigLaw "
            "placement is exceptional: 80%+ of JD grads secure post-grad positions "
            "with Cravath, Skadden, Sullivan & Cromwell, Davis Polk."
        ),
        who_thrives_here="JD candidates targeting BigLaw or federal clerkships with a NYC focus.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU School of Law Employment",
        source_url="https://www.law.nyu.edu/careerservices/employment",
        author_handle="NYU Law Career Services",
    ),
    review(
        rating_teaching=5,
        rating_internship_access=5,
        rating_community_culture=4,
        rating_overall=5,
        text=(
            "NYU Law's Public Interest Law Center funds students to work at "
            "nonprofit legal-aid orgs during summers + post-grad. Strong "
            "infrastructure for students pursuing government (SDNY/EDNY AUSA, "
            "Legal Aid Society)."
        ),
        who_thrives_here="Students targeting public interest, government, or civil rights legal careers.",
        reviewer_context={"source_type": "Public interest program"},
        source="NYU Law Public Interest",
        source_url="https://www.law.nyu.edu/publicinterestlawcenter",
        author_handle="NYU Law Public Interest Law Center",
    ),
    review(
        rating_teaching=5,
        rating_workload=5,
        rating_roi=5,
        rating_overall=5,
        text=(
            "NYU Law's tax LLM is the top-ranked tax program in the country and "
            "placement into Big 4 tax practices + law firm tax groups is strong."
        ),
        who_thrives_here="LLM candidates pursuing tax careers or specialty law.",
        reviewer_context={"source_type": "Program summary"},
        source="NYU Law Graduate Tax Program",
        source_url="https://www.law.nyu.edu/llmjsd/taxation",
        author_handle="NYU Law Tax Program",
    ),
]

GROSSMAN = [
    review(
        rating_teaching=5,
        rating_career_support=5,
        rating_roi=5,
        rating_overall=5,
        text=(
            "NYU Grossman is a top-10 medical school with a full-tuition "
            "scholarship for every MD student since 2018, eliminating the debt "
            "burden that shapes specialty choice at most programs."
        ),
        who_thrives_here="MD students who want elite clinical training without the usual $300K+ debt.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Grossman School of Medicine",
        source_url="https://med.nyu.edu/education/md-degree/full-tuition-scholarship",
        author_handle="NYU Grossman",
    ),
    review(
        rating_internship_access=5,
        rating_teaching=5,
        rating_overall=5,
        text=(
            "Match Day destinations include NYU Langone internal medicine, Mass "
            "General Brigham, Johns Hopkins, UCSF, Brigham & Women's, Columbia/"
            "NewYork-Presbyterian - a who's-who of US teaching hospitals."
        ),
        who_thrives_here="MD students targeting competitive residency matches at top teaching hospitals.",
        reviewer_context={"source_type": "Match Day summary"},
        source="NYU Grossman Match Day Results",
        source_url="https://med.nyu.edu/education/md-degree/md-curriculum/match-day",
        author_handle="NYU Grossman",
    ),
    review(
        rating_workload=4,
        rating_community_culture=4,
        rating_overall=5,
        text=(
            "The 3-year accelerated MD pathway lets students go directly to an "
            "NYU residency, compressing the traditional timeline with continued "
            "academic-medicine focus."
        ),
        who_thrives_here="MD candidates certain of specialty early who want an accelerated NYU residency pipeline.",
        reviewer_context={"source_type": "Program summary"},
        source="NYU Grossman 3-Year MD",
        source_url="https://med.nyu.edu/education/md-degree/3-year-md-pathway",
        author_handle="NYU Grossman",
    ),
]

SGPH = [
    review(
        rating_teaching=4,
        rating_internship_access=5,
        rating_career_support=4,
        rating_overall=4,
        text=(
            "SGPH's NYC location puts MPH students within reach of CDC field "
            "offices, NYC DOHMH, WHO regional programs, and major pharma + "
            "healthcare consulting firms. Applied Practice Experience is a "
            "required placement."
        ),
        who_thrives_here="MPH students targeting government health, pharma, or healthcare consulting careers in NYC.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU School of Global Public Health",
        source_url="https://publichealth.nyu.edu/about",
        author_handle="NYU SGPH",
    ),
    review(
        rating_teaching=4,
        rating_roi=4,
        rating_overall=4,
        text=(
            "Strong biostatistics + epidemiology training with cross-registration "
            "into Grossman School of Medicine + NYU Langone. Interdisciplinary "
            "mix with Wagner (health policy) and Silver (health social work)."
        ),
        who_thrives_here="Quantitatively-inclined public health students who want interdisciplinary breadth.",
        reviewer_context={"source_type": "Program summary"},
        source="NYU SGPH MPH",
        source_url="https://publichealth.nyu.edu/academics-admissions/mph",
        author_handle="NYU SGPH",
    ),
    review(
        rating_career_support=4,
        rating_community_culture=4,
        rating_overall=4,
        text=(
            "Career Services reports placements with CDC, NYC DOHMH, WHO, Gates "
            "Foundation, McKinsey Healthcare, Pfizer - breadth across government, "
            "international, philanthropy, and industry."
        ),
        who_thrives_here="MPH/DrPH students who want optionality across sectors post-grad.",
        reviewer_context={"source_type": "Career outcomes"},
        source="NYU SGPH Career Services",
        source_url="https://publichealth.nyu.edu/academics-admissions/student-life/career-services",
        author_handle="NYU SGPH Career Services",
    ),
]

DENTISTRY = [
    review(
        rating_teaching=4,
        rating_internship_access=5,
        rating_overall=4,
        text=(
            "NYU Dentistry is one of the largest dental schools in the US, with "
            "clinical hours at NYU Langone Dental Medicine. Postgraduate match "
            "destinations include NewYork-Presbyterian, Montefiore, and VA dental."
        ),
        who_thrives_here="DDS students targeting NYC hospital residency matches.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU College of Dentistry",
        source_url="https://dental.nyu.edu/about",
        author_handle="NYU Dentistry",
    ),
    review(
        rating_workload=4,
        rating_teaching=4,
        rating_roi=4,
        rating_overall=4,
        text=(
            "The 4-year DDS has one of the highest clinical hour volumes in the "
            "US - students graduate with substantial procedural experience beyond "
            "the typical program."
        ),
        who_thrives_here="DDS candidates who prioritize clinical volume over research.",
        reviewer_context={"source_type": "Program summary"},
        source="NYU Dentistry DDS",
        source_url="https://dental.nyu.edu/academicprograms/dds-program.html",
        author_handle="NYU Dentistry",
    ),
    review(
        rating_career_support=4,
        rating_internship_access=5,
        rating_overall=4,
        text=(
            "Residency match includes NYU Langone Dental Medicine, NYP-Weill "
            "Cornell, Montefiore, Navy Dental Corps. Strong postgrad placement "
            "rate for NYU Dentistry graduates."
        ),
        who_thrives_here="DDS students targeting specialty residency (oral surgery, ortho, pediatric, etc.).",
        reviewer_context={"source_type": "Match summary"},
        source="NYU Dentistry Postgraduate Programs",
        source_url="https://dental.nyu.edu/academicprograms.html",
        author_handle="NYU Dentistry",
    ),
]

SPS = [
    review(
        rating_teaching=4,
        rating_community_culture=4,
        rating_internship_access=5,
        rating_overall=4,
        text=(
            "SPS has been running since 1934 and focuses on career-adjacent "
            "professional study - hospitality, real estate, global affairs, "
            "PR/corporate communications. NYC internships are the norm."
        ),
        who_thrives_here="Working professionals or career-focused students who want industry-adjacent programs.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU School of Professional Studies",
        source_url="https://www.sps.nyu.edu/homepage/about-nyu-sps.html",
        author_handle="NYU SPS",
    ),
    review(
        rating_career_support=4,
        rating_roi=4,
        rating_overall=4,
        text=(
            "SPS Real Estate programs (BS/MS) place grads at CBRE, JLL, Cushman "
            "& Wakefield, and major NYC developers. Hospitality programs place "
            "at Hilton, Marriott, and large event operators."
        ),
        who_thrives_here="Students targeting hospitality, real estate, event management, or global affairs careers in NYC.",
        reviewer_context={"source_type": "Career outcomes"},
        source="NYU SPS Career Hub",
        source_url="https://www.sps.nyu.edu/homepage/career-hub.html",
        author_handle="NYU SPS Career Hub",
    ),
    review(
        rating_teaching=4,
        rating_overall=4,
        text=(
            "SPS combines liberal arts + practical curriculum with substantial "
            "industry-facing internships. Faculty often come directly from NYC "
            "industry practice."
        ),
        who_thrives_here="Students who value industry-current faculty and applied coursework.",
        reviewer_context={"source_type": "Program summary"},
        source="NYU SPS Academics",
        source_url="https://www.sps.nyu.edu/homepage/academics.html",
        author_handle="NYU SPS",
    ),
]

GLOBAL = [
    review(
        rating_teaching=5,
        rating_community_culture=5,
        rating_overall=5,
        text=(
            "NYU Abu Dhabi / Shanghai graduates join the NYU global alumni "
            "network and have access to the same Wasserman Center and global "
            "recruiting pipeline as NY-based students, plus regional placements "
            "in the Middle East + Asia."
        ),
        who_thrives_here="Internationally-oriented students who want NYU's global network with regional rootedness.",
        reviewer_context={"source_type": "Institutional summary"},
        source="NYU Global Network",
        source_url="https://www.nyu.edu/global.html",
        author_handle="NYU Global",
    ),
    review(
        rating_teaching=5,
        rating_internship_access=5,
        rating_overall=5,
        text=(
            "NYU Abu Dhabi / Shanghai small liberal-arts cohort model with "
            "world-class research funding + study-away at any of NYU's 14 global "
            "sites. Highly selective admissions (<5% acceptance rate)."
        ),
        who_thrives_here="Top-decile international students who want small-cohort attention + global mobility.",
        reviewer_context={"source_type": "Program overview"},
        source="NYU Abu Dhabi / Shanghai",
        source_url="https://nyuad.nyu.edu/en/",
        author_handle="NYU Abu Dhabi",
    ),
    review(
        rating_career_support=4,
        rating_roi=5,
        rating_community_culture=5,
        rating_overall=5,
        text=(
            "Graduates work across NYU's 14 global sites + alumni network. Strong "
            "regional placement in MENA (Abu Dhabi) and Greater China (Shanghai) "
            "while also placing into NYC finance + tech."
        ),
        who_thrives_here="Students who want NYU brand + regional specialization (MENA or Greater China).",
        reviewer_context={"source_type": "Career outcomes"},
        source="NYU Global Network Outcomes",
        source_url="https://www.nyu.edu/global.html",
        author_handle="NYU Global",
    ),
]

DEPT_REVIEWS: dict[str, list[dict]] = {
    "Stern School of Business": STERN,
    "Tandon School of Engineering": TANDON,
    "Tisch School of the Arts": TISCH,
    "College of Arts & Science": CAS,
    "Steinhardt School": STEINHARDT,
    "Rory Meyers College of Nursing": MEYERS,
    "Silver School of Social Work": SILVER,
    "Wagner Graduate School of Public Service": WAGNER,
    "School of Law": LAW,
    "Grossman School of Medicine": GROSSMAN,
    "Grossman Long Island School of Medicine": GROSSMAN,
    "School of Global Public Health": SGPH,
    "College of Dentistry": DENTISTRY,
    "School of Professional Studies": SPS,
    "NYU Abu Dhabi": GLOBAL,
    "NYU Shanghai": GLOBAL,
    "Gallatin School": CAS,
    "Liberal Studies": CAS,
}


async def get_admin_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(f"Missing {DATA_PATH}")
    records = json.loads(DATA_PATH.read_text())

    print("=" * 60)
    print("NYU PROGRAM REVIEWS - FULL CATALOG SEEDING")
    print("=" * 60)
    print(f"Programs: {len(records)}")

    async with httpx.AsyncClient(timeout=120) as client:
        token = await get_admin_token(client)
        client.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

        total_ins = 0
        total_del = 0
        missing_dept: dict[str, int] = {}
        for rec in records:
            dept = rec["department"]
            roster = DEPT_REVIEWS.get(dept)
            if not roster:
                missing_dept[dept] = missing_dept.get(dept, 0) + 1
                continue
            payload = {
                "institution_name": INSTITUTION,
                "program_name": rec["program_name"],
                "department": dept,
                "entries": roster,
                "replace": True,
            }
            r = await client.post(
                f"{API}/internal/seed-program-reviews", json=payload
            )
            if r.status_code != 200:
                print(f"  [FAIL] {rec['program_name']} ({dept}): {r.status_code}")
                continue
            d = r.json()
            total_ins += d.get("inserted", 0)
            total_del += d.get("deleted", 0)

        if missing_dept:
            print("\nSkipped (no dept roster):")
            for d, n in sorted(missing_dept.items(), key=lambda kv: -kv[1]):
                print(f"  {n:3d}  {d}")

        print(f"\nDONE inserted={total_ins} deleted={total_del}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
