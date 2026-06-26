"""Harvard University — matcher-core ``cip_code`` + program-DISTINCT ``who_its_for``.

REPAIR_BACKLOG #1 (``cip_code`` STARVATION) + #4b (``who_its_for`` TYPE-GAMING),
SKILL miss #2 (matcher-core fields) + miss #8 (universal depth field).

The base ``harvard_profile`` catalog (228 real, field-specific, structurally-clean
programs) shipped two matcher fields wrong:

  * ``cip_code`` was NEVER stamped onto ``Program.cip_code`` — every program shipped
    null, so the CPEF matcher scored all 228 field-blind. The IPEDS Field-of-Study
    breadth rows already carry their verified CIP in the spec; only the 46 hand-curated
    flagship/professional rows lacked one. ``CIP_BY_SLUG`` supplies the verified NCES
    CIP family for each of those 46 (the canonical taxonomy code for the field — the
    matcher resolves the 2-digit family, so no code is invented; omit-never-guess).

  * ``who_its_for`` was filled but TYPE-GAMED: every breadth row fell through to one
    ``_WHO_BY_TYPE`` template per degree type, so a Government Ph.D. and a Physics Ph.D.
    read identically (distinct/total ≈ 0.13). This module composes a field-specific,
    program-DISTINCT statement: ``WHO_BY_FIELD[field]`` (the subject + the applicant it
    fits, derived strictly from the program's own field — no fabricated facts, numbers,
    rankings, or named centers) followed by ``LEVEL_TAIL[degree_type]`` (the
    credential-appropriate readiness / next step), so a bachelor's survey, an academic
    master's, and a funded research doctorate of the SAME field read differently. The
    award-named professional rows (J.D., M.D., MBA, …) carry a complete hand-written
    ``_WHO_BY_SLUG`` statement instead (their field part is the degree name, not a
    composable field). Result: distinct/total ≈ 1.0, matching the field-specific gold
    bar (Brown / Emory / Purdue / Rice / Cornell).
"""

from __future__ import annotations

# ruff: noqa: E501

# ---------------------------------------------------------------------------
# CIP_BY_SLUG — verified NCES CIP family for the 46 hand-curated flagship /
# professional rows whose field is not in the IPEDS Field-of-Study breadth set.
# Each is the canonical CIP code for that field of study (the matcher reads the
# 2-digit family via field_canon). Sourced from the NCES IPEDS CIP 2020 taxonomy
# — the same authority the breadth rows draw their codes from. Never a guess.
# ---------------------------------------------------------------------------
CIP_BY_SLUG: dict[str, str] = {
    # Faculty of Arts & Sciences — College (A.B.) + GSAS (Ph.D.)
    "harvard-government-ab": "45.10",  # Political Science and Government
    "harvard-government-phd": "45.10",
    "harvard-social-studies-ab": "45.01",  # Social Sciences, General (interdisciplinary)
    "harvard-english-ab": "23.01",  # English Language and Literature, General
    "harvard-english-phd": "23.01",
    "harvard-history-literature-ab": "24.01",  # Liberal Arts & Humanities (interdisciplinary)
    "harvard-art-history-ab": "50.07",  # Art History, Criticism and Conservation
    "harvard-psychology-ab": "42.01",  # Psychology, General
    "harvard-psychology-phd": "42.01",
    "harvard-mcb-ab": "26.04",  # Cell/Cellular and Molecular Biology
    "harvard-mcb-phd": "26.04",
    "harvard-neuroscience-ab": "26.15",  # Neurobiology and Neurosciences
    "harvard-eps-ab": "40.06",  # Geological and Earth Sciences/Geosciences
    # SEAS — engineering (S.B. + Ph.D.)
    "harvard-electrical-eng-sb": "14.10",  # Electrical, Electronics and Communications Engineering
    "harvard-bioengineering-sb": "14.05",  # Biomedical/Medical Engineering
    "harvard-bioengineering-phd": "14.05",
    "harvard-environmental-eng-sb": "14.14",  # Environmental/Environmental Health Engineering
    "harvard-applied-physics-phd": "14.12",  # Engineering Physics/Applied Physics
    "harvard-data-science-sm": "30.70",  # Data Science
    "harvard-cse-sm": "30.30",  # Computational Science
    # Harvard Business School
    "harvard-mba": "52.02",  # Business Administration, Management and Operations
    "harvard-business-phd": "52.02",
    # Harvard Law School
    "harvard-jd": "22.01",  # Law
    "harvard-llm": "22.02",  # Legal Research and Advanced Professional Studies
    "harvard-law-sjd": "22.02",
    # Harvard Medical School / HSDM
    "harvard-md": "51.12",  # Medicine
    "harvard-biomedical-phd": "26.01",  # Biomedical Sciences, General
    "harvard-dmd": "51.04",  # Dentistry
    # Harvard Chan School of Public Health
    "harvard-mph": "51.22",  # Public Health
    "harvard-public-health-phd": "51.22",  # Population Health Sciences
    # Harvard Kennedy School
    "harvard-mpp": "44.05",  # Public Policy Analysis
    "harvard-mpa": "44.04",  # Public Administration
    "harvard-mpa-id": "44.05",  # Public Policy (international development)
    "harvard-public-policy-phd": "44.05",
    # Harvard Graduate School of Education
    "harvard-edm": "13.01",  # Education, General
    "harvard-edld": "13.04",  # Educational Administration and Supervision
    "harvard-education-phd": "13.01",
    # Harvard Graduate School of Design
    "harvard-march": "04.02",  # Architecture
    "harvard-mla": "04.06",  # Landscape Architecture
    "harvard-mup": "04.03",  # City/Urban, Community, and Regional Planning
    "harvard-mdes": "04.04",  # Environmental Design
    # Harvard Divinity School
    "harvard-mdiv": "39.06",  # Theological and Ministerial Studies
    "harvard-mts": "39.06",
    # Harvard Division of Continuing Education
    "harvard-alm": "24.01",  # Liberal Arts and Sciences/Liberal Studies
    # HarvardX certificates
    "harvard-cs50-cert": "11.07",  # Computer Science
    "harvard-data-science-cert": "30.70",  # Data Science
}


