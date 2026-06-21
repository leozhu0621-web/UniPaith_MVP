"""Per-program gold descriptions for New York University (enrich-profile gold repair).

Background (2026-06-20, nyugold1): NYU's catalog descriptions are first-party NYU
Bulletin prose, but the joint majors, dual-degree programs, and per-specialty/
per-subject tracks reused a *base* department blurb verbatim — so two genuinely
different programs (e.g. "BA in Italian" and "BA in Italian and Linguistics", or all
twelve "Combined B.S." CAS+Tandon dual degrees) shared a 400–950-character body. That
cross-field stamping is invisible to the field-keyed anti-stub gate (each combined name
is its own ``field_of``) but violates the gold standard: gold MIT gives every program a
unique, researched description (REPAIR_BACKLOG miss #8 school-blurb / cross-field
sub-bullet). It also relocated the Chemistry department-history paragraph onto the
"BA in Biochemistry" row, leaving that body with no biochemistry-specific content.

This module gives each affected program its OWN truthful, distinct description. Every
clause is grounded in verified, public facts: the program's real structure (dual-degree
between the College of Arts and Science and the NYU Tandon School of Engineering; NYU
Journalism's Global & Joint Program Studies model; New York State 7–12 teacher
certification) plus the well-established subject matter of each field. No statistics,
rankings, or named centers are invented. The descriptions are applied last in
``nyu_profile._build_catalog`` so they win over the generated bodies, and the build
self-check asserts no two programs share a >=150-character run.
"""

from __future__ import annotations

# ── Combined B.S. — five-year CAS + NYU Tandon dual degrees (two BS, begun first year) ──
_COMBINED_BS: dict[str, str] = {
    "nyu-biology-chemical-biomolecular-engineering-bs-bs": (
        "Pairs the College of Arts and Science biology major — molecular, cellular, and "
        "organismal biology — with chemical and biomolecular engineering at NYU Tandon, "
        "training students to engineer biological processes, biomaterials, and "
        "pharmaceutical manufacturing. The five-year plan awards a BS from each school, "
        "and the dual-degree sequence must begin in the first year."
    ),
    "nyu-chemistry-chemical-biomolecular-engineering-bs-bs": (
        "Combines the College of Arts and Science chemistry major — organic, inorganic, "
        "and physical chemistry — with chemical and biomolecular engineering at NYU "
        "Tandon, bridging molecular science and process design for the energy, materials, "
        "and pharmaceutical industries. Two BS degrees are earned over five years, one "
        "from each school."
    ),
    "nyu-computer-science-electrical-engineering-bs-bs": (
        "Joins the College of Arts and Science computer science major — algorithms, "
        "systems, and software — with electrical engineering at NYU Tandon, spanning "
        "circuits, signals, and embedded hardware for students who design across the "
        "hardware–software boundary. The five-year program confers a BS from each school."
    ),
    "nyu-computer-science-engineering-bs-bs": (
        "Combines the College of Arts and Science computer science major with a general "
        "engineering program at NYU Tandon, giving software-oriented students a grounding "
        "in engineering analysis and design. The five-year path awards a BS from the "
        "College of Arts and Science and a BS from NYU Tandon, begun in the first year."
    ),
    "nyu-mathematics-civil-engineering-bs-bs": (
        "Applies the College of Arts and Science mathematics major — analysis, linear "
        "algebra, and differential equations — to civil engineering at NYU Tandon, where "
        "graduates model structures, transportation networks, and environmental systems. "
        "Students earn a BS from each school across five years."
    ),
    "nyu-mathematics-computer-engineering-bs-bs": (
        "Pairs the College of Arts and Science mathematics major with computer "
        "engineering at NYU Tandon, connecting discrete mathematics and computation with "
        "digital systems, processor design, and embedded hardware. The five-year program "
        "awards two BS degrees, one from each school."
    ),
    "nyu-mathematics-electrical-engineering-bs-bs": (
        "Brings the College of Arts and Science mathematics major together with "
        "electrical engineering at NYU Tandon, applying mathematical analysis to signal "
        "processing, control, and communications. Two BS degrees are conferred over five "
        "years, one from CAS and one from Tandon."
    ),
    "nyu-mathematics-mechanical-engineering-bs-bs": (
        "Couples the College of Arts and Science mathematics major with mechanical "
        "engineering at NYU Tandon, applying analysis and modeling to mechanics, "
        "thermodynamics, and dynamical systems. Graduates earn a BS from each school in a "
        "five-year plan that starts in the first year."
    ),
    "nyu-physics-civil-engineering-bs-bs": (
        "Combines the College of Arts and Science physics major — mechanics, "
        "electromagnetism, and modern physics — with civil engineering at NYU Tandon, "
        "grounding infrastructure and structural design in physical principles. The "
        "five-year dual-degree path awards a BS from each school."
    ),
    "nyu-physics-computer-engineering-bs-bs": (
        "Joins the College of Arts and Science physics major with computer engineering at "
        "NYU Tandon, linking the physics of devices and materials to digital systems and "
        "hardware design. Students complete two BS degrees over five years, one from CAS "
        "and one from Tandon."
    ),
    "nyu-physics-electrical-engineering-bs-bs": (
        "Pairs the College of Arts and Science physics major with electrical engineering "
        "at NYU Tandon, connecting electromagnetism and solid-state physics to circuits, "
        "photonics, and communications. The five-year program confers a BS from each "
        "school, with coursework begun in the first year."
    ),
    "nyu-physics-mechanical-engineering-bs-bs": (
        "Brings the College of Arts and Science physics major together with mechanical "
        "engineering at NYU Tandon, applying classical and modern physics to mechanics, "
        "thermodynamics, and energy systems. Two BS degrees are earned across five years, "
        "one from each school."
    ),
}

