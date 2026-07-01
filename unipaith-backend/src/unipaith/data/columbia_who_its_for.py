"""Columbia University — program-distinct ``who_its_for`` statements.

One field-specific "Who it's for" statement per program slug. ``who_its_for`` is a
UNIVERSAL depth field (SKILL.md miss #3): every program can state the applicant it fits,
derived from its own published subject, audience and typical outcomes. These replace the
type-gamed pair of baseline strings (``_WHO_BASELINE`` for bachelor's, ``_WHO_GRAD_BASELINE``
for graduate) that shipped on ~164 of 167 programs — distinctness ≈ 0.10, one undergraduate
"Core Curriculum" line and one "top-ranked Columbia degree" line across the whole catalog.

Each statement names the subject + who it fits + a typical next step, and the same field's
credential siblings (B.A./B.S. → M.A./M.S. → Ph.D. → professional) differ by level (an
undergraduate foundation vs advanced graduate expertise vs original doctoral research vs a
practice-oriented professional degree). Nothing invents a fact — the audience is grounded in
the program's real field and level. Full coverage + distinctness are asserted at build time
in ``columbia_profile``.
"""

from __future__ import annotations

# ruff: noqa: E501

WHO_BY_SLUG: dict[str, str] = {
    # ── Columbia College — Bachelor of Arts (Arts & Sciences) ──
    "columbia-economics-ba": (
        "Analytically minded undergraduates who want to understand markets, incentives "
        "and policy through microeconomics, macroeconomics and econometrics, on paths "
        "into finance, consulting, government or graduate economics."
    ),
    "columbia-political-science-ba": (
        "Students who want to analyze power, institutions and public life across "
        "American, comparative and international politics, toward law, government, "
        "policy or journalism."
    ),
    "columbia-history-ba": (
        "Undergraduates who want to study the past across periods and regions, building "
        "research and argument skills for law, education, public history or graduate study."
    ),
    "columbia-english-ba": (
        "Students who love literature and want close reading and critical writing across "
        "English and comparative literature, toward publishing, law, teaching or the arts."
    ),
    "columbia-psychology-ba": (
        "Undergraduates fascinated by the mind and behavior who want cognitive, clinical, "
        "developmental and social psychology with research experience, toward health, "
        "human services or graduate study."
    ),
    "columbia-sociology-ba": (
        "Students who want to understand inequality, institutions and social change "
        "through quantitative and qualitative methods, toward law, policy or social research."
    ),
    "columbia-biology-ba": (
        "Undergraduates drawn to the molecular and cellular basis of life who want "
        "laboratory research experience, on paths into medicine, biotech or graduate science."
    ),
    "columbia-anthropology-ba": (
        "Students curious about human societies and cultures who want ethnographic and "
        "archaeological training, toward research, global health, development or graduate study."
    ),
    "columbia-art-history-ba": (
        "Undergraduates who want to study the history of art and visual culture across "
        "periods, toward museums, conservation, the art world or academia."
    ),
    "columbia-archaeology-ba": (
        "Students drawn to the material past who want fieldwork, artifacts and the "
        "interpretation of ancient societies, toward archaeology, museums or graduate research."
    ),
    "columbia-chemistry-ba": (
        "Undergraduates fascinated by molecules and reactions who want a rigorous "
        "chemistry foundation with research, on paths into medicine, industry or graduate science."
    ),
    "columbia-biochemistry-ba": (
        "Students at the interface of chemistry and biology who want to study the "
        "molecular machinery of life, toward medicine, biotech or graduate research."
    ),
    "columbia-physics-ba": (
        "Undergraduates who want rigorous training in physical law and mathematics — "
        "from mechanics to quantum theory — toward research, engineering or graduate physics."
    ),
    "columbia-astronomy-ba": (
        "Students captivated by the cosmos who want observational and theoretical "
        "astronomy grounded in physics and mathematics, toward research or graduate study."
    ),
    "columbia-astrophysics-ba": (
        "Undergraduates who want a physics-intensive study of stars, galaxies and "
        "cosmology, preparing for astrophysics research or graduate school."
    ),
    "columbia-mathematics-ba": (
        "Students who love rigorous mathematics — algebra, analysis and geometry — toward "
        "research, quantitative careers, teaching or graduate study."
    ),
    "columbia-statistics-ba": (
        "Undergraduates who want probability, statistical inference and data analysis as "
        "a foundation for analytics, data science, research or graduate study."
    ),
    "columbia-philosophy-ba": (
        "Students drawn to logic, ethics and the theory of knowledge who want rigorous "
        "argument and analysis, toward law, policy, technology or graduate philosophy."
    ),
    "columbia-religion-ba": (
        "Undergraduates who want to study religious traditions, texts and their role in "
        "society across cultures, toward humanities careers, law or graduate study."
    ),
    "columbia-classics-ba": (
        "Students drawn to the languages, literature and history of Greece and Rome who "
        "want rigorous linguistic and interpretive training for law, the humanities or academia."
    ),
    "columbia-music-ba": (
        "Undergraduates who want to combine performance, composition and musicology in a "
        "liberal-arts setting, toward the arts, education or graduate music study."
    ),
    "columbia-french-ba": (
        "Students who want advanced fluency in French and immersion in its literature and "
        "culture, toward international work, translation, teaching or graduate study."
    ),
    "columbia-german-ba": (
        "Undergraduates who want German language, literature and thought, toward "
        "international careers, translation or graduate study in German studies."
    ),
    "columbia-italian-ba": (
        "Students who want fluency in Italian and study of its literature, art and "
        "history, toward international work, the arts or graduate study."
    ),
    "columbia-hispanic-studies-ba": (
        "Undergraduates who want advanced Spanish and study of the literatures and "
        "cultures of Spain and Latin America, toward international, education or graduate paths."
    ),
    "columbia-russian-ba": (
        "Students drawn to Russian language and culture who want fluency and cultural "
        "study, toward diplomacy, area studies, translation or graduate work."
    ),
    "columbia-slavic-studies-ba": (
        "Undergraduates interested in the languages, literatures and cultures of the "
        "Slavic world, toward area studies, international careers or graduate study."
    ),
    "columbia-east-asian-studies-ba": (
        "Students who want interdisciplinary study of China, Japan or Korea with language "
        "training, toward diplomacy, business, journalism or scholarship on East Asia."
    ),
    "columbia-mesaas-ba": (
        "Undergraduates focused on the Middle East, South Asia and Africa who want "
        "interdisciplinary regional study with languages, toward policy, research or "
        "international careers."
    ),
    "columbia-aaads-ba": (
        "Students who want to study the histories, cultures and politics of African and "
        "African-diaspora peoples, toward law, public policy, the arts or academia."
    ),
    "columbia-linguistics-ba": (
        "Undergraduates fascinated by the structure of language — phonetics, syntax and "
        "semantics — toward research, language technology or graduate study."
    ),
    "columbia-earth-science-ba": (
        "Students drawn to the solid earth, oceans and climate who want quantitative "
        "earth-science training, toward environmental careers, energy or graduate science."
    ),
    "columbia-environmental-science-ba": (
        "Undergraduates focused on the science of environmental systems — ecology, "
        "climate and sustainability — toward environmental careers, policy or graduate study."
    ),
    "columbia-environmental-biology-ba": (
        "Students interested in ecology, biodiversity and organisms in their environment, "
        "toward conservation, environmental science or graduate research."
    ),
    "columbia-neuroscience-and-behavior-ba": (
        "Undergraduates fascinated by the brain and behavior who want integrated "
        "neuroscience and psychology with research, toward medicine, neuroscience or graduate study."
    ),
    "columbia-financial-economics-ba": (
        "Students who want economics focused on financial markets, asset pricing and "
        "corporate finance, toward finance, consulting or graduate study."
    ),
    "columbia-american-studies-ba": (
        "Undergraduates who want an interdisciplinary study of U.S. history, culture and "
        "identity, toward law, media, public service or graduate study."
    ),
    "columbia-ancient-studies-ba": (
        "Students drawn to the ancient Mediterranean who want to combine archaeology, "
        "history and classical languages across civilizations, toward the humanities or academia."
    ),
    "columbia-comparative-literature-and-society-ba": (
        "Undergraduates who want to read literature across languages and cultures "
        "alongside social theory, toward the humanities, international work or graduate study."
    ),
    "columbia-creative-writing-ba": (
        "Students committed to fiction, poetry or nonfiction who want to develop a craft "
        "through workshops, toward writing, publishing or an M.F.A."
    ),
    "columbia-drama-and-theatre-arts-ba": (
        "Undergraduates drawn to theater — performance, dramaturgy and production — who "
        "want to study and make theater, toward the performing arts or graduate study."
    ),
    "columbia-film-and-media-studies-ba": (
        "Students interested in the analysis of film and media who want critical and "
        "historical study, toward media industries, criticism or graduate work."
    ),
    "columbia-visual-arts-ba": (
        "Undergraduates committed to studio practice — painting, sculpture and new media — "
        "who want to develop an artistic practice, toward the arts or an M.F.A."
    ),
    "columbia-architecture-ba": (
        "Students drawn to the built environment who want a liberal-arts approach to "
        "architecture — design, history and theory — as a foundation for a professional M.Arch."
    ),
    "columbia-cognitive-science-ba": (
        "Undergraduates curious about how minds work who want to integrate psychology, "
        "linguistics, philosophy, neuroscience and computation, toward AI, research or graduate study."
    ),
    "columbia-data-science-ba": (
        "Students who want to reason with data across domains, combining statistics and "
        "computing with societal impact, toward analytics, machine learning or research."
    ),
    "columbia-human-rights-ba": (
        "Undergraduates committed to human rights who want interdisciplinary study of "
        "rights, law and advocacy, toward law, policy, NGOs or graduate work."
    ),
    "columbia-medical-humanities-ba": (
        "Students interested in medicine through the humanities — ethics, narrative and "
        "the social dimensions of health — toward medicine, health policy or graduate study."
    ),
    "columbia-sustainable-development-ba": (
        "Undergraduates focused on the economics, science and policy of sustainable "
        "development, toward environmental and development careers or graduate study."
    ),
    "columbia-urban-studies-ba": (
        "Students interested in cities — inequality, housing and urban life — who want "
        "interdisciplinary study, toward planning, policy or graduate work."
    ),
    "columbia-ethnicity-and-race-studies-ba": (
        "Undergraduates who want comparative study of ethnicity, race and social justice, "
        "toward law, policy, education, the arts or graduate study."
    ),
    "columbia-womens-and-gender-studies-ba": (
        "Students who want interdisciplinary study of gender, sexuality and society, "
        "toward law, policy, advocacy or graduate work."
    ),
    "columbia-latin-american-studies-ba": (
        "Undergraduates focused on Latin America and the Caribbean who want "
        "interdisciplinary regional study with language, toward international careers or research."
    ),
    "columbia-economics-mathematics-ba": (
        "Quantitatively strong students who want economics with rigorous mathematics, "
        "toward quantitative finance, data-driven policy or graduate economics."
    ),
    "columbia-mathematics-statistics-ba": (
        "Undergraduates who want a joint foundation in mathematics and statistics, toward "
        "data science, actuarial work, quantitative finance or graduate study."
    ),
    "columbia-computer-science-mathematics-ba": (
        "Students who want computer science paired with rigorous mathematics, toward "
        "software, machine learning, quantitative roles or graduate study."
    ),
    # ── GSAS — Doctor of Philosophy (and terminal M.A.) ──
    "columbia-economics-phd": (
        "Aspiring economists pursuing doctoral research across theory and applied fields, "
        "on academic, central-bank and research-institute paths."
    ),
    "columbia-political-science-phd": (
        "Aspiring political scientists pursuing doctoral research across American, "
        "comparative and international politics, on academic and policy-research paths."
    ),
    "columbia-history-phd": (
        "Aspiring historians pursuing doctoral research across periods and regions, on "
        "academic, archival and public-history paths."
    ),
    "columbia-english-phd": (
        "Aspiring literary scholars pursuing doctoral research in English and comparative "
        "literature, on academic and teaching paths."
    ),
    "columbia-psychology-phd": (
        "Aspiring researchers pursuing doctoral work in cognitive, clinical, "
        "developmental or social psychology, on academic and research paths."
    ),
    "columbia-sociology-phd": (
        "Aspiring sociologists pursuing doctoral research on inequality, institutions and "
        "social change, on academic and research paths."
    ),
    "columbia-biological-sciences-phd": (
        "Aspiring researchers pursuing doctoral work in the biological sciences — from "
        "molecular to systems biology — on academic and biomedical research paths."
    ),
    "columbia-chemistry-phd": (
        "Aspiring chemists pursuing doctoral research across organic, inorganic and "
        "physical chemistry, on academic, national-lab and industry paths."
    ),
    "columbia-physics-phd": (
        "Aspiring physicists pursuing doctoral research from particle to condensed-matter "
        "physics, on academic and national-lab paths."
    ),
    "columbia-mathematics-phd": (
        "Aspiring mathematicians pursuing doctoral research across pure and applied "
        "mathematics, on academic and research-institute paths."
    ),
    "columbia-statistics-phd": (
        "Aspiring statisticians pursuing doctoral research in statistical theory and "
        "methods, on academic, industry-research and data-science paths."
    ),
    "columbia-astronomy-phd": (
        "Aspiring astronomers pursuing doctoral research from stars to cosmology, on "
        "academic and observatory research paths."
    ),
    "columbia-anthropology-phd": (
        "Aspiring anthropologists pursuing doctoral research through fieldwork and "
        "cross-cultural theory, on academic and research paths."
    ),
    "columbia-art-history-and-archaeology-phd": (
        "Aspiring scholars pursuing doctoral research in the history of art and "
        "archaeology, on academic, museum and curatorial paths."
    ),
    "columbia-classics-phd": (
        "Aspiring classicists pursuing doctoral research on Greek and Roman language, "
        "literature and history, on academic paths."
    ),
    "columbia-music-phd": (
        "Aspiring scholars and composers pursuing doctoral research in musicology, theory "
        "or composition, on academic and creative paths."
    ),
    "columbia-philosophy-phd": (
        "Aspiring philosophers pursuing doctoral research across the analytic tradition, "
        "on academic paths."
    ),
    "columbia-religion-phd": (
        "Aspiring scholars pursuing doctoral research on religious traditions, texts and "
        "societies, on academic paths."
    ),
    "columbia-earth-and-environmental-sciences-phd": (
        "Aspiring researchers pursuing doctoral work on the earth, oceans and climate, "
        "on academic, energy and agency research paths."
    ),
    "columbia-ecology-evolution-phd": (
        "Aspiring researchers pursuing doctoral work in ecology, evolution and "
        "environmental biology, on academic, conservation and research paths."
    ),
    "columbia-french-phd": (
        "Aspiring scholars pursuing doctoral research on French literature and thought, "
        "on academic paths."
    ),
    "columbia-german-phd": (
        "Aspiring scholars pursuing doctoral research on German literature and "
        "intellectual history, on academic paths."
    ),
    "columbia-italian-phd": (
        "Aspiring scholars pursuing doctoral research on Italian literature and culture, "
        "on academic paths."
    ),
    "columbia-hispanic-studies-phd": (
        "Aspiring scholars pursuing doctoral research on the literatures and cultures of "
        "Spain and Latin America, on academic paths."
    ),
    "columbia-slavic-studies-phd": (
        "Aspiring scholars pursuing doctoral research on Slavic languages, literatures and "
        "cultures, on academic paths."
    ),
    "columbia-east-asian-studies-phd": (
        "Aspiring scholars pursuing doctoral research on the languages, literatures and "
        "histories of China, Japan or Korea, on academic paths."
    ),
    "columbia-mesaas-phd": (
        "Aspiring scholars pursuing doctoral research on the Middle East, South Asia and "
        "Africa, on academic paths."
    ),
    "columbia-aaads-phd": (
        "Aspiring scholars pursuing doctoral research in African American and African "
        "diaspora studies, on academic paths."
    ),
    "columbia-neuroscience-phd": (
        "Aspiring researchers pursuing doctoral work in neuroscience — from circuits to "
        "behavior — on academic and biomedical research paths."
    ),
    "columbia-climate-and-society-ma": (
        "Graduate students who want to translate climate science into policy and practice, "
        "toward careers in climate adaptation, sustainability and environmental management."
    ),
    "columbia-human-rights-studies-ma": (
        "Advocates and researchers seeking advanced interdisciplinary study of human "
        "rights, toward careers in NGOs, international organizations, law or policy."
    ),
    "columbia-qmss-ma": (
        "Graduate students who want rigorous quantitative and computational methods for "
        "the social sciences, toward data analysis, research and applied social science."
    ),
    "columbia-statistics-ma": (
        "Graduate students seeking advanced statistical and data-analysis training as a "
        "step into data-science careers or a doctorate."
    ),
    # ── Fu Foundation School of Engineering and Applied Science ──
    "columbia-computer-science-bs": (
        "Technically strong undergraduates who want a rigorous computer-science education "
        "— algorithms, systems and AI — in the heart of New York's tech and research ecosystem."
    ),
    "columbia-operations-research-bs": (
        "Undergraduates who want to optimize complex systems through optimization, "
        "modeling and analytics, toward tech, finance, logistics or graduate study."
    ),
    "columbia-mechanical-engineering-bs": (
        "Students drawn to how physical systems work — mechanics, robotics and design — "
        "who want a project-based engineering education, toward industry or graduate study."
    ),
    "columbia-electrical-engineering-bs": (
        "Undergraduates interested in circuits, signals and devices who want an "
        "electrical-engineering foundation, toward hardware, communications or graduate study."
    ),
    "columbia-applied-mathematics-bs": (
        "Students who love mathematics and want to apply it — modeling and computation — "
        "across science, engineering and finance, toward technical careers or graduate study."
    ),
    "columbia-biomedical-engineering-bs": (
        "Undergraduates at the interface of engineering and medicine who want device "
        "design, imaging and tissue engineering, toward medicine, biotech or graduate research."
    ),
    "columbia-applied-physics-bs": (
        "Students who want physics applied to engineering — from quantum devices to "
        "materials — toward research, advanced technology or graduate study."
    ),
    "columbia-materials-science-and-engineering-bs": (
        "Undergraduates fascinated by the materials behind technology — electronic, "
        "structural and nanoscale — toward the tech, energy or materials industries or graduate study."
    ),
    "columbia-chemical-engineering-bs": (
        "Students who want to turn chemistry into processes and products — reaction "
        "engineering and transport — toward the energy, pharmaceutical or materials industries."
    ),
    "columbia-civil-engineering-bs": (
        "Undergraduates who want to design and protect infrastructure — structures and "
        "environmental systems — toward engineering practice or graduate study."
    ),
    "columbia-engineering-mechanics-bs": (
        "Students drawn to the mechanics of solids, fluids and structures who want a "
        "rigorous engineering-science foundation, toward research or advanced engineering."
    ),
    "columbia-computer-engineering-bs": (
        "Undergraduates at the hardware-software boundary who want to design computing "
        "systems — from chips to embedded systems — toward technology careers or graduate study."
    ),
    "columbia-earth-and-environmental-engineering-bs": (
        "Students focused on energy, resources and environmental systems who want "
        "engineering for sustainability, toward environmental engineering or graduate study."
    ),
    "columbia-industrial-engineering-bs": (
        "Undergraduates who want to optimize systems, operations and decisions using "
        "analytics, toward operations, consulting, tech or graduate study."
    ),
    "columbia-computer-science-ms": (
        "Graduate students deepening computer science — from AI to systems — who want "
        "advanced technical training in New York's tech hub, toward industry R&D or a doctorate."
    ),
    "columbia-mechanical-engineering-ms": (
        "Graduate students advancing mechanical engineering — robotics, controls and "
        "design — toward specialized industry roles or a doctorate."
    ),
    "columbia-electrical-engineering-ms": (
        "Graduate students in circuits, signals and communications who want advanced "
        "electrical-engineering training, toward industry R&D or a doctorate."
    ),
    "columbia-biomedical-engineering-ms": (
        "Graduate students advancing bioengineering — devices, imaging and therapeutics — "
        "toward the medical-technology industry or a doctorate."
    ),
    "columbia-chemical-engineering-ms": (
        "Graduate students deepening chemical engineering for advanced roles in energy, "
        "pharmaceuticals or materials, or a doctorate."
    ),
    "columbia-civil-engineering-ms": (
        "Graduate students specializing in structural, geotechnical or environmental "
        "civil engineering, toward advanced practice or a doctorate."
    ),
    "columbia-applied-physics-ms": (
        "Graduate students in applied physics — devices, photonics and materials — who "
        "want research-grade training toward industry R&D or a doctorate."
    ),
    "columbia-applied-mathematics-ms": (
        "Graduate students in mathematical modeling and computation who want applied "
        "training for science, engineering or data careers."
    ),
    "columbia-materials-science-and-engineering-ms": (
        "Graduate students in materials science — electronic, structural and nanoscale "
        "materials — toward advanced industry roles or a doctorate."
    ),
    "columbia-earth-and-environmental-engineering-ms": (
        "Graduate students in energy, resource and environmental engineering who want "
        "training for sustainability careers or a doctorate."
    ),
    "columbia-computer-engineering-ms": (
        "Graduate students at the hardware-software boundary who want advanced "
        "computer-engineering training, toward industry R&D or a doctorate."
    ),
    "columbia-operations-research-ms": (
        "Graduate students in optimization, stochastic modeling and analytics who want "
        "advanced quantitative training for analytics and operations careers."
    ),
    "columbia-industrial-engineering-ms": (
        "Graduate students in operations, analytics and systems engineering who want "
        "advanced training for operations and consulting careers."
    ),
    "columbia-financial-engineering-ms": (
        "Quantitatively strong graduate students who want financial engineering — "
        "derivatives, risk and stochastic modeling — for quantitative finance careers on Wall Street."
    ),
    "columbia-management-science-and-engineering-ms": (
        "Graduate students who want to combine engineering, analytics and management for "
        "data-driven decision and operations roles in industry."
    ),
    "columbia-data-science-ms": (
        "Graduate students who want rigorous machine learning, statistics and data "
        "engineering through the Data Science Institute, toward data-science and research careers."
    ),
    "columbia-computer-science-phd": (
        "Aspiring researchers pursuing doctoral work in computer science — from theory to "
        "AI and systems — on academic and industry-research paths."
    ),
    "columbia-mechanical-engineering-phd": (
        "Aspiring researchers pursuing doctoral work in mechanical engineering — robotics, "
        "controls and mechanics — on academic and industry-research paths."
    ),
    "columbia-electrical-engineering-phd": (
        "Aspiring researchers pursuing doctoral work in electrical engineering, from "
        "devices to communications, on academic and industry-research paths."
    ),
    "columbia-biomedical-engineering-phd": (
        "Aspiring researchers pursuing doctoral work in bioengineering, from imaging to "
        "therapeutics, on academic and biomedical-industry paths."
    ),
    "columbia-chemical-engineering-phd": (
        "Aspiring researchers pursuing doctoral work in chemical engineering across "
        "catalysis, energy and biomolecular systems, on academic and industry-research paths."
    ),
    "columbia-civil-engineering-phd": (
        "Aspiring researchers pursuing doctoral work in civil engineering — structures and "
        "environmental systems — on academic and research paths."
    ),
    "columbia-applied-physics-phd": (
        "Aspiring researchers pursuing doctoral work in applied physics — photonics, "
        "plasma and materials — on academic and national-lab paths."
    ),
    "columbia-materials-science-and-engineering-phd": (
        "Aspiring researchers pursuing doctoral work in materials science and "
        "engineering, on academic, national-lab and industry-research paths."
    ),
    "columbia-earth-and-environmental-engineering-phd": (
        "Aspiring researchers pursuing doctoral work in earth and environmental "
        "engineering, on academic, energy and sustainability research paths."
    ),
    "columbia-operations-research-phd": (
        "Aspiring researchers pursuing doctoral work in operations research — "
        "optimization and stochastic systems — on academic and industry-research paths."
    ),
    # ── Business (Columbia Business School) ──
    "columbia-mba": (
        "Aspiring leaders seeking a full-time MBA that connects academic theory to "
        "practice from the financial and business capital of the world."
    ),
    "columbia-emba": (
        "Experienced professionals seeking an Executive MBA that builds leadership and "
        "general-management depth while they keep working, in the heart of New York business."
    ),
    "columbia-accounting-ms": (
        "Graduate students seeking rigorous accounting and financial-analysis training "
        "for careers in investment research, corporate finance or a doctorate."
    ),
    "columbia-financial-economics-ms": (
        "Quantitatively strong graduate students who want a research-oriented master's in "
        "financial economics, toward finance research, quantitative roles or a doctorate."
    ),
    "columbia-marketing-science-ms": (
        "Analytically minded graduate students who want data-driven marketing science — "
        "consumer analytics and modeling — toward marketing analytics or a doctorate."
    ),
    "columbia-business-phd": (
        "Aspiring management scholars pursuing doctoral research across finance, "
        "marketing, management and decision sciences, on academic paths."
    ),
    # ── Law ──
    "columbia-jd": (
        "Aspiring attorneys seeking the J.D. at one of the nation's most influential law "
        "schools, with strength in corporate, constitutional and international law."
    ),
    "columbia-llm": (
        "Lawyers — often internationally trained — seeking a one-year master's to deepen "
        "expertise in a field of law or qualify for U.S. practice."
    ),
    "columbia-jsd": (
        "Legal scholars pursuing the J.S.D. research doctorate to produce original legal "
        "scholarship, on paths into law-faculty careers."
    ),
    # ── Medicine, health and nursing ──
    "columbia-md": (
        "Future physicians seeking the M.D. at a leading academic medical center, "
        "combining clinical training with biomedical research."
    ),
    "columbia-physical-therapy-dpt": (
        "Future physical therapists seeking the clinical doctorate — movement science and "
        "supervised patient care — for licensed rehabilitation practice."
    ),
    "columbia-genetic-counseling-ms": (
        "Students preparing to become genetic counselors who want clinical genetics, "
        "counseling and supervised training for certified practice."
    ),
    "columbia-human-nutrition-ms": (
        "Graduate students in nutrition science who want metabolic and clinical nutrition "
        "training, toward dietetics, research or health careers."
    ),
    "columbia-dental-dds": (
        "Future dentists seeking the D.D.S. — biomedical science and supervised clinical "
        "training — for licensed dental practice."
    ),
    # ── Journalism and communications ──
    "columbia-journalism-ms": (
        "Aspiring journalists seeking a rigorous reporting and writing degree at the only "
        "Ivy League journalism school, home of the Pulitzer Prizes."
    ),
    "columbia-journalism-ma": (
        "Working and specializing journalists who want to deepen subject expertise and "
        "reporting craft in an advanced master's, toward specialized and long-form journalism."
    ),
    "columbia-data-journalism-ms": (
        "Journalists who want to combine reporting with data analysis and visualization, "
        "toward investigative and data-driven journalism."
    ),
    "columbia-communications-phd": (
        "Aspiring scholars pursuing doctoral research on media, communication and society, "
        "on academic and research paths."
    ),
    # ── SIPA — international and public affairs ──
    "columbia-sipa-mia": (
        "Future global-affairs professionals seeking the Master of International Affairs — "
        "policy, economics and regional expertise — for careers in diplomacy, development "
        "and international organizations."
    ),
    "columbia-sipa-mpa": (
        "Future public leaders seeking the Master of Public Administration — policy "
        "analysis, economics and management — for government, nonprofit and public-sector careers."
    ),
    "columbia-sustainable-development-phd": (
        "Aspiring researchers pursuing doctoral work on the economics, science and policy "
        "of sustainable development, on academic and policy-research paths."
    ),
    # ── Public Health (Mailman) ──
    "columbia-public-health-mph": (
        "Future public-health leaders seeking the M.P.H. — epidemiology, biostatistics "
        "and health policy — for practice across public health, health systems and global health."
    ),
    "columbia-health-administration-mha": (
        "Aspiring health-care managers seeking the M.H.A. — health systems, finance and "
        "leadership — for management careers across hospitals and health organizations."
    ),
    "columbia-biostatistics-ms": (
        "Quantitatively strong graduate students who want biostatistics — study design "
        "and statistical analysis of health data — toward public health, pharma or a doctorate."
    ),
    "columbia-public-health-drph": (
        "Experienced public-health professionals pursuing the DrPH — advanced leadership "
        "and applied research — for senior roles in public-health practice and policy."
    ),
    # ── Social Work ──
    "columbia-social-work-msw": (
        "Future social workers seeking the M.S.S.W. — clinical practice, policy and "
        "community work — for direct-service and leadership careers in social welfare."
    ),
    "columbia-social-work-phd": (
        "Aspiring scholars pursuing doctoral research on social welfare, inequality and "
        "clinical practice, on academic and policy-research paths."
    ),
    # ── Architecture, Planning and Preservation (GSAPP) ──
    "columbia-architecture-march": (
        "Design-focused students seeking the professional Master of Architecture — design "
        "studios with history, theory and technology — toward licensed architectural practice."
    ),
    "columbia-urban-planning-ms": (
        "Future planners who want urban planning — housing, transportation and community "
        "development — for careers in city planning, policy and development."
    ),
    "columbia-historic-preservation-ms": (
        "Graduate students committed to preserving the built environment who want "
        "conservation, history and technology, toward preservation practice and policy."
    ),
    "columbia-real-estate-development-ms": (
        "Graduate students combining finance, design and development who want a "
        "professional real-estate degree, toward development, investment and urban careers."
    ),
    "columbia-urban-design-ms": (
        "Designers seeking advanced urban design — the shaping of streets, blocks and "
        "public space — toward urban-design practice at the city scale."
    ),
    "columbia-architecture-aad-ms": (
        "Licensed architects and advanced designers seeking a post-professional degree in "
        "cutting-edge architectural design and research."
    ),
    # ── School of the Arts ──
    "columbia-arts-mfa": (
        "Committed artists and writers seeking the M.F.A. to develop a professional "
        "practice in the arts through intensive studio and workshop training."
    ),
    "columbia-film-media-studies-ma": (
        "Graduate students who want advanced critical and historical study of film and "
        "media, toward criticism, curation or a doctorate."
    ),
    # ── Nursing ──
    "columbia-nursing-msn": (
        "Career-changers with a bachelor's in another field who want an accelerated "
        "direct-entry path to become registered nurses through Columbia Nursing."
    ),
    "columbia-nursing-dnp": (
        "Advanced-practice nurses seeking the clinical doctorate — advanced clinical "
        "training and leadership — for the highest level of nursing practice."
    ),
    "columbia-nursing-phd": (
        "Aspiring nurse-scientists pursuing doctoral research on health, care and nursing "
        "science, on academic and research paths."
    ),
}