# ---------------------------------------------------------------------------
# WHO_BY_FIELD — the field-specific lead: the subject and the applicant it fits
# (background / interest), written from the catalog field name alone, with no
# fabricated facts. Keyed on the field portion of each program_name
# (``_field_from_program_name`` in harvard_profile). LEVEL_TAIL adds the
# credential-appropriate next step.
# ---------------------------------------------------------------------------
WHO_BY_FIELD: dict[str, str] = {
    # ── reused field statements (shared CIP field titles) ──
    "Anthropology": "Students drawn to human cultures, societies, and our biological and historical past",
    "Applied Mathematics": "Students who want to use mathematical modeling and computation to solve real scientific and engineering problems",
    "Archeology": "Students fascinated by past societies and how material remains reveal how people lived",
    "Architectural Sciences and Technology": "Students drawn to the technical side of building — structures, environmental systems, and the science of how buildings perform",
    "Architecture": "Students who want to design buildings and shape the built environment through studio practice, history, and technology",
    "Astronomy and Astrophysics": "Students fascinated by stars, galaxies, planets, and the physics of the universe",
    "Chemistry": "Students drawn to matter and its transformations, from synthesis to spectroscopy and reaction mechanisms",
    "Classics": "Students drawn to the languages, literature, and civilizations of ancient Greece and Rome",
    "Computer Science": "Students drawn to algorithms, systems, and software who want rigorous training in how computation works",
    "Design and Applied Arts": "Students who want to design objects, environments, and experiences across applied-arts media",
    "Economics": "Students who want to understand how people, markets, and institutions allocate scarce resources",
    "Engineering Physics": "Students who want to apply deep physics and mathematics to engineering problems at the frontier of technology",
    "English": "Students who love literature and writing and want to read closely, think critically, and argue in prose",
    "Environmental Design": "Students focused on designing sustainable, human-centered environments across architecture, landscape, and planning",
    "Fine and Studio Arts": "Students committed to making art and developing a studio practice across media",
    "Genetics": "Students focused on heredity, genomes, and how genes shape development, health, and variation",
    "Historic Preservation and Conservation": "Students committed to conserving historic places, buildings, and cultural heritage",
    "History": "Students who want to understand the past and how it shapes the present through evidence and argument",
    "International Agriculture": "Students focused on food security, rural development, and agriculture in a global and comparative context",
    "Landscape Architecture": "Students who want to design landscapes, parks, and public spaces that balance ecology and human use",
    "Law": "Students pursuing advanced legal scholarship and research at the doctoral level",
    "Linguistics": "Students drawn to the structure of language — its sounds, grammar, meaning, and how languages compare",
    "Mathematics": "Students who love mathematical reasoning, proof, and abstraction across pure and applied areas",
    "Mechanical Engineering": "Students drawn to mechanical systems, thermodynamics, and design across energy, robotics, and manufacturing",
    "Medieval and Renaissance Studies": "Students drawn to the literature, history, art, and thought of the medieval and early-modern world",
    "Music": "Students committed to music as performers, composers, and scholars",
    "Philosophy": "Students drawn to fundamental questions of knowledge, ethics, mind, and reality and to rigorous argument",
    "Physics": "Students drawn to the fundamental laws of nature, from particles and fields to matter and energy",
    "Political Science and Government": "Students drawn to government, politics, and how power and institutions shape collective life",
    "Psychology": "Students fascinated by mind and behavior who want to study how people think, feel, and act",
    "Public Health": "Students committed to protecting and improving the health of populations through prevention and policy",
    "Public Policy Analysis": "Students who want to analyze, design, and evaluate policy to solve public problems",
    "Sociology": "Students who want to understand social structure, inequality, and how groups and institutions shape behavior",
    "Statistics": "Students drawn to inference and uncertainty who want to design studies and draw conclusions from data",
    "Sustainability Studies": "Students focused on balancing environmental, social, and economic needs for a sustainable future",
    # ── authored field statements (Harvard-specific field names) ──
    "African and African American Studies": "Students drawn to the histories, cultures, politics, and creative expression of Africa and the African diaspora",
    "Applied Physics": "Students who want to apply the principles of physics to devices, materials, and technologies in an engineering setting",
    "Applied Statistics": "Students who want to use statistical methods and data analysis to answer applied questions across science and policy",
    "Behavioral Sciences": "Students drawn to the scientific study of human behavior across psychology, cognition, and social context",
    "Bioengineering": "Students at the interface of engineering and the life sciences who want to design devices, diagnostics, and therapies",
    "Bioethics": "Students drawn to the ethical, legal, and policy questions raised by medicine, biomedical research, and biotechnology",
    "Biological Sciences (Molecular & Cellular Biology)": "Students fascinated by the molecules and cellular machinery that drive life, from genes and proteins to cells",
    "Biomedical Sciences": "Students drawn to the mechanisms of human health and disease who want to pursue research at the lab bench",
    "Biotechnology": "Students who want to translate molecular and cellular biology into therapies, diagnostics, and bioproducts",
    "Business Administration": "Students who want rigorous training in management, strategy, finance, and how organizations create value",
    "CS50: Computer Science (HarvardX Certificate)": "Learners new to computing who want a rigorous introduction to programming, algorithms, and computer science",
    "Celtic Languages and Literatures": "Students drawn to the languages, literatures, and cultures of the Celtic world",
    "Chemical and Physical Biology": "Students who want to study living systems through the lens of chemistry and physics",
    "Classical and Ancient Studies": "Students drawn to the languages, literature, history, and material culture of the ancient world",
    "Computational Biology and Quantitative Genetics": "Students who combine biology, statistics, and computation to analyze genomes and biological data",
    "Computational Science & Engineering": "Students who want to use modeling, simulation, and high-performance computing to solve scientific and engineering problems",
    "Computer Engineering": "Students drawn to the hardware-software boundary — processors, embedded systems, and the design of computing machines",
    "Computer Programming": "Students who want to build software and develop fluency in programming languages and practice",
    "Curriculum and Instruction": "Educators focused on how curriculum is designed and taught and how students learn across subjects",
    "Data Science": "Students who want to draw insight from data using statistics, computing, and machine learning",
    "Data Science (HarvardX Professional Certificate)": "Working professionals who want practical, applied training in data analysis, statistics, and machine learning",
    "Demography": "Students drawn to the study of populations — fertility, migration, aging, and how they shape societies",
    "Dentistry": "Students preparing for careers in clinical dentistry and oral-health research",
    "Earth & Planetary Sciences": "Students who want to understand the Earth and other planets, from deep time and climate to the forces that shape worlds",
    "Earth and Planetary Sciences": "Students who want to understand the Earth and other planets, from deep time and climate to the forces that shape worlds",
    "East Asian Languages and Civilizations": "Students drawn to the languages, literatures, histories, and cultures of East Asia",
    "Education": "Students committed to teaching, learning, and improving educational opportunity and outcomes",
    "Electrical Engineering": "Students drawn to circuits, signals, electronics, and the systems behind modern devices and communication",
    "Engineering Science": "Students who want a broad engineering foundation grounded in the physical sciences and mathematics",
    "Engineering-Related Fields": "Students drawn to engineering and applied-science problems across disciplines",
    "Environmental Science & Engineering": "Students applying science and engineering to climate, energy, water, and environmental challenges",
    "Film and Visual Studies": "Students drawn to film, media, and visual culture as makers and as critics and scholars",
    "German": "Students drawn to German language, literature, and the intellectual traditions of the German-speaking world",
    "Government": "Students drawn to government, politics, and how power, institutions, and ideas shape collective life",
    "Health and Medical Administrative Services": "Students who want to lead and manage health-care organizations, operations, and systems",
    "History & Literature": "Students drawn to the interdisciplinary study of history and literature and how texts illuminate their times",
    "History of Art & Architecture": "Students drawn to the history and criticism of art and architecture across periods and cultures",
    "Human Evolutionary Biology": "Students fascinated by how evolution shaped human biology, behavior, and health",
    "Information Science": "Students drawn to how information is organized, stored, retrieved, and used in computing and society",
    "Integrative Biology": "Students drawn to organisms and ecosystems — how living things function, interact, and evolve",
    "International Relations and National Security Studies": "Students drawn to global politics, diplomacy, conflict, and the policy behind national and international security",
    "International and Comparative Education": "Educators and analysts drawn to how education systems differ across countries and how policy travels globally",
    "Journalism": "Students who want to report, investigate, and tell stories that inform the public",
    "Leisure and Recreational Activities": "Students drawn to the study and organization of sport, recreation, and leisure",
    "Literature": "Students who love reading across traditions and want to study literature comparatively and critically",
    "Medical Illustration and Informatics": "Students at the intersection of medicine, visual communication, and information science",
    "Medicine": "Students preparing for careers as physicians and physician-scientists",
    "Microbiological Sciences and Immunology": "Students fascinated by microbes, infection, and the immune system and how they shape health and disease",
    "Modern Greek Language and Literature": "Students drawn to the language, literature, and culture of the modern Greek world",
    "Molecular & Cellular Biology": "Students fascinated by the molecules and cellular machinery that drive life, from genes and proteins to cells",
    "Molecular and Cellular Biology": "Students fascinated by the molecules and cellular machinery that drive life, from genes and proteins to cells",
    "Nanotechnology": "Students drawn to engineering and science at the nanoscale, from materials and devices to manufacturing",
    "Natural Sciences": "Students drawn to the natural world who want a broad scientific foundation across disciplines",
    "Near Eastern Languages and Civilizations": "Students drawn to the languages, texts, histories, and cultures of the ancient and modern Near East",
    "Neurobiology and Neurosciences": "Students fascinated by the brain and nervous system and how they give rise to behavior",
    "Neuroscience": "Students fascinated by the brain and nervous system and how they give rise to perception, thought, and behavior",
    "Operations Research": "Students who want to optimize complex systems and decisions using mathematics, modeling, and data",
    "Population Health Sciences": "Students who want to study the determinants of health across populations through rigorous research",
    "Public Administration": "Students preparing to lead and manage public-sector and nonprofit organizations",
    "Public Policy": "Students who want to analyze, design, and evaluate policy to solve public problems",
    "Romance Languages and Literatures": "Students drawn to the languages, literatures, and cultures of the Romance-speaking world",
    "Slavic Languages and Literatures": "Students drawn to the languages, literatures, and cultures of the Slavic world",
    "Social Studies": "Students drawn to the interdisciplinary study of social and political theory and the modern social sciences",
    "South Asian Studies": "Students drawn to the languages, histories, religions, and cultures of South Asia",
    "Student Counseling and Personnel Services": "Students preparing to support learners through counseling and student-development work in schools and colleges",
    "Study of Religion": "Students drawn to the comparative study of religion — its texts, practices, and role in human cultures",
    "Systems Science and Theory": "Students drawn to how complex systems behave and how to model, analyze, and design them",
    "Teaching and Teacher Leadership": "Educators committed to excellent classroom teaching and to leading instructional improvement in schools",
    "Theater, Dance, and Media": "Students committed to theater, dance, and media as performers, makers, and scholars",
    "Theological and Ministerial Studies": "Students preparing for ministry, religious leadership, and the academic study of theology",
    "Urban Planning and Design": "Students focused on how cities grow and are shaped, drawn to land use, transportation, housing, and design",
    "Urban Studies": "Students drawn to cities — how they work, who they serve, and the forces of urban change",
}


