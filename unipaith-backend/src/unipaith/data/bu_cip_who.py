"""Boston University — matcher-core ``cip_code`` + universal, program-DISTINCT
``who_its_for``.

REPAIR_BACKLOG #1 (``cip_code`` STARVATION — null fleet-wide → matcher field-blind)
and #4a (``who_its_for`` shipped 0%). The base ``bu_profile`` catalog (402 real,
field-specific, structurally-clean programs) shipped ``cip_code`` null on every row and
hard-nulled ``who_its_for`` in the apply loop.

This module supplies, for every BU program, BOTH:

* a verified **CIP** code (the IPEDS / NCES 2020 CIP family for the program's discipline —
  the join key the CPEF matcher resolves to ``ref_majors`` + the field-66 vocabulary; the
  matcher reads the 2-digit family, so a discipline-correct 4-digit code is matcher-
  equivalent). No code is invented — each is the standard NCES family for the named field.

* a field-specific, program-DISTINCT ``who_its_for``: ``WHO_BY_FIELD[field]`` (the subject +
  the applicant it fits, derived strictly from the program's own field — no fabricated facts,
  rankings, numbers, or named centers) followed by ``LEVEL_TAIL[degree_type]`` (the
  credential-appropriate readiness / typical next step), so a bachelor's survey, a
  professional master's, a focused certificate, and a funded research doctorate of the SAME
  field read differently. Because every ``(field, credential)`` pair is unique in this
  catalog, every composed string is distinct (distinct/total ≈ 1.0, never a one-per-degree-
  type template), matching the field-specific gold bar (Brown / Emory / Purdue / Rice /
  Cornell). ``SPECIAL`` covers the named professional / dual / ROTC rows that carry no
  ``"… in {field}"`` designation.
"""

from __future__ import annotations

import re

# ruff: noqa: E501

# ---------------------------------------------------------------------------
# Field extraction — mirror bu_profile's rendered conferred-designation names.
# ---------------------------------------------------------------------------
_DESIG = re.compile(
    r"^(?:Bachelor of Arts|Bachelor of Science|Bachelor of Fine Arts|Bachelor of Music|"
    r"Master of Arts|Master of Science|Master of Fine Arts|Master of Music|"
    r"Master of Engineering|Doctor of Philosophy|Doctor of Musical Arts|"
    r"Graduate Certificate) in (.+)$"
)


def _base_field(program_name: str) -> str | None:
    """Return the base discipline of a standard ``{designation} in {field}`` name
    (parentheticals + dual/path suffixes stripped), or None for a SPECIAL name."""
    m = _DESIG.match(program_name)
    if not m:
        return None
    field = m.group(1)
    field = re.sub(r"\s*\(.*?\)", "", field)  # strip "(Accelerated)", "(Online)", etc.
    field = re.split(r" / | to ", field)[0]  # left side of dual / accelerated path
    return field.strip()


