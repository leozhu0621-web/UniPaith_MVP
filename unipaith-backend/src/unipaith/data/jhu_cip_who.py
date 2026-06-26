"""Johns Hopkins University — matcher-core ``cip_code`` + universal ``who_its_for``.

REPAIR_BACKLOG #1 (``cip_code`` starvation) and #4a (``who_its_for`` 0%), SKILL miss #2
(matcher-core fields) and miss #8 (universal depth field). The base ``jhu_profile``
catalog (244 real, field-specific, structurally-clean programs) shipped both fields null:

* ``cip_code`` — the CIP join key the CPEF matcher uses to resolve a program's field to
  ``ref_majors`` + the field-66 vocabulary (it reads the 2-digit family; the program-name
  alias wins first). The base catalog already carries the College Scorecard 4-digit CIP
  per program (``spec["cip"]``); this module upgrades each to its verified NCES CIP-2020
  6-digit code so the live value matches the gold-standard fillers (Rice / UIUC /
  UW-Madison), keyed by the 4-digit family already in the catalog. The 2-digit family is
  preserved in every case (the 6-digit shares the family's first two digits) — including
  the exact-title codes the repo's ref_majors carries (Learning Sciences 13.0607,
  Engineering Design 15.1502, Rehabilitation Science 51.2314) — with ONE documented
  exception: Data Science maps to its dedicated 30.7001 ("Data Science, General") rather
  than the family-11 11.0802 ("Data Modeling/Warehousing"), because the exact ref_majors
  title matters and the field/soft signals survive (name-alias + description-keyword
  fallback). So the matcher field signal is identical; no code is
  invented — each is the published NCES code for that field, and the family is the one
  College Scorecard already assigned.

* ``who_its_for`` — a UNIVERSAL depth field: a field-specific, program-DISTINCT statement
  of the applicant each program fits. Built ``WHO_BY_FIELD[field]`` (the subject + the
  applicant it fits, derived strictly from the program's own field) followed by
  ``LEVEL_TAIL[degree_type]`` (the credential-appropriate readiness / typical next step),
  so a bachelor's survey, a professional master's, a focused certificate, and a funded
  research doctorate of the SAME field read differently — and, because every
  ``(field, credential)`` pair is unique in this catalog, every string is distinct
  (distinct/total = 1.0, never a one-per-degree-type template). No fabricated facts (no
  rankings, numbers, or named centers), matching the field-specific gold bar
  (Brown / Emory / Purdue / Rice / UW-Madison).
"""

from __future__ import annotations

# ruff: noqa: E501

