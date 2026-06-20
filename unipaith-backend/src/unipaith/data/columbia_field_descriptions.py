"""Field-substance description clauses for Columbia University's real degree catalog.

Rebuilt 2026-06-19 (columbiadefab1) to replace the prior IPEDS×award-level catalog,
whose machine-generated descriptions had imported PEER-institution units (Harvard's
Nieman Foundation, Carpenter Center, and Visual & Environmental Studies program) onto
Columbia rows — fabrication-by-cross-institution-templating (SKILL.md miss #8). Every
clause here is a TRUE, field-specific statement about what the discipline studies; no
Columbia-specific named unit is asserted unless verified, and no peer-institution unit
appears anywhere. The per-credential description is assembled in ``columbia_profile.py``
by pairing one of these field cores with a credential-distinct lead, so a field's
bachelor's / master's / doctoral rows never share a leading body (gold MIT = 0%).

``SLUG_DESCRIPTIONS`` carries the verified, hand-written descriptions for Columbia's
flagship professional/graduate programs verbatim (they were already clean).
"""

# ruff: noqa: E501

from __future__ import annotations

# Field-of-study cores: a short, true clause naming the actual substance of the
# discipline. Used by ``columbia_profile._description`` with a credential-specific lead.
CORE: dict[str, str] = {
    # ── Arts & Sciences — social sciences ──
    "Economics": "microeconomic and macroeconomic theory, econometrics, and economic history",
    "Financial Economics": "asset pricing, corporate finance, and the economics of financial markets",
    "Political Science": "American, comparative, and international politics together with political theory",
    "Sociology": "social structure, inequality, organizations, and the study of modern urban society",
    "Anthropology": "the comparative study of human societies, cultures, and biological and archaeological evidence",
    "Psychology": "cognitive, developmental, social, and clinical foundations of mind and behavior",
    "History": "the human past across periods and world regions through archival and interpretive methods",
    "Urban Studies": "cities and metropolitan life through urban planning, policy, sociology, and design",
    "Human Rights": "the law, politics, and history of human rights and the institutions that protect them",
    "American Studies": "the literature, history, politics, and culture of the United States across disciplines",
    "Ethnicity and Race Studies": "the comparative study of race, ethnicity, migration, and identity in the Americas",
    "Women's and Gender Studies": "gender, sexuality, and feminist theory across the humanities and social sciences",
    # ── Arts & Sciences — humanities ──
    "English and Comparative Literature": "literature, literary criticism, and writing across English and comparative traditions",
    "Philosophy": "logic, ethics, metaphysics, epistemology, and the history of philosophy",
    "Religion": "the comparative and historical study of religious traditions, texts, and practices",
    "Classics": "the languages, literature, history, and material culture of ancient Greece and Rome",
    "Ancient Studies": "the languages, texts, and civilizations of the ancient Mediterranean world",
    "Archaeology": "the recovery and interpretation of past societies through material remains and fieldwork",
    "Comparative Literature and Society": "literature read across languages alongside social and political theory",
    "Creative Writing": "the craft of fiction, poetry, and nonfiction through workshops and close reading",
    "Drama and Theatre Arts": "dramatic literature, theatre history, and the practice of performance and production",
    "Film and Media Studies": "the history, theory, and criticism of film and moving-image media",
    "Visual Arts": "studio practice across painting, sculpture, photography, and new media",
    "Medical Humanities": "the intersection of medicine, ethics, narrative, and the humanities",
    "Linguistics": "the structure of language across phonology, syntax, semantics, and sociolinguistics",
    "Music": "music history, theory, composition, and ethnomusicology",
    "Art History": "the history, theory, and interpretation of art and architecture across cultures",
    "Art History and Archaeology": "the history and interpretation of art and architecture together with archaeological method",
    "Architecture": "architectural design, history, and theory and the shaping of the built environment",
    # ── Arts & Sciences — area & language studies ──
    "East Asian Studies": "the languages, literatures, histories, and cultures of China, Japan, and Korea",
    "Middle Eastern, South Asian, and African Studies": "the languages, literatures, and histories of the Middle East, South Asia, and Africa",
    "African American and African Diaspora Studies": "the history, politics, and cultural production of Black communities across the diaspora",
    "Latin American and Caribbean Studies": "the politics, history, and cultures of Latin America and the Caribbean",
    "Hispanic Studies": "the literatures and cultures of Spain, Latin America, and the Iberian world",
    "French": "French and Francophone literature, language, and culture from the medieval era to the present",
    "German": "German literature, philosophy, and intellectual history",
    "Italian": "Italian literature, language, and culture from Dante to the present",
    "Russian Language and Culture": "Russian language, literature, and cultural history",
    "Slavic Studies": "the languages, literatures, and cultures of the Slavic world",
    # ── Arts & Sciences — natural sciences & mathematics ──
    "Biology": "molecular, cellular, and organismal biology and genetics",
    "Biological Sciences": "molecular, cellular, and developmental biology, genetics, and neuroscience research",
    "Biochemistry": "the chemistry of biological molecules and the molecular basis of life",
    "Environmental Biology": "organisms and ecosystems, biodiversity, and the biology of environmental change",
    "Ecology, Evolution, and Environmental Biology": "ecology, evolutionary biology, and conservation across organisms and ecosystems",
    "Neuroscience and Behavior": "the neural and biological bases of perception, cognition, and behavior",
    "Chemistry": "organic, inorganic, physical, and analytical chemistry and chemical research",
    "Physics": "classical and quantum physics, from particles and fields to condensed matter and astrophysics",
    "Astronomy": "stars, galaxies, and cosmology through observational and theoretical astrophysics",
    "Astrophysics": "the physics of stars, galaxies, and the early universe",
    "Earth Science": "the physical processes of the Earth, oceans, atmosphere, and climate",
    "Earth and Environmental Sciences": "the solid Earth, oceans, atmosphere, and climate system and their interactions",
    "Environmental Science": "the science of the environment across the geosciences, biology, and chemistry",
    "Sustainable Development": "the science, economics, and policy of sustainable development and climate",
    "Mathematics": "algebra, analysis, geometry, topology, and number theory",
    "Statistics": "probability, statistical inference, and the analysis of data",
    "Applied Mathematics": "mathematical modeling, analysis, and computation applied to science and engineering",
    "Cognitive Science": "the interdisciplinary study of mind across psychology, linguistics, philosophy, and computation",
    "Data Science": "statistical learning, computation, and data-driven inference at scale",
    "Computer Science": "algorithms, systems, theory, artificial intelligence, and software across computing",
    "Economics-Mathematics": "economic theory together with the mathematical methods of optimization and analysis",
    "Mathematics-Statistics": "mathematics together with probability and statistical inference",
    "Computer Science-Mathematics": "computer science together with the mathematical foundations of computation",
    "Climate and Society": "the science, impacts, and policy of climate change and society's response",
    "Human Rights Studies": "the history, law, and practice of international human rights",
    "Quantitative Methods in the Social Sciences": "advanced quantitative and computational methods for social-science research",
    # ── Engineering (Fu Foundation School of Engineering and Applied Science) ──
    "Applied Physics": "the physics of materials, plasmas, optics, and devices for engineering applications",
    "Materials Science and Engineering": "the structure, properties, and processing of metals, ceramics, polymers, and nanomaterials",
    "Biomedical Engineering": "engineering principles applied to medicine, imaging, biomechanics, and biomaterials",
    "Chemical Engineering": "reaction engineering, transport phenomena, thermodynamics, and materials processing",
    "Civil Engineering": "the analysis and design of structures, geotechnical systems, and infrastructure",
    "Engineering Mechanics": "the mechanics of solids and fluids and the modeling of engineering systems",
    "Computer Engineering": "the design of digital systems, computer architecture, and hardware–software integration",
    "Earth and Environmental Engineering": "energy, water, and environmental systems and the engineering of sustainability",
    "Electrical Engineering": "circuits, signals, communications, devices, and systems",
    "Industrial Engineering": "the optimization of complex systems across operations, logistics, and decision-making",
    "Operations Research": "optimization, stochastic modeling, and analytics for decision-making under uncertainty",
    "Mechanical Engineering": "mechanics, thermofluids, robotics, controls, and mechanical design",
    "Management Science and Engineering": "analytics, optimization, and the management of technology-driven enterprises",
    "Financial Engineering": "stochastic modeling, derivatives, and computational methods for quantitative finance",
}