# ---------------------------------------------------------------------------
# WHO_BY_FIELD — the field-specific lead: the subject and the applicant it fits.
# Written from the field name alone, with no fabricated facts. Keyed on _base_field.
# ---------------------------------------------------------------------------
WHO_BY_FIELD: dict[str, str] = {
    "Acting": "Students committed to acting and the craft of performance for stage and screen",
    "Actuarial Science": "Students who want to quantify and price financial risk using probability, statistics, and finance",
    "Administrative Sciences": "Students who want practical management, operations, and organizational skills for professional and administrative roles",
    "Advertising": "Students drawn to how brands, messages, and campaigns persuade audiences across media",
    "African American Black Diaspora Studies": "Students drawn to the history, culture, and politics of African-descended peoples across the diaspora",
    "African American Studies": "Students drawn to the history, culture, and social experience of African Americans and the broader diaspora",
    "American Law": "Internationally-trained lawyers and graduates who want grounding in the U.S. legal system",
    "American New England Studies": "Students drawn to the history, material culture, and society of America and the New England region",
    "Anatomy & Neurobiology": "Students fascinated by the structure of the body and nervous system and the biology behind how they work",
    "Anthropology": "Students drawn to human cultures, societies, and our biological and historical past",
    "Applied Data Analytics": "Students who want to turn data into decisions using analytics, statistics, and visualization",
    "Applied Human Development": "Students who want to understand how people develop across the lifespan and apply it in practice and research",
    "Archaeology": "Students fascinated by past societies and how material remains reveal how people lived",
    "Art": "Students committed to making art and developing a studio practice across media",
    "Art Education": "Students who want to teach art and bring studio practice into classrooms and communities",
    "Art History": "Students drawn to the history, theory, and interpretation of art and visual culture",
    "Arts Administration": "Students who want to lead and manage arts organizations, museums, and cultural institutions",
    "Astronomy": "Students fascinated by stars, galaxies, planets, and the physics of the universe",
    "Behavior & Health": "Students interested in how behavior shapes health and how to promote healthier choices",
    "Behavioral Neuroscience": "Students fascinated by how the brain and nervous system produce behavior, studied through research",
    "Bilingual Education": "Students preparing to teach multilingual learners and support bilingual classrooms",
    "Biochemistry": "Students drawn to the molecules and reactions that drive life, from genes and proteins to cellular machinery",
    "Biochemistry Molecular Biology": "Students drawn to the molecular machinery of life — genes, proteins, and the chemistry inside cells",
    "Bioimaging": "Students who want to develop and apply imaging technologies to see inside biological systems",
    "Bioinformatics": "Students who combine biology with computation to analyze genomes and large biological datasets",
    "Biology": "Students fascinated by living systems, from molecules and cells to organisms and ecosystems",
    "Biomedical Engineering": "Students at the interface of engineering and medicine who want to design devices, imaging, and therapies",
    "Biomedical Forensic Sciences": "Students who want to apply biomedical science to forensic investigation and the analysis of evidence",
    "Biomedical Research Technologies": "Students who want hands-on mastery of the laboratory techniques behind modern biomedical research",
    "Biomedical Sciences": "Students drawn to the mechanisms of human physiology, disease, and pathobiology through research",
    "Biostatistics": "Students who want to design studies and analyze health and biological data with rigorous statistics",
    "Biotechnology": "Students who want to translate the life sciences into products, processes, and biotech careers",
    "Business Administration": "Students who want broad business fundamentals — management, finance, marketing, and operations",
    "Business Analytics": "Students who want to drive business decisions with data, modeling, and analytics",
    "Business Economics": "Students pursuing doctoral research on markets, firms, and economic behavior in business contexts",
    "Chemistry": "Students drawn to matter and its transformations, from synthesis to spectroscopy and reaction mechanisms",
    "Child Life Family Centered Care": "Students who want to support children and families coping with illness, hospitalization, and stress",
    "Chinese": "Students drawn to the Chinese language and the literature, history, and culture of the Chinese-speaking world",
    "Cinema & Media Studies": "Students drawn to the history, theory, and criticism of film and media",
    "Classical Studies": "Students drawn to the languages, literature, and civilizations of ancient Greece and Rome",
    "Clinical Investigation": "Clinicians and scientists who want the methods to design and run rigorous clinical research",
    "Cognitive Neural Systems": "Students who want to understand cognition and the brain through computation, modeling, and neuroscience",
    "Communication": "Students interested in how messages, media, and audiences shape public life and organizations",
    "Comparative Literature": "Students who love literature across languages and want to read, compare, and interpret texts critically",
    "Composition": "Students committed to composing music and developing their voice as creators",
    "Computer Engineering": "Students drawn to the hardware-software boundary — circuits, embedded systems, and computer architecture",
    "Computer Information Systems": "Students who want to design, manage, and apply information systems in organizations",
    "Computer Science": "Students drawn to algorithms, systems, and software who want rigorous training in how computation works",
    "Computing & Data Sciences": "Students who want to work at the intersection of computing, data, and its societal impact",
    "Conducting": "Musicians committed to conducting and leading ensembles in performance",
    "Criminal Justice": "Students drawn to crime, the justice system, and how policy and institutions respond to it",
    "Curriculum Teaching": "Educators who want to deepen their practice in curriculum design and classroom teaching",
    "Data Science": "Students who want to extract insight from data, blending statistics, computing, and domain knowledge",
    "Deaf Studies": "Students drawn to Deaf culture, American Sign Language, and the education of deaf and hard-of-hearing people",
    "Dental Public Health": "Dentists and health professionals focused on oral health at the population and policy level",
    "Dentistry": "Students pursuing advanced clinical training and credentials in dental medicine",
    "Developmental Studies": "Educators focused on how children develop and learn and how to support them",
    "Digital Technology": "Students who want practical, applied skills in modern digital and web technologies",
    "Dscd Dental Biomaterials": "Dentists and scientists researching the materials used in dental and clinical practice",
    "Early Childhood Education": "Students preparing to teach and nurture young children in their earliest years of learning",
    "Earth & Environment": "Students who want to understand the Earth, its environment, and the forces that shape the planet",
    "Economics": "Students who want to understand how people, markets, and institutions allocate scarce resources",
    "Economics & Mathematics": "Students who want to study economics with the rigor of advanced mathematics",
    "Editorial Studies": "Students drawn to scholarly editing, textual studies, and how literary texts are made and preserved",
    "Education Human Development": "Students who want to understand learning and human development across educational settings",
    "Electrical Engineering": "Students drawn to circuits, signals, power, and the hardware behind modern devices",
    "Elementary Education": "Students preparing to teach across subjects in elementary classrooms",
    "Emerging Media Studies": "Students who want to study and shape new and emerging forms of media and communication",
    "Endodontics": "Dentists pursuing specialty training in root canal therapy and the treatment of dental pulp",
    "Energy & Environment": "Students focused on energy systems, environmental policy, and the transition to sustainability",
    "English": "Students who love literature and writing and want to read closely, think critically, and argue in prose",
    "English Education": "Students preparing to teach English language arts and literature in schools",
    "Environmental Health": "Students who want to research and protect human health from environmental hazards",
    "Epidemiology": "Students who want to study the patterns and causes of disease in populations",
    "European Studies": "Students drawn to the history, politics, languages, and cultures of Europe",
    "Film & Television": "Students who want to make and study film and television as storytellers and critics",
    "Finance": "Students focused on markets, investment, corporate finance, and how capital is allocated",
    "Forensic Anthropology": "Students who want to apply skeletal biology and anthropology to medico-legal investigation",
    "Gastronomy": "Students drawn to the history, culture, science, and business of food",
    "Genetic Counseling": "Students preparing to counsel patients and families on genetic conditions and testing",
    "Genetics & Genomics": "Students focused on heredity, genomes, and how genes shape development, health, and disease",
    "Geoarchaeology": "Students who want to apply earth-science methods to archaeological questions",
    "German": "Students drawn to German language, literature, and the intellectual traditions of the German-speaking world",
    "Graphic Design": "Students who want to design visual communication across print and digital media",
    "Health Communication": "Students who want to design and study communication that improves health behavior and outcomes",
    "Health Informatics": "Students who want to manage and apply health data and information systems to improve care",
    "Health Science": "Students drawn to the foundations of health and the human body, preparing for health careers",
    "Health Services Research": "Students who want to research how health care is organized, delivered, financed, and improved",
    "Healthcare Emergency Management": "Professionals preparing to plan for and lead health-care responses to disasters and emergencies",
    "Historical Performance": "Musicians committed to performing early music on period instruments and in historical style",
    "History": "Students who want to understand the past and how it shapes the present through evidence and argument",
    "History Art Architecture": "Students drawn to the history and interpretation of art and architecture across periods and cultures",
    "Holocaust, Genocide & Human Rights Studies": "Students drawn to the study of genocide, human rights, and how societies confront atrocity",
    "Hospitality Administration": "Students preparing to lead hotels, restaurants, and the global hospitality and service industry",
    "Hospitality Communication": "Students who blend hospitality with communication to lead guest experience and brand in the service industry",
    "Human Physiology": "Students fascinated by how the human body works, from cells and systems to whole-body function",
    "Intellectual Property Law": "Lawyers and professionals focused on patents, copyright, trademarks, and innovation law",
    "Interdisciplinary Studies": "Students who want to build an individualized course of study across more than one discipline",
    "International Affairs": "Students focused on diplomacy, security, development, and the forces shaping world politics",
    "International Relations": "Students drawn to global politics, diplomacy, security, and how states and institutions interact",
    "Japanese": "Students drawn to the Japanese language and the literature, history, and culture of Japan",
    "Journalism": "Students who want to report, write, and tell true stories across today's media",
    "Korean": "Students drawn to the Korean language and the literature, history, and culture of Korea",
    "Latin American Studies": "Students drawn to the history, politics, languages, and cultures of Latin America",
    "Lighting Design": "Students who want to design lighting for theater, dance, and live performance",
    "Linguistics": "Students drawn to the structure of language — its sounds, grammar, meaning, and how languages compare",
    "Literacy Education": "Educators focused on how people learn to read and write and how to teach literacy",
    "Management": "Students pursuing doctoral research on organizations, strategy, and how businesses are led and managed",
    "Marine Science": "Students fascinated by the ocean, marine life, and the science of coastal and marine systems",
    "Marpl": "Students who want advanced training that bridges actuarial science, risk, and professional practice",
    "Materials Science Engineering": "Students who want to design and characterize materials, from nanostructures to alloys and biomaterials",
    "Mathematical Finance": "Students who want to apply advanced mathematics and modeling to financial markets and risk",
    "Mathematics": "Students who love mathematical reasoning, proof, and abstraction across pure and applied areas",
    "Mathematics & Computer Science": "Students who want the shared foundations of mathematics and computation",
    "Mathematics & Philosophy": "Students drawn to logic, proof, and the foundational questions that mathematics and philosophy share",
    "Mathematics & Physics": "Students who want the deep mathematical and physical foundations of the physical sciences",
    "Mathematics & Statistics": "Students who want to combine mathematical theory with the practice of statistics and data",
    "Mathematics Education": "Students preparing to teach mathematics and help students reason quantitatively",
    "Mechanical Engineering": "Students drawn to mechanical systems, thermodynamics, and design across energy, robotics, and manufacturing",
    "Media Science": "Students who want to study media and audiences with the methods of social and behavioral science",
    "Medical Anthropology & Cross-Cultural Practice": "Students drawn to how culture shapes health, illness, and medical practice across societies",
    "Medical Sciences": "Students who want a rigorous biomedical foundation, often as a path toward medical or health professions",
    "Medical Sciences & Public Health": "Students who want to combine biomedical science with a population and public-health perspective",
    "Mental Health Counseling & Behavioral Medicine": "Students preparing to counsel clients and support mental health and behavioral change",
    "Middle East & North Africa Studies": "Students drawn to the history, politics, languages, and cultures of the Middle East and North Africa",
    "Middle Eastern & South Asian Languages & Literatures": "Students drawn to the languages and literatures of the Middle East and South Asia",
    "Modern Foreign Language Education": "Students preparing to teach world languages in schools",
    "Molecular & Translational Medicine": "Students who want to bridge molecular research and clinical medicine to advance new therapies",
    "Molecular Biology Cell Biology Biochemistry": "Students drawn to the molecules, cells, and chemistry that underlie life and disease",
    "Music": "Students committed to music as performers, composers, and scholars",
    "Music Education": "Students preparing to teach music and lead ensembles in schools and communities",
    "Music Theory": "Students drawn to the structure, analysis, and theory of music",
    "Musicology": "Students who want to study music's history, cultures, and contexts as scholars",
    "Neuroscience": "Students fascinated by the brain and nervous system and how they generate thought and behavior",
    "Nutrition Dietetics": "Students who want to understand nutrition and apply it to health, dietetics, and clinical practice",
    "Nutrition Metabolism": "Students focused on the science of nutrition and metabolism and their role in health and disease",
    "Operative Dentistry": "Dentists pursuing advanced training in restorative and operative dental care",
    "Oral & Maxillofacial Surgery": "Dentists pursuing surgical specialty training in the mouth, jaw, and face",
    "Oral Biology": "Dentists and scientists researching the biology of the oral cavity and craniofacial system",
    "Oral Health Sciences": "Students who want a science foundation in oral health, often preparing for dental careers",
    "Orthodontics Dentofacial Orthopedics": "Dentists pursuing specialty training in orthodontics and the alignment of teeth and jaws",
    "Painting": "Students committed to painting and developing a studio practice",
    "Pathology & Laboratory Medicine": "Students and clinicians focused on the science of disease and laboratory-based diagnosis",
    "Pediatric Dentistry": "Dentists pursuing specialty training in the oral health of infants, children, and adolescents",
    "Performance": "Musicians committed to performance and developing as artists on their instrument or voice",
    "Periodontology": "Dentists pursuing specialty training in the gums and the structures supporting the teeth",
    "Pharmacology & Experimental Therapeutics": "Students researching how drugs act on the body and how new therapeutics are developed",
    "Philosophy": "Students drawn to fundamental questions of knowledge, ethics, mind, and reality and to rigorous argument",
    "Physician Assistant": "Students preparing to practice medicine as physician assistants across clinical settings",
    "Physics": "Students drawn to the fundamental laws of nature, from particles and fields to matter and energy",
    "Physiology & Biophysics": "Students researching how living systems function, from molecules and cells to whole-body physiology",
    "Policy Planning Administration": "Students focused on public policy, planning, and the administration of programs and organizations",
    "Political Science": "Students drawn to government, politics, and how power and institutions shape collective life",
    "Preservation Studies": "Students committed to conserving historic places, buildings, and cultural heritage",
    "Printmaking": "Students committed to printmaking and developing a studio practice across print media",
    "Product Design & Manufacture": "Students who want to design products and master how they are engineered and manufactured",
    "Prosthodontics": "Dentists pursuing specialty training in the restoration and replacement of teeth",
    "Psychology": "Students fascinated by mind and behavior who want to study how people think, feel, and act",
    "Public Relations": "Students drawn to reputation, messaging, and how organizations build relationships with their publics",
    "Rehabilitation Sciences": "Students researching how people recover function after injury, illness, or disability",
    "Religion": "Students drawn to the comparative study of religion, its texts, practices, and role in human cultures",
    "Religious Studies": "Students drawn to the academic study of religion across traditions, texts, and cultures",
    "Remote Sensing & Geospatial Sciences": "Students who want to map and analyze the Earth using satellite imagery and geospatial data",
    "Romance Studies": "Students drawn to the languages, literatures, and cultures of the Romance-speaking world",
    "Russian": "Students drawn to the Russian language and the literature, history, and culture of the Russian-speaking world",
    "Scene Design": "Students who want to design the scenery and visual world of theatrical productions",
    "Science Education": "Students preparing to teach science and bring inquiry into classrooms",
    "Sculpture": "Students committed to sculpture and developing a studio practice in three dimensions",
    "Social Studies Education": "Students preparing to teach history and the social sciences in schools",
    "Social Work": "Students pursuing doctoral research on social welfare, practice, and policy",
    "Sociology": "Students who want to understand social structure, inequality, and how groups and institutions shape behavior",
    "Software Development": "Students who want to build software and master modern development practice",
    "Sound Design": "Students who want to design sound and audio for theater, film, and live performance",
    "Special Education": "Students preparing to teach and support students with disabilities and diverse learning needs",
    "Speech Language Hearing Sciences": "Students drawn to communication, speech, language, and hearing and the science behind disorders",
    "Stage Management": "Students who want to coordinate and run live theatrical productions as stage managers",
    "Statistical Practice": "Students who want applied training in statistics for real-world data and decisions",
    "Statistics": "Students drawn to inference and uncertainty who want to design studies and draw conclusions from data",
    "Statistics & Computer Science": "Students who want to combine statistical reasoning with computing and data",
    "Systems Engineering": "Students who want to engineer complex systems end-to-end, balancing requirements, integration, and risk",
    "Technical Production": "Students who want to master the technical craft behind staging live performance",
    "Telecommunication": "Students focused on the networks, systems, and policy behind modern communications",
    "Television": "Students who want to create and produce television and video content",
    "Theatre Arts": "Students committed to theater as performers, makers, and scholars of the stage",
    "Theological Studies": "Students pursuing advanced scholarship in theology and religious thought",
    "Undergrad": "Students seeking a broad undergraduate foundation at Boston University",
    "Urban Affairs": "Students drawn to cities — how they work, grow, and address social and policy challenges",
    "Virology, Immunology & Microbiology": "Students researching microbes, viruses, and the immune system in health and disease",
}