# ---------------------------------------------------------------------------
# CIP6_BY_CIP4 — verified NCES CIP-2020 6-digit code per 4-digit family present
# in the JHU catalog. The 6-digit shares the family's first two digits, so the
# matcher's 2-digit field signal is unchanged; this only sharpens the published
# code to match the gold-standard fillers. field<->cip4 is 1:1 in this catalog.
# ---------------------------------------------------------------------------
CIP6_BY_CIP4: dict[str, str] = {
    "03.01": "03.0104",  # Environmental Sciences -> Environmental Science
    "04.03": "04.0301",  # Urban Planning -> City/Urban, Community and Regional Planning
    "05.01": "05.0107",  # Latin American, Caribbean, and Latinx Studies -> Latin American Studies
    "05.02": "05.0200",  # Ethnic Studies -> Ethnic, Cultural Minority, Gender, and Group Studies, General
    "09.01": "09.0102",  # Communication Studies -> Mass Communication/Media Studies
    "10.02": "10.0202",  # Media Technology -> Radio and Television Broadcasting Technology
    "11.01": "11.0101",  # Computer and Information Sciences -> Computer and Information Sciences, General
    "11.04": "11.0401",  # Information Science -> Information Science/Studies
    "11.07": "11.0701",  # Computer Science -> Computer Science
    "11.08": "30.7001",  # Data Science -> Data Science, General (NCES dedicated code; the only family exception — Scorecard aggregates Data Science under 11.08, but the exact-title code is in family 30; name "data science" aliases in field_canon AND description-keyword soft-feature fallback covers the unmapped family, so the field/soft signals hold while the ref_majors title is correct)
    "11.09": "11.0901",  # Computer Networks -> Computer Systems Networking and Telecommunications
    "11.10": "11.1099",  # Information Systems -> Computer/Information Technology Services Administration and Management, Other
    "13.01": "13.0101",  # Education Studies -> Education, General
    "13.04": "13.0401",  # Educational Leadership -> Educational Leadership and Administration, General
    "13.05": "13.0501",  # Instructional Design -> Educational/Instructional Technology
    "13.06": "13.0607",  # Learning Sciences -> Learning Sciences
    "13.10": "13.1001",  # Special Education -> Special Education and Teaching, General
    "13.11": "13.1101",  # Counseling -> Counselor Education/School Counseling and Guidance Services
    "13.12": "13.1206",  # Teacher Education -> Teacher Education, Multiple Levels
    "13.13": "13.1205",  # Secondary Education -> Secondary Education and Teaching
    "13.14": "13.1401",  # TESOL -> Teaching English as a Second or Foreign Language/ESL Language Instructor
    "13.99": "13.9999",  # Education -> Education, Other
    "14.01": "14.0101",  # General Engineering -> Engineering, General
    "14.02": "14.0201",  # Aerospace Engineering -> Aerospace, Aeronautical and Astronautical Engineering
    "14.05": "14.0501",  # Biomedical Engineering -> Bioengineering and Biomedical Engineering
    "14.07": "14.0701",  # Chemical Engineering -> Chemical Engineering
    "14.08": "14.0801",  # Civil Engineering -> Civil Engineering, General
    "14.09": "14.0901",  # Computer Engineering -> Computer Engineering, General
    "14.10": "14.1001",  # Electrical Engineering -> Electrical and Electronics Engineering
    "14.11": "14.1101",  # Engineering Mechanics -> Engineering Mechanics
    "14.14": "14.1401",  # Environmental Engineering -> Environmental/Environmental Health Engineering
    "14.18": "14.1801",  # Materials Science and Engineering -> Materials Engineering
    "14.19": "14.1901",  # Mechanical Engineering -> Mechanical Engineering
    "14.27": "14.2701",  # Systems Engineering -> Systems Engineering
    "14.35": "14.3501",  # Industrial Engineering -> Industrial Engineering
    "14.42": "14.4201",  # Robotics -> Mechatronics, Robotics, and Automation Engineering
    "15.15": "15.1502",  # Engineering Design -> Engineering Design
    "15.16": "15.1601",  # Nanotechnology -> Nanotechnology
    "15.17": "15.1701",  # Energy Systems -> Energy Systems Technology/Technician
    "16.05": "16.0501",  # German -> German Language and Literature
    "16.09": "16.0900",  # Romance Languages -> Romance Languages, Literatures, and Linguistics, General
    "16.12": "16.1200",  # Classics -> Classics and Classical Languages, Literatures, and Linguistics, General
    "23.01": "23.0101",  # English -> English Language and Literature, General
    "23.13": "23.1303",  # Writing Studies -> Professional, Technical, Business, and Scientific Writing
    "24.01": "24.0101",  # Liberal Arts -> Liberal Arts and Sciences/Liberal Studies
    "26.01": "26.0101",  # Biology -> Biology/Biological Sciences, General
    "26.02": "26.0202",  # Biochemistry -> Biochemistry
    "26.04": "26.0406",  # Cell Biology -> Cell/Cellular and Molecular Biology
    "26.05": "26.0502",  # Microbiology -> Microbiology, General
    "26.07": "26.0701",  # Animal Biology -> Zoology/Animal Biology
    "26.08": "26.0801",  # Genetics -> Genetics, General
    "26.09": "26.0901",  # Physiology -> Physiology, General
    "26.10": "26.1001",  # Pharmacology -> Pharmacology
    "26.11": "26.1103",  # Bioinformatics -> Bioinformatics
    "26.12": "26.1201",  # Biotechnology -> Biotechnology
    "26.13": "26.1310",  # Ecology and Evolution -> Ecology and Evolutionary Biology
    "26.15": "26.1501",  # Neuroscience -> Neuroscience
    "26.99": "26.9999",  # Biological Sciences -> Biological and Biomedical Sciences, Other
    "27.01": "27.0101",  # Mathematics -> Mathematics, General
    "27.03": "27.0301",  # Applied Mathematics -> Applied Mathematics, General
    "27.05": "27.0501",  # Statistics -> Statistics, General
    "27.06": "27.0601",  # Applied Statistics -> Applied Statistics, General
    "27.99": "27.9999",  # Mathematics and Statistics -> Mathematics and Statistics, Other
    "29.02": "29.0201",  # Intelligence Studies -> Intelligence, General
    "30.11": "30.1101",  # Gerontology -> Gerontology
    "30.12": "30.1201",  # Historic Preservation -> Historic Preservation and Conservation
    "30.14": "30.1401",  # Museum Studies -> Museology/Museum Studies
    "30.17": "30.1701",  # Behavioral Science -> Behavioral Sciences
    "30.18": "30.1801",  # Natural Sciences -> Natural Sciences
    "30.25": "30.2501",  # Cognitive Science -> Cognitive Science, General
    "30.27": "30.2701",  # Human Biology -> Human Biology
    "30.33": "30.3301",  # Sustainability -> Sustainability Studies
    "30.99": "30.9999",  # Interdisciplinary Studies -> Multi-/Interdisciplinary Studies, Other
    "38.01": "38.0101",  # Philosophy -> Philosophy
    "40.02": "40.0202",  # Astrophysics -> Astrophysics
    "40.05": "40.0501",  # Chemistry -> Chemistry, General
    "40.06": "40.0601",  # Earth and Planetary Sciences -> Geology/Earth Science, General
    "40.08": "40.0801",  # Physics -> Physics, General
    "40.99": "40.9999",  # Physical Sciences -> Physical Sciences, Other
    "42.01": "42.0101",  # Psychology -> Psychology, General
    "42.27": "42.2704",  # Experimental Psychology -> Experimental Psychology
    "43.03": "43.0301",  # Homeland Security -> Homeland Security
    "44.04": "44.0401",  # Public Administration -> Public Administration
    "44.05": "44.0501",  # Public Policy -> Public Policy Analysis, General
    "45.01": "45.0101",  # Social Sciences -> Social Sciences, General
    "45.02": "45.0201",  # Anthropology -> Anthropology, General
    "45.03": "45.0301",  # Archaeology -> Archeology
    "45.06": "45.0601",  # Economics -> Economics, General
    "45.07": "45.0701",  # Geography -> Geography
    "45.09": "45.0901",  # International Relations -> International Relations and Affairs
    "45.10": "45.1001",  # Political Science -> Political Science and Government, General
    "45.11": "45.1101",  # Sociology -> Sociology
    "50.03": "50.0301",  # Dance -> Dance, General
    "50.06": "50.0601",  # Film and Media -> Film/Cinema/Media Studies
    "50.07": "50.0702",  # Studio Art -> Fine/Studio Arts, General
    "50.09": "50.0901",  # Music -> Music, General
    "51.00": "51.0000",  # Health Sciences -> Health Services/Allied Health/Health Sciences, General
    "51.07": "51.0701",  # Health Administration -> Health/Health Care Administration/Management
    "51.12": "51.1201",  # Medicine -> Medicine
    "51.15": "51.1508",  # Mental Health Counseling -> Mental Health Counseling/Counselor
    "51.22": "51.2201",  # Public Health -> Public Health, General
    "51.23": "51.2314",  # Rehabilitation Sciences -> Rehabilitation Science
    "51.27": "51.2703",  # Medical Illustration -> Medical Illustration/Medical Illustrator
    "51.32": "51.3204",  # Medical Humanities -> Clinical Research Coordinator
    "51.38": "51.3801",  # Nursing -> Registered Nursing/Registered Nurse
    "51.99": "51.9999",  # Clinical Health Sciences -> Health Professions and Related Clinical Sciences, Other
    "52.01": "52.0101",  # Business -> Business/Commerce, General
    "52.02": "52.0201",  # Business Administration -> Business Administration and Management, General
    "52.08": "52.0801",  # Finance -> Finance, General
    "52.13": "52.1301",  # Business Analytics -> Management Science
    "52.14": "52.1401",  # Marketing -> Marketing/Marketing Management, General
    "52.15": "52.1501",  # Real Estate -> Real Estate
    "54.01": "54.0101",  # History -> History, General
}