# ── Journalism dual MA — Global & Joint Program Studies (reporting + a regional master's) ──
_JOURNALISM: dict[str, str] = {
    "nyu-journalism-africana-studies-ma": (
        "A joint MA uniting NYU's Journalism program with Africana Studies, preparing "
        "reporters to cover the histories, politics, and cultures of Africa and the "
        "African diaspora. In the Global & Joint Program Studies model, small cohorts "
        "combine reporting training with deep regional study across two master's degrees."
    ),
    "nyu-journalism-east-asian-studies-ma": (
        "A joint MA combining NYU Journalism with East Asian Studies, equipping reporters "
        "to cover China, Japan, Korea, and the wider region with linguistic and "
        "historical depth. Global & Joint Program Studies cohorts pair rigorous "
        "journalism training with graduate area study."
    ),
    "nyu-journalism-european-mediterranean-studies-ma": (
        "A joint MA linking NYU Journalism with European and Mediterranean Studies, "
        "preparing journalists to report on the politics, economies, and societies of "
        "Europe and the Mediterranean basin. The Global & Joint Program Studies structure "
        "pairs reporting craft with regional expertise."
    ),
    "nyu-journalism-french-studies-ma": (
        "A joint MA pairing NYU Journalism with French Studies, training reporters to "
        "cover France and the Francophone world with command of language, culture, and "
        "intellectual history. Global & Joint Program Studies cohorts blend journalistic "
        "method with graduate regional study."
    ),
    "nyu-journalism-international-relations-ma": (
        "A joint MA combining NYU Journalism with International Relations, preparing "
        "reporters to cover diplomacy, security, and the global political economy. The "
        "Global & Joint Program Studies model joins reporting training with graduate "
        "study of world affairs across two degrees."
    ),
    "nyu-journalism-latin-american-caribbean-studies-ma": (
        "A joint MA uniting NYU Journalism with Latin American and Caribbean Studies, "
        "preparing reporters to cover the region's politics, social movements, and "
        "cultures. Global & Joint Program Studies cohorts pair reporting craft with deep "
        "area knowledge across two master's degrees."
    ),
    "nyu-journalism-near-eastern-studies-ma": (
        "A joint MA linking NYU Journalism with Near Eastern Studies, equipping reporters "
        "to cover the Middle East and North Africa with language skills and historical "
        "context. The Global & Joint Program Studies structure combines journalism "
        "training with graduate regional study."
    ),
    "nyu-journalism-russian-slavic-studies-ma": (
        "A joint MA combining NYU Journalism with Russian and Slavic Studies, preparing "
        "journalists to report on Russia, Eastern Europe, and Eurasia with linguistic and "
        "cultural fluency. Global & Joint Program Studies cohorts pair reporting method "
        "with graduate area expertise."
    ),
}