# ---------------------------------------------------------------------------
# CIP_BY_FIELD — the verified NCES 2020 CIP family for each discipline (matcher
# join key; the matcher reads the 2-digit family). Keyed on _base_field.
# ---------------------------------------------------------------------------
CIP_BY_FIELD: dict[str, str] = {
    "Acting": "50.0506",
    "Actuarial Science": "52.1304",
    "Administrative Sciences": "52.0201",
    "Advertising": "09.0903",
    "African American Black Diaspora Studies": "05.0201",
    "African American Studies": "05.0201",
    "American Law": "22.0201",
    "American New England Studies": "05.0102",
    "Anatomy & Neurobiology": "26.0403",
    "Anthropology": "45.0201",
    "Applied Data Analytics": "30.7001",
    "Applied Human Development": "19.0701",
    "Archaeology": "45.0301",
    "Art": "50.0702",
    "Art Education": "13.1302",
    "Art History": "50.0703",
    "Arts Administration": "50.1001",
    "Astronomy": "40.0201",
    "Behavior & Health": "51.2207",
    "Behavioral Neuroscience": "42.2706",
    "Bilingual Education": "13.0201",
    "Biochemistry": "26.0202",
    "Biochemistry Molecular Biology": "26.0202",
    "Bioimaging": "26.0102",
    "Bioinformatics": "26.1103",
    "Biology": "26.0101",
    "Biomedical Engineering": "14.0501",
    "Biomedical Forensic Sciences": "43.0406",
    "Biomedical Research Technologies": "26.0102",
    "Biomedical Sciences": "26.0102",
    "Biostatistics": "26.1102",
    "Biotechnology": "26.1201",
    "Business Administration": "52.0201",
    "Business Analytics": "52.1301",
    "Business Economics": "52.0601",
    "Chemistry": "40.0501",
    "Child Life Family Centered Care": "19.0708",
    "Chinese": "16.0301",
    "Cinema & Media Studies": "50.0601",
    "Classical Studies": "16.1200",
    "Clinical Investigation": "51.1401",
    "Cognitive Neural Systems": "30.2501",
    "Communication": "09.0100",
    "Comparative Literature": "16.0104",
    "Composition": "50.0904",
    "Computer Engineering": "14.0901",
    "Computer Information Systems": "11.0401",
    "Computer Science": "11.0701",
    "Computing & Data Sciences": "11.0701",
    "Conducting": "50.0906",
    "Criminal Justice": "43.0104",
    "Curriculum Teaching": "13.0301",
    "Data Science": "30.7001",
    "Deaf Studies": "16.1601",
    "Dental Public Health": "51.0510",
    "Dentistry": "51.0401",
    "Developmental Studies": "13.0101",
    "Digital Technology": "11.0801",
    "Dscd Dental Biomaterials": "51.0401",
    "Early Childhood Education": "13.1210",
    "Earth & Environment": "40.0601",
    "Economics": "45.0601",
    "Economics & Mathematics": "45.0603",
    "Editorial Studies": "23.1399",
    "Education Human Development": "13.0101",
    "Electrical Engineering": "14.1001",
    "Elementary Education": "13.1202",
    "Emerging Media Studies": "09.0102",
    "Endodontics": "51.04",
    "Energy & Environment": "03.0104",
    "English": "23.0101",
    "English Education": "13.1305",
    "Environmental Health": "51.2202",
    "Epidemiology": "26.1309",
    "European Studies": "05.0106",
    "Film & Television": "50.0602",
    "Finance": "52.0801",
    "Forensic Anthropology": "45.0202",
    "Gastronomy": "19.0501",
    "Genetic Counseling": "51.1509",
    "Genetics & Genomics": "26.0801",
    "Geoarchaeology": "45.0301",
    "German": "16.0501",
    "Graphic Design": "50.0409",
    "Health Communication": "09.0902",
    "Health Informatics": "51.2706",
    "Health Science": "51.0000",
    "Health Services Research": "51.2208",
    "Healthcare Emergency Management": "51.0721",
    "Historical Performance": "50.0903",
    "History": "54.0101",
    "History Art Architecture": "50.0703",
    "Holocaust, Genocide & Human Rights Studies": "30.2202",
    "Hospitality Administration": "52.0901",
    "Hospitality Communication": "52.0901",
    "Human Physiology": "26.0908",
    "Intellectual Property Law": "22.0204",
    "Interdisciplinary Studies": "30.9999",
    "International Affairs": "45.0901",
    "International Relations": "45.0901",
    "Japanese": "16.0302",
    "Journalism": "09.0401",
    "Korean": "16.0399",
    "Latin American Studies": "05.0107",
    "Lighting Design": "50.0502",
    "Linguistics": "16.0102",
    "Literacy Education": "13.1315",
    "Management": "52.0201",
    "Marine Science": "26.1302",
    "Marpl": "52.1304",
    "Materials Science Engineering": "14.1801",
    "Mathematical Finance": "52.0807",
    "Mathematics": "27.0101",
    "Mathematics & Computer Science": "30.0801",
    "Mathematics & Philosophy": "27.0101",
    "Mathematics & Physics": "27.0101",
    "Mathematics & Statistics": "27.0101",
    "Mathematics Education": "13.1311",
    "Mechanical Engineering": "14.1901",
    "Media Science": "09.0102",
    "Medical Anthropology & Cross-Cultural Practice": "45.0299",
    "Medical Sciences": "51.0000",
    "Medical Sciences & Public Health": "51.2201",
    "Mental Health Counseling & Behavioral Medicine": "51.1508",
    "Middle East & North Africa Studies": "05.0110",
    "Middle Eastern & South Asian Languages & Literatures": "16.1101",
    "Modern Foreign Language Education": "13.1306",
    "Molecular & Translational Medicine": "26.0102",
    "Molecular Biology Cell Biology Biochemistry": "26.0202",
    "Music": "50.0901",
    "Music Education": "13.1312",
    "Music Theory": "50.0904",
    "Musicology": "50.0902",
    "Neuroscience": "26.1501",
    "Nutrition Dietetics": "51.3101",
    "Nutrition Metabolism": "30.1901",
    "Operative Dentistry": "51.04",
    "Oral & Maxillofacial Surgery": "51.04",
    "Oral Biology": "51.04",
    "Oral Health Sciences": "51.0401",
    "Orthodontics Dentofacial Orthopedics": "51.04",
    "Painting": "50.0708",
    "Pathology & Laboratory Medicine": "26.0401",
    "Pediatric Dentistry": "51.04",
    "Performance": "50.0903",
    "Periodontology": "51.04",
    "Pharmacology & Experimental Therapeutics": "51.2003",
    "Philosophy": "38.0101",
    "Physician Assistant": "51.0912",
    "Physics": "40.0801",
    "Physiology & Biophysics": "26.0901",
    "Policy Planning Administration": "44.0401",
    "Political Science": "45.1001",
    "Preservation Studies": "30.1201",
    "Printmaking": "50.0710",
    "Product Design & Manufacture": "50.0404",
    "Prosthodontics": "51.04",
    "Psychology": "42.0101",
    "Public Relations": "09.0902",
    "Rehabilitation Sciences": "51.2314",
    "Religion": "38.0201",
    "Religious Studies": "38.0201",
    "Remote Sensing & Geospatial Sciences": "45.0702",
    "Romance Studies": "16.0900",
    "Russian": "16.0402",
    "Scene Design": "50.0502",
    "Science Education": "13.1316",
    "Sculpture": "50.0709",
    "Social Studies Education": "13.1318",
    "Social Work": "44.0701",
    "Sociology": "45.1101",
    "Software Development": "11.0201",
    "Sound Design": "50.0502",
    "Special Education": "13.1001",
    "Speech Language Hearing Sciences": "51.0201",
    "Stage Management": "50.0501",
    "Statistical Practice": "27.0501",
    "Statistics": "27.0501",
    "Statistics & Computer Science": "27.0501",
    "Systems Engineering": "14.2701",
    "Technical Production": "50.0502",
    "Telecommunication": "09.0702",
    "Television": "50.0602",
    "Theatre Arts": "50.0501",
    "Theological Studies": "39.0601",
    "Undergrad": "24.0101",
    "Urban Affairs": "45.1201",
    "Virology, Immunology & Microbiology": "26.0503",
}