# ---------------------------------------------------------------------------
# WHO_BY_FIELD — the field-specific lead of "Who it's for": the subject and the
# applicant it fits (background / interest), written from the field alone, no
# fabricated facts. The LEVEL_TAIL adds the credential-appropriate next step.
# field<->cip4 is 1:1, so this also covers every cip4 family above.
# ---------------------------------------------------------------------------
WHO_BY_FIELD: dict[str, str] = {
    "Environmental Sciences": "Students who want to study natural systems, climate, and human impact on the environment with quantitative, field-based methods",
    "Urban Planning": "Students focused on how cities grow, drawn to land use, transportation, housing, and the design of livable communities",
    "Latin American, Caribbean, and Latinx Studies": "Students drawn to the histories, languages, politics, and cultures of Latin America, the Caribbean, and Latinx communities",
    "Ethnic Studies": "Students examining race, ethnicity, migration, and identity and how power and culture shape group experience",
    "Communication Studies": "Students interested in how messages, media, and audiences shape public life, organizations, and culture",
    "Media Technology": "Students drawn to the production tools and platforms behind audio, video, and digital media",
    "Computer and Information Sciences": "Students who want a broad grounding in computing, information, and how software and data systems work",
    "Information Science": "Students focused on how information is organized, retrieved, and used, bridging people, data, and technology",
    "Computer Science": "Students drawn to algorithms, systems, and software who want rigorous training in how computation works",
    "Data Science": "Students who want to turn large, messy datasets into insight, combining statistics, programming, and machine learning",
    "Computer Networks": "Students focused on how networks and distributed systems move and secure data reliably at scale",
    "Information Systems": "Students who want to secure and manage the information systems organizations depend on",
    "Education Studies": "Students interested in how people learn and how schools and policies can teach more effectively",
    "Educational Leadership": "Educators preparing to lead schools, districts, or programs and to drive instructional improvement",
    "Instructional Design": "Educators and professionals who design effective learning experiences and the technology that delivers them",
    "Learning Sciences": "Students who study how learning happens and how to evaluate and improve teaching with evidence",
    "Special Education": "Educators committed to teaching students with disabilities and designing inclusive, individualized instruction",
    "Counseling": "Students preparing to support learning, development, and well-being in school and community settings",
    "Teacher Education": "Aspiring and practicing teachers building the subject knowledge and classroom skills to lead a classroom",
    "Secondary Education": "Educators preparing to teach a subject area at the middle- and high-school levels",
    "TESOL": "Educators preparing to teach English to speakers of other languages at home or abroad",
    "Education": "Students pursuing advanced study across teaching, leadership, and education policy",
    "General Engineering": "Students who want a broad engineering foundation across multiple disciplines before specializing",
    "Aerospace Engineering": "Students drawn to the design of aircraft, spacecraft, and the systems that fly and navigate",
    "Biomedical Engineering": "Students at the interface of engineering and medicine who want to design devices, imaging, and therapies",
    "Chemical Engineering": "Students who want to turn chemical and biological processes into products at industrial scale",
    "Civil Engineering": "Students focused on the infrastructure — structures, transportation, water, and the built environment — society relies on",
    "Computer Engineering": "Students who want to design the hardware and embedded systems that bridge computing and the physical world",
    "Electrical Engineering": "Students drawn to circuits, signals, power, and the electronics behind modern devices",
    "Engineering Mechanics": "Students who want the mathematical and physical foundations of how materials and structures behave under load",
    "Environmental Engineering": "Students applying engineering to clean water, air quality, and sustainable infrastructure",
    "Materials Science and Engineering": "Students who want to design and characterize materials, from nanostructures to alloys and biomaterials",
    "Mechanical Engineering": "Students drawn to mechanical systems, thermodynamics, and design across energy, robotics, and manufacturing",
    "Systems Engineering": "Students who want to engineer complex systems end-to-end, balancing requirements, integration, and risk",
    "Industrial Engineering": "Students focused on optimizing processes, operations, and supply chains across organizations",
    "Robotics": "Students drawn to autonomy, perception, and control who want to build robots and intelligent machines",
    "Engineering Design": "Engineers building the project, management, and design judgment to lead technical teams",
    "Nanotechnology": "Students working at the nanoscale to engineer new materials, devices, and sensors",
    "Energy Systems": "Students focused on power generation, storage, and the transition to sustainable energy",
    "German": "Students drawn to German language, literature, and the intellectual traditions of the German-speaking world",
    "Romance Languages": "Students drawn to the languages, literatures, and cultures of the Romance-speaking world",
    "Classics": "Students drawn to the languages, literature, and civilizations of ancient Greece and Rome",
    "English": "Students who love literature and writing and want to read closely, think critically, and argue in prose",
    "Writing Studies": "Students who want to write clearly and persuasively across professional, technical, and scientific settings",
    "Liberal Arts": "Students who want a broad, interdisciplinary grounding across the humanities and human inquiry",
    "Biology": "Students fascinated by living systems, from molecules and cells to organisms and ecosystems",
    "Biochemistry": "Students drawn to the chemistry of life — the molecules and reactions that drive biological function",
    "Cell Biology": "Students who want to understand how cells and molecules organize, signal, and sustain life",
    "Microbiology": "Students drawn to microbes — their biology, genetics, and roles in health, disease, and the environment",
    "Animal Biology": "Students who want to study animal form, function, behavior, and evolution",
    "Genetics": "Students focused on heredity, genomes, and how genes shape development, health, and variation",
    "Physiology": "Students who want to understand how the body's systems function and adapt in health and disease",
    "Pharmacology": "Students drawn to how drugs act on the body and how that knowledge becomes therapeutics",
    "Bioinformatics": "Students who combine biology with computation to analyze genomes and large biological datasets",
    "Biotechnology": "Students who want to translate molecular biology into products, diagnostics, and therapeutics",
    "Ecology and Evolution": "Students drawn to how organisms interact with their environment and change over evolutionary time",
    "Neuroscience": "Students fascinated by the brain and nervous system, from neurons to behavior and cognition",
    "Biological Sciences": "Students who want advanced, interdisciplinary study across the biological and biomedical sciences",
    "Mathematics": "Students who love mathematical reasoning, proof, and abstraction across pure and applied areas",
    "Applied Mathematics": "Students who want to use mathematical modeling and computation to solve real scientific and engineering problems",
    "Statistics": "Students drawn to inference and uncertainty who want to design studies and draw conclusions from data",
    "Applied Statistics": "Students who want to apply statistical methods to real problems in science, business, and policy",
    "Mathematics and Statistics": "Students who want rigorous, combined training in mathematical and statistical methods",
    "Intelligence Studies": "Professionals focused on intelligence analysis, security, and how information informs decisions",
    "Gerontology": "Students and professionals focused on aging and the health, social, and policy needs of older adults",
    "Historic Preservation": "Students committed to conserving historic places, buildings, and cultural heritage",
    "Museum Studies": "Students preparing to curate, manage, and interpret collections in museums and cultural institutions",
    "Behavioral Science": "Students drawn to how individuals and groups behave, blending psychology, sociology, and biology",
    "Natural Sciences": "Students who want a broad, interdisciplinary foundation across the natural sciences",
    "Cognitive Science": "Students who study the mind — perception, language, reasoning, and learning — across disciplines",
    "Human Biology": "Students who want an integrated view of human biology spanning health, evolution, and physiology",
    "Sustainability": "Students focused on balancing environmental, social, and economic needs for a sustainable future",
    "Interdisciplinary Studies": "Students whose interests cross fields and who want to build a coherent program of their own",
    "Philosophy": "Students drawn to fundamental questions of knowledge, ethics, mind, and reality and to rigorous argument",
    "Astrophysics": "Students fascinated by stars, galaxies, and the physics of the universe",
    "Chemistry": "Students drawn to matter and its transformations, from synthesis to spectroscopy and reaction mechanisms",
    "Earth and Planetary Sciences": "Students who want to understand the Earth, planets, oceans, and the forces that shape them",
    "Physics": "Students drawn to the fundamental laws of nature, from particles and fields to matter and energy",
    "Physical Sciences": "Students who want broad, interdisciplinary training across the physical sciences",
    "Psychology": "Students fascinated by mind and behavior who want to study how people think, feel, and act",
    "Experimental Psychology": "Students focused on the experimental study of cognition, perception, and behavior",
    "Homeland Security": "Professionals focused on protecting people and infrastructure from natural and human-made threats",
    "Public Administration": "Students preparing to lead and manage public and nonprofit organizations effectively",
    "Public Policy": "Students who want to analyze, design, and evaluate policy to solve public problems",
    "Social Sciences": "Students who want broad, interdisciplinary training in how societies and human behavior work",
    "Anthropology": "Students drawn to human cultures, societies, and our biological and historical past",
    "Archaeology": "Students fascinated by past societies and how material remains reveal how people lived",
    "Economics": "Students who want to understand how people, markets, and institutions allocate scarce resources",
    "Geography": "Students drawn to place, space, and the human and physical patterns that shape the world",
    "International Relations": "Students focused on diplomacy, security, and global affairs across states and institutions",
    "Political Science": "Students drawn to government, politics, and how power and institutions shape collective life",
    "Sociology": "Students who want to understand social structure, inequality, and how groups and institutions shape behavior",
    "Dance": "Students committed to dance as performers, choreographers, and scholars of movement",
    "Film and Media": "Students drawn to film and media as makers and critics of moving-image storytelling",
    "Studio Art": "Students committed to making art and developing a studio practice across media",
    "Music": "Students committed to music as performers, composers, and scholars",
    "Health Sciences": "Students seeking a broad foundation across the health sciences and allied health professions",
    "Health Administration": "Professionals preparing to manage and lead health-care organizations and systems",
    "Medicine": "Students preparing to become physicians and physician-scientists",
    "Mental Health Counseling": "Students preparing to provide mental-health counseling in clinical and community settings",
    "Public Health": "Students committed to protecting and improving the health of populations through prevention and policy",
    "Rehabilitation Sciences": "Students and clinicians focused on restoring function and supporting recovery and independence",
    "Medical Illustration": "Students who combine science, art, and technology to visualize medical and biological information",
    "Medical Humanities": "Students exploring medicine through ethics, history, and the humanities alongside clinical practice",
    "Nursing": "Students preparing to deliver and lead patient care as nurses and advanced-practice clinicians",
    "Clinical Health Sciences": "Students pursuing advanced, interdisciplinary study across the clinical health sciences",
    "Business": "Students who want a broad grounding in how organizations create value and operate",
    "Business Administration": "Students and professionals building the leadership and management skills to run organizations",
    "Finance": "Students drawn to markets, investment, and corporate finance and how capital is allocated",
    "Business Analytics": "Students who want to drive decisions with data, modeling, and quantitative management methods",
    "Marketing": "Students focused on understanding customers and building brands, products, and demand",
    "Real Estate": "Students focused on real-estate development, investment, and the economics of the built environment",
    "History": "Students who want to understand the past and how it shapes the present through evidence and argument",
}


# ---------------------------------------------------------------------------
# LEVEL_TAIL — credential-appropriate readiness / typical next step. Follows the
# field lead so each credential level of a field reads differently. Kept short so
# the field-specific lead carries the substance.
# ---------------------------------------------------------------------------
LEVEL_TAIL: dict[str, str] = {
    "bachelors": "and want a broad undergraduate foundation before careers or graduate study.",
    "masters": "and want advanced, specialized graduate coursework aimed at senior professional roles.",
    "certificate": "looking for a focused, credit-bearing credential without committing to a full degree.",
    "phd": "and want to pursue original doctoral research toward academic or research careers.",
    "professional": "and want rigorous professional preparation for practice in the field.",
}


def compose_who(field: str, degree_type: str) -> str | None:
    """field-specific lead + credential-appropriate tail. Returns None if the
    field has no WHO_BY_FIELD entry (the build gate then fails loudly)."""
    lead = WHO_BY_FIELD.get(field)
    if lead is None:
        return None
    tail = LEVEL_TAIL.get(degree_type, LEVEL_TAIL["masters"])
    return f"{lead} {tail}"