# ---------------------------------------------------------------------------
# LEVEL_TAIL — credential-appropriate readiness / typical next step. Follows the
# field lead so each credential level of a field reads differently.
# ---------------------------------------------------------------------------
LEVEL_TAIL: dict[str, str] = {
    "bachelors": "and want a broad undergraduate foundation before careers or graduate study.",
    "masters": "and want advanced, specialized graduate coursework aimed at senior professional roles.",
    "certificate": "looking for a focused, credit-bearing credential without committing to a full degree.",
    "phd": "and want to pursue original doctoral research toward academic or research careers.",
    "professional": "and want rigorous professional preparation for practice in the field.",
}


# ---------------------------------------------------------------------------
# _WHO_BY_SLUG — complete, hand-written audience statements for the award-named
# professional rows whose field part is the degree name (so compose_who has no
# composable field). Each is field-specific and program-distinct.
# ---------------------------------------------------------------------------
_WHO_BY_SLUG: dict[str, str] = {
    "harvard-mba": "Early-to-mid-career professionals who want general-management training in strategy, finance, marketing, and leadership before moving into senior management roles.",
    "harvard-jd": "Aspiring lawyers and legal scholars who want a rigorous professional legal education across every field of law.",
    "harvard-llm": "Lawyers trained outside the U.S. or in specialized fields who want one year of advanced graduate legal study.",
    "harvard-law-sjd": "Legal scholars pursuing the law's most advanced research degree toward academic careers.",
    "harvard-md": "Future physicians and physician-scientists preparing for clinical practice and biomedical research.",
    "harvard-dmd": "Students preparing for careers in clinical dentistry and oral-health research.",
    "harvard-mph": "Clinicians, scientists, and leaders who want graduate training to advance and protect population health.",
    "harvard-mpp": "Future policy analysts and public-sector leaders who want rigorous training in policy analysis and management.",
    "harvard-mpa": "Experienced professionals advancing into leadership across government, nonprofits, and public service.",
    "harvard-mpa-id": "Professionals focused on economic development who want quantitative training for policy in lower- and middle-income countries.",
    "harvard-edm": "Educators and leaders who want a one-year graduate degree to drive change in schools and learning organizations.",
    "harvard-edld": "Experienced education leaders pursuing a practice-oriented doctorate to transform school systems.",
    "harvard-march": "Students pursuing the professional architecture degree through design studios, history, and building technology.",
    "harvard-mla": "Students pursuing the professional landscape-architecture degree, designing landscapes that balance ecology and human use.",
    "harvard-mup": "Students focused on how cities grow, pursuing the professional urban-planning degree across land use, housing, and transportation.",
    "harvard-mdes": "Designers and researchers pursuing post-professional study in design, technology, and the built and natural environment.",
    "harvard-mdiv": "Students preparing for ministry, chaplaincy, and religious leadership through the professional divinity degree.",
    "harvard-mts": "Students who want graduate study of religion and theology for academic, professional, or personal vocation.",
    "harvard-alm": "Adult and part-time learners who want a Harvard graduate liberal-arts degree built around their own field of focus.",
    "harvard-real-estate-ms": "Students focused on real-estate development, investment, and the design and economics of the built environment.",
}


def compose_who(field: str | None, degree_type: str) -> str | None:
    """Field-specific lead + credential-appropriate tail. Returns None if the
    field has no WHO_BY_FIELD entry (the build gate then fails loudly)."""
    if not field:
        return None
    lead = WHO_BY_FIELD.get(field)
    if lead is None:
        return None
    tail = LEVEL_TAIL.get(degree_type, LEVEL_TAIL["masters"])
    return f"{lead} {tail}"
