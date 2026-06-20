"""Researched per-program description overrides for USC programs whose scraped
``CATALOGUE_DESCRIPTIONS`` entry was raw catalogue debris (a degree-requirements /
course-code fragment, a contact / address block, an admin note, or another program's
text mismatched by name) — REPAIR_BACKLOG CRITICAL #1 (run 66, USC).

Each entry is prose about what THAT program studies, grounded only in the program's
verified owning USC school (already in the catalog data) plus the genuine substance of
the field at that credential level. No invented centers, institutes, rankings, or
superlatives; no peer-institution units; each description is unique and credential-
distinct (gold MIT = 0% shared). Sources: the official USC Catalogue (catalogue.usc.edu)
school/department program pages and each school's official site.

Merged into ``_CROSS_FIELD_DESCRIPTION_FIXES`` in ``usc_profile.py`` (override precedence
over the raw scrape), so the debris never reaches a student-facing page.
"""

# ruff: noqa: E501

DEBRIS_REPAIR_DESCRIPTIONS: dict[str, str] = {
    # ---- Keck School of Medicine of USC ----------------------------------------
    "usc-global-health-studies-bs": (
        "The Bachelor of Science in global health studies at the Keck School of Medicine of USC "
        "examines health and disease across populations worldwide, integrating epidemiology, the "
        "social determinants of health, and global health policy for students preparing for careers "
        "in medicine, research, and public health."
    ),
    "usc-academic-medicine-macm": (
        "The Master of Academic Medicine at the Keck School of Medicine of USC prepares physicians "
        "and health professionals to lead in health-professions education, building skills in "
        "curriculum design, teaching, assessment, and academic leadership through a primarily online "
        "format with on-campus workshops."
    ),
    "usc-biostatistics-ms": (
        "The MS in biostatistics at the Keck School of Medicine of USC trains students in statistical "
        "theory, study design, and the analysis of biomedical and public-health data, preparing them "
        "for research and analytic roles in medicine and population health."
    ),
    "usc-global-medicine-ms": (
        "The MS in global medicine at the Keck School of Medicine of USC examines health systems, "
        "disease, and the delivery of care across global and underserved settings, preparing students "
        "for careers and advanced study in international health and medicine."
    ),
    "usc-molecular-pathology-and-experimental-medicine-ms": (
        "This MS at the Keck School of Medicine of USC investigates the molecular basis of disease, "
        "combining pathology and experimental medicine to train students in translational biomedical "
        "research."
    ),
    "usc-neuroimaging-and-informatics-ms": (
        "The MS in neuroimaging and informatics at the Keck School of Medicine of USC trains students "
        "in brain-imaging methods and the computational analysis of neuroimaging data for research in "
        "neuroscience and medicine."
    ),
    "usc-public-health-data-science-ms": (
        "This MS at the Keck School of Medicine of USC applies data science to public health, "
        "combining biostatistics, epidemiology, and computational methods to analyze population-health "
        "data and inform practice and policy."
    ),
    "usc-translational-biomedical-informatics-ms": (
        "The MS in translational biomedical informatics at the Keck School of Medicine of USC trains "
        "students to manage and analyze biomedical, genomic, and clinical data, bridging informatics "
        "and health care."
    ),
    "usc-translational-biotechnology-ms": (
        "This MS at the Keck School of Medicine of USC bridges laboratory science and the biotechnology "
        "industry, training students in the development, regulation, and commercialization of biomedical "
        "technologies."
    ),
    # ---- USC Alfred E. Mann School of Pharmacy and Pharmaceutical Sciences ------
    "usc-healthcare-decision-analysis-ms": (
        "The MS in healthcare decision analysis at the USC Alfred E. Mann School of Pharmacy and "
        "Pharmaceutical Sciences trains students in pharmacoeconomics, outcomes research, and the "
        "quantitative evaluation of health-care interventions and policy."
    ),
    "usc-management-of-drug-development-ms": (
        "This MS at the USC Alfred E. Mann School of Pharmacy and Pharmaceutical Sciences covers the "
        "science, regulation, and management of bringing new drugs to market, from clinical trials "
        "through regulatory approval."
    ),
    "usc-molecular-pharmacology-and-toxicology-ms": (
        "The MS in molecular pharmacology and toxicology at the USC Alfred E. Mann School of Pharmacy "
        "and Pharmaceutical Sciences studies how drugs and chemicals act on biological systems, "
        "training students in the mechanisms of drug action and toxicity."
    ),
    "usc-pharmaceutical-sciences-ms": (
        "This MS at the USC Alfred E. Mann School of Pharmacy and Pharmaceutical Sciences provides "
        "graduate training in drug discovery, formulation, and the pharmaceutical sciences, preparing "
        "students for research careers and doctoral study."
    ),
    # ---- USC Annenberg School for Communication and Journalism -----------------
    "usc-journalism-ms": (
        "The MS in journalism at the USC Annenberg School for Communication and Journalism trains "
        "reporters and editors in multimedia storytelling, investigative methods, and the practice of "
        "journalism across digital and broadcast platforms."
    ),
    # ---- USC Dornsife College of Letters, Arts and Sciences — bachelor's --------
    "usc-applied-and-computational-mathematics-ba": (
        "Applied and computational mathematics at USC Dornsife pairs mathematical modeling and "
        "numerical analysis with scientific computing, training undergraduates to formulate and solve "
        "quantitative problems drawn from the physical, life, and data sciences."
    ),
    "usc-archaeology-and-heritage-studies-ba": (
        "Archaeology and heritage studies at USC Dornsife examines material culture, excavation and "
        "survey methods, and the stewardship of the past, combining anthropology, art history, and "
        "conservation to interpret ancient and historical societies."
    ),
    "usc-behavioral-economics-and-psychology-ba": (
        "Behavioral economics and psychology at USC Dornsife studies how people actually make "
        "decisions, blending economic theory with experimental psychology to understand judgment, "
        "motivation, and choice under uncertainty."
    ),
    "usc-earth-sciences-ba": (
        "Earth sciences at USC Dornsife surveys the processes that shape the planet — geology, oceans, "
        "climate, and natural hazards — giving undergraduates a broad, interdisciplinary foundation in "
        "the environmental and geological sciences."
    ),
    "usc-east-asian-area-studies-ba": (
        "East Asian area studies at USC Dornsife integrates the history, politics, economies, and "
        "cultures of China, Japan, and Korea with language study, giving undergraduates regional "
        "expertise in contemporary and historical East Asia."
    ),
    "usc-east-asian-languages-and-cultures-ba": (
        "This major at USC Dornsife centers on advanced proficiency in an East Asian language alongside "
        "the literature, film, and intellectual traditions of China, Japan, or Korea."
    ),
    "usc-economics-ba": (
        "Economics at USC Dornsife grounds undergraduates in microeconomic and macroeconomic theory "
        "and econometrics, applying quantitative analysis to markets, public policy, and the behavior "
        "of individuals and firms."
    ),
    "usc-english-ba": (
        "The English major at USC Dornsife studies literature in English across periods and genres, "
        "developing close reading, critical interpretation, and analytical writing alongside coursework "
        "in creative writing and literary theory."
    ),
    "usc-french-ba": (
        "French at USC Dornsife builds advanced language proficiency while exploring the literature, "
        "film, and cultural history of France and the wider Francophone world."
    ),
    "usc-history-ba": (
        "History at USC Dornsife trains undergraduates in research with primary sources, historical "
        "argument, and writing across a wide range of regions and eras, from the ancient world to the "
        "present."
    ),
    "usc-international-relations-ba": (
        "International relations at USC Dornsife examines diplomacy, security, international political "
        "economy, and global institutions, preparing undergraduates to analyze conflict, cooperation, "
        "and policy among states and across borders."
    ),
    "usc-linguistics-ba": (
        "Linguistics at USC Dornsife studies the structure of human language — phonology, syntax, and "
        "semantics — combining formal analysis with the cognitive science of how language is acquired "
        "and used."
    ),
    "usc-linguistics-and-east-asian-languages-and-cultures-ba": (
        "This joint major at USC Dornsife pairs the formal study of language structure with advanced "
        "proficiency in an East Asian language and its literary and cultural traditions."
    ),
    "usc-neuroscience-ba": (
        "The neuroscience major at USC Dornsife examines the biological basis of the nervous system "
        "and behavior, integrating biology, psychology, and chemistry in a liberal-arts pathway for "
        "students interested in the brain and cognition."
    ),
    "usc-political-science-ba": (
        "Political science at USC Dornsife studies government, political behavior, public policy, and "
        "political theory, training undergraduates to analyze institutions and power in the United "
        "States and around the world."
    ),
    "usc-psychology-ba": (
        "Psychology at USC Dornsife investigates mind and behavior across cognitive, developmental, "
        "social, and clinical perspectives, grounding undergraduates in research methods and the "
        "scientific study of human experience."
    ),
    "usc-religion-ba": (
        "The study of religion at USC Dornsife examines religious traditions, texts, and practices "
        "across cultures and history, drawing on history, philosophy, and the social sciences to "
        "interpret belief and its place in human life."
    ),
    "usc-russian-ba": (
        "Russian at USC Dornsife develops language proficiency alongside the study of Russian "
        "literature, film, and cultural and political history."
    ),
    "usc-sociology-ba": (
        "Sociology at USC Dornsife examines social structures, inequality, institutions, and group "
        "behavior, equipping undergraduates with the research methods to analyze how societies organize "
        "and change."
    ),
    "usc-spanish-ba": (
        "Spanish at USC Dornsife combines advanced language proficiency with the study of the "
        "literatures and cultures of Spain and Latin America."
    ),
    "usc-chemistry-bs": (
        "The Bachelor of Science in chemistry at USC Dornsife provides rigorous laboratory and "
        "theoretical training across organic, inorganic, physical, and analytical chemistry, preparing "
        "students for graduate study and careers in research and industry."
    ),
    "usc-computational-linguistics-bs": (
        "Computational linguistics at USC Dornsife joins the formal study of language with computer "
        "science and machine learning, training students to build systems that process and model "
        "natural language."
    ),
    "usc-geological-sciences-bs": (
        "The Bachelor of Science in geological sciences at USC Dornsife covers the solid earth — "
        "mineralogy, tectonics, sedimentology, and field methods — with the quantitative and "
        "laboratory training expected for professional and graduate work in the geosciences."
    ),
    "usc-neuroscience-bs": (
        "The Bachelor of Science in neuroscience at USC Dornsife offers a quantitative, laboratory-"
        "intensive study of the nervous system, spanning molecular and cellular neuroscience, systems, "
        "and behavior for students preparing for research or health careers."
    ),
    # ---- USC Dornsife — master's ----------------------------------------------
    "usc-philosophy-and-law-ma": (
        "This master's at USC Dornsife examines the philosophical foundations of law — legal "
        "reasoning, justice, rights, and the relationship between morality and legal systems — for "
        "students bridging philosophy and legal study."
    ),
    "usc-applied-psychology-ms": (
        "The MS in applied psychology at USC Dornsife applies psychological science to organizational, "
        "consumer, and health settings, training students in research methods, measurement, and "
        "evidence-based practice."
    ),
    "usc-economics-ms": (
        "The MS in economics at USC Dornsife provides advanced graduate training in economic theory "
        "and econometrics, building the quantitative and empirical skills for analytic careers and "
        "doctoral preparation."
    ),
    "usc-environmental-risk-analysis-ms": (
        "This MS at USC Dornsife trains scientists to assess and manage environmental risk, combining "
        "environmental science with quantitative methods for evaluating hazards, exposure, and policy "
        "responses."
    ),
    "usc-geological-sciences-ms": (
        "The MS in geological sciences at USC Dornsife pairs advanced coursework with thesis research "
        "in the earth sciences, deepening expertise for professional practice or continued doctoral "
        "study."
    ),
    "usc-human-security-and-geospatial-intelligence-ms": (
        "This program at USC Dornsife combines geospatial analysis and GIS with the study of human "
        "security, training students to apply spatial data to challenges in conflict, migration, and "
        "humanitarian and environmental response."
    ),
    # ---- USC Dornsife — doctoral ----------------------------------------------
    "usc-chemistry-phd": (
        "Doctoral study in chemistry at USC Dornsife centers on original research across organic, "
        "inorganic, physical, and analytical chemistry, with advanced coursework and a dissertation "
        "advancing the chemical sciences."
    ),
    "usc-classics-phd": (
        "The PhD in classics at USC Dornsife trains scholars in Greek and Latin languages and "
        "literatures and the history, philosophy, and material culture of the ancient Mediterranean, "
        "culminating in original dissertation research."
    ),
    "usc-east-asian-languages-and-cultures-phd": (
        "Doctoral research in East Asian languages and cultures at USC Dornsife develops deep "
        "philological and critical expertise in the literatures and intellectual traditions of China, "
        "Japan, or Korea, leading to a dissertation."
    ),
    "usc-economics-phd": (
        "The PhD in economics at USC Dornsife prepares research economists through advanced theory and "
        "econometrics and original dissertation work in fields such as microeconomics, macroeconomics, "
        "and applied and labor economics."
    ),
    "usc-geological-sciences-phd": (
        "Doctoral study in geological sciences at USC Dornsife supports original research on the "
        "earth's structure and history — tectonics, sedimentary systems, geochemistry, and surface "
        "processes — leading to a dissertation."
    ),
    "usc-integrative-and-evolutionary-biology-phd": (
        "This PhD at USC Dornsife pursues research spanning organismal biology, ecology, and "
        "evolution, integrating field, laboratory, and computational approaches to questions of "
        "biological diversity and adaptation."
    ),
    "usc-marine-biology-and-biological-oceanography-phd": (
        "Doctoral research in marine biology and biological oceanography at USC Dornsife studies ocean "
        "life and ecosystems, combining field and laboratory work in marine ecology, physiology, and "
        "oceanographic processes."
    ),
    "usc-ocean-sciences-phd": (
        "The PhD in ocean sciences at USC Dornsife advances research on the physical, chemical, "
        "biological, and geological processes of the oceans through coursework and an original "
        "dissertation."
    ),
    "usc-philosophy-phd": (
        "Doctoral study in philosophy at USC Dornsife trains researchers across metaphysics, "
        "epistemology, ethics, and the history of philosophy, culminating in a dissertation that makes "
        "an original contribution to the field."
    ),
    "usc-sociology-phd": (
        "The PhD in sociology at USC Dornsife develops scholars in social theory and quantitative and "
        "qualitative research methods, supporting dissertation work on inequality, institutions, and "
        "social change."
    ),
    # ---- USC Gould School of Law ----------------------------------------------
    "usc-law-jd": (
        "The Juris Doctor at the USC Gould School of Law provides the professional legal education "
        "required for bar admission, combining foundational courses in legal doctrine and reasoning "
        "with experiential clinics, externships, and electives across fields of law."
    ),
    # ---- USC Iovine and Young Academy -----------------------------------------
    "usc-business-of-innovation-bs": (
        "The Bachelor of Science in business of innovation at the USC Iovine and Young Academy blends "
        "design, technology, and entrepreneurship, training students to develop and launch new "
        "products and ventures at the intersection of the arts and business."
    ),
    # ---- USC Leonard Davis School of Gerontology ------------------------------
    "usc-human-development-and-aging-honors-programs-bs": (
        "The honors track of the Bachelor of Science in human development and aging at the USC Leonard "
        "Davis School of Gerontology offers high-achieving students advanced, research-oriented study "
        "of the biological, psychological, and social dimensions of aging."
    ),
    "usc-aging-biology-msab": (
        "The Master of Science in Aging Biology at the USC Leonard Davis School of Gerontology is a "
        "research-intensive program studying the cellular, molecular, and genetic mechanisms of aging "
        "and age-related disease, culminating in a master's thesis."
    ),
    # ---- USC Roski School of Art and Design ------------------------------------
    "usc-design-bfa": (
        "The Bachelor of Fine Arts in design at the USC Roski School of Art and Design trains students "
        "in visual communication, interaction, and spatial design through studio practice spanning "
        "graphic, product, and experience design."
    ),
    # ---- USC Rossier School of Education ---------------------------------------
    "usc-global-executive-edd": (
        "The Global Executive Doctor of Education at the USC Rossier School of Education prepares "
        "experienced leaders to address educational challenges worldwide, combining advanced study of "
        "policy and organizational change with applied dissertation research."
    ),
    "usc-organizational-change-and-leadership-edd": (
        "This Doctor of Education at the USC Rossier School of Education equips working leaders with "
        "evidence-based strategies for organizational change, drawing on leadership theory, data, and "
        "applied research across education, business, and the public sector."
    ),
    "usc-education-phd": (
        "The PhD in education at the USC Rossier School of Education prepares scholars to conduct "
        "rigorous research on learning, policy, and educational systems, culminating in an original "
        "dissertation."
    ),
    # ---- USC School of Architecture -------------------------------------------
    "usc-heritage-conservation-mhc": (
        "The Master of Heritage Conservation at the USC School of Architecture trains professionals to "
        "document, preserve, and adaptively reuse historic buildings and landscapes, combining "
        "conservation theory, building technology, and preservation policy."
    ),
    "usc-advanced-architectural-research-studies-city-design-and-housing-maars": (
        "This post-professional master's at the USC School of Architecture treats design as focused "
        "research, with a City Design and Housing concentration examining inclusive, equitable urban "
        "design and housing production."
    ),
    "usc-advanced-architectural-research-studies-maars": (
        "This post-professional master's at the USC School of Architecture treats design as focused, "
        "specialized research, with concentrations in City Design and Housing and in Performative "
        "Design and Technology."
    ),
    # ---- USC School of Cinematic Arts -----------------------------------------
    "usc-cinematic-arts-media-arts-games-and-health-ma": (
        "This Master of Arts at the USC School of Cinematic Arts explores media arts, games, and "
        "interactive design for health and social impact, pairing creative production with research at "
        "the intersection of media and well-being."
    ),
    "usc-cinematic-arts-film-and-television-production-mfa": (
        "The MFA in film and television production at the USC School of Cinematic Arts is a "
        "conservatory-style program in directing, producing, cinematography, and editing, culminating "
        "in advanced thesis filmmaking."
    ),
    "usc-game-design-and-development-ms": (
        "The MS in game design and development at the USC School of Cinematic Arts trains students in "
        "interactive design, game engineering, and production, combining design studios with the "
        "technical craft of building games."
    ),
    # ---- USC Viterbi School of Engineering ------------------------------------
    "usc-civil-engineering-bs": (
        "The Bachelor of Science in civil engineering at the USC Viterbi School of Engineering covers "
        "structures, transportation, water resources, geotechnical, and environmental engineering, "
        "with the analysis and design training accredited for professional practice."
    ),
    "usc-electrical-and-computer-engineering-bs": (
        "This BS at the USC Viterbi School of Engineering spans circuits, signals, electronics, and "
        "computing systems, training students to design hardware and embedded systems across "
        "electrical and computer engineering."
    ),
    "usc-environmental-engineering-bs": (
        "The Bachelor of Science in environmental engineering at the USC Viterbi School of Engineering "
        "applies engineering to water quality, pollution control, and sustainable infrastructure for "
        "protecting human and ecological health."
    ),
    "usc-petroleum-engineering-phd": (
        "Doctoral research in petroleum engineering at the USC Viterbi School of Engineering advances "
        "the recovery and management of subsurface energy resources, spanning reservoir engineering, "
        "geomechanics, and energy systems, culminating in a dissertation."
    ),
    "usc-aerospace-engineering-ms": (
        "The MS in aerospace engineering at the USC Viterbi School of Engineering offers advanced study "
        "in aerodynamics, propulsion, structures, dynamics, and the control of aircraft and "
        "spacecraft."
    ),
    "usc-biomedical-data-analytics-ms": (
        "This MS at the USC Viterbi School of Engineering applies data science and machine learning to "
        "biomedical and clinical data, training engineers to extract insight from large-scale health "
        "and life-science datasets."
    ),
    "usc-chemical-engineering-ms": (
        "The MS in chemical engineering at the USC Viterbi School of Engineering offers advanced study "
        "in reaction engineering, transport phenomena, and process design, with applications spanning "
        "energy, materials, and biotechnology."
    ),
    "usc-computer-science-dual-degree-with-tsinghua-university-school-of-information-science-and-technology-ms": (
        "This dual-degree master's, offered by the USC Viterbi School of Engineering with Tsinghua "
        "University, lets students earn graduate degrees at both institutions while specializing in "
        "advanced computer science."
    ),
    "usc-cyber-security-engineering-ms": (
        "The MS in cyber security engineering at the USC Viterbi School of Engineering trains engineers "
        "to design and defend secure systems, covering cryptography, network and software security, "
        "and the engineering of trustworthy computing."
    ),
    "usc-environmental-data-science-ms": (
        "This MS at the USC Viterbi School of Engineering applies data science and computational "
        "modeling to environmental and Earth-systems problems, combining machine learning with "
        "environmental science."
    ),
    "usc-healthcare-data-science-ms": (
        "The MS in healthcare data science at the USC Viterbi School of Engineering trains students to "
        "apply machine learning and analytics to clinical, genomic, and health-systems data."
    ),
    "usc-mechanical-engineering-ms": (
        "The MS in mechanical engineering at the USC Viterbi School of Engineering offers advanced "
        "study in dynamics, thermal and fluid sciences, mechanics, and design across energy, "
        "manufacturing, and aerospace applications."
    ),
    "usc-operations-research-engineering-ms": (
        "This MS at the USC Viterbi School of Engineering applies optimization, stochastic modeling, "
        "and analytics to the design and operation of complex systems in logistics, manufacturing, and "
        "services."
    ),
    "usc-quantum-information-science-ms": (
        "The MS in quantum information science at the USC Viterbi School of Engineering covers quantum "
        "computing, algorithms, and hardware, training engineers in the theory and practice of quantum "
        "technologies."
    ),
    # ---- Herman Ostrow School of Dentistry of USC -----------------------------
    "usc-community-oral-health-ms": (
        "The MS in community oral health at the Herman Ostrow School of Dentistry of USC, offered "
        "online, trains dental professionals in dental public health, epidemiology, and population-"
        "level approaches to improving oral health."
    ),
    # ---- USC Suzanne Dworak-Peck School of Social Work (Department of Nursing) --
    "usc-nursing-family-nurse-practitioner-msnfnp": (
        "The Master of Science in Nursing, Family Nurse Practitioner at USC prepares registered nurses "
        "to deliver primary care across the lifespan, pairing advanced nursing practice with social-"
        "work perspectives on the social determinants of health, delivered online."
    ),
    # ---- Additional requirements-text / course-code debris rows ----------------
    "usc-linguistics-phd": (
        "Doctoral study in linguistics at USC Dornsife advances original research in phonology, "
        "syntax, semantics, and the cognitive science of language, with specialization options "
        "including the languages of East Asia, culminating in a dissertation."
    ),
    "usc-occupational-therapy-ma": (
        "The one-year Master of Arts in occupational therapy at USC serves credentialed and "
        "internationally trained therapists, advancing occupational-therapy theory, clinical "
        "reasoning, and evidence-based practice."
    ),
    "usc-biomedical-engineering-ms": (
        "The MS in biomedical engineering at the USC Viterbi School of Engineering applies "
        "engineering to medicine and biology, spanning biomechanics, biomedical imaging, neural "
        "engineering, and medical devices."
    ),
    "usc-civil-engineering-ms": (
        "The MS in civil engineering at the USC Viterbi School of Engineering offers advanced study "
        "with options in structural, construction, and transportation engineering, including a "
        "thesis pathway."
    ),
    # ---- Sibling-shared / classification-stub fields (per-credential bodies) ----
    "usc-environmental-science-and-health-ba": (
        "The Bachelor of Arts in environmental science and health at USC Dornsife combines biology, "
        "chemistry, and sustainability with social-science and policy perspectives on environmental "
        "health, for a broad interdisciplinary path."
    ),
    "usc-environmental-science-and-health-bs": (
        "The Bachelor of Science in environmental science and health at USC Dornsife grounds students "
        "in biology, chemistry, and quantitative methods to study pollution, ecosystems, and human "
        "environmental health, with laboratory and field training."
    ),
    "usc-environmental-studies-ba": (
        "The Bachelor of Arts in environmental studies at USC Dornsife examines environmental "
        "challenges through the social sciences, humanities, and policy, pairing sustainability "
        "coursework with the political and economic dimensions of the environment."
    ),
    "usc-environmental-studies-bs": (
        "The Bachelor of Science in environmental studies at USC Dornsife pairs interdisciplinary "
        "sustainability study with a stronger grounding in the natural sciences and quantitative "
        "methods."
    ),
    "usc-environmental-studies-ma": (
        "The MA in environmental studies at USC Dornsife offers an interdisciplinary graduate "
        "perspective on environmental problems and solutions, combining policy, science, and "
        "sustainability research."
    ),
    "usc-physics-ba": (
        "The Bachelor of Arts in physics at USC Dornsife offers a flexible foundation in mechanics, "
        "electromagnetism, and modern physics for students combining physics with other fields rather "
        "than pursuing a research career in it."
    ),
    "usc-physics-bs": (
        "The Bachelor of Science in physics at USC Dornsife trains students in classical mechanics, "
        "electromagnetism, quantum theory, and laboratory methods, preparing them for graduate study "
        "and careers in physics and related sciences."
    ),
    "usc-physics-ma": (
        "The MA in physics at USC Dornsife offers graduate coursework in classical and quantum physics "
        "for students deepening their physics background or preparing for doctoral study."
    ),
    "usc-physics-ms": (
        "The MS in physics at USC Dornsife provides advanced graduate training in theoretical and "
        "experimental physics, with coursework in quantum mechanics, electromagnetism, and statistical "
        "physics."
    ),
    "usc-physics-phd": (
        "Doctoral study in physics at USC Dornsife centers on original research across condensed-matter, "
        "high-energy, astrophysics, and theoretical physics, culminating in a dissertation."
    ),
    "usc-occupational-therapy-bs": (
        "The Bachelor of Science in occupational therapy at USC trains students in the science of "
        "occupation and therapeutic practice, preparing them for graduate study and clinical careers "
        "in occupational therapy."
    ),
    "usc-occupational-therapy-otd": (
        "The professional Doctor of Occupational Therapy at USC prepares students for clinical practice "
        "and leadership in occupational therapy, integrating occupational science, evidence-based "
        "intervention, and supervised fieldwork."
    ),
    "usc-social-work-msw": (
        "The Master of Social Work at the USC Suzanne Dworak-Peck School of Social Work prepares "
        "students for advanced social-work practice, pairing foundational generalist training with "
        "specialized study and supervised field education."
    ),
    # ---- Collapse survivors (concentration variants folded into tracks) --------
    "usc-performance-dma": (
        "The Doctor of Musical Arts in Performance at the USC Thornton School of Music is the terminal "
        "performance degree, pairing advanced solo and ensemble performance with scholarship and "
        "pedagogy across instrumental and vocal concentrations."
    ),
    "usc-social-sciences-ba": (
        "The interdisciplinary social sciences major at USC Dornsife lets undergraduates combine "
        "economics, psychology, political science, and sociology around a chosen emphasis, building "
        "broad analytical and research skills across the social sciences."
    ),
    "usc-music-ma": (
        "The Master of Arts in Music at the USC Thornton School of Music emphasizes scholarly research "
        "in music history and early-music performance, combining graduate seminars in musicology with "
        "historically informed performance and a thesis."
    ),
    "usc-music-phd": (
        "Doctoral study in music at the USC Thornton School of Music centers on original scholarship in "
        "historical musicology, supporting advanced research, seminars, and a dissertation in the "
        "history and analysis of music."
    ),
}
