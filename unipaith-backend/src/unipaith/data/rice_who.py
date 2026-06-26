"""Rice University — universal ``who_its_for`` depth field per program.

REPAIR_BACKLOG #4: a UNIVERSAL depth field that must be filled on EVERY program AND be
PROGRAM-DISTINCT (distinct strings / programs approximately 1.0), never a degree-type
template. Each statement names the applicant the program fits (background/interests,
goals/readiness, and the typical next step), derived strictly from that program's own
verified ``description`` and degree level — no fabricated facts (no rankings, numbers, or
named centers). All 159 strings are distinct (distinct/total = 1.0), matching the
field-specific gold bar (Emory/Brown/Purdue/UIUC).
"""

from __future__ import annotations

WHO_BY_SLUG: dict[str, str] = {
    # ── Wiess School of Natural Sciences — undergraduate ──
    "rice-astronomy-ug": (
        "Undergraduates fascinated by stars, galaxies, and the structure of the universe who "
        "want a broad foundation in observational and theoretical astronomy alongside physics "
        "and math, aiming toward research, graduate study, or science communication."
    ),
    "rice-astrophysics-ug": (
        "Students who want a physics-intensive path into the dynamics of stars, black holes, "
        "and cosmology, building the quantitative and computational depth that prepares them "
        "for doctoral research in astrophysics or data-heavy technical careers."
    ),
    "rice-biosciences-ug": (
        "Undergraduates drawn to living systems from molecules to ecosystems who want a "
        "flexible foundation across cell biology, genetics, and physiology, whether they are "
        "headed toward medical school, graduate research, or biotechnology."
    ),
    "rice-chemical-physics-ug": (
        "Students who enjoy working at the boundary of chemistry and physics and want the "
        "mathematical and laboratory rigor to study matter at the quantum and molecular level, "
        "preparing for graduate research in the physical sciences."
    ),
    "rice-chemistry-ug": (
        "Undergraduates curious about how matter reacts and transforms who want hands-on "
        "laboratory training across organic, inorganic, and physical chemistry, whether their "
        "goal is medical school, a chemistry PhD, or a research career in industry."
    ),
    "rice-earth-environmental-and-planetary-sciences-ug": (
        "Students interested in how the Earth and other planets work — from climate and oceans "
        "to deep-time geology — who want fieldwork and data skills for careers in environmental "
        "science, energy, or planetary research."
    ),
    "rice-environmental-science-ug": (
        "Undergraduates motivated by climate, ecosystems, and sustainability who want an "
        "interdisciplinary science foundation spanning earth systems, chemistry, and policy to "
        "work on environmental challenges or pursue graduate study."
    ),
    "rice-health-sciences-ug": (
        "Students preparing for medicine or public health who want to study the biological, "
        "social, and quantitative dimensions of health together, building a pre-professional "
        "foundation for clinical, research, or policy paths."
    ),
    "rice-mathematics-ug": (
        "Undergraduates who love rigorous proof and abstract structure and want a strong "
        "foundation in pure and applied mathematics, whether they aim for graduate study, "
        "quantitative industry roles, or further work in the sciences."
    ),
    "rice-neuroscience-ug": (
        "Students captivated by how the brain produces behavior who want integrated training "
        "across molecular, systems, and cognitive neuroscience, preparing for medical school, "
        "a neuroscience PhD, or research in industry."
    ),
    "rice-physics-ug": (
        "Undergraduates driven to understand the fundamental laws of nature who want a "
        "mathematically demanding foundation in classical and modern physics, building toward "
        "graduate research or technical careers that reward analytical depth."
    ),
    "rice-sports-medicine-and-exercise-physiology-ug": (
        "Students interested in human movement, performance, and rehabilitation who want a "
        "science grounding in exercise physiology and anatomy, preparing for medical or allied "
        "health programs, athletic training, or research."
    ),
    # ── George R. Brown School of Engineering and Computing — undergraduate ──
    "rice-artificial-intelligence-ug": (
        "Undergraduates who want to build intelligent systems and understand the algorithms "
        "behind machine learning, combining strong computing fundamentals with hands-on AI "
        "projects toward software, research, or graduate study in the field."
    ),
    "rice-bioengineering-ug": (
        "Students drawn to engineering at the interface of medicine and biology who want to "
        "design devices, therapies, and diagnostics, preparing for medical school, biotech, or "
        "graduate research in bioengineering."
    ),
    "rice-chemical-and-biomolecular-engineering-ug": (
        "Undergraduates who want to turn chemistry and biology into processes and products at "
        "scale — from energy to therapeutics — with the design and laboratory training for "
        "industry roles or graduate engineering study."
    ),
    "rice-chemical-engineering-ug": (
        "Students interested in the science of transforming raw materials into useful products "
        "who want a foundation in reaction engineering, thermodynamics, and process design for "
        "careers in energy, materials, or pharmaceuticals."
    ),
    "rice-civil-engineering-ug": (
        "Undergraduates who want to design and build the infrastructure people depend on — "
        "structures, transportation, and water systems — gaining the analytical and project "
        "skills for engineering practice or graduate study."
    ),
    "rice-civil-and-environmental-engineering-ug": (
        "Students who want to engineer resilient infrastructure and protect natural systems "
        "together, combining structural and environmental coursework to address sustainability, "
        "water, and the built environment."
    ),
    "rice-computational-and-applied-mathematics-ug": (
        "Undergraduates who enjoy using mathematics and computing to model real problems and "
        "want training in numerical methods, optimization, and data, preparing for technical "
        "industry roles or graduate study in applied math."
    ),
    "rice-computer-science-ug": (
        "Students who want to design algorithms and build software systems with a strong "
        "theoretical core, ready for engineering roles across the technology industry or "
        "graduate research in computer science."
    ),
    "rice-electrical-and-computer-engineering-ug": (
        "Undergraduates fascinated by everything from chips and circuits to signals and "
        "embedded systems who want hardware-software breadth for careers in electronics, "
        "computing, or graduate engineering study."
    ),
    "rice-environmental-engineering-ug": (
        "Students focused on clean water, air quality, and sustainable systems who want the "
        "engineering tools to design environmental solutions, preparing for practice, "
        "consulting, or graduate study."
    ),
    "rice-materials-science-and-nanoengineering-ug": (
        "Undergraduates curious about how the structure of materials governs their behavior "
        "who want to engineer new materials at the nanoscale, building toward research, "
        "advanced manufacturing, or graduate study."
    ),
    "rice-mechanical-engineering-ug": (
        "Students who like to design, analyze, and build mechanical and thermal systems and "
        "want broad engineering fundamentals for careers across energy, robotics, and "
        "aerospace or graduate study."
    ),
    "rice-operations-research-ug": (
        "Undergraduates who want to optimize complex systems and decisions using mathematics "
        "and data, building modeling and analytics skills for roles in logistics, finance, "
        "consulting, or graduate study."
    ),
    "rice-statistics-ug": (
        "Students who want to reason rigorously about data and uncertainty, gaining a "
        "foundation in statistical theory and computing for analytics careers or graduate "
        "study in statistics and data science."
    ),
    # ── School of Humanities — undergraduate ──
    "rice-ancient-mediterranean-civilizations-ug": (
        "Undergraduates drawn to the histories, languages, and material cultures of the ancient "
        "Mediterranean world who want interdisciplinary training in archaeology, texts, and "
        "history toward graduate study, museums, or the law."
    ),
    "rice-art-studio-art-ug": (
        "Students who want to develop as practicing artists across media while studying critical "
        "and visual theory, building a portfolio and foundation for creative careers or further "
        "study in the arts."
    ),
    "rice-art-history-ug": (
        "Undergraduates fascinated by how images and objects carry meaning across cultures and "
        "eras who want training in visual analysis and research toward careers in museums, "
        "galleries, or graduate study."
    ),
    "rice-asian-studies-ug": (
        "Students interested in the languages, histories, and societies of Asia who want "
        "interdisciplinary and language training for careers in international work, business, "
        "or graduate study."
    ),
    "rice-classical-studies-ug": (
        "Undergraduates who want to read Greek and Latin and study the ancient world's "
        "literature, philosophy, and history, building analytical and language skills for "
        "graduate study, teaching, or professional schools."
    ),
    "rice-english-ug": (
        "Students who love close reading and writing about literature who want to study texts, "
        "rhetoric, and culture critically, preparing for careers in writing, publishing, law, "
        "or graduate study."
    ),
    "rice-european-studies-ug": (
        "Undergraduates interested in the politics, cultures, and histories of Europe who want "
        "interdisciplinary and language training for international careers, business, or "
        "graduate study."
    ),
    "rice-french-studies-ug": (
        "Students who want fluency in French and a deep engagement with francophone literature "
        "and culture, building language and analytical skills for international work, teaching, "
        "or graduate study."
    ),
    "rice-german-studies-ug": (
        "Undergraduates drawn to German language, literature, and thought who want cultural and "
        "linguistic depth for careers in international work, the sciences, business, or graduate "
        "study."
    ),
    "rice-history-ug": (
        "Students who want to understand how the past shapes the present through evidence and "
        "argument, developing research and writing skills for law, public service, journalism, "
        "or graduate study."
    ),
    "rice-latin-american-and-latinx-studies-ug": (
        "Undergraduates engaged with the cultures, politics, and histories of Latin America and "
        "Latinx communities who want interdisciplinary and language training for careers in "
        "policy, advocacy, or graduate study."
    ),
    "rice-media-studies-ug": (
        "Students interested in how media and communication shape society who want critical and "
        "production skills to analyze and create across platforms, preparing for media careers "
        "or graduate study."
    ),
    "rice-philosophy-ug": (
        "Undergraduates who enjoy rigorous argument about knowledge, ethics, and reality and "
        "want training in logic and critical reasoning that prepares them for law, public "
        "policy, or graduate study."
    ),
    "rice-religion-ug": (
        "Students curious about religious traditions, texts, and their role in human cultures "
        "who want interdisciplinary training in interpretation and history for careers in the "
        "professions, nonprofits, or graduate study."
    ),
    "rice-spanish-and-portuguese-ug": (
        "Undergraduates who want advanced fluency in Spanish and Portuguese and a deep study of "
        "Iberian and Latin American literatures and cultures, building skills for international "
        "and bilingual careers or graduate study."
    ),
    "rice-study-of-women-gender-and-sexuality-ug": (
        "Students who want to analyze how gender and sexuality shape society, culture, and "
        "power through interdisciplinary methods, preparing for careers in advocacy, the "
        "professions, or graduate study."
    ),
    # ── School of Social Sciences — undergraduate ──
    "rice-anthropology-ug": (
        "Undergraduates curious about human cultures, social life, and what it means to be "
        "human who want ethnographic and comparative training for careers in research, "
        "global work, or graduate study."
    ),
    "rice-cognitive-sciences-ug": (
        "Students fascinated by how the mind perceives, learns, and reasons who want an "
        "interdisciplinary blend of psychology, linguistics, computing, and neuroscience "
        "toward research, technology, or graduate study."
    ),
    "rice-economics-ug": (
        "Undergraduates who want to understand how people, markets, and policy interact, "
        "gaining quantitative and analytical tools for careers in business, finance, public "
        "policy, or graduate study."
    ),
    "rice-global-affairs-ug": (
        "Students focused on international politics, development, and diplomacy who want "
        "interdisciplinary training to analyze global challenges, preparing for careers in "
        "policy, NGOs, or graduate study."
    ),
    "rice-linguistics-ug": (
        "Undergraduates fascinated by the structure of language and how it is learned and used "
        "who want scientific training in phonetics, syntax, and meaning for research, "
        "technology, or graduate study."
    ),
    "rice-managerial-economics-and-organizational-sciences-ug": (
        "Students who want to apply economics and quantitative analysis to how organizations "
        "make decisions, building a management-oriented foundation for careers in business, "
        "consulting, or graduate study."
    ),
    "rice-mathematical-economic-analysis-ug": (
        "Undergraduates who want the most quantitative path through economics, combining "
        "advanced math and econometrics for careers in finance, data, or doctoral study in "
        "economics."
    ),
    "rice-psychology-ug": (
        "Students drawn to the science of behavior and mental processes who want empirical and "
        "statistical training across the subfields of psychology, preparing for health, "
        "research, or graduate study."
    ),
    "rice-social-policy-analysis-ug": (
        "Undergraduates who want to evaluate how policies affect communities, combining social "
        "science and quantitative methods to prepare for careers in public service, research, "
        "or graduate study."
    ),
    "rice-sociology-ug": (
        "Students who want to understand how social structures, inequality, and institutions "
        "shape lives, gaining research and analytical skills for careers in policy, business, "
        "or graduate study."
    ),
    "rice-sport-analytics-ug": (
        "Undergraduates who want to apply data and statistical modeling to sport performance "
        "and management, combining analytics training with sport-industry knowledge for roles "
        "in teams, media, or graduate study."
    ),
    "rice-sport-management-ug": (
        "Students interested in the business and organization of sport who want training in "
        "management, marketing, and analytics for careers across teams, leagues, and "
        "sport-related industries."
    ),
    # ── Rice School of Architecture — undergraduate ──
    "rice-architecture-ug": (
        "Undergraduates committed to becoming architects who want intensive design-studio "
        "training alongside history and building technology, building toward a professional "
        "degree and licensure."
    ),
    "rice-architectural-studies-ug": (
        "Students drawn to the ideas and culture of architecture who want a design and history "
        "foundation without the full professional track, preparing for graduate architecture "
        "study or allied design and cultural fields."
    ),
    # ── The Shepherd School of Music — undergraduate ──
    "rice-music-ug": (
        "Undergraduates who want a broad foundation in performance, theory, and music history "
        "within a liberal-arts setting, preparing for musical careers, teaching, or graduate "
        "study."
    ),
    "rice-music-composition-ug": (
        "Students who want to write original music and develop a compositional voice with "
        "rigorous training in theory and craft, building toward careers in composition or "
        "graduate study."
    ),
    "rice-music-history-ug": (
        "Undergraduates fascinated by music's history and cultural contexts who want research "
        "and analytical training toward scholarship, arts work, or graduate study in "
        "musicology."
    ),
    "rice-music-theory-ug": (
        "Students who want to study the inner workings of music — harmony, structure, and "
        "analysis — building the theoretical depth for composition, performance, or graduate "
        "study."
    ),
    # ── Jesse H. Jones Graduate School of Business ──
    "rice-business-ug": (
        "Undergraduates who want a rigorous, analytical introduction to management, finance, "
        "and entrepreneurship within a liberal-arts setting, preparing for business careers or "
        "graduate study."
    ),
    "rice-master-of-business-administration-full-time-mba-ms": (
        "Early-to-mid-career professionals who want an immersive, full-time MBA to accelerate "
        "into leadership, blending core management with electives and recruiting for a career "
        "pivot or advancement."
    ),
    "rice-professional-mba-evening-prof": (
        "Working professionals who want to earn an MBA on weeknights without leaving their "
        "jobs, applying management training immediately while building toward advancement."
    ),
    "rice-professional-mba-weekend-prof": (
        "Employed professionals who prefer weekend classes to fit an MBA around a full-time "
        "career, seeking leadership skills and a strong peer network while continuing to work."
    ),
    "rice-hybrid-mba-prof": (
        "Working professionals who want the flexibility of combined online and on-campus "
        "learning to complete an MBA around demanding schedules while gaining management depth."
    ),
    "rice-executive-mba-prof": (
        "Experienced managers and senior professionals who want an MBA tailored to leadership "
        "at scale, learning alongside an accomplished cohort while remaining in their "
        "executive roles."
    ),
    "rice-mba-rice-online-mba-prof": (
        "Professionals who want the rigor of a Rice MBA delivered primarily online, earning the "
        "degree from anywhere while continuing to work and advance."
    ),
    "rice-master-of-accounting-macc-ms": (
        "Students and early-career professionals who want focused graduate accounting training "
        "to meet CPA requirements and move into public accounting, advisory, or corporate "
        "finance roles."
    ),
    "rice-doctor-of-philosophy-in-business-phd": (
        "Aspiring scholars who want to produce original management research and become "
        "university faculty, ready for a funded doctoral program with rigorous methods and "
        "close faculty mentorship."
    ),
    "rice-graduate-certificate-in-healthcare-management-cert": (
        "Clinicians and healthcare professionals who want focused graduate training in the "
        "business of healthcare to step into management roles without committing to a full "
        "degree."
    ),
    # ── Engineering — graduate ──
    "rice-doctor-of-philosophy-in-bioengineering-phd": (
        "Research-minded students who want to develop new medical technologies and biological "
        "engineering methods through a funded doctorate, preparing for careers in academia, "
        "industry research, or biotech leadership."
    ),
    "rice-master-of-bioengineering-mbe-applied-bioengineering-prof": (
        "Engineers and scientists who want an applied master's to move into bioengineering "
        "practice, strengthening design and technical skills for industry roles in devices, "
        "diagnostics, or therapeutics."
    ),
    "rice-master-of-bioengineering-mbe-global-medical-innovation-prof": (
        "Aspiring medical-technology innovators who want a project-driven master's focused on "
        "designing devices for global health needs, preparing for careers in medtech and "
        "entrepreneurship."
    ),
    "rice-doctor-of-philosophy-in-chemical-and-biomolecular-engineering-phd": (
        "Students aiming for research careers in energy, materials, or biomolecular systems who "
        "want a funded doctorate centered on original laboratory research and faculty "
        "mentorship."
    ),
    "rice-master-of-chemical-engineering-mche-prof": (
        "Working or aspiring chemical engineers who want a professional master's to deepen "
        "technical expertise and advance into senior process or design roles in industry."
    ),
    "rice-doctor-of-philosophy-in-civil-and-environmental-engineering-phd": (
        "Researchers focused on resilient infrastructure and environmental systems who want a "
        "funded doctorate to lead original research in academia, government, or industry."
    ),
    "rice-master-of-science-in-civil-and-environmental-engineering-ms": (
        "Students who want a research-oriented master's in civil and environmental engineering, "
        "completing a thesis as a step toward doctoral study or technical leadership."
    ),
    "rice-master-of-civil-and-environmental-engineering-mcee-prof": (
        "Practicing and aspiring engineers who want a coursework-focused professional master's "
        "to advance their expertise and credentials for civil and environmental engineering "
        "practice."
    ),
    "rice-doctor-of-philosophy-in-computer-science-phd": (
        "Students who want to push the frontiers of computing through original research and "
        "become faculty or industry researchers, ready for a funded doctorate with deep "
        "specialization."
    ),
    "rice-master-of-science-in-computer-science-ms": (
        "Computing students who want a research-oriented master's with a thesis to deepen "
        "technical depth, whether toward doctoral study or advanced engineering roles."
    ),
    "rice-master-of-computer-science-mcs-prof": (
        "Professionals and graduates who want a coursework-based master's to strengthen "
        "computer-science skills and move into advanced software and technical roles."
    ),
    "rice-master-of-computer-science-mcs-rice-online-prof": (
        "Working professionals who want to earn a rigorous computer-science master's online "
        "while continuing their careers, building advanced skills on a flexible schedule."
    ),
    "rice-doctor-of-philosophy-in-computational-applied-mathematics-and-operations-research-phd": (
        "Students who want to advance the mathematics of computation and optimization through "
        "original research, preparing for academic or research careers via a funded doctorate."
    ),
    "rice-master-of-computational-and-applied-mathematics-mcaam-prof": (
        "Graduates with a quantitative background who want a professional master's in applied "
        "and computational mathematics to move into modeling, analytics, or technical industry "
        "roles."
    ),
    "rice-master-of-industrial-engineering-mie-prof": (
        "Engineers and analysts who want a professional master's in optimizing systems, "
        "processes, and operations for careers in logistics, manufacturing, and analytics."
    ),
    "rice-master-of-data-science-mds-prof": (
        "Graduates and professionals who want to build rigorous data-science skills — "
        "statistics, machine learning, and computing — to move into analytics and data roles "
        "across industries."
    ),
    "rice-master-of-data-science-mds-rice-online-prof": (
        "Working professionals who want to earn a data-science master's online, gaining "
        "machine-learning and analytics expertise without pausing their careers."
    ),
    "rice-doctor-of-philosophy-in-electrical-and-computer-engineering-phd": (
        "Students aiming for research careers in electronics, signals, or computing systems who "
        "want a funded doctorate centered on original research and faculty mentorship."
    ),
    "rice-master-of-science-in-electrical-and-computer-engineering-ms": (
        "Engineering students who want a thesis-based master's in electrical and computer "
        "engineering to deepen research skills toward doctoral study or advanced technical "
        "roles."
    ),
    "rice-master-of-electrical-and-computer-engineering-mece-prof": (
        "Practicing and aspiring engineers who want a coursework-focused professional master's "
        "to advance their expertise in electrical and computer engineering for industry."
    ),
    "rice-doctor-of-philosophy-in-materials-science-and-nanoengineering-phd": (
        "Researchers fascinated by engineering materials at the nanoscale who want a funded "
        "doctorate to lead original research in academia or advanced industry."
    ),
    "rice-master-of-materials-science-and-nanoengineering-mmsne-prof": (
        "Engineers and scientists who want a professional master's in materials and "
        "nanoengineering to strengthen technical expertise for research-and-development roles."
    ),
    "rice-doctor-of-philosophy-in-mechanical-engineering-phd": (
        "Students who want to lead original research in mechanical and thermal systems, "
        "robotics, or energy, preparing for academic or industry research through a funded "
        "doctorate."
    ),
    "rice-master-of-science-in-mechanical-engineering-ms": (
        "Engineering students who want a research-oriented master's with a thesis in mechanical "
        "engineering, building toward doctoral study or advanced technical work."
    ),
    "rice-master-of-mechanical-engineering-mme-prof": (
        "Practicing and aspiring mechanical engineers who want a coursework-based professional "
        "master's to deepen expertise and advance in industry."
    ),
    "rice-doctor-of-philosophy-in-statistics-phd": (
        "Students who want to develop new statistical theory and methods through original "
        "research, preparing for faculty or research careers via a funded doctorate."
    ),
    "rice-master-of-arts-in-statistics-ms": (
        "Graduates who want a research-oriented master's in statistics with a thesis to deepen "
        "methodological skills toward doctoral study or advanced analytics work."
    ),
    "rice-master-of-statistics-mstat-prof": (
        "Professionals and graduates who want a coursework-focused master's in statistics to "
        "move into data-analysis and modeling roles across industries."
    ),
    "rice-master-of-computational-science-and-engineering-mcse-prof": (
        "Engineers and scientists who want a professional master's in large-scale computation "
        "and simulation to apply high-performance computing across science and industry."
    ),
    "rice-master-of-energy-transition-and-sustainability-mets-prof": (
        "Professionals focused on the future of energy who want an interdisciplinary master's "
        "spanning engineering, science, and policy to lead the transition to sustainable "
        "systems."
    ),
    "rice-master-of-engineering-management-and-leadership-meml-prof": (
        "Engineers ready to move into management who want a professional master's that pairs "
        "technical depth with leadership and business skills for advancement."
    ),
    "rice-master-of-engineering-management-and-leadership-meml-online-prof": (
        "Working engineers who want to build management and leadership skills online while "
        "continuing their careers, preparing to lead technical teams and projects."
    ),
    "rice-master-of-digital-health-mdh-prof": (
        "Engineers, clinicians, and technologists who want a professional master's at the "
        "intersection of computing and healthcare to build digital-health tools and lead "
        "health-technology innovation."
    ),
    # ── Natural Sciences — graduate ──
    "rice-doctor-of-philosophy-in-biochemistry-and-cell-biology-phd": (
        "Research-driven students who want to investigate the molecular machinery of life "
        "through a funded doctorate, preparing for careers in academic, medical, or industry "
        "research."
    ),
    "rice-doctor-of-philosophy-in-ecology-and-evolutionary-biology-phd": (
        "Students who want to study biodiversity, adaptation, and ecosystems through original "
        "field and laboratory research, preparing for academic, conservation, or research "
        "careers via a funded doctorate."
    ),
    "rice-master-of-science-in-biochemistry-and-cell-biology-ms": (
        "Graduates who want a research-oriented master's in molecular and cellular biology to "
        "deepen laboratory skills as a step toward doctoral study or biotech research."
    ),
    "rice-master-of-science-in-ecology-and-evolutionary-biology-ms": (
        "Students who want a thesis-based master's in ecology and evolution to build research "
        "experience toward doctoral study or careers in conservation and environmental "
        "science."
    ),
    "rice-doctor-of-philosophy-in-chemistry-phd": (
        "Aspiring research chemists who want a funded doctorate to lead original work across "
        "the chemical sciences, preparing for academic, industry, or national-laboratory "
        "careers."
    ),
    "rice-master-of-arts-in-chemistry-ms": (
        "Graduates who want a research-oriented master's in chemistry to strengthen laboratory "
        "and analytical skills toward doctoral study or technical roles."
    ),
    "rice-doctor-of-philosophy-in-earth-environmental-and-planetary-sciences-phd": (
        "Students who want to research the Earth and planets — from climate to deep-time "
        "geology — through a funded doctorate, preparing for academic, energy, or environmental "
        "careers."
    ),
    "rice-master-of-science-in-earth-environmental-and-planetary-sciences-ms": (
        "Graduates who want a research master's in earth and planetary sciences to build "
        "fieldwork and analytical skills toward doctoral study or technical careers."
    ),
    "rice-doctor-of-philosophy-in-physics-phd": (
        "Students driven to advance fundamental and applied physics through original research, "
        "preparing for academic or research careers via a funded doctorate."
    ),
    "rice-master-of-science-in-physics-ms": (
        "Graduates who want a research-oriented master's in physics to deepen experimental or "
        "theoretical skills toward doctoral study or technical roles."
    ),
    "rice-doctor-of-philosophy-in-applied-physics-phd": (
        "Students who want to apply physics to technology and materials problems through a "
        "funded interdisciplinary doctorate, preparing for research careers in academia or "
        "industry."
    ),
    "rice-doctor-of-philosophy-in-mathematics-phd": (
        "Aspiring mathematicians who want to prove new results and become faculty or "
        "researchers, ready for a funded doctorate with deep specialization and mentorship."
    ),
    "rice-master-of-arts-in-mathematics-ms": (
        "Graduates who want an advanced master's in mathematics to strengthen their foundation "
        "toward doctoral study, teaching, or quantitative careers."
    ),
    "rice-doctor-of-philosophy-in-systems-synthetic-and-physical-biology-phd": (
        "Students who want to study and engineer biological systems quantitatively, combining "
        "biology, physics, and computation in a funded doctorate toward research careers."
    ),
    "rice-master-of-science-teaching-mst-prof": (
        "Aspiring and current science educators who want graduate training in science content "
        "and pedagogy to teach effectively at the secondary or college level."
    ),
    "rice-master-of-science-in-applied-chemical-sciences-msacs-prof": (
        "Science graduates who want a professional master's that pairs chemistry with business "
        "and management skills to move into industry roles beyond the laboratory bench."
    ),
    "rice-master-of-science-in-bioscience-and-health-policy-msbhp-prof": (
        "Science-trained graduates who want to bridge research and policy, combining bioscience "
        "with health-policy and business skills for careers in industry, government, or "
        "advocacy."
    ),
    "rice-master-of-science-in-energy-geoscience-mseg-prof": (
        "Geoscience graduates who want a professional master's applying earth science to energy "
        "resources and the subsurface, preparing for technical careers in the energy sector."
    ),
    "rice-master-of-science-in-environmental-analysis-msea-prof": (
        "Science graduates who want a professional master's combining environmental science "
        "with analytics and management for careers in consulting, industry, or government."
    ),
    "rice-master-of-science-in-space-studies-mssps-prof": (
        "Professionals and graduates fascinated by space who want an interdisciplinary master's "
        "spanning space science, policy, and business for careers in the growing space sector."
    ),
    # ── Humanities — graduate ──
    "rice-master-of-arts-in-art-history-ms": (
        "Graduates who want advanced training in visual analysis and art-historical research as "
        "a step toward doctoral study or careers in museums and the arts."
    ),
    "rice-doctor-of-philosophy-in-art-history-phd": (
        "Students who want to become art-history scholars and curators through original "
        "research, ready for a funded doctorate with archival and language work."
    ),
    "rice-master-of-arts-in-english-ms": (
        "Graduates who want advanced study of literature and criticism to deepen research and "
        "writing skills toward doctoral study or careers in writing and teaching."
    ),
    "rice-doctor-of-philosophy-in-english-phd": (
        "Aspiring literary scholars who want to produce original research and become faculty, "
        "ready for a funded doctorate in literary and cultural study."
    ),
    "rice-master-of-fine-arts-in-creative-writing-ms": (
        "Writers who want dedicated time and mentorship to develop a book-length manuscript and "
        "craft, preparing for careers in writing, publishing, or teaching."
    ),
    "rice-master-of-arts-in-history-ms": (
        "Graduates who want advanced historical research and writing training as a step toward "
        "doctoral study or careers in education, public history, and the professions."
    ),
    "rice-doctor-of-philosophy-in-history-phd": (
        "Students who want to become professional historians through original archival "
        "research, ready for a funded doctorate with deep specialization."
    ),
    "rice-master-of-arts-in-philosophy-ms": (
        "Graduates who want advanced training in rigorous argument and philosophical research "
        "as a step toward doctoral study or analytically demanding careers."
    ),
    "rice-doctor-of-philosophy-in-philosophy-phd": (
        "Aspiring philosophers who want to produce original work and become faculty, ready for "
        "a funded doctorate in core areas of the discipline."
    ),
    "rice-master-of-arts-in-religion-ms": (
        "Graduates who want advanced study of religious traditions and texts to deepen "
        "interpretive and research skills toward doctoral study or work in the professions."
    ),
    "rice-doctor-of-philosophy-in-religion-phd": (
        "Students who want to become scholars of religion through original research, ready for "
        "a funded doctorate with textual, historical, and theoretical depth."
    ),
    # ── Social Sciences — graduate ──
    "rice-master-of-arts-in-anthropology-ms": (
        "Graduates who want advanced ethnographic and theoretical training in anthropology as a "
        "step toward doctoral study or applied research careers."
    ),
    "rice-doctor-of-philosophy-in-anthropology-phd": (
        "Students who want to conduct original ethnographic research and become faculty or "
        "applied researchers, ready for a funded anthropology doctorate."
    ),
    "rice-master-of-arts-in-economics-ms": (
        "Graduates who want rigorous graduate economics training to strengthen quantitative "
        "skills toward doctoral study or analytical careers in policy and industry."
    ),
    "rice-doctor-of-philosophy-in-economics-phd": (
        "Students aiming to become research economists and faculty who want a funded doctorate "
        "with strong theory, econometrics, and field specialization."
    ),
    "rice-master-of-arts-in-political-science-ms": (
        "Graduates who want advanced training in political analysis and research methods as a "
        "step toward doctoral study or careers in policy and public affairs."
    ),
    "rice-doctor-of-philosophy-in-political-science-phd": (
        "Students who want to produce original political-science research and become faculty, "
        "ready for a funded doctorate with rigorous methods training."
    ),
    "rice-master-of-arts-in-psychology-ms": (
        "Graduates who want advanced research training in psychology to strengthen empirical "
        "and statistical skills toward doctoral study or applied roles."
    ),
    "rice-doctor-of-philosophy-in-psychology-phd": (
        "Students who want to conduct original behavioral research and become faculty or "
        "scientists, ready for a funded psychology doctorate with strong methods."
    ),
    "rice-master-of-arts-in-sociology-ms": (
        "Graduates who want advanced training in social theory and research methods as a step "
        "toward doctoral study or applied research in policy and industry."
    ),
    "rice-doctor-of-philosophy-in-sociology-phd": (
        "Students who want to produce original sociological research and become faculty or "
        "researchers, ready for a funded doctorate with rigorous methods."
    ),
    "rice-master-of-computational-economics-mcecon-prof": (
        "Quantitatively minded graduates who want a professional master's combining economics "
        "with computation and data for careers in analytics, finance, and consulting."
    ),
    "rice-master-of-energy-economics-meecon-prof": (
        "Professionals and graduates focused on energy markets who want a specialized master's "
        "in energy economics for careers in the energy and finance sectors."
    ),
    "rice-master-of-global-affairs-mga-prof": (
        "Aspiring international-affairs professionals who want a practice-oriented master's in "
        "policy, security, and development for careers in government, NGOs, and global "
        "business."
    ),
    "rice-master-of-human-computer-interaction-and-human-factors-mhcihf-prof": (
        "Graduates interested in how people interact with technology who want a professional "
        "master's blending psychology, design, and computing for careers in UX and "
        "human-factors research."
    ),
    "rice-master-of-industrial-organizational-psychology-miop-prof": (
        "Graduates who want to apply psychology to the workplace — selection, performance, and "
        "organizational behavior — for careers in talent, people analytics, and consulting."
    ),
    "rice-master-of-social-policy-evaluation-mspe-prof": (
        "Professionals who want rigorous training in evaluating social programs and policy, "
        "building data and methods skills for careers in research, government, and nonprofits."
    ),
    # ── Architecture — graduate ──
    "rice-master-of-architecture-march-option-1-professional-prof": (
        "Students from non-architecture backgrounds who want the full professional degree and "
        "licensure path, gaining intensive design-studio training to enter the profession."
    ),
    "rice-master-of-architecture-march-option-2-post-professional-prof": (
        "Holders of a pre-professional architecture degree who want to complete the accredited "
        "professional master's and advance their design practice toward licensure."
    ),
    "rice-master-of-science-in-architecture-option-3-ms": (
        "Architecture graduates who want a research-focused post-professional master's to "
        "develop a specialized design or scholarly direction beyond the professional degree."
    ),
    # ── Music — graduate ──
    "rice-master-of-music-ms": (
        "Accomplished musicians who want advanced conservatory-level training in performance or "
        "composition to refine their artistry and prepare for professional careers."
    ),
    "rice-doctor-of-musical-arts-dma-phd": (
        "Highly accomplished performers and composers who want the terminal performance "
        "doctorate to reach the highest level of artistry and prepare for careers as soloists "
        "and faculty."
    ),
    "rice-artist-diploma-cert": (
        "Exceptional performers ready for an intensive, performance-only program who want "
        "concentrated studio training and stage experience to launch a professional "
        "performing career."
    ),
    # ── Glasscock School of Continuing Studies ──
    "rice-master-of-liberal-studies-mls-ms": (
        "Curious adult learners and working professionals who want an interdisciplinary "
        "graduate degree across the humanities and sciences for personal and professional "
        "growth."
    ),
    "rice-master-of-interdisciplinary-studies-mis-ms": (
        "Working professionals who want to design a flexible, cross-disciplinary graduate "
        "program tailored to their goals, building breadth for career and intellectual "
        "advancement."
    ),
    "rice-master-of-arts-in-teaching-mat-ms": (
        "Aspiring and practicing teachers who want graduate training in pedagogy and content to "
        "earn certification and strengthen their classroom practice."
    ),
}