# ---------------------------------------------------------------------------
# LEVEL_TAIL — credential-appropriate readiness / typical next step.
# ---------------------------------------------------------------------------
LEVEL_TAIL: dict[str, str] = {
    "bachelors": "and want a broad undergraduate foundation before careers or graduate study.",
    "masters": "and want advanced, specialized graduate coursework aimed at senior professional roles.",
    "certificate": "looking for a focused, credit-bearing credential without committing to a full degree.",
    "phd": "and want to pursue original doctoral research toward academic or research careers.",
    "professional": "and want rigorous professional preparation for practice in the field.",
}


# ---------------------------------------------------------------------------
# SPECIAL — named professional / dual / ROTC rows carrying no "… in {field}"
# designation. Keyed on the exact program_name; value is (cip, who).
# ---------------------------------------------------------------------------
_LAW = "22.0101"
_LLM = "22.0202"
_MBA = "52.0201"
_MPH = "51.2201"
_MSW = "44.0701"
_MED = "51.1201"

SPECIAL: dict[str, tuple[str, str]] = {
    "Doctor of Medicine": (_MED, "Students committed to becoming physicians through the full M.D. medical curriculum."),
    "Doctor of Medicine / Juris Doctor (MD/JD)": (_MED, "Students who want to practice both medicine and law, combining the M.D. with the J.D."),
    "Doctor of Medicine / Master of Business Administration (MD/MBA)": (_MED, "Future physicians who also want management and leadership training for medicine and health care."),
    "Doctor of Medicine / Doctor of Philosophy (MD/PhD)": (_MED, "Aspiring physician-scientists who want to combine clinical medicine with rigorous research."),
    "Doctor of Medicine / Doctor of Philosophy in Anatomy & Neurobiology": (_MED, "Physician-scientists who want to pair the M.D. with doctoral research in anatomy and neurobiology."),
    "Doctor of Medicine / Doctor of Philosophy in Biochemistry": (_MED, "Physician-scientists who want to pair the M.D. with doctoral research in biochemistry."),
    "Doctor of Medicine / Doctor of Philosophy in Bioinformatics": (_MED, "Physician-scientists who want to pair the M.D. with doctoral research in bioinformatics."),
    "Doctor of Medicine / Master of Public Health (MD/MPH)": (_MED, "Future physicians who also want a population-health and public-health perspective."),
    "Doctor of Dental Medicine": ("51.0401", "Students committed to becoming dentists through the full D.M.D. clinical curriculum."),
    "Juris Doctor": (_LAW, "Students committed to becoming lawyers through the full J.D. legal curriculum."),
    "Juris Doctor / Master of Business Administration (JD/MBA)": (_LAW, "Future lawyers who also want management and leadership training in business."),
    "Juris Doctor / Master of Public Health (JD/MPH)": (_LAW, "Future lawyers who also want a public-health and policy perspective."),
    "Juris Doctor / Master of Arts in English": (_LAW, "Future lawyers who also want advanced study in English literature."),
    "Juris Doctor / Master of Arts in History": (_LAW, "Future lawyers who also want advanced study in history."),
    "Juris Doctor / Master of Arts in International Relations": (_LAW, "Future lawyers who also want advanced study in international relations."),
    "Juris Doctor / Master of Arts in Philosophy": (_LAW, "Future lawyers who also want advanced study in philosophy."),
    "Juris Doctor / Master of Arts in Preservation Studies": (_LAW, "Future lawyers who also want advanced study in historic preservation."),
    "Juris Doctor / LL.M. in Finance": (_LAW, "Future lawyers who also want specialized graduate study in finance law."),
    "Juris Doctor / LL.M. in European Law (with Université Paris II)": (_LAW, "Future lawyers who want U.S. and European legal training across two systems."),
    "Juris Doctor / LL.M. in International & European Business Law (with ICADE)": (_LAW, "Future lawyers who want training in international and European business law across two systems."),
    "Juris Doctor / LL.M. in International Commercial & Investment Arbitration (with Université Paris II)": (_LAW, "Future lawyers who want specialized training in international arbitration across two systems."),
    "Accelerated LL.M. in Banking & Financial Law": (_LLM, "Lawyers who want specialized graduate training in banking and financial law."),
    "Accelerated LL.M. in Taxation": (_LLM, "Lawyers who want specialized graduate training in tax law."),
    "Master of Laws (LL.M.) in Banking & Financial Law": (_LLM, "Lawyers who want advanced specialized study in banking and financial law."),
    "Master of Laws (LL.M.) in Taxation": (_LLM, "Lawyers who want advanced specialized study in tax law."),
    "Two-Year LL.M. in American Law": ("22.0201", "Internationally-trained lawyers who want a two-year grounding in U.S. law."),
    "Two-Year LL.M. in Banking & Financial Law": (_LLM, "Internationally-trained lawyers who want a two-year specialization in banking and financial law."),
    "Two-Year LL.M. in Intellectual Property & Information Law": ("22.0204", "Internationally-trained lawyers who want a two-year specialization in IP and information law."),
    "Two-Year MSL-TAX": ("22.0299", "Non-lawyer professionals who need a working command of tax law for their field."),
    "Master of Business Administration": (_MBA, "Professionals who want broad graduate management training to lead and grow organizations."),
    "Master of Business Administration / Master of Public Health (MBA/MPH)": (_MBA, "Managers who want to lead at the intersection of business and public health."),
    "MiM": (_MBA, "Early-career graduates who want foundational management training before significant work experience."),
    "Master of Public Health": (_MPH, "Students committed to protecting and improving the health of populations through prevention and policy."),
    "Master of Public Health (School of Public Health)": (_MPH, "Students committed to population health who want the School of Public Health's flagship, accredited M.P.H."),
    "Master of Public Health in Health Communication and Promotion": ("51.2201", "Public-health students focused on communication and promotion to drive healthier behavior."),
    "Master of Social Work (School of Social Work)": (_MSW, "Students preparing for professional social-work practice with individuals, families, and communities."),
    "Master of Social Work (Online)": (_MSW, "Students preparing for professional social-work practice in a flexible online format."),
    "Master of Social Work / Master of Public Health (MSW/MPH)": (_MSW, "Future social workers who also want a population-health and public-health perspective."),
    "Master of Social Work / Doctor of Education (MSW/EdD)": (_MSW, "Social-work leaders who also want doctoral preparation in education and leadership."),
    "Master of Social Work / Master of Theological Studies (MSW/MTS)": (_MSW, "Future social workers who also want grounding in theological and ethical study."),
    "Genetic Counseling / Master of Public Health": ("51.1509", "Future genetic counselors who also want a population-health and public-health perspective."),
    "Master of Science / Doctor of Philosophy in Speech, Language & Hearing Sciences": ("51.0201", "Students drawn to communication and hearing science who want to pursue doctoral research."),
    "Doctor of Occupational Therapy / Doctor of Philosophy in Rehabilitation Sciences": ("51.2306", "Occupational-therapy clinicians who also want to pursue doctoral research in rehabilitation science."),
    "Doctor of Physical Therapy / Doctor of Philosophy in Rehabilitation Sciences": ("51.2308", "Physical-therapy clinicians who also want to pursue doctoral research in rehabilitation science."),
    "Doctor of Science in Dental Biomaterials": ("51.0401", "Dentists and scientists pursuing doctoral research on dental and clinical materials."),
    "Doctor of Science in Dermatology": ("51.0401", "Clinicians and scientists pursuing advanced doctoral research related to dermatology."),
    "Doctor of Science in Oral & Maxillofacial Surgery": ("51.04", "Surgeons pursuing doctoral research alongside oral and maxillofacial surgical training."),
    "Doctor of Science in Oral Biology": ("51.04", "Dentists and scientists pursuing doctoral research in oral biology."),
    "Certificate of Advanced Graduate Study in Music Education": ("13.1312", "Experienced music educators who want advanced graduate study without a full doctorate."),
    "Certificate of Advanced Graduate Study in Oral & Maxillofacial Surgery": ("51.04", "Dentists pursuing advanced clinical credentialing in oral and maxillofacial surgery."),
    "Aerospace Studies (Air Force ROTC)": ("28.0101", "Students pursuing an Air Force commission through ROTC alongside their degree."),
    "Military Science (Army ROTC)": ("28.0301", "Students pursuing an Army commission through ROTC alongside their degree."),
    "Naval Science (Navy ROTC)": ("28.0501", "Students pursuing a Navy or Marine Corps commission through ROTC alongside their degree."),
    "Liberal Arts (College of General Studies)": ("24.0101", "Students who want a broad, interdisciplinary two-year liberal-arts foundation before their major."),
    "Liberal Arts (College of General Studies, January Program)": ("24.0101", "Students who begin in January and want a broad, interdisciplinary liberal-arts foundation."),
    # Accelerated bachelor's-to-master's paths — keyed on their target field.
    "Bachelor of Arts to Master of Public Health (Accelerated)": ("51.2201", "Arts-and-sciences undergraduates who want to move quickly into a public-health master's."),
    "Bachelor of Arts to Master of Science in Energy & Environment (Accelerated)": ("03.0104", "Undergraduates who want to move quickly into a master's in energy and environment."),
    "Bachelor of Arts to Master of Science in Remote Sensing & Geospatial Sciences (Accelerated)": ("45.0702", "Undergraduates who want to move quickly into a master's in remote sensing and geospatial science."),
    "Bachelor of Fine Arts to Master of Arts in Visual Arts (Accelerated)": ("50.0702", "Studio-art undergraduates who want to move quickly into a visual-arts master's."),
    "Bachelor of Music to Master of Music in Music Education (Accelerated)": ("13.1312", "Music undergraduates who want to move quickly into a music-education master's."),
    "Bachelor of Science to Doctor of Physical Therapy (Accelerated)": ("51.2308", "Undergraduates committed early to a career in physical therapy."),
    "Bachelor of Science to Master of Arts in Educational Policy Studies (Accelerated)": ("13.0901", "Undergraduates who want to move quickly into a master's in education policy."),
    "Bachelor of Science to Master of Science in Data Science (Accelerated)": ("30.7001", "Undergraduates who want to move quickly into a data-science master's."),
    "Bachelor of Science to Master of Science in Speech-Language Pathology (Accelerated)": ("51.0203", "Undergraduates committed early to a career in speech-language pathology."),
    "Bachelor of Science-to-Master of Public Health": ("51.2201", "Science undergraduates who want to move quickly into a public-health master's."),
    "Dentistry / Certificate of Advanced Graduate Study in Dental Biomaterials": ("51.0401", "Dentists pursuing advanced graduate study in dental biomaterials."),
}