# Verified, hand-written descriptions for flagship professional/graduate programs and
# a small set of named undergraduate majors — kept verbatim (already clean, no peer units).
SLUG_DESCRIPTIONS: dict[str, str] = {
    # Columbia College — verified hand-written A&S majors (real Columbia centers/institutes).
    "columbia-economics-ba": (
        "Microeconomics, macroeconomics, econometrics, and economic history within Columbia "
        "College's Core Curriculum and the Department of Economics."
    ),
    "columbia-political-science-ba": (
        "American, comparative, and international politics plus political theory through "
        "Columbia's Department of Political Science and the Saltzman Institute."
    ),
    "columbia-history-ba": (
        "Period and regional history across human civilizations with Columbia's renowned "
        "historical collections and the History Department's research seminars."
    ),
    "columbia-english-ba": (
        "Literature, criticism, and writing in English and comparative traditions through "
        "Columbia College and the Department of English and Comparative Literature."
    ),
    "columbia-psychology-ba": (
        "Cognitive, developmental, social, and clinical science through Columbia Psychology "
        "and the Zuckerman Mind Brain Behavior Institute."
    ),
    "columbia-sociology-ba": (
        "Social structure, inequality, and urban society through Columbia Sociology — home "
        "of the Chicago-school tradition's New York counterpart."
    ),
    "columbia-biology-ba": (
        "Molecular, cellular, and organismal biology and genetics through Columbia's "
        "Department of Biological Sciences and CUIMC research labs."
    ),
    # Engineering — verified hand-written undergraduate majors.
    "columbia-computer-science-bs": (
        "Columbia's flagship computing major — offered as the B.S. (Columbia Engineering) "
        "and the B.A. (Columbia College), spanning AI, machine learning, systems, theory "
        "and graphics through the Department of Computer Science."
    ),
    "columbia-operations-research-bs": (
        "Optimization, stochastic modeling, and analytics in the Department of Industrial "
        "Engineering and Operations Research with Wall Street placement pipelines."
    ),
    "columbia-mechanical-engineering-bs": (
        "Mechanics, thermofluids, robotics, and design in Columbia Engineering's Department "
        "of Mechanical Engineering."
    ),
    "columbia-electrical-engineering-bs": (
        "Circuits, signals, devices, communications, and systems in Columbia's Department "
        "of Electrical Engineering."
    ),
    "columbia-applied-mathematics-bs": (
        "Modeling, analysis, and computation in the Department of Applied Physics and "
        "Applied Mathematics with ties to Columbia's physics and engineering labs."
    ),
    "columbia-biomedical-engineering-bs": (
        "Engineering principles applied to medicine and biology through Columbia BME and "
        "Columbia University Irving Medical Center."
    ),
    # Flagship professional / graduate degrees — verified hand-written.
    "columbia-computer-science-ms": (
        "The 30-point M.S. in Computer Science — advanced study across tracks such as "
        "machine learning, systems, vision, NLP, security and theory."
    ),
    "columbia-mba": (
        "The full-time, two-year MBA — connecting academic theory to real-world practice "
        "from the heart of New York City."
    ),
    "columbia-jd": (
        "The three-year Juris Doctor — Columbia Law School's professional law degree, with "
        "strength in corporate, constitutional and international law."
    ),
    "columbia-md": (
        "The four-year Doctor of Medicine — awarded by the first U.S. medical school to "
        "confer the M.D., at Columbia University Irving Medical Center."
    ),
    "columbia-journalism-ms": (
        "The Master of Science in Journalism — the flagship reporting degree of the only "
        "Ivy League journalism school, which administers the Pulitzer Prizes."
    ),
    "columbia-sipa-mia": (
        "The two-year Master of International Affairs — policy, security and development "
        "for careers in international and public affairs."
    ),
    "columbia-sipa-mpa": (
        "The two-year Master of Public Administration — management and policy analysis for "
        "public-service and policy leadership."
    ),
    "columbia-public-health-mph": (
        "The accredited Master of Public Health — biostatistics, epidemiology, "
        "environmental health, health policy and population health."
    ),
    "columbia-social-work-msw": (
        "The Master of Science in Social Work — clinical practice and social policy at the "
        "oldest school of social work in the United States."
    ),
    "columbia-architecture-march": (
        "The three-year professional Master of Architecture — Columbia GSAPP's flagship "
        "design degree."
    ),
    "columbia-arts-mfa": (
        "The Master of Fine Arts — Columbia's terminal arts degree in film, theatre, "
        "visual arts or writing."
    ),
    "columbia-nursing-msn": (
        "The Master's Direct Entry program — an accelerated path to registered-nurse "
        "licensure for students entering nursing from another field."
    ),
    # Additional professional / graduate degrees (verified against each school's site).
    "columbia-emba": (
        "The Executive MBA — Columbia Business School's degree for working managers, "
        "delivered on a weekend or block schedule while students continue their careers."
    ),
    "columbia-accounting-ms": (
        "The M.S. in Accounting and Fundamental Analysis — financial-statement analysis, "
        "valuation, and capital-markets research at Columbia Business School."
    ),
    "columbia-financial-economics-ms": (
        "The M.S. in Financial Economics — a rigorous, research-oriented preparation in "
        "asset pricing and corporate finance at Columbia Business School."
    ),
    "columbia-marketing-science-ms": (
        "The M.S. in Marketing Science — quantitative marketing, consumer analytics, and "
        "data-driven decision-making at Columbia Business School."
    ),
    "columbia-business-phd": (
        "The Ph.D. in Business — doctoral research across accounting, finance, management, "
        "marketing, and decision sciences at Columbia Business School."
    ),
    "columbia-llm": (
        "The Master of Laws (LL.M.) — a one-year advanced law degree at Columbia Law School "
        "for graduates of a first law degree, with strength in transnational practice."
    ),
    "columbia-jsd": (
        "The Doctor of the Science of Law (J.S.D.) — Columbia Law School's research "
        "doctorate for scholars pursuing sustained, original legal research."
    ),
    "columbia-physical-therapy-dpt": (
        "The Doctor of Physical Therapy — clinical training in movement science, "
        "rehabilitation, and patient care through the Programs in Physical Therapy at CUIMC."
    ),
    "columbia-genetic-counseling-ms": (
        "The M.S. in Genetic Counseling — training in medical genetics, risk assessment, "
        "and patient counseling at Columbia University Irving Medical Center."
    ),
    "columbia-human-nutrition-ms": (
        "The M.S. in Human Nutrition — nutritional science, metabolism, and clinical and "
        "public-health nutrition at Columbia University Irving Medical Center."
    ),
    "columbia-dental-dds": (
        "The Doctor of Dental Surgery — Columbia's four-year professional dental degree, "
        "integrating the basic biomedical sciences with supervised clinical patient care."
    ),
    "columbia-journalism-ma": (
        "The M.A. in Journalism — a subject-specialized degree (arts, business, politics, "
        "science) for experienced journalists at the Columbia Journalism School."
    ),
    "columbia-data-journalism-ms": (
        "The M.S. in Data Journalism — reporting with data, computation, and visualization "
        "at the Columbia Journalism School."
    ),
    "columbia-communications-phd": (
        "The Ph.D. in Communications — doctoral research on media, journalism, and "
        "communication, offered jointly by the Journalism School and GSAS."
    ),
    "columbia-sustainable-development-phd": (
        "The Ph.D. in Sustainable Development — doctoral research bridging economics and the "
        "natural sciences on development and the environment at SIPA."
    ),
    "columbia-health-administration-mha": (
        "The Master of Health Administration — management, finance, and leadership for "
        "health-care organizations at the Mailman School of Public Health."
    ),
    "columbia-biostatistics-ms": (
        "The M.S. in Biostatistics — statistical theory and methods for the design and "
        "analysis of health and biomedical studies at the Mailman School of Public Health."
    ),
    "columbia-public-health-drph": (
        "The Doctor of Public Health — advanced leadership and applied research training for "
        "senior public-health practice at the Mailman School of Public Health."
    ),
    "columbia-social-work-phd": (
        "The Ph.D. in Social Work — doctoral research in social welfare policy and clinical "
        "intervention at the Columbia School of Social Work."
    ),
    "columbia-urban-planning-ms": (
        "The M.S. in Urban Planning — planning theory, policy, and practice for equitable "
        "and sustainable cities at Columbia GSAPP."
    ),
    "columbia-historic-preservation-ms": (
        "The M.S. in Historic Preservation — conservation, history, and policy of the built "
        "environment at Columbia GSAPP."
    ),
    "columbia-real-estate-development-ms": (
        "The M.S. in Real Estate Development — finance, design, and development of real "
        "estate at Columbia GSAPP."
    ),
    "columbia-urban-design-ms": (
        "The M.S. in Urban Design — the design of cities and public space at Columbia GSAPP."
    ),
    "columbia-architecture-aad-ms": (
        "The M.S. in Advanced Architectural Design — a post-professional design degree for "
        "architects at Columbia GSAPP."
    ),
    "columbia-film-media-studies-ma": (
        "The M.A. in Film and Media Studies — the history, theory, and criticism of film "
        "and moving-image media at the Columbia School of the Arts."
    ),
    "columbia-nursing-dnp": (
        "The Doctor of Nursing Practice — the terminal practice doctorate preparing "
        "advanced-practice nurse leaders at Columbia School of Nursing."
    ),
    "columbia-nursing-phd": (
        "The Ph.D. in Nursing — doctoral nursing-science research at Columbia School of "
        "Nursing."
    ),
}

# Field-name aliases: map a program-name field to its CORE key when they differ.
FIELD_ALIASES: dict[str, str] = {
    "Russian Literature and Culture": "Russian Language and Culture",
}