# ── BS in Teaching a World Language 7-12 (language in CAS, pedagogy in Steinhardt) ──
_TEACH_LANG: dict[str, str] = {
    "nyu-teaching-world-language-7-12-chinese-bs": (
        "Prepares teachers of Mandarin Chinese for New York State certification in grades "
        "7–12, combining advanced Chinese language and culture with world-language "
        "pedagogy. Language coursework is taken in the College of Arts and Science and "
        "teaching methods in the Steinhardt School, culminating in supervised student "
        "teaching."
    ),
    "nyu-teaching-world-language-7-12-french-bs": (
        "Prepares teachers of French for grades 7–12 certification, joining advanced "
        "French language, literature, and culture with methods for second-language "
        "instruction. Students take language courses in the College of Arts and Science "
        "and pedagogy in Steinhardt, ending with classroom student teaching."
    ),
    "nyu-teaching-world-language-7-12-italian-bs": (
        "Prepares teachers of Italian for grades 7–12 certification, pairing advanced "
        "Italian language and culture with world-language teaching methods. Language "
        "study sits in the College of Arts and Science and pedagogical training in "
        "Steinhardt, concluding with supervised student teaching."
    ),
    "nyu-teaching-world-language-7-12-japanese-bs": (
        "Prepares teachers of Japanese for grades 7–12 certification, combining advanced "
        "Japanese language and culture with methods for teaching a world language. "
        "Coursework spans language study in the College of Arts and Science and teaching "
        "methods in Steinhardt, with a student-teaching placement."
    ),
    "nyu-teaching-world-language-7-12-spanish-bs": (
        "Prepares teachers of Spanish for grades 7–12 certification, uniting advanced "
        "Spanish language, literature, and culture with second-language pedagogy. "
        "Students complete language courses in the College of Arts and Science and "
        "teaching methods in Steinhardt, finishing with supervised student teaching."
    ),
}

# ── BS in Teaching Science 7-12 (content core + science pedagogy; NY State certification) ──
_TEACH_SCI: dict[str, str] = {
    "nyu-teaching-chemistry-7-12-bs": (
        "Prepares teachers of chemistry for grades 7–12 with a 5–6 extension, pairing a "
        "rigorous chemistry foundation with methods for teaching science in diverse "
        "classrooms. The Steinhardt program culminates in two semesters of supervised "
        "teaching and leads to New York State certification."
    ),
    "nyu-teaching-earth-science-7-12-bs": (
        "Prepares teachers of earth science for grades 7–12 with a 5–6 extension, "
        "combining geology, meteorology, and astronomy content with science-teaching "
        "pedagogy. Two semesters of supervised classroom teaching lead to New York State "
        "certification."
    ),
    "nyu-teaching-physics-7-12-bs": (
        "Prepares teachers of physics for grades 7–12 with a 5–6 extension, joining a "
        "physics content core with methods for teaching science to middle and high school "
        "students. The Steinhardt program ends with supervised student teaching and New "
        "York State certification."
    ),
}

# ── Combined majors in Global Public Health (CAS: public health + a discipline) ──
_GPH: dict[str, str] = {
    "nyu-global-public-health-science-bs": (
        "A combined BS in Global Public Health and Science, pairing the foundations of "
        "public health — epidemiology, biostatistics, and global health systems — with "
        "the natural sciences for students aiming at medicine, research, or health "
        "policy. This selective College of Arts and Science major integrates "
        "public-health coursework with a science concentration."
    ),
    "nyu-global-public-health-anthropology-ba": (
        "A combined BA in Global Public Health and Anthropology, joining public-health "
        "foundations with the anthropological study of culture, society, and health — "
        "well suited to global health and community practice. The selective major weaves "
        "GPH coursework together with anthropology."
    ),
    "nyu-global-public-health-history-ba": (
        "A combined BA in Global Public Health and History, pairing public-health "
        "training with historical analysis of disease, medicine, and society to "
        "understand how health is shaped over time. This selective major blends GPH "
        "coursework with the study of history."
    ),
    "nyu-global-public-health-sociology-ba": (
        "A combined BA in Global Public Health and Sociology, uniting public-health "
        "foundations with sociological analysis of inequality, institutions, and "
        "population health. The selective major integrates GPH coursework with sociology."
    ),
}