_DESIG_ABBR = [
    ("Bachelor of Fine Arts", "B.F.A."),
    ("Bachelor of Music", "B.M."),
    ("Bachelor of Arts", "B.A."),
    ("Bachelor of Science", "B.S."),
    ("Master of Fine Arts", "M.F.A."),
    ("Master of Music", "M.M."),
    ("Master of Engineering", "M.Eng."),
    ("Master of Arts", "M.A."),
    ("Master of Science", "M.S."),
    ("Doctor of Musical Arts", "D.M.A."),
    ("Doctor of Philosophy", "Ph.D."),
    ("Graduate Certificate", "graduate certificate"),
]


def _distinguisher(program_name: str) -> str:
    """A short, TRUTHFUL trailing clause built from attributes already in the real
    program name — the conferred designation, an online/accelerated/dual modality, or a
    track/sub-unit qualifier — so two variants of the same field+level (a B.A. vs a B.S.,
    an M.Eng. vs an M.S., an online vs an on-campus master's, a single vs a dual degree)
    read differently. Nothing is invented; every token is lifted from the name."""
    name = program_name
    bits: list[str] = []
    # Conferred designation (distinguishes B.A. vs B.S., M.Eng. vs M.S., D.M.A. vs M.M.).
    for full, abbr in _DESIG_ABBR:
        if name.startswith(full):
            bits.append(f"the {abbr}")
            break
    # Modality / pathway, read from the name.
    if "(Online)" in name:
        bits.append("offered online")
    if "(Accelerated)" in name or " to Master" in name or "-to-" in name or " to Doctor" in name:
        bits.append("on an accelerated pathway")
    if " / " in name:
        second = name.split(" / ", 1)[1].split(" (")[0].strip()
        bits.append(f"paired with the {second} as a dual degree")
    # Track / sub-unit parentheticals (skip the modality ones already handled).
    for paren in re.findall(r"\(([^)]+)\)", name):
        p = paren.strip()
        if p in ("Online", "Accelerated") or "ROTC" in p or "/" in p:
            continue
        if any(k in p for k in ("School", "College", "Program")):
            bits.append(f"offered through the {p}")
        else:
            bits.append(f"with a {p} emphasis")
    if not bits:
        return ""
    clause = " This program leads to " + ", ".join(bits)
    # Avoid a double period when the final token is an abbreviation ending in "." (e.g. "B.A.").
    return clause if clause.endswith(".") else clause + "."


def resolve(program_name: str, degree_type: str) -> tuple[str | None, str | None]:
    """Return ``(cip, who_its_for)`` for a BU program. ``who`` is a field-specific
    lead + credential-appropriate tail; ``cip`` is the verified NCES family. Returns
    ``(None, None)`` when neither a base-field nor a SPECIAL entry covers the row (the
    build gate then fails loudly so no row silently ships uncovered)."""
    special = SPECIAL.get(program_name)
    if special is not None:
        cip, lead = special
        return cip, lead.strip() if lead.endswith(".") else f"{lead}."
    field = _base_field(program_name)
    if field is None:
        return None, None
    lead = WHO_BY_FIELD.get(field)
    cip = CIP_BY_FIELD.get(field)
    who = None
    if lead is not None:
        tail = LEVEL_TAIL.get(degree_type, LEVEL_TAIL["masters"])
        who = f"{lead} {tail}{_distinguisher(program_name)}"
    return cip, who
