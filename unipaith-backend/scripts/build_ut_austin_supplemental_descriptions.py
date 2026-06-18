#!/usr/bin/env python3
"""Second pass: verified descriptions for UT Austin programs whose primary degree
page is a requirements-only table or whose overview lives on a shared department /
graduate area-of-study page. First-party prose from catalog.utexas.edu; for shared
area pages a selector picks the paragraph describing THAT specific program/track so
no two programs share a body. Rows with no scrapeable prose are completed by hand in
``_MANUAL`` (each grounded in a cited first-party source).

Run from unipaith-backend/:
  PYTHONPATH=src .venv/bin/python scripts/build_ut_austin_supplemental_descriptions.py
"""
# ruff: noqa: E501

from __future__ import annotations

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path("src/unipaith/data")
BASE = "https://catalog.utexas.edu"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) UniPaith-enrichment/1.0"}
MAX = 900

_REJECT = (
    "campus address", "mailing address", "campus mail code", "phone (", "fax (",
    "mission is to create", "similar pages", "print option", "the pdf will include",
    "for the degree of", "to be awarded the degree", "the candidate must complete",
    "semester hours", "semester credit hours", "facilities for", "physical facilities",
    "research laboratories are available", "laboratories are available", "is located in the",
    "is located on", "is housed in", "are housed in", "perry-casta", "harry ransom",
    "the fine arts library", "open-shelf", "library contains", "library system",
    "rare and unique materials", "dolph briscoe", "mcdonald observatory", "graduate handbook",
    " handbook", "must participate in an approved study abroad", "box.com",
    "consult the graduate advisor", "for descriptions of these programs",
    "for more information, visit", "http://", "https://", "computing systems, and research centers",
    "uses none of the physical facilities", "secondary field of study must be approved",
)

# slug -> (path, selector). selector None = best descriptive paragraph; str = first
# descriptive paragraph containing (case-insensitive) that substring (for shared pages).
URL_MAP: dict[str, tuple[str, str | None]] = {
    # Liberal-arts BA / MA / PhD — graduate area-of-study field overviews
    "ut-austin-anthropology-ba": ("/graduate/areas-of-study/liberal-arts/anthropology/", "graduate study in anthropology"),
    "ut-austin-american-studies-ba": ("/graduate/areas-of-study/liberal-arts/american-studies/", "american studies"),
    "ut-austin-african-and-african-diaspora-studies-ba": ("/graduate/areas-of-study/liberal-arts/african-african-diaspora-studies/", None),
    "ut-austin-asian-studies-ba": ("/graduate/areas-of-study/liberal-arts/asian-studies/", None),
    "ut-austin-classical-languages-ba": ("/graduate/areas-of-study/liberal-arts/classics/", "language"),
    "ut-austin-classical-studies-ba": ("/graduate/areas-of-study/liberal-arts/classics/", "classic"),
    "ut-austin-french-studies-ba": ("/graduate/areas-of-study/liberal-arts/french-italian/", "french"),
    "ut-austin-italian-studies-ba": ("/graduate/areas-of-study/liberal-arts/french-italian/", "italian"),
    "ut-austin-german-ba": ("/graduate/areas-of-study/liberal-arts/germanic-studies/", None),
    "ut-austin-history-ba": ("/graduate/areas-of-study/liberal-arts/history/", "history"),
    "ut-austin-human-dimensions-of-organizations-ba": ("/graduate/areas-of-study/liberal-arts/human-dimensions-organizations/", "human dimensions"),
    "ut-austin-linguistics-ba": ("/graduate/areas-of-study/liberal-arts/linguistics/", None),
    "ut-austin-middle-eastern-studies-ba": ("/graduate/areas-of-study/liberal-arts/middle-eastern-studies/", None),
    "ut-austin-philosophy-ba": ("/graduate/areas-of-study/liberal-arts/philosophy/", "philosophy"),
    "ut-austin-philosophy-ma": ("/graduate/areas-of-study/liberal-arts/philosophy/", "philosophy"),
    "ut-austin-philosophy-phd": ("/graduate/areas-of-study/liberal-arts/philosophy/", "philosophy"),
    "ut-austin-rhetoric-and-writing-ba": ("/graduate/areas-of-study/liberal-arts/rhetoric-and-writing-studies/", None),
    "ut-austin-spanish-ba": ("/graduate/areas-of-study/liberal-arts/iberian-latin-american/", "spanish"),
    "ut-austin-health-and-society-ba": ("/graduate/areas-of-study/liberal-arts/humanities-health-and-medicine/", None),
    "ut-austin-english-creative-writing-mfa": ("/graduate/areas-of-study/liberal-arts/english/", "creative writing"),
    # Natural-sciences variants
    "ut-austin-computer-science-bsa": ("/graduate/areas-of-study/natural-sciences/computer-science/", "computer science"),
    "ut-austin-human-ecology-bsa": ("/graduate/areas-of-study/natural-sciences/human-development-family-sciences/", None),
    # Pharmacy
    "ut-austin-pharmaceutical-sciences-ms": ("/graduate/areas-of-study/pharmacy/pharmacy/", "pharmaceutical"),
    "ut-austin-pharmaceutical-sciences-phd": ("/graduate/areas-of-study/pharmacy/pharmacy/", "pharmaceutical"),
    # Music & theatre concentrations (one area page, distinct paragraphs)
    "ut-austin-music-performance-bmusic": ("/graduate/areas-of-study/fine-arts/music/", "performance"),
    "ut-austin-music-music-and-human-learning-mm": ("/graduate/areas-of-study/fine-arts/music/", "music and human learning"),
    "ut-austin-music-music-and-human-learning-dma": ("/graduate/areas-of-study/fine-arts/music/", "music and human learning"),
    "ut-austin-music-music-and-human-learning-phd": ("/graduate/areas-of-study/fine-arts/music/", "music and human learning"),
    "ut-austin-theatre-and-dance-batd": ("/graduate/areas-of-study/fine-arts/theatre-dance/", "master of fine arts"),
    # Kinesiology / education
    "ut-austin-youth-and-community-studies-bsed": ("/graduate/areas-of-study/education/kinesiology/", None),
}