# ── Urban Studies joint majors (interdisciplinary study of cities + a discipline) ──
_URBAN: dict[str, str] = {
    "nyu-urban-studies-anthropology-ba": (
        "A joint major in Urban Studies and Anthropology, examining cities through "
        "ethnography and the study of urban communities, culture, and everyday life. It "
        "combines the interdisciplinary urban-studies core — cities, regions, and the "
        "built environment — with anthropological methods."
    ),
    "nyu-urban-studies-history-ba": (
        "A joint major in Urban Studies and History, studying cities through their "
        "historical development, politics, and social change. It pairs the urban-studies "
        "core with historical research on how cities and metropolitan regions have "
        "evolved."
    ),
    "nyu-urban-studies-social-cultural-analysis-ba": (
        "A joint major in Urban Studies and Social and Cultural Analysis, reading cities "
        "through race, gender, and cultural formations alongside the built environment. "
        "It combines the urban-studies core with critical social-and-cultural-analysis "
        "frameworks."
    ),
    "nyu-urban-studies-sociology-ba": (
        "A joint major in Urban Studies and Sociology, analyzing cities through social "
        "structure, inequality, and urban institutions. It joins the interdisciplinary "
        "urban-studies core with sociological theory and methods."
    ),
}

# ── Joint humanities / language + linguistics majors (rewrite the variant; base kept) ──
_HUMANITIES: dict[str, str] = {
    "nyu-french-linguistics-ba": (
        "A joint major combining French — language, literature, and the cultures of the "
        "Francophone world — with linguistics, the scientific study of language structure "
        "and use. Students pair advanced French study with coursework in phonology, "
        "syntax, and language acquisition."
    ),
    "nyu-german-linguistics-ba": (
        "A joint major uniting German language, literature, and thought with linguistics, "
        "the systematic study of language. Students combine advanced German with training "
        "in phonology, syntax, semantics, and the analysis of language."
    ),
    "nyu-italian-linguistics-ba": (
        "A joint major pairing Italian — language, literature, and culture — with "
        "linguistics, the scientific study of how language works. Students combine "
        "advanced Italian with coursework in the structure and acquisition of language."
    ),
    "nyu-spanish-linguistics-ba": (
        "A joint major combining Spanish — the languages and cultures of Spain, Latin "
        "America, and the Hispanic world — with linguistics. Students pair advanced "
        "Spanish study with the formal analysis of language structure, sound, and meaning."
    ),
    "nyu-spanish-portuguese-ba": (
        "A major in the Department of Spanish and Portuguese spanning the languages, "
        "literatures, and cultures of the Spanish- and Portuguese-speaking worlds — Latin "
        "America, the Caribbean, the Iberian Peninsula, and the Luso-Afro-Brazilian "
        "sphere. Students develop advanced proficiency in both languages."
    ),
    "nyu-classics-art-history-ba": (
        "A joint major combining Classics — the languages, literature, and history of "
        "ancient Greece and Rome — with Art History, the study of art from antiquity to "
        "the present. Students read classical texts alongside the analysis of ancient and "
        "later visual culture."
    ),
    "nyu-classical-civilization-ba": (
        "A major in the Department of Classics centered on the civilizations of ancient "
        "Greece and Rome — their literature, history, philosophy, art, and society — "
        "studied largely in English translation. It offers a broad humanistic grounding "
        "without a language-proficiency requirement."
    ),
    "nyu-classical-civilization-hellenic-studies-ba": (
        "A joint major pairing Classical Civilization — the literature, history, and "
        "thought of ancient Greece and Rome — with Hellenic Studies, the study of Greek "
        "culture from antiquity through the modern era. Students trace the Greek world "
        "across its ancient and later periods."
    ),
    "nyu-cinema-studies-ba": (
        "Cinema Studies at NYU is housed in the Martin Scorsese Department of Cinema "
        "Studies, where students pursue the critical and historical study of film as both "
        "an art form and a form of mass culture. This College of Arts and Science major "
        "emphasizes film history, theory, and analysis rather than production."
    ),
}

# ── Professional / other distinct programs sharing a base blurb ──
_OTHER: dict[str, str] = {
    "nyu-biochemistry-ba": (
        "NYU's Bachelor of Arts in Biochemistry, in the Department of Chemistry, studies "
        "the chemical processes of living systems — proteins, nucleic acids, metabolism, "
        "and enzyme function — at the interface of chemistry and biology. The major "
        "combines core chemistry and biology coursework with laboratory training and "
        "opportunities for undergraduate research."
    ),
    "nyu-stern-nyu-abu-dhabi-mba": (
        "Stern at NYU Abu Dhabi delivers a globally focused MBA on NYU's Abu Dhabi "
        "campus, combining the Stern curriculum with immersion in Middle Eastern and "
        "emerging-market business. It serves experienced professionals through full-time "
        "and part-time executive formats."
    ),
    "nyu-drama-therapy-alternate-licensure-ma": (
        "A variant of NYU's Drama Therapy MA structured for an alternate licensure "
        "pathway toward Licensed Creative Arts Therapist (LCAT) eligibility. Like the "
        "standard track, it trains students to use theatre techniques therapeutically "
        "through coursework, fieldwork, and supervised internships with creative-arts "
        "therapists."
    ),
    "nyu-teaching-social-studies-7-12-5-6-extension-students-disabilities-7-12-generalist-ma": (
        "A dual-certification MA preparing teachers of social studies — US and world "
        "history, geography, economics, and civics — for grades 7–12, with a 5–6 "
        "extension and a Students-with-Disabilities generalist certification. Content "
        "courses pair with inclusive-classroom pedagogy, fieldwork, and supervised "
        "student teaching in New York City schools."
    ),
    "nyu-early-childhood-education-special-bs": (
        "A dual-certification BS preparing teachers for both early childhood education "
        "(birth through grade 2) and early childhood special education, blending child "
        "development, inclusive pedagogy, and content methods. Extensive fieldwork and "
        "student teaching lead to New York State initial certification in both areas."
    ),
    "nyu-applied-general-studies-ba": (
        "An interdisciplinary major in the School of Professional Studies' Division of "
        "Applied Undergraduate Studies that lets students design a personalized plan of "
        "study across disciplines, anchored by a liberal-arts foundation. It suits adult "
        "and transfer students building a custom path toward professional goals."
    ),
    "nyu-social-sciences-ba": (
        "A School of Professional Studies major grounding students in the social "
        "sciences — drawing on economics, politics, psychology, and sociology — within "
        "the Division of Applied Undergraduate Studies' liberal-arts core. It develops "
        "analytical and research skills for careers and graduate study."
    ),
}

GOLD_DESCRIPTIONS: dict[str, str] = {
    **_COMBINED_BS,
    **_JOURNALISM,
    **_TEACH_LANG,
    **_TEACH_SCI,
    **_GPH,
    **_URBAN,
    **_HUMANITIES,
    **_OTHER,
}


# ── DNP collapse (REPAIR_BACKLOG miss #2 — six "Doctor of Nursing Practice — {specialty}"
# concentration-split rows collapse into ONE DNP carrying the specialties as tracks) ──
DNP_SLUG = "nyu-doctor-of-nursing-practice-dnp"
DNP_NAME = "Doctor of Nursing Practice"
DNP_DEPARTMENT = "Rory Meyers College of Nursing"
DNP_WEBSITE = "https://bulletins.nyu.edu/graduate/nursing/"
DNP_DESCRIPTION = (
    "The Doctor of Nursing Practice at NYU Rory Meyers College of Nursing is a practice "
    "doctorate preparing advanced practice registered nurses to lead clinical care and "
    "translate evidence into practice. Students specialize in one advanced-practice "
    "population focus and build doctoral competencies in healthcare policy, informatics, "
    "quality improvement, and systems leadership."
)
DNP_TRACKS = {
    "concentrations": [
        "Adult-Gerontology Acute Care Nurse Practitioner",
        "Adult-Gerontology Primary Care Nurse Practitioner",
        "Family Nurse Practitioner",
        "Nurse-Midwifery",
        "Pediatric Nurse Practitioner",
        "Psychiatric-Mental Health Nurse Practitioner",
    ],
    "note": "NYU Meyers offers the DNP across these advanced-practice specializations.",
}