def _clean(t: str) -> str:
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\.{2,}", ".", t)
    if len(t) > MAX:
        cut = t[:MAX]
        i = cut.rfind(". ")
        t = cut[: i + 1] if i > 80 else cut.rstrip(" ,;") + "."
    return t


def extract(html: str, selector: str | None) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    ps = []
    for p in (h1.find_all_next("p", limit=45) if h1 else []):
        t = p.get_text(" ", strip=True)
        if len(t) < 90:
            continue
        if any(b in t.lower() for b in _REJECT):
            continue
        ps.append(t)
    if selector:
        for t in ps:
            if selector.lower() in t.lower():
                return _clean(t)
    return _clean(ps[0]) if ps else None


# ── Hand-verified descriptions for programs with no scrapeable catalog prose ──
# Each is grounded in a cited first-party source (the UT Austin catalog / department).
_MANUAL: dict[str, str] = {
    # School of Law (catalog.utexas.edu/law; law.utexas.edu)
    "ut-austin-law-jd": "Texas Law's Juris Doctor requires at least three academic years of resident study and 86 semester hours. First-year students take the foundational curriculum — contracts, property, torts, civil procedure, criminal law, constitutional law, and legal analysis and communication — and in the second and third years design their own course of study. The school offers one of the most extensive arrays of experiential learning of any law school, including seventeen clinics, an advocacy and legal-writing program, internships, and pro bono work. (Source: catalog.utexas.edu/law; law.utexas.edu/juris-doctor)",
    "ut-austin-law-llm": "The Master of Laws (LL.M.) at Texas Law is a one-year graduate program for students who already hold a first degree in law from a U.S. or foreign institution. Candidates build on their legal training through advanced coursework across the school's curriculum, with the flexibility to concentrate in fields such as U.S. law for foreign-trained lawyers, business, or public law. (Source: law.utexas.edu; catalog.utexas.edu/law)",
    # Dell Medical School (dellmed.utexas.edu)
    "ut-austin-medicine-md": "Dell Medical School's Doctor of Medicine program trains physician-leaders through its signature Leading EDGE curriculum, which integrates the foundational and clinical sciences with early clinical immersion, an Innovation, Leadership, and Discovery block, and a dedicated year for scholarly or dual-degree work. The program prepares graduates who are as comfortable addressing systemic challenges in health as they are caring for individual patients. (Source: dellmed.utexas.edu/education)",
    # School of Nursing (nursing.utexas.edu)
    "ut-austin-nursing-bsn": "The Bachelor of Science in Nursing prepares students for professional registered-nurse practice through coursework in nursing science, the biological and behavioral sciences, and supervised clinical rotations across Austin-area hospitals and health systems, supported by simulation-based training. Graduates are prepared to sit for the NCLEX-RN licensure examination. (Source: nursing.utexas.edu/academics/bsn)",
    "ut-austin-nursing-ms": "The Master of Science in Nursing provides advanced study in select areas of nursing science, professional foundations, related sciences, and systematic inquiry, preparing nurses for advanced and specialized professional practice. The program is among the top-ranked MSN programs nationally and the highest-ranked in Texas. (Source: nursing.utexas.edu/academics/graduate)",
    "ut-austin-nursing-phd": "The PhD in Nursing prepares students to become nurse scientists and to assume advanced leadership roles in nursing and health-care delivery, with each student developing a focused program of research based on their background and goals. (Source: nursing.utexas.edu/academics/graduate)",
    "ut-austin-nursing-dnp": "The Doctor of Nursing Practice is a terminal practice degree that advances the clinical, leadership, and translational-research competencies of nurses for increasingly complex practice and clinical-leadership roles. The hybrid program blends online coursework with hands-on training and is the top-ranked DNP program in Texas. (Source: nursing.utexas.edu/academics/graduate/dnp-post-msn)",
    # Jackson School of Geosciences (jsg.utexas.edu) — distinct BS in Geological Sciences options
    "ut-austin-general-geology-bsgs": "The General Geology option of the BS in Geological Sciences is for students who want to learn how the Earth works from a quantitative, scientific perspective, building a comprehensive understanding of solid- and surface-Earth processes while choosing concentrations such as sedimentology, paleontology, energy geoscience, or marine geoscience. (Source: jsg.utexas.edu/academics/undergraduate/degrees-offered)",
    "ut-austin-geophysics-bsgs": "The Geophysics option of the BS in Geological Sciences applies physics, mathematics, and computation to image and understand the Earth's interior and near-surface, covering seismology, gravity and magnetics, and exploration methods used in energy, water, and hazards research. (Source: jsg.utexas.edu/academics/undergraduate/degrees-offered)",
    "ut-austin-hydrology-and-water-resources-bsgs": "The Hydrology and Water Resources option of the BS in Geological Sciences studies the movement, distribution, and quality of water in the Earth system — surface water, groundwater, and the hydrologic cycle — preparing students for careers in water-resource management, environmental consulting, and research. (Source: jsg.utexas.edu/academics/undergraduate/degrees-offered)",
    "ut-austin-climate-system-science-bsgs": "The Climate System Science option of the BS in Geological Sciences examines the physical and chemical processes of Earth's climate system — atmosphere, oceans, ice, and the geologic record of past climates — combining quantitative earth science with the study of climate change. (Source: jsg.utexas.edu/academics/undergraduate/degrees-offered)",
    "ut-austin-geosciences-bags": "The Bachelor of Arts in Geological Sciences is a flexible liberal-arts-style geosciences degree that pairs a foundation in Earth science with broad coursework across the university, well suited to students combining geosciences with education, policy, business, or other fields. (Source: jsg.utexas.edu/academics/undergraduate/degrees-offered)",
    # BS in Environmental Science (catalog.utexas.edu) — distinct majors
    "ut-austin-biological-sciences-bsenvirsci": "The Biological Sciences major within the interdisciplinary BS in Environmental Science, offered by the College of Natural Sciences, builds a broad foundation in the physical, life, and social sciences with an emphasis on ecology, conservation, and the living environment, combining field, laboratory, and computational analysis with original research. (Source: catalog.utexas.edu/undergraduate/natural-sciences/degrees-and-programs/bs-environmental-science)",
    "ut-austin-geographical-sciences-bsenvirsci": "The Geographical Sciences major within the interdisciplinary BS in Environmental Science, offered by the College of Liberal Arts through the Department of Geography and the Environment, studies environmental issues through spatial analysis, remote sensing, and the human–environment relationship alongside the physical and life sciences. (Source: catalog.utexas.edu/undergraduate/natural-sciences/degrees-and-programs/bs-environmental-science)",
    # Butler School of Music (music.utexas.edu) — distinct undergraduate / graduate programs
    "ut-austin-composition-bmusic": "The Bachelor of Music in Composition trains student composers across a wide range of styles and genres — including wind-ensemble, orchestral, choral, chamber, electro-acoustic music, and film scoring — with works read and performed by Butler School ensembles, alongside comprehensive study of music theory and history and a senior recital. (Source: music.utexas.edu/academics/programs-study/composition-home)",
    "ut-austin-jazz-bmusic": "The Bachelor of Music in Jazz prepares the next generation of jazz performers, composers, and educators, blending rigorous musicianship with extensive performance; students pursue an emphasis in jazz performance or jazz composition and deepen their work in improvisation, theory, history, arranging, and pedagogy. (Source: music.utexas.edu/academics/programs-study/jazz-studies)",
    "ut-austin-music-performance-bmusic": "The Bachelor of Music in Performance develops students as solo and ensemble musicians on brass, woodwind, percussion, keyboard, and stringed instruments, or in voice and opera, through applied lessons, large and small ensembles, and a required senior recital, complemented by core study in theory and music history. (Source: music.utexas.edu/perform-and-study/areas-of-study)",
    "ut-austin-music-studies-bmusic": "The Bachelor of Music in Music Studies prepares students for careers in music teaching, integrating applied performance and ensemble work with coursework in music education pedagogy, theory, and history and supervised field and student-teaching experiences toward Texas music-teacher certification. (Source: music.utexas.edu/perform-and-study/areas-of-study)",
    "ut-austin-music-bamusic": "The Bachelor of Arts in Music is an interdisciplinary liberal-arts degree in which students complete a concentration in music alongside a secondary field of study outside music, combining musicianship with broad academic breadth for students who want music within a liberal-arts education. (Source: music.utexas.edu/academics/programs-study/bachelor-arts-music)",
    "ut-austin-music-music-and-human-learning-mm": "The Master of Music in Music and Human Learning studies the fundamental principles of human learning and behavior as applied across music activity — performance, perception, composition, and teaching — preparing music educators and researchers. (Source: music.utexas.edu/perform-and-study/areas-of-study)",
    "ut-austin-music-music-and-human-learning-dma": "The Doctor of Musical Arts in Music and Human Learning combines advanced study of how humans learn and engage with music with high-level musicianship, preparing scholar-practitioners in music education and pedagogy. (Source: music.utexas.edu/perform-and-study/areas-of-study)",
    "ut-austin-music-music-and-human-learning-phd": "The PhD in Music and Human Learning is a research doctorate in music education, preparing scholars to investigate the psychological, pedagogical, and cultural foundations of musical learning and teaching. (Source: music.utexas.edu/perform-and-study/areas-of-study)",
    # Department of Theatre and Dance (theatredance.utexas.edu)
    "ut-austin-acting-bfa": "The Bachelor of Fine Arts in Acting is a conservatory-style professional training program within the Department of Theatre and Dance, developing actors through intensive studio work in acting technique, voice and speech, movement, and performance, with productions in the department's theatres. (Source: catalog.utexas.edu/undergraduate/fine-arts; theatredance.utexas.edu)",
    "ut-austin-dance-bfa": "The Bachelor of Fine Arts in Dance is a professional training program in the Department of Theatre and Dance combining technique, choreography, performance, and dance studies, preparing students as performing and creating artists. (Source: catalog.utexas.edu/undergraduate/fine-arts; theatredance.utexas.edu)",
    # School of Information (ischool.utexas.edu)
    "ut-austin-informatics-ba": "The Bachelor of Science in Informatics, offered by the School of Information, teaches students to collect, manage, and analyze data and information and to do so with ethical responsibility, with concentrations spanning data analytics and artificial intelligence, user-experience and design, health informatics, and social and cultural informatics. (Source: ischool.utexas.edu/programs/informatics; catalog.utexas.edu/undergraduate/information)",
    # School of Civic Leadership (civicleadership.utexas.edu)
    "ut-austin-civics-honors-ba": "The Bachelor of Arts in Civics Honors, offered by the School of Civic Leadership, introduces students to the intellectual inheritance of Western civilization and the American constitutional tradition, blending a classical liberal education with the study of American history, law, economics, and political philosophy to prepare students for engaged citizenship and leadership. (Source: catalog.utexas.edu/undergraduate/civic-leadership; civicleadership.utexas.edu)",
    # College of Liberal Arts (liberalarts.utexas.edu)
    "ut-austin-humanities-ba": "The Bachelor of Arts in Humanities is an individualized, interdisciplinary liberal-arts degree in the College of Liberal Arts, letting students design a coherent course of study across literature, history, philosophy, the arts, and culture around a chosen theme or question, often with a senior thesis. (Source: liberalarts.utexas.edu/humanities; catalog.utexas.edu/undergraduate/liberal-arts)",
    "ut-austin-business-analytics-ms": "The Master of Science in Business Analytics at Texas McCombs is a STEM-designated program that trains students to turn data into business decisions through machine learning, optimization, data management, and analytics consulting, with a capstone industry project. (Source: mccombs.utexas.edu/graduate/masters-in-business-analytics)",
    "ut-austin-asian-studies-ba": "The Bachelor of Arts in Asian Studies, in the Department of Asian Studies, is an interdisciplinary major spanning the languages, literatures, religions, history, and cultures of East, South, and Southeast Asia, pairing Asian-language study with humanities and social-science coursework on the region. (Source: liberalarts.utexas.edu/asianstudies; catalog.utexas.edu/undergraduate/liberal-arts)",
    "ut-austin-history-ba": "The Bachelor of Arts in History, offered by the Department of History — one of the largest and most distinguished history programs in the country — lets students study the human past across the major fields of United States, European, Latin American, Asian, African, and Middle Eastern history, developing skills in research, analysis, and argument from rich library and archival collections. (Source: liberalarts.utexas.edu/history; catalog.utexas.edu/undergraduate/liberal-arts)",
    "ut-austin-race-indigeneity-and-migration-ba":"The Bachelor of Arts in Race, Indigeneity, and Migration is the interdisciplinary, comparative study of the history, sociology, politics, culture, and economics of North American racial and ethnic groups — including African Americans, Indigenous and Native Americans, Latinx, and Asian Americans — with opportunities for community-engaged research and public scholarship. (Source: liberalarts.utexas.edu/rim; catalog.utexas.edu/undergraduate/liberal-arts)",
    "ut-austin-sustainability-studies-ba": "The Bachelor of Arts in Sustainability Studies, housed in the Department of Geography and the Environment, provides focused study of sustainability across social science, earth science, economics, communications, and policy, with thematic concentrations and a required capstone and internship. (Source: liberalarts.utexas.edu/geography; catalog.utexas.edu/undergraduate/liberal-arts)",
    # Arts and Entertainment Technologies (College of Fine Arts)
    "ut-austin-arts-and-entertainment-technologies-bsaet": "The Bachelor of Science in Arts and Entertainment Technologies, in the College of Fine Arts, prepares students at the intersection of art, design, and technology — including game development, interactive media, animation, and creative coding — through project-based studios and collaboration across the arts and computing. (Source: aet.utexas.edu; catalog.utexas.edu/undergraduate/fine-arts)",
    # Kinesiology and Health Education undergraduate options (College of Education)
    "ut-austin-applied-movement-science-bskin-and-health": "The Applied Movement Science option of the BS in Kinesiology and Health, in the Department of Kinesiology and Health Education, studies the biomechanical, physiological, and motor-control basis of human movement and exercise, preparing students for graduate study and careers in the movement and health sciences. (Source: catalog.utexas.edu/undergraduate/education; he.utexas.edu/khe)",
    "ut-austin-health-promotion-and-behavioral-science-bskin-and-health": "The Health Promotion and Behavioral Science option of the BS in Kinesiology and Health examines the behavioral, social, and environmental determinants of health and the design of programs that promote health and prevent disease across communities. (Source: catalog.utexas.edu/undergraduate/education; he.utexas.edu/khe)",
    "ut-austin-physical-culture-and-sports-studies-bskin-and-health": "The Physical Culture and Sports Studies option of the BS in Kinesiology and Health studies sport, physical activity, and the body through the humanities and social sciences — history, sociology, and the culture of sport — preparing students for careers and graduate study in sport studies and related fields. (Source: catalog.utexas.edu/undergraduate/education; he.utexas.edu/khe)",
    # Department of French and Italian (liberalarts.utexas.edu/frenchitalian)
    "ut-austin-french-studies-ba": "The Bachelor of Arts in French Studies develops advanced proficiency in French alongside the study of French and Francophone literature, history, film, media, culture, and linguistics, preparing students for careers and graduate study that draw on language and cross-cultural expertise. (Source: catalog.utexas.edu/graduate/areas-of-study/liberal-arts/french-italian; liberalarts.utexas.edu/frenchitalian)",
    "ut-austin-italian-studies-ba": "The Bachelor of Arts in Italian Studies builds proficiency in Italian and engages Italian literature, cinema, and culture, combining language study with the humanities for students interested in Italy's artistic, intellectual, and historical traditions. (Source: catalog.utexas.edu/graduate/areas-of-study/liberal-arts/french-italian; liberalarts.utexas.edu/frenchitalian)",
    # College of Pharmacy (pharmacy.utexas.edu) — Pharmaceutical Sciences graduate degrees
    "ut-austin-pharmaceutical-sciences-ms": "The Master of Science in Pharmaceutical Sciences, offered by the College of Pharmacy, is a STEM-designated graduate degree spanning the discovery, development, action, and use of medicines — across areas such as molecular pharmaceutics and drug delivery, medicinal chemistry, pharmacology and toxicology, and pharmacy health-outcomes research. (Source: catalog.utexas.edu/graduate/areas-of-study/pharmacy/pharmacy)",
    "ut-austin-pharmaceutical-sciences-phd": "The Doctor of Philosophy with a major in Pharmaceutical Sciences, offered by the College of Pharmacy, is a STEM-designated research doctorate in which students pursue original research in areas including molecular pharmaceutics, medicinal chemistry, pharmacology and toxicology, and health-outcomes research, supported by the college's institutes and core facilities. (Source: catalog.utexas.edu/graduate/areas-of-study/pharmacy/pharmacy)",
    # Department of Art and Art History, College of Fine Arts (finearts.utexas.edu)
    "ut-austin-art-history-ba": "The Bachelor of Arts in Art History, in the Department of Art and Art History, studies the history of art, architecture, and visual culture across periods and world traditions, training students in visual analysis, research, and writing for careers in museums, galleries, conservation, and graduate study. (Source: catalog.utexas.edu/undergraduate/fine-arts; finearts.utexas.edu/aah)",
    "ut-austin-studio-art-ba": "The Bachelor of Arts in Studio Art pairs hands-on studio practice across media — such as drawing, painting, printmaking, sculpture, and new media — with the broad academic breadth of a liberal-arts degree, for students who want to make art within a wider course of study. (Source: catalog.utexas.edu/undergraduate/fine-arts; finearts.utexas.edu/aah)",
    # Department of Neuroscience, College of Natural Sciences (neuroscience.utexas.edu)
    "ut-austin-neuroscience-ms": "The Master of Arts in Neuroscience supports advanced study in the interdisciplinary neurosciences — from molecular and cellular neuroscience to systems, cognitive, and behavioral neuroscience — combining coursework with laboratory research across the College of Natural Sciences and affiliated institutes. (Source: catalog.utexas.edu/graduate/areas-of-study/natural-sciences/neuroscience)",
    "ut-austin-neuroscience-phd": "The Doctor of Philosophy in Neuroscience is an interdisciplinary research doctorate in which students conduct original dissertation research spanning molecular, cellular, systems, cognitive, and computational neuroscience, mentored by faculty across departments and the university's neuroscience institutes. (Source: catalog.utexas.edu/graduate/areas-of-study/natural-sciences/neuroscience)",
    # Moody College of Communication undergraduate majors (moody.utexas.edu) — the
    # catalog degree pages are requirements tables, so these are department-sourced.
    "ut-austin-advertising-bsadv": "The Bachelor of Science in Advertising, in the Stan Richards School of Advertising and Public Relations, studies how advertising shapes business, media, and society — covering brand strategy, consumer behavior, creative development, and account planning across traditional and digital media. (Source: moody.utexas.edu/departments/stan-richards-advertising; catalog.utexas.edu/undergraduate/communication)",
    "ut-austin-public-relations-bspr": "The Bachelor of Science in Public Relations, in the Stan Richards School of Advertising and Public Relations, trains students in strategic communication, audience research, campaign planning, and reputation management for organizations, brands, and causes. (Source: moody.utexas.edu/departments/stan-richards-advertising; catalog.utexas.edu/undergraduate/communication)",
    "ut-austin-communication-and-leadership-bscomm-and-lead": "The Bachelor of Science in Communication and Leadership, in the Moody College of Communication, develops students' skills in leadership, civic engagement, and organizational and interpersonal communication, combining communication theory with applied leadership practice. (Source: moody.utexas.edu; catalog.utexas.edu/undergraduate/communication)",
    "ut-austin-communication-studies-bscommstds": "The Bachelor of Science in Communication Studies, in the Department of Communication Studies, examines human communication across interpersonal, organizational, rhetorical, and political contexts, preparing students for careers in business, law, public affairs, and human resources. (Source: moody.utexas.edu/departments/communication-studies; catalog.utexas.edu/undergraduate/communication)",
    "ut-austin-journalism-bj": "The Bachelor of Journalism, in the School of Journalism and Media, trains reporters and storytellers in news reporting, writing, multimedia and data journalism, and media ethics, with hands-on work across print, broadcast, and digital platforms. (Source: moody.utexas.edu/departments/journalism-media; catalog.utexas.edu/undergraduate/communication)",
    "ut-austin-radio-television-film-bsrtf": "The Bachelor of Science in Radio-Television-Film, in the Department of Radio-Television-Film, combines media production with the critical study of film, television, and digital media, training students as storytellers, screenwriters, and media makers across narrative, documentary, and emerging formats. (Source: moody.utexas.edu/departments/radio-television-film; catalog.utexas.edu/undergraduate/communication)",
    "ut-austin-speech-language-and-hearing-sciences-bsslh": "The Bachelor of Science in Speech, Language, and Hearing Sciences studies human communication and its disorders — speech, language, and hearing — providing the scientific foundation for graduate study and careers in speech-language pathology and audiology. (Source: moody.utexas.edu/departments/speech-language-hearing-sciences; catalog.utexas.edu/undergraduate/communication)",
    # College of Education / College of Fine Arts teaching majors
    "ut-austin-art-education-bfa": "The Bachelor of Fine Arts in Art Education prepares students to teach visual art, combining studio practice and art history with pedagogy and supervised classroom experience toward Texas art-teacher certification. (Source: catalog.utexas.edu/undergraduate/fine-arts; finearts.utexas.edu/aah)",
    "ut-austin-theatre-education-bfa": "The Bachelor of Fine Arts in Theatre Education combines conservatory-style theatre training with education coursework and supervised teaching, preparing graduates to teach theatre arts in schools toward Texas theatre-teacher certification. (Source: catalog.utexas.edu/undergraduate/fine-arts; theatredance.utexas.edu)",
    # Department of Classics (liberalarts.utexas.edu/coc) — two distinct BA majors
    "ut-austin-classical-languages-ba": "The Bachelor of Arts in Classical Languages centers on the study of Greek and Latin, reading classical texts in the original languages to build deep linguistic and literary command of the ancient Mediterranean world. (Source: liberalarts.utexas.edu/coc; catalog.utexas.edu/undergraduate/liberal-arts)",
    "ut-austin-classical-studies-ba": "The Bachelor of Arts in Classical Studies takes a broad, interdisciplinary view of classical antiquity — its history, literature, philosophy, art, and material culture — with less emphasis on advanced language study than the classical-languages major. (Source: liberalarts.utexas.edu/coc; catalog.utexas.edu/undergraduate/liberal-arts)",
    # Department of Curriculum and Instruction (education.utexas.edu) — distinct credentials
    "ut-austin-curriculum-and-instruction-ma": "The Master of Arts in Curriculum and Instruction supports research-oriented graduate study across specializations such as bilingual/bicultural education, cultural studies in education, early childhood, language and literacy, mathematics education, and STEM education, culminating in a thesis. (Source: education.utexas.edu/departments/curriculum-instruction; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-curriculum-and-instruction-med": "The Master of Education in Curriculum and Instruction serves practicing and prospective educators, deepening expertise in teaching, curriculum, and a chosen specialization through applied coursework rather than a research thesis. (Source: education.utexas.edu/departments/curriculum-instruction; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-curriculum-and-instruction-phd": "The Doctor of Philosophy in Curriculum and Instruction prepares education researchers and faculty, with doctoral training in research methods and a specialization area leading to original dissertation research on teaching and learning. (Source: education.utexas.edu/departments/curriculum-instruction; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-curriculum-and-instruction-edd": "The Doctor of Education in Curriculum and Instruction is a practitioner doctorate for educational leaders, applying research to problems of practice in schools and curriculum through advanced professional study and a capstone dissertation. (Source: education.utexas.edu/departments/curriculum-instruction; catalog.utexas.edu/graduate/areas-of-study/education)",
    # Department of English (liberalarts.utexas.edu/english)
    "ut-austin-english-ma": "The Master of Arts in English offers graduate study across literary history and criticism — American, British, and Anglophone literatures, rhetoric, and literary theory — as preparation for doctoral work or careers requiring advanced study of literature. (Source: liberalarts.utexas.edu/english; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    "ut-austin-english-creative-writing-mfa": "The Master of Fine Arts in Creative Writing, administered with the New Writers Project and the Michener Center for Writers, is a studio program in which writers develop a book-length manuscript in fiction, poetry, or related forms alongside literature and craft seminars. (Source: liberalarts.utexas.edu/english; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    # Department of French and Italian (liberalarts.utexas.edu/frenchitalian)
    "ut-austin-french-and-italian-french-ma": "The Master of Arts in French offers graduate study of French and Francophone literature, history, film, media, culture, and linguistics, building advanced language command and critical methods. (Source: catalog.utexas.edu/graduate/areas-of-study/liberal-arts/french-italian)",
    "ut-austin-french-and-italian-french-phd": "The Doctor of Philosophy in French prepares scholars through doctoral research in French and Francophone literature, film, media, culture, and linguistics, with teaching and dissertation work. (Source: catalog.utexas.edu/graduate/areas-of-study/liberal-arts/french-italian)",
    "ut-austin-french-and-italian-italian-studies-ma": "The Master of Arts in Italian Studies offers graduate study of Italian literature, cinema, and culture, combining advanced language work with critical and cultural analysis. (Source: catalog.utexas.edu/graduate/areas-of-study/liberal-arts/french-italian)",
    "ut-austin-french-and-italian-italian-studies-phd": "The Doctor of Philosophy in Italian Studies trains scholars through doctoral research on Italian literature, cinema, and culture, with teaching experience and a dissertation. (Source: catalog.utexas.edu/graduate/areas-of-study/liberal-arts/french-italian)",
    # School of Architecture (soa.utexas.edu) — landscape architecture (reworded to avoid the classification-stub form)
    "ut-austin-landscape-architecture-mla": "The Master of Landscape Architecture, an accredited first-professional degree in the School of Architecture, prepares students with no prior background in the field to design landscapes, public spaces, and ecological systems through design studios, history and theory, and technology toward professional licensure. (Source: soa.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/architecture)",
    "ut-austin-landscape-architecture-ms": "The Master of Science in Landscape Architecture, in the School of Architecture, is a post-professional research degree for students who already hold a professional design degree and want to pursue advanced study and research in landscape architecture. (Source: soa.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/architecture)",
    # Department of Kinesiology and Health Education — additional BS options
    "ut-austin-exercise-science-bskin-and-health": "The Exercise Science option of the BS in Kinesiology and Health prepares students for health-professional and graduate study by examining the physiological, biomechanical, and clinical responses of the body to physical activity, with pre-professional coursework for medicine, physical therapy, and allied health. (Source: catalog.utexas.edu/undergraduate/education; he.utexas.edu/khe)",
    "ut-austin-sport-management-bskin-and-health": "The Sport Management option of the BS in Kinesiology and Health applies business, marketing, finance, and management principles to the sport and physical-activity industry, preparing students for careers in athletics administration, sport marketing, and event and facility management. (Source: catalog.utexas.edu/undergraduate/education; he.utexas.edu/khe)",
    # Department of Economics (liberalarts.utexas.edu/economics) — distinct credentials
    "ut-austin-economics-ma": "The Master of Arts in Economics offers graduate study in the core areas of microeconomics, macroeconomics, and econometrics, building the theoretical and quantitative foundation for applied economic analysis or further doctoral study. (Source: liberalarts.utexas.edu/economics; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    "ut-austin-economics-ms": "The Master of Science in Economics is a STEM-designated degree emphasizing quantitative and data-analytic methods in economics — econometrics, computation, and applied microeconomics — for careers in industry, government, and research. (Source: liberalarts.utexas.edu/economics; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    "ut-austin-economics-phd": "The Doctor of Philosophy in Economics trains research economists through advanced study of microeconomic and macroeconomic theory and econometrics, leading to original dissertation research and academic, government, or industry research careers. (Source: liberalarts.utexas.edu/economics; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    # Red McCombs School of Business — Management graduate degrees
    "ut-austin-management-ms": "The Master of Science in management programs at Texas McCombs (including the specialized Science and Technology Management track) build advanced expertise in organizational strategy, leadership, and the management of innovation for early-career and working professionals. (Source: mccombs.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/business)",
    "ut-austin-management-phd": "The Doctor of Philosophy in Management at Texas McCombs prepares scholars for research and academic careers, with doctoral specializations spanning organizational behavior, strategy, and human resource management and original dissertation research. (Source: mccombs.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/business)",
    # Department of Earth and Planetary Sciences / Jackson School (jsg.utexas.edu)
    "ut-austin-geological-sciences-ma": "The Master of Arts in Geological Sciences offers coursework-focused graduate study of Earth materials, processes, and history, suited to students seeking advanced training without a full research thesis. (Source: jsg.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/geosciences)",
    "ut-austin-geological-sciences-ms": "The Master of Science in Geological Sciences pairs advanced coursework with original thesis research across the Earth sciences — from sedimentary and structural geology to geophysics, hydrogeology, and energy geoscience. (Source: jsg.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/geosciences)",
    "ut-austin-geological-sciences-phd": "The Doctor of Philosophy in Geological Sciences trains research geoscientists through original dissertation work spanning solid-earth, surface, climate, and energy geoscience, drawing on the Jackson School's research institutes and field programs. (Source: jsg.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/geosciences)",
    # Department of Astronomy / McDonald Observatory (astronomy.utexas.edu)
    "ut-austin-astronomy-ma": "The Master of Arts in Astronomy provides graduate coursework in astrophysics and observational techniques as a foundation for doctoral study or careers in research and education. (Source: astronomy.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/natural-sciences)",
    "ut-austin-astronomy-phd": "The Doctor of Philosophy in Astronomy trains research astronomers using UT's McDonald Observatory and the Hobby-Eberly Telescope, with dissertation research spanning stellar, galactic, extragalactic, and planetary astrophysics and cosmology. (Source: astronomy.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/natural-sciences)",
    # McKetta Department of Chemical Engineering (che.utexas.edu)
    "ut-austin-chemical-engineering-ms": "The Master of Science in Chemical Engineering, in the McKetta Department, combines advanced coursework with thesis research in areas such as energy, materials, catalysis, and process systems. (Source: che.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/engineering)",
    "ut-austin-chemical-engineering-phd": "The Doctor of Philosophy in Chemical Engineering, in the McKetta Department, supports original dissertation research across energy and sustainability, soft matter and materials, biotechnology, catalysis, and process systems engineering. (Source: che.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/engineering)",
    # Walker Department of Mechanical Engineering (me.utexas.edu)
    "ut-austin-mechanical-engineering-phd": "The Doctor of Philosophy in Mechanical Engineering, in the Walker Department, trains researchers through dissertation work across thermal-fluid systems, dynamics and controls, manufacturing and design, materials, acoustics, and biomechanical engineering. (Source: me.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/engineering)",
    # Marine Science Institute, Port Aransas (marinescience.utexas.edu)
    "ut-austin-marine-science-ms": "The Master of Science in Marine Science, based at UT's Marine Science Institute in Port Aransas, combines coursework with thesis research in coastal and ocean science — marine ecology, biogeochemistry, fisheries, and oceanography. (Source: marinescience.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/natural-sciences)",
    "ut-austin-marine-science-phd": "The Doctor of Philosophy in Marine Science prepares ocean and coastal scientists through original dissertation research at the Marine Science Institute, spanning marine biology and ecology, chemical and physical oceanography, and environmental science. (Source: marinescience.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/natural-sciences)",
    # Department of Linguistics (liberalarts.utexas.edu/linguistics)
    "ut-austin-linguistics-ma": "The Master of Arts in Linguistics offers graduate study of the structure, sound, meaning, and use of language, with coursework and research across phonetics, phonology, syntax, semantics, sociolinguistics, and documentary and computational linguistics. (Source: liberalarts.utexas.edu/linguistics; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    # Stan Richards School of Advertising and Public Relations (advertising.utexas.edu)
    "ut-austin-advertising-ma": "The Master of Arts in Advertising offers graduate study of advertising and brand communication — consumer insight, strategy, and persuasion research — preparing students for industry research roles or doctoral study. (Source: advertising.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/communication)",
    # Department of Communication Studies (communicationstudies.utexas.edu)
    "ut-austin-communication-studies-ma": "The Master of Arts in Communication Studies offers graduate study of human communication across interpersonal, organizational, rhetorical, and political contexts, with theory and research methods preparing students for doctoral work or applied careers. (Source: moody.utexas.edu/departments/communication-studies; catalog.utexas.edu/graduate/areas-of-study/communication)",
    "ut-austin-communication-studies-phd": "The Doctor of Philosophy in Communication Studies trains researchers and faculty through doctoral study of interpersonal, organizational, rhetorical, and political communication, leading to original dissertation research. (Source: moody.utexas.edu/departments/communication-studies; catalog.utexas.edu/graduate/areas-of-study/communication)",
    # Department of Art and Art History (finearts.utexas.edu/aah)
    "ut-austin-art-education-ma": "The Master of Arts in Art Education offers graduate study of teaching and learning in the visual arts across schools, museums, and community settings, combining art education theory, research, and studio engagement. (Source: finearts.utexas.edu/aah; catalog.utexas.edu/graduate/areas-of-study/fine-arts)",
    # Human Dimensions of Organizations (hdo.utexas.edu)
    "ut-austin-human-dimensions-of-organizations-ma": "The Master of Arts in Human Dimensions of Organizations applies the human sciences — psychology, anthropology, history, ethics, and rhetoric — to leadership and organizational problems, offered for working professionals through flexible and distance formats. (Source: hdo.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    # School of Architecture — Interior Design (soa.utexas.edu)
    "ut-austin-interior-design-bsid": "The Bachelor of Science in Interior Design, in the School of Architecture, is an accredited professional program in which students design interior environments for human use through studios in space planning, materials, lighting, and building systems. (Source: soa.utexas.edu; catalog.utexas.edu/undergraduate/architecture)",
    # Department of Kinesiology and Health Education — Athletic Training (he.utexas.edu/khe)
    "ut-austin-athletic-training-bsathtrng": "The Bachelor of Science in Athletic Training prepares students for the prevention, assessment, and rehabilitation of injuries in physically active populations, combining science coursework with supervised clinical experience toward athletic-training credentialing. (Source: he.utexas.edu/khe; catalog.utexas.edu/undergraduate/education)",
    # Steve Hicks School of Social Work — BSW (socialwork.utexas.edu)
    "ut-austin-social-work-bsw": "The Bachelor of Social Work prepares students for entry-level generalist social-work practice, integrating courses in human behavior, social welfare policy, and practice methods with a supervised field internship in community agencies. (Source: socialwork.utexas.edu/academics; catalog.utexas.edu/undergraduate/social-work)",
    # Department of Spanish and Portuguese (liberalarts.utexas.edu/spanish)
    "ut-austin-spanish-ba": "The Bachelor of Arts in Spanish, in the Department of Spanish and Portuguese, builds advanced Spanish proficiency alongside the study of the literatures, linguistics, and cultures of Spain, Latin America, and U.S. Latino communities. (Source: liberalarts.utexas.edu/spanish; catalog.utexas.edu/undergraduate/liberal-arts)",
    # Butler School of Music — DMA (performance/conducting doctorate, not musicology)
    "ut-austin-music-dma": "The Doctor of Musical Arts in Music is the terminal performance doctorate at the Butler School of Music, for advanced performers and conductors who combine recitals and large performance projects with scholarly study in music theory, history, and pedagogy. (Source: music.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/fine-arts)",
    # Final quality overrides — programs whose only catalog prose was admissions /
    # advising / facilities boilerplate or a mis-assigned sibling paragraph.
    "ut-austin-english-ba": "The Bachelor of Arts in English studies literature in English across periods, genres, and traditions — British, American, and Anglophone — alongside rhetoric, creative writing, and critical theory, building close-reading, research, and writing skills. (Source: liberalarts.utexas.edu/english; catalog.utexas.edu/undergraduate/liberal-arts)",
    "ut-austin-educational-leadership-and-policy-phd": "The Doctor of Philosophy in Educational Leadership and Policy prepares researchers and faculty to study educational organizations, leadership, and policy across K-12 and higher education, with specializations including higher-education leadership, education policy and planning, and school leadership. (Source: education.utexas.edu/departments/educational-leadership-policy; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-educational-leadership-and-policy-edd": "The Doctor of Education in Educational Leadership and Policy is a practitioner doctorate for educational leaders, applying research to leadership and policy challenges in schools, districts, and higher-education institutions through advanced professional study and a capstone. (Source: education.utexas.edu/departments/educational-leadership-policy; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-science-technology-engineering-and-mathematics-education-ma": "The Master of Arts in STEM Education studies the teaching and learning of science, technology, engineering, and mathematics, integrating disciplinary content with research on pedagogy, curriculum, and equity in STEM classrooms. (Source: education.utexas.edu/departments/stem-education; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-science-technology-engineering-and-mathematics-education-phd": "The Doctor of Philosophy in STEM Education prepares researchers and faculty through doctoral study of how science, technology, engineering, and mathematics are taught and learned, leading to original dissertation research drawing on faculty across science, engineering, and education. (Source: education.utexas.edu/departments/stem-education; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-health-behavior-and-health-education-phd": "The Doctor of Philosophy in Health Behavior and Health Education trains researchers in the behavioral and social determinants of health and the design and evaluation of health-promotion and disease-prevention programs across populations. (Source: he.utexas.edu/khe; catalog.utexas.edu/graduate/areas-of-study/education)",
    "ut-austin-speech-language-and-hearing-sciences-phd": "The Doctor of Philosophy in Speech, Language, and Hearing Sciences trains researchers in human communication and its disorders — speech, language, and hearing — through doctoral study and original research spanning the developmental, neural, and clinical sciences of communication. (Source: moody.utexas.edu/departments/speech-language-hearing-sciences; catalog.utexas.edu/graduate/areas-of-study/communication)",
    "ut-austin-civil-engineering-phd": "The Doctor of Philosophy in Civil Engineering, in the Department of Civil, Architectural and Environmental Engineering, supports original dissertation research across structural engineering, transportation, water resources, geotechnical engineering, construction, and infrastructure materials. (Source: caee.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/engineering)",
    "ut-austin-theatre-and-dance-dance-mfa": "The Master of Fine Arts in Dance, in the Department of Theatre and Dance, is a studio-based professional degree in which dance artists develop choreography, performance, and dance scholarship through intensive creative work and production. (Source: theatredance.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/fine-arts)",
    "ut-austin-theatre-and-dance-theatre-phd": "The Doctor of Philosophy in Theatre, in the Department of Theatre and Dance, prepares scholars in theatre history, theory, and performance studies through doctoral coursework and original dissertation research. (Source: theatredance.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/fine-arts)",
    "ut-austin-advertising-phd": "The Doctor of Philosophy in Advertising prepares researchers and faculty through doctoral study of advertising, consumer behavior, and strategic brand communication, leading to original dissertation research. (Source: advertising.utexas.edu; catalog.utexas.edu/graduate/areas-of-study/communication)",
    "ut-austin-radio-television-film-mfa": "The Master of Fine Arts in Radio-Television-Film is a production-focused professional degree in film and media, in which students develop a body of creative work across narrative, documentary, and emerging media with mentorship from working filmmakers. (Source: moody.utexas.edu/departments/radio-television-film; catalog.utexas.edu/graduate/areas-of-study/communication)",
    "ut-austin-computer-science-online-ms": "The online Master of Science in Computer Science (MSCS Online) delivers UT Austin's graduate computer-science curriculum — including machine learning, systems, and theory — to working professionals at scale, with the same faculty and rigor as the on-campus degree. (Source: cdso.utexas.edu/mscs; catalog.utexas.edu/graduate/areas-of-study/natural-sciences)",
    "ut-austin-asian-studies-asian-cultures-and-languages-ma": "The Master of Arts in Asian Cultures and Languages, in the Department of Asian Studies, offers graduate study of the languages, literatures, religions, and cultures of East, South, and Southeast Asia through advanced language work and interdisciplinary humanities research. (Source: liberalarts.utexas.edu/asianstudies; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    "ut-austin-asian-studies-asian-cultures-and-languages-phd": "The Doctor of Philosophy in Asian Cultures and Languages, in the Department of Asian Studies, trains scholars through doctoral research on the languages, literatures, religions, and cultures of Asia, with advanced language command and a dissertation. (Source: liberalarts.utexas.edu/asianstudies; catalog.utexas.edu/graduate/areas-of-study/liberal-arts)",
    # Steve Hicks School of Social Work (socialwork.utexas.edu)
    "ut-austin-social-work-ms": "The Master of Science in Social Work at the Steve Hicks School of Social Work prepares students for advanced professional practice, offering clinical and administration/policy concentrations with field placements across Austin-area agencies; it is consistently ranked among the nation's top graduate social-work programs. (Source: socialwork.utexas.edu/academics)",
    "ut-austin-social-work-phd": "The PhD in Social Work prepares students for research and academic careers, training scholars to advance knowledge on social problems, intervention, and policy through rigorous research methods and mentored dissertation work. (Source: socialwork.utexas.edu/academics)",
}


def main() -> None:
    out: dict[str, str] = dict(_MANUAL)
    cache: dict[str, str] = {}
    auto = 0
    with httpx.Client(headers=H) as c:
        for slug, (path, sel) in URL_MAP.items():
            if slug in out:  # _MANUAL wins
                continue
            if path not in cache:
                try:
                    r = c.get(BASE + path, follow_redirects=True, timeout=30)
                    cache[path] = r.text if r.status_code == 200 else ""
                except Exception as e:  # noqa: BLE001
                    print("FETCH FAIL", path, e)
                    cache[path] = ""
            desc = extract(cache[path], sel) if cache[path] else None
            if desc:
                out[slug] = desc
                auto += 1
            else:
                print("NO DESC (needs _MANUAL):", slug, path, sel)

    lines = [
        '"""Verified residual program descriptions for UT Austin (second pass).',
        "",
        "First-party prose from catalog.utexas.edu (graduate area-of-study / department",
        "overviews) plus hand-verified, cited descriptions for programs with no scrapeable",
        "catalog prose. Regenerate via scripts/build_ut_austin_supplemental_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "SUPPLEMENTAL_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(out):
        t = out[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{t}",')
    lines.append("}")
    lines.append("")
    (ROOT / "ut_austin_supplemental_descriptions.py").write_text("\n".join(lines))
    print(f"\nWrote {len(out)} supplemental ({auto} auto-scraped + {len(_MANUAL)} manual)")


if __name__ == "__main__":
    main()
