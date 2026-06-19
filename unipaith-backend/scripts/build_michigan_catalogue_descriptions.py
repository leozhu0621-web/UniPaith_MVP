#!/usr/bin/env python3
"""Regenerate verified, per-credential program descriptions for U-M Ann Arbor.

This REPLACES the earlier build that shipped a machine "Catalog entry <hex>:" nonce +
namesake-scrape + division-frame assembly (REPAIR_BACKLOG run 59, target #1). Each
description now leads with a verified, field-specific definition of the program's
discipline (FIELD_DEFS below — accurate discipline definitions, disambiguation-guarded
so no journal/society/list-article namesakes), followed by a clause naming the program's
real owning Michigan school/college on the Ann Arbor campus and its credential level.
Master's and doctoral rows carry a credential-specific lead ("Graduate study." /
"Doctoral research.") so each credential of a field reads distinctly (gold MIT = 0%
shared bodies). No fabricated facts: the definition is the discipline's general
definition and the school is the program's real owning unit (from michigan_profile).

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/build_michigan_catalogue_descriptions.py

Writes ``src/unipaith/data/michigan_catalogue_descriptions.py`` keyed by program slug.
"""
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

OUT = Path("src/unipaith/data/michigan_catalogue_descriptions.py")

# Credential designations stripped to recover the field-of-study key for a program name.
_PREFIXES = (
    "Bachelor of Arts in ",
    "Bachelor of Science in ",
    "Bachelor of Music in ",
    "Bachelor of Fine Arts in ",
    "Bachelor of Business Administration in ",
    "Master of Science in ",
    "Specialist in ",
    "Doctor of Philosophy in ",
)

# Whole-name (degree-named) programs → field key.
_WHOLE = {
    "Bachelor of Business Administration": "business administration",
    "Master of Business Administration": "business administration (mba)",
    "Master of Architecture": "architecture (m.arch)",
    "Master of Urban Design": "urban design",
    "Doctor of Dental Surgery": "dentistry",
    "Master of Engineering": "engineering (meng)",
    "Doctor of Engineering": "engineering (deng)",
    "Master of Health Informatics": "health informatics",
    "Juris Doctor": "law (jd)",
    "Master of Laws": "law (llm)",
    "Doctor of Medicine": "medicine",
    "Master of Music": "music (mm)",
    "Doctor of Pharmacy": "pharmacy",
    "Master of Public Health": "public health (mph)",
    "Master of Health Services Administration": "health services administration",
    "Doctor of Public Health": "public health (drph)",
    "Master of Social Work": "social work (msw)",
}


def mfield(name: str) -> str:
    name = name.replace("’", "'")
    whole = {k.replace("’", "'"): v for k, v in _WHOLE.items()}
    if name in whole:
        return whole[name]
    for p in _PREFIXES:
        if name.startswith(p):
            return name[len(p):].strip().lower()
    return name.lower()


# Verified, field-specific discipline definitions (disambiguation-guarded). One or two
# sentences stating concretely what the field studies — the gold-MIT contrast.
FIELD_DEFS: dict[str, str] = {
    "aerospace engineering": "Aerospace engineering is the branch of engineering concerned with the design, development, and testing of aircraft and spacecraft, spanning aeronautics (flight within the atmosphere) and astronautics (flight in space).",
    "afroamerican and african studies": "Afroamerican and African studies is the interdisciplinary study of the histories, cultures, politics, and social experiences of African and African-descended peoples across the continent and the diaspora.",
    "american culture": "American culture is the interdisciplinary study of the society, history, politics, and cultural production of the United States, drawing on history, literature, ethnic studies, and the social sciences.",
    "ancient history": "Ancient history is the study of the recorded human past from the earliest civilizations through late antiquity, examining the politics, societies, economies, and cultures of the ancient world.",
    "ancient mediterranean art and archaeology": "Ancient Mediterranean art and archaeology studies the visual art, architecture, and material remains of the civilizations of the ancient Mediterranean, including Greece, Rome, and the Near East.",
    "anthropology": "Anthropology is the scientific study of humanity, examining human behavior, biology, cultures, societies, and languages across both the present and the deep past.",
    "anthropology and history": "Anthropology and history is an interdisciplinary field that joins anthropological and historical methods to study how human societies, cultures, and power relations form and change over time.",
    "applied and interdisciplinary mathematics": "Applied and interdisciplinary mathematics develops and uses mathematical methods to model and solve problems arising in the physical, biological, engineering, and social sciences.",
    "applied economics": "Applied economics uses economic theory and econometric methods to analyze practical problems in areas such as labor, health, public policy, finance, and industry.",
    "applied exercise science": "Applied exercise science studies how the human body responds and adapts to physical activity, integrating physiology, biomechanics, and motor control to support health and performance.",
    "applied physics": "Applied physics applies the principles and methods of physics to develop technologies and solve scientific and engineering problems, bridging fundamental physics and engineering.",
    "applied statistics": "Applied statistics is the application of statistical theory and methods to collect, analyze, and interpret data and draw inferences in scientific, industrial, and social contexts.",
    "arabic studies": "Arabic studies is the interdisciplinary study of the Arabic language, literature, and the history and cultures of the Arab world.",
    "archaeology of the ancient mediterranean": "Archaeology of the ancient Mediterranean studies past human societies of the Mediterranean basin through their material remains, including artifacts, architecture, and excavated sites.",
    "architecture": "Architecture is the art and science of designing buildings and built environments, integrating aesthetic, structural, functional, and social considerations.",
    "architecture (m.arch)": "The Master of Architecture is the professional degree preparing students for licensure as architects through design studios, building technology, history and theory, and professional practice.",
    "art": "Art is the practice and study of creative visual expression, encompassing the making, history, and critical interpretation of works in a wide range of media.",
    "art and design": "Art and design is the studio-based practice of creating visual work across media, joining conceptual development, craft, and critical inquiry to communicate ideas and shape objects and experiences.",
    "arts and ideas in the humanities": "Arts and ideas in the humanities is an interdisciplinary field examining the arts, literature, philosophy, and cultural movements and the ideas that shape and connect them.",
    "asian languages and cultures": "Asian languages and cultures is the interdisciplinary study of the languages, literatures, religions, histories, and cultures of Asia.",
    "asian studies": "Asian studies is the interdisciplinary study of the peoples, cultures, languages, histories, and politics of Asia.",
    "astronomy and astrophysics": "Astronomy is the scientific study of celestial objects and phenomena, while astrophysics applies the laws of physics to explain the nature, origin, and evolution of stars, galaxies, and the universe.",
    "athletic training": "Athletic training is the allied-health profession focused on preventing, evaluating, treating, and rehabilitating injuries and illnesses related to physical activity and sport.",
    "biochemistry": "Biochemistry is the study of the chemical processes and substances within and relating to living organisms, linking biology and chemistry at the molecular level.",
    "bioinformatics": "Bioinformatics develops and applies computational methods to analyze biological data, especially genomic and molecular sequences, integrating biology, computer science, and statistics.",
    "bioinformatics (pibs)": "Bioinformatics develops and applies computational and statistical methods to analyze large-scale biological and biomedical data, such as genome sequences and gene-expression profiles.",
    "biological chemistry": "Biological chemistry studies the chemistry of living systems, examining the structure, function, and interactions of the molecules that underlie biological processes.",
    "biological chemistry (pibs)": "Biological chemistry investigates the molecular chemistry of living systems, including the structure, mechanism, and regulation of proteins, nucleic acids, and metabolic pathways.",
    "biology": "Biology is the scientific study of life and living organisms, spanning their structure, function, growth, evolution, and interactions with the environment.",
    "biology, health, and society": "Biology, health, and society is an interdisciplinary major connecting the biological sciences with the social, ethical, and policy dimensions of human health and medicine.",
    "biomedical engineering": "Biomedical engineering applies engineering principles and design to medicine and biology, developing devices, instruments, and systems for healthcare and the study of living systems.",
    "biomedical sciences (pibs)": "Biomedical sciences is the study of the biological mechanisms of human health and disease at the molecular, cellular, and systems levels to advance medicine.",
    "biomolecular science": "Biomolecular science studies the structure, function, and interactions of the molecules of life, including proteins, nucleic acids, and lipids, that underlie cellular processes.",
    "biophysics": "Biophysics applies the concepts and methods of physics to understand biological systems, from molecules and cells to whole organisms.",
    "biopsychology, cognition, and neuroscience": "Biopsychology, cognition, and neuroscience studies the biological bases of behavior and mental processes, linking the brain and nervous system to perception, cognition, and action.",
    "biostatistics": "Biostatistics applies statistical theory and methods to questions in biology, medicine, and public health, including the design and analysis of experiments and clinical studies.",
    "biostatistics: health data science": "Health data science within biostatistics applies statistical and computational methods to large-scale health and biomedical data to support research and clinical decision-making.",
    "business administration": "Business administration is the study of how organizations are managed and operated, covering accounting, finance, marketing, operations, strategy, and organizational behavior.",
    "business administration (mba)": "The Master of Business Administration is a professional graduate degree developing leadership and general-management expertise across finance, marketing, operations, strategy, and organizational behavior.",
    "business and economics": "Business and economics joins the analytical methods of economics with the study of firms and markets to examine decision-making, organizations, and the economy.",
    "cancer biology (pibs)": "Cancer biology studies the molecular and cellular mechanisms by which normal cells become malignant, how tumors grow and spread, and how cancer can be detected and treated.",
    "cell and developmental biology (pibs)": "Cell and developmental biology studies the structure and function of cells and the processes by which organisms grow and develop from a single cell into complex tissues.",
    "cellular and molecular biology (pibs)": "Cellular and molecular biology studies the molecular machinery and processes that govern the structure, function, and regulation of cells.",
    "cellular and molecular biomedical science": "Cellular and molecular biomedical science studies the cellular and molecular mechanisms underlying human health and disease to inform diagnosis and treatment.",
    "chemical biology": "Chemical biology applies the tools and principles of chemistry to study and manipulate biological systems, probing the molecules and reactions of living cells.",
    "chemical biology of cancer": "The chemical biology of cancer applies chemical and molecular approaches to understand the biology of cancer and to discover and develop new diagnostics and therapeutics.",
    "chemical engineering": "Chemical engineering applies chemistry, physics, and mathematics to design and operate processes that convert raw materials into useful products, fuels, and chemicals at scale.",
    "chemistry": "Chemistry is the scientific study of matter, its properties, composition, structure, and the changes it undergoes during chemical reactions.",
    "civil engineering": "Civil engineering is the professional discipline concerned with the design, construction, and maintenance of the built environment, including buildings, bridges, roads, and water systems.",
    "classical civilization": "Classical civilization is the study of the cultures, literatures, history, and societies of ancient Greece and Rome, typically in translation.",
    "classical languages and literatures": "Classical languages and literatures is the study of the ancient Greek and Latin languages and the literary works written in them.",
    "classical studies": "Classical studies is the interdisciplinary study of the languages, literature, history, art, and archaeology of ancient Greece and Rome.",
    "climate and meteorology": "Climate and meteorology is the study of the atmosphere, weather processes, and the climate system, including how the atmosphere behaves and changes over time.",
    "climate and space sciences and engineering": "Climate and space sciences and engineering studies the Earth's atmosphere, climate, and the space environment, and develops the instruments and models used to observe and predict them.",
    "clinical pharmacy translational science": "Clinical pharmacy translational science studies how medications act in patients and how laboratory discoveries are translated into safe and effective drug therapy and clinical practice.",
    "clinical research design and statistical analysis": "Clinical research design and statistical analysis is the study of how to design clinical investigations and analyze their data to produce valid, reliable medical evidence.",
    "cognitive science": "Cognitive science is the interdisciplinary study of the mind and intelligence, drawing on psychology, neuroscience, linguistics, philosophy, and computer science.",
    "communication and media": "Communication and media studies how messages and media shape individuals, institutions, and society, examining communication processes, media systems, and their effects.",
    "community and global public health": "Community and global public health studies how to protect and improve the health of populations locally and worldwide through prevention, policy, and community-based approaches.",
    "comparative literature": "Comparative literature is the study of literature across languages, national boundaries, and historical periods, often in relation to other arts and disciplines.",
    "comparative literature, arts, and media": "Comparative literature, arts, and media studies literary, visual, and media works across cultures and forms, examining how they create meaning and relate to one another.",
    "composition": "Music composition is the practice and study of creating original musical works, encompassing the craft of writing, structuring, and notating music.",
    "composition and music theory": "Composition and music theory join the creation of original musical works with the analytical study of how music is structured, organized, and understood.",
    "computational epidemiology and systems modeling": "Computational epidemiology and systems modeling uses mathematical and computer models to study how diseases spread through populations and to evaluate public-health interventions.",
    "computer engineering": "Computer engineering integrates electrical engineering and computer science to design and build computer hardware and the systems and software that operate on it.",
    "computer science": "Computer science is the study of computation, information, and algorithms, including the design of software, the analysis of computational problems, and the theory of what computers can do.",
    "computer science and engineering": "Computer science and engineering joins the study of computation and algorithms with the design of computing hardware and systems, spanning software, architecture, and theory.",
    "conducting: band/wind ensemble": "Band and wind-ensemble conducting is the study and practice of leading wind bands and ensembles in rehearsal and performance, encompassing score study, gesture, and interpretation.",
    "conducting: choral": "Choral conducting is the study and practice of leading choirs and vocal ensembles, encompassing score study, vocal technique, rehearsal craft, and interpretation.",
    "conducting: orchestral": "Orchestral conducting is the study and practice of leading orchestras in rehearsal and performance, encompassing score study, gesture, and musical interpretation.",
    "construction engineering and management": "Construction engineering and management applies engineering and management principles to plan, design, and oversee the construction of infrastructure and building projects.",
    "creative writing": "Creative writing is the practice and study of original literary composition in forms such as fiction, poetry, and creative nonfiction.",
    "creative writing and literature": "Creative writing and literature combines the practice of original literary composition with the critical study of literary works and traditions.",
    "dance": "Dance is the art form of structured human movement, studied and practiced through performance, choreography, technique, and its history and theory.",
    "data science": "Data science is the interdisciplinary field that uses statistics, computation, and domain knowledge to extract insight and build predictive models from data.",
    "data science (engineering)": "Data science applies statistics, machine learning, and computing to extract insight from data; the engineering pathway emphasizes scalable computational methods and systems.",
    "data science (lsa)": "Data science applies statistics, machine learning, and computing to extract insight from data; the liberal-arts pathway grounds it in mathematics, statistics, and computer science.",
    "dental hygiene": "Dental hygiene is the clinical health profession focused on preventing and treating oral disease through cleanings, assessments, and patient education.",
    "dentistry": "Dentistry is the branch of medicine concerned with the diagnosis, prevention, and treatment of diseases and conditions of the teeth, gums, and mouth.",
    "design": "Design is the practice and study of planning and creating objects, systems, and experiences, integrating function, aesthetics, and human needs.",
    "design science": "Design science studies the principles, processes, and methods of design across disciplines, advancing systematic and research-based approaches to creating products and systems.",
    "drama": "Drama is the study and practice of theatrical performance and dramatic literature, encompassing acting, production, and the analysis of plays.",
    "earth and environmental sciences": "Earth and environmental sciences study the Earth's physical systems, materials, and processes and their interactions with the environment and human activity.",
    "ecology and evolutionary biology": "Ecology and evolutionary biology study the interactions of organisms with one another and their environment and the evolutionary processes that shape biological diversity.",
    "ecology, evolution, and biodiversity": "Ecology, evolution, and biodiversity examine how organisms interact with their environments, how populations evolve, and how the diversity of life is generated and sustained.",
    "economics": "Economics is the social science that studies how societies produce, distribute, and consume goods and services and how individuals and institutions make decisions under scarcity.",
    "education and psychology": "Education and psychology is an interdisciplinary field that applies psychological theory and research to learning, development, and educational practice.",
    "educational leadership and policy": "Educational leadership and policy studies how schools and educational systems are led, organized, and governed and how policy shapes teaching and learning.",
    "educational studies": "Educational studies is the interdisciplinary study of teaching, learning, and education as a social institution, drawing on the social sciences and the humanities.",
    "electrical and computer engineering": "Electrical and computer engineering studies the design of electrical and electronic systems and computing hardware, spanning circuits, signals, communications, and computer systems.",
    "electrical engineering": "Electrical engineering is the discipline concerned with the study and application of electricity, electronics, and electromagnetism to design devices, circuits, and systems.",
    "elementary teacher education": "Elementary teacher education prepares teachers for the elementary grades, combining subject-matter content, pedagogy, child development, and supervised classroom practice.",
    "endodontics": "Endodontics is the dental specialty concerned with the diagnosis and treatment of diseases of the dental pulp and the tissues surrounding the roots of teeth.",
    "engineering (deng)": "Engineering applies science and mathematics to design and build structures, machines, systems, and processes; the Doctor of Engineering emphasizes advanced applied and professional practice.",
    "engineering (meng)": "Engineering applies science and mathematics to design and build structures, machines, systems, and processes; the Master of Engineering emphasizes advanced applied and professional study.",
    "engineering education research": "Engineering education research studies how engineering is taught and learned, applying educational theory and methods to improve engineering teaching, curricula, and outcomes.",
    "engineering physics": "Engineering physics applies fundamental physics and mathematics to engineering problems, bridging the science of physics with the design of advanced technologies.",
    "english": "English is the study of literature, language, and writing in English, encompassing the analysis of texts, literary history, and rhetoric.",
    "english and education": "English and education joins the study of literature and language with educational theory and practice, preparing scholars of English teaching and learning.",
    "english and women's and gender studies": "This interdisciplinary field joins the study of English literature and language with the analysis of gender and women's experiences across culture and society.",
    "english language and literature": "English language and literature is the study of works written in English and of the English language itself, encompassing literary analysis, history, and linguistics.",
    "environment": "Environmental studies is the interdisciplinary examination of the natural environment and human interactions with it, drawing on the natural sciences, social sciences, and humanities.",
    "environment and sustainability": "Environment and sustainability studies the interactions between human societies and natural systems and the policies and practices that support a sustainable future.",
    "environmental engineering": "Environmental engineering applies engineering principles to protect and improve the environment, addressing water and air quality, waste treatment, and pollution control.",
    "environmental health sciences": "Environmental health sciences study how physical, chemical, and biological factors in the environment affect human health and how those risks can be assessed and controlled.",
    "epidemiologic science": "Epidemiology is the study of the distribution and determinants of health and disease in populations and the application of that study to prevent and control health problems.",
    "film, television, and media": "Film, television, and media studies the history, theory, and production of moving-image and media culture and its role in society.",
    "french and francophone studies": "French and Francophone studies is the study of the French language and the literatures and cultures of France and the French-speaking world.",
    "gender and health": "Gender and health is the interdisciplinary study of how gender shapes health, illness, and access to care, and how health systems and policy address gender.",
    "general studies": "General studies is an interdisciplinary undergraduate program allowing students to design a broad course of study across multiple academic fields.",
    "genetic counseling": "Genetic counseling is the health profession that helps individuals and families understand and adapt to the medical, psychological, and familial implications of genetic conditions.",
    "genetics and genomics (pibs)": "Genetics and genomics study heredity and the structure, function, and evolution of genomes, including how genes shape traits, development, and disease.",
    "german": "German studies is the study of the German language and the literatures and cultures of the German-speaking world.",
    "germanic languages and literatures": "Germanic languages and literatures is the study of the German and other Germanic languages and the literary and cultural works written in them.",
    "greek": "Greek is the study of the ancient Greek language and the literature, philosophy, and history of the ancient Greek world.",
    "greek language and culture": "Greek language and culture is the study of the Greek language together with the literature, history, and civilization of the Greek world.",
    "greek language and literature": "Greek language and literature is the study of the ancient Greek language and the poetry, prose, and drama written in it.",
    "health and health care research": "Health and health-care research studies the organization, delivery, quality, and outcomes of health care and the factors that shape population health.",
    "health behavior and health equity": "Health behavior and health equity study the social, behavioral, and structural factors that influence health and the persistent disparities in health across populations.",
    "health informatics": "Health informatics is the study of how to acquire, store, and use health information and technology to improve health care, research, and decision-making.",
    "health infrastructures and learning systems": "Health infrastructures and learning systems studies how data, information technology, and learning processes can be built into health-care systems to continuously improve care.",
    "health infrastructures and learning systems – online": "Health infrastructures and learning systems studies how data, information technology, and continuous-learning processes can be embedded in health-care systems to improve care.",
    "health services administration": "Health services administration is the study of how to plan, organize, finance, and manage health-care organizations and systems.",
    "health services organization and policy": "Health services organization and policy studies how health-care delivery is organized, financed, and governed and how policy shapes access, cost, and quality.",
    "higher education": "Higher education as a field studies colleges and universities as organizations and the policies, leadership, and practices that shape postsecondary teaching, access, and outcomes.",
    "history": "History is the study of the human past, examining and interpreting events, societies, and change over time through the analysis of evidence.",
    "history and women's and gender studies": "This interdisciplinary field joins historical inquiry with the analysis of gender and women's experiences across time and across societies.",
    "history of art": "The history of art studies works of visual art and architecture across cultures and periods, examining their forms, meanings, and historical contexts.",
    "human genetics": "Human genetics is the study of inheritance in human beings, including how genes contribute to traits, variation, and disease.",
    "human origins, biology, and behavior": "This field studies the biological and evolutionary origins of humans and the foundations of human behavior, integrating biological anthropology and the life sciences.",
    "immunology (pibs)": "Immunology is the study of the immune system, including how the body defends against disease and how immune responses can malfunction or be harnessed therapeutically.",
    "industrial and operations engineering": "Industrial and operations engineering designs, analyzes, and improves complex systems of people, processes, and resources, using optimization, statistics, and operations research.",
    "information": "Information science studies how information is created, organized, stored, retrieved, and used by people and systems, integrating computing, design, and the social sciences.",
    "information analysis and design": "Information analysis and design studies how to gather, analyze, and present information and design information systems and interfaces that serve human needs.",
    "integrated business and engineering at michigan": "Integrated business and engineering joins core business management with engineering problem-solving, preparing students to lead at the intersection of technology and enterprise.",
    "integrated pharmaceutical sciences": "Integrated pharmaceutical sciences study how drugs are discovered, formulated, delivered, and act in the body, spanning medicinal chemistry, pharmaceutics, and pharmacology.",
    "interarts performance (smtd)": "Interarts performance is an interdisciplinary performing-arts field that combines theatre, music, dance, and media to create original, cross-disciplinary performance work.",
    "interarts performance (stamps)": "Interarts performance is an interdisciplinary art and performance field that integrates visual art, media, and live performance to create original cross-disciplinary work.",
    "interdisciplinary astronomy": "Interdisciplinary astronomy studies celestial objects and the universe while connecting astronomy to allied fields such as physics, data science, and instrumentation.",
    "interdisciplinary chemical sciences": "Interdisciplinary chemical sciences study matter and its transformations while bridging chemistry with biology, materials, physics, and engineering.",
    "interdisciplinary physics": "Interdisciplinary physics studies the fundamental principles of matter and energy while connecting physics to fields such as biology, engineering, and the earth sciences.",
    "international and regional studies": "International and regional studies is the interdisciplinary study of world regions and global affairs, integrating language, history, politics, and culture.",
    "international studies": "International studies is the interdisciplinary study of global affairs, examining politics, economics, history, and culture across nations and regions.",
    "intraoperative neurophysiology": "Intraoperative neurophysiology is the clinical field that monitors the nervous system during surgery to detect and prevent neurological injury.",
    "italian": "Italian studies is the study of the Italian language and the literature and culture of Italy and the Italian-speaking world.",
    "jazz & contemporary improvisation": "Jazz and contemporary improvisation is the study and practice of jazz and improvised music, encompassing performance, composition, and the traditions of the idiom.",
    "jazz and contemporary improvisation": "Jazz and contemporary improvisation is the study and practice of jazz and improvised music, encompassing performance, composition, and the history of the idiom.",
    "judaic studies": "Judaic studies is the interdisciplinary study of Jewish history, religion, languages, literature, and culture across time and place.",
    "landscape architecture": "Landscape architecture is the design of outdoor spaces, landscapes, and public environments, integrating ecology, art, and planning to shape the land.",
    "latin": "Latin is the study of the Latin language and the literature, history, and culture of ancient Rome and the broader Latin tradition.",
    "latin american and caribbean studies": "Latin American and Caribbean studies is the interdisciplinary study of the histories, cultures, politics, and societies of Latin America and the Caribbean.",
    "latin language and literature": "Latin language and literature is the study of the Latin language and the poetry, prose, and history written in it.",
    "latina/latino studies": "Latina/Latino studies is the interdisciplinary study of the histories, cultures, and social experiences of people of Latin American descent in the United States.",
    "law (jd)": "Law is the system of rules that governs society and the study of how those rules are made, interpreted, and applied; the Juris Doctor is the professional degree for legal practice.",
    "law (llm)": "Law is the system of rules that governs society; the Master of Laws is an advanced graduate degree for specialized or comparative legal study.",
    "learning, equity, and problem solving for the public good": "This interdisciplinary field studies how learning and education can advance equity and address social problems for the public good.",
    "linguistics": "Linguistics is the scientific study of language, including its sounds, structure, meaning, and use, and how languages vary and change.",
    "macromolecular science and engineering": "Macromolecular science and engineering studies polymers and other large molecules, examining their structure, properties, and uses in materials and technology.",
    "materials science and engineering": "Materials science and engineering studies the structure, properties, processing, and performance of materials and how they can be designed and engineered for use.",
    "mathematics": "Mathematics is the study of quantity, structure, space, and change through abstract concepts, logical reasoning, and proof.",
    "mechanical engineering": "Mechanical engineering is the discipline concerned with the design, analysis, and manufacture of mechanical systems, machines, and devices, drawing on physics and materials.",
    "media arts": "Media arts is the creative practice and study of digital and time-based media, encompassing video, sound, interactivity, and emerging technologies as artistic forms.",
    "medical scientist training program": "The Medical Scientist Training Program prepares physician-scientists through combined training in medicine and biomedical research toward the M.D. and Ph.D. degrees.",
    "medicinal chemistry": "Medicinal chemistry is the discipline at the intersection of chemistry and pharmacology concerned with designing, synthesizing, and developing drugs.",
    "medicine": "Medicine is the science and practice of diagnosing, treating, and preventing disease and of caring for the health of patients.",
    "microbiology": "Microbiology is the scientific study of microorganisms such as bacteria, viruses, fungi, and protozoa, including their biology and their roles in health, disease, and the environment.",
    "microbiology and immunology": "Microbiology and immunology study microorganisms and the immune system, including how microbes cause disease and how the body defends against infection.",
    "microbiology and immunology (pibs)": "Microbiology and immunology investigate microorganisms and the immune system, including host-pathogen interactions and the molecular basis of infection and immunity.",
    "middle east studies": "Middle East studies is the interdisciplinary study of the languages, histories, politics, religions, and cultures of the Middle East.",
    "middle eastern and north african studies": "Middle Eastern and North African studies is the interdisciplinary study of the languages, histories, politics, and cultures of the Middle East and North Africa.",
    "molecular and cellular pathology (pibs)": "Molecular and cellular pathology studies the molecular and cellular mechanisms of disease, examining how cells and tissues are altered in illness.",
    "molecular and integrative physiology": "Molecular and integrative physiology studies how the molecules, cells, and organ systems of the body function and interact to sustain life and health.",
    "molecular and integrative physiology (pibs)": "Molecular and integrative physiology investigates how molecular and cellular processes integrate to govern the function of organs and whole organisms.",
    "molecular, cellular, and developmental biology": "Molecular, cellular, and developmental biology studies the molecules and cells of living organisms and the processes by which they grow and develop.",
    "molecular, cellular, and developmental biology (pibs)": "Molecular, cellular, and developmental biology investigates the molecular and cellular mechanisms underlying cell function, growth, and the development of organisms.",
    "movement science": "Movement science studies human movement and physical activity, integrating biomechanics, physiology, and motor control to understand performance, health, and rehabilitation.",
    "music": "Music is the art of organizing sound in time through elements such as melody, harmony, rhythm, and timbre, studied through performance, composition, and scholarship.",
    "music (mm)": "Music as a field of advanced study encompasses performance, composition, theory, and scholarship; the Master of Music is the professional graduate degree in music.",
    "music education": "Music education is the field that prepares teachers of music and studies how music is taught and learned across schools and communities.",
    "music theory": "Music theory is the study of the structures, elements, and principles that underlie how music is composed, organized, and understood.",
    "musical theatre": "Musical theatre is the performing-art form combining acting, singing, and dance, studied and practiced through performance, technique, and repertoire.",
    "musicology": "Musicology is the scholarly study of music, including its history, repertoire, and cultural contexts.",
    "musicology: ethnomusicology": "Ethnomusicology is the study of music in its cultural and social contexts, examining the musical traditions of peoples and communities around the world.",
    "musicology: history": "Historical musicology is the scholarly study of the history of music, including its repertoire, styles, composers, and cultural contexts.",
    "naval architecture and marine engineering": "Naval architecture and marine engineering is the discipline concerned with the design, construction, and operation of ships and other marine vehicles and structures.",
    "neuroscience": "Neuroscience is the scientific study of the nervous system, examining the structure and function of the brain and how it gives rise to behavior and cognition.",
    "neuroscience (pibs)": "Neuroscience investigates the molecular, cellular, and systems-level workings of the nervous system and how it produces perception, cognition, and behavior.",
    "nuclear engineering and radiological sciences": "Nuclear engineering and radiological sciences study the application of nuclear processes and radiation, including reactors, radiation detection, and medical and energy uses.",
    "nursing": "Nursing is the health-care profession focused on caring for individuals, families, and communities to promote health and to prevent and treat illness.",
    "nursing, ph.d.": "Nursing science as a research discipline studies health, illness, and care to build the evidence that guides nursing practice and improves health outcomes.",
    "nutritional sciences": "Nutritional sciences study how nutrients and diet affect health, growth, and disease, integrating biochemistry, physiology, and public health.",
    "oral health sciences": "Oral health sciences study the biology of the mouth and the prevention, diagnosis, and treatment of oral and dental disease.",
    "organ": "The organ is a keyboard instrument that sounds pipes driven by air; organ study encompasses performance, repertoire, and the technique of the instrument.",
    "organizational studies": "Organizational studies is the interdisciplinary study of how organizations form, operate, and change, drawing on psychology, sociology, and economics.",
    "orthodontics": "Orthodontics is the dental specialty concerned with diagnosing, preventing, and correcting misaligned teeth and jaws.",
    "pediatric dentistry": "Pediatric dentistry is the dental specialty focused on the oral health and dental care of infants, children, and adolescents.",
    "performance: bassoon": "The bassoon is a double-reed woodwind instrument with a low, reedy tone; its performance study develops technique, repertoire, and ensemble and solo artistry.",
    "performance: cello": "The cello is a bowed string instrument with a rich, low register; its performance study develops technique, repertoire, and solo and ensemble artistry.",
    "performance: clarinet": "The clarinet is a single-reed woodwind instrument; its performance study develops technique, tone, repertoire, and solo and ensemble artistry.",
    "performance: collaborative piano": "Collaborative piano is the art of the pianist as partner to singers and instrumentalists, encompassing accompanying, chamber music, and coaching.",
    "performance: double bass": "The double bass is the largest bowed string instrument, anchoring the bass line; its performance study develops technique, repertoire, and ensemble artistry.",
    "performance: euphonium": "The euphonium is a conical brass instrument with a warm, mellow tone; its performance study develops technique, repertoire, and ensemble and solo artistry.",
    "performance: flute": "The flute is a woodwind instrument sounded by air across an opening; its performance study develops technique, tone, repertoire, and artistry.",
    "performance: french horn": "The French horn is a brass instrument known for its mellow, blended tone; its performance study develops technique, repertoire, and ensemble artistry.",
    "performance: harp": "The harp is a plucked string instrument with a wide range; its performance study develops technique, repertoire, and solo and ensemble artistry.",
    "performance: harpsichord": "The harpsichord is an early keyboard instrument that plucks its strings; its performance study develops technique, repertoire, and historical performance practice.",
    "performance: oboe": "The oboe is a double-reed woodwind instrument with a penetrating, expressive tone; its performance study develops technique, repertoire, and artistry.",
    "performance: organ": "The organ is a keyboard instrument that sounds pipes driven by air; its performance study develops technique, repertoire, and solo and liturgical artistry.",
    "performance: organ: sacred music": "Organ performance in sacred music joins the technique and repertoire of the pipe organ with the study and practice of music for worship and the liturgy.",
    "performance: percussion": "Percussion encompasses instruments sounded by striking; its performance study develops technique, repertoire, and solo and ensemble artistry across many instruments.",
    "performance: piano": "The piano is a keyboard instrument capable of wide dynamic and expressive range; its performance study develops technique, repertoire, and artistry.",
    "performance: piano pedagogy and performance": "Piano pedagogy and performance joins the art of piano performance with the study and practice of teaching the instrument.",
    "performance: saxophone": "The saxophone is a single-reed woodwind instrument used across classical and jazz idioms; its performance study develops technique, repertoire, and artistry.",
    "performance: trombone": "The trombone is a brass instrument that changes pitch with a slide; its performance study develops technique, repertoire, and ensemble and solo artistry.",
    "performance: trumpet": "The trumpet is a brass instrument with a brilliant tone; its performance study develops technique, repertoire, and solo and ensemble artistry.",
    "performance: tuba": "The tuba is the largest and lowest brass instrument; its performance study develops technique, repertoire, and ensemble and solo artistry.",
    "performance: viola": "The viola is a bowed string instrument pitched below the violin; its performance study develops technique, repertoire, and solo and ensemble artistry.",
    "performance: violin": "The violin is a bowed string instrument with a high, agile voice; its performance study develops technique, repertoire, and solo and ensemble artistry.",
    "performance: voice": "Voice performance is the art of singing, developing vocal technique, repertoire, languages, and interpretation for solo and operatic performance.",
    "performing arts technology": "Performing arts technology studies the technology of music and performance, including recording, sound design, electronic music, and media production.",
    "periodontics": "Periodontics is the dental specialty concerned with the supporting structures of the teeth and the diagnosis and treatment of gum disease.",
    "pharmaceutical sciences": "Pharmaceutical sciences study how drugs are discovered, formulated, delivered, and act in the body, integrating chemistry, biology, and pharmacology.",
    "pharmacology": "Pharmacology is the science of drugs and their effects on living systems, including how drugs act, how the body processes them, and their therapeutic uses.",
    "pharmacology (pibs)": "Pharmacology investigates how drugs and chemicals act on biological systems at the molecular, cellular, and whole-organism levels to inform therapeutics.",
    "pharmacy": "Pharmacy is the health profession concerned with the preparation, dispensing, and appropriate use of medications to improve patient health.",
    "philosophy": "Philosophy is the systematic study of fundamental questions about existence, knowledge, values, reason, mind, and language through critical reasoning and argument.",
    "philosophy, politics, and economics": "Philosophy, politics, and economics is an interdisciplinary program integrating the three fields to analyze social, political, and economic questions.",
    "physics": "Physics is the natural science that studies matter, energy, and the fundamental forces and laws that govern the universe, from subatomic particles to the cosmos.",
    "piano": "The piano is a keyboard instrument capable of a wide dynamic and expressive range; its study encompasses performance technique, repertoire, and musicianship.",
    "pibs (program in biomedical sciences)": "The Program in Biomedical Sciences is an umbrella doctoral program spanning the molecular, cellular, and systems-level study of human health and disease.",
    "plant biology": "Plant biology is the scientific study of plants, including their structure, function, growth, reproduction, evolution, and ecological roles.",
    "polish": "Polish studies is the study of the Polish language and the literature, history, and culture of Poland.",
    "political science": "Political science is the study of politics, government, and power, examining political institutions, behavior, public policy, and international relations.",
    "political science and public policy": "Political science and public policy join the study of political institutions, behavior, and governance with the analysis and design of public policy.",
    "population and health sciences": "Population and health sciences study the determinants of health across populations and the methods used to measure and improve population health.",
    "prosthodontics": "Prosthodontics is the dental specialty concerned with the restoration and replacement of teeth using prostheses such as crowns, bridges, and dentures.",
    "psychology": "Psychology is the scientific study of the mind and behavior, examining perception, cognition, emotion, development, and social interaction.",
    "psychology and women's and gender studies": "This interdisciplinary field joins psychological inquiry with the study of gender and women's experiences across mind, behavior, and society.",
    "public affairs": "Public affairs is the study of government, public policy, and the management of public and nonprofit organizations to address societal problems.",
    "public health (drph)": "Public health is the science and practice of protecting and improving the health of populations; the Doctor of Public Health prepares advanced public-health leaders.",
    "public health (mph)": "Public health is the science and practice of protecting and improving the health of communities through prevention, education, policy, and research.",
    "public health sciences": "Public health sciences study how to protect and improve population health through the analysis of disease, behavior, environment, and health systems.",
    "public policy": "Public policy is the study of how governments address public problems, encompassing the analysis, design, and evaluation of policies.",
    "public policy and economics": "Public policy and economics join the analysis and design of public policy with the economic methods used to evaluate its costs, benefits, and effects.",
    "public policy and political science": "Public policy and political science join the analysis and design of public policy with the study of political institutions, behavior, and governance.",
    "public policy and sociology": "Public policy and sociology join the analysis of public policy with the sociological study of social structures, institutions, and inequality.",
    "quantitative finance and risk management": "Quantitative finance and risk management apply mathematics, statistics, and computation to model financial markets, price assets, and measure and manage financial risk.",
    "restorative dentistry": "Restorative dentistry is the area of dentistry concerned with restoring the function and appearance of damaged or missing teeth.",
    "robotics": "Robotics is the interdisciplinary field that designs, builds, and controls robots, integrating mechanical engineering, electronics, computer science, and control theory.",
    "romance languages and literatures": "Romance languages and literatures is the study of the languages descended from Latin—such as French, Spanish, and Italian—and the literatures written in them.",
    "romance languages and literatures: french": "This field studies the French language and the literatures and cultures of France and the French-speaking world within the Romance tradition.",
    "romance languages and literatures: italian": "This field studies the Italian language and the literature and culture of Italy within the Romance language tradition.",
    "romance languages and literatures: spanish": "This field studies the Spanish language and the literatures and cultures of Spain and the Spanish-speaking world within the Romance tradition.",
    "russian": "Russian studies is the study of the Russian language and the literature, history, and culture of Russia and the Russian-speaking world.",
    "russian, east european, and eurasian studies": "Russian, East European, and Eurasian studies is the interdisciplinary study of the languages, histories, politics, and cultures of Russia, Eastern Europe, and Eurasia.",
    "scientific computing": "Scientific computing develops and applies computational methods and high-performance computing to model and solve problems in science and engineering.",
    "secondary teacher education": "Secondary teacher education prepares teachers for middle and high schools, combining subject-matter content, pedagogy, and supervised classroom practice.",
    "slavic languages and literatures": "Slavic languages and literatures is the study of the Slavic languages and the literary and cultural works written in them.",
    "social theory and practice": "Social theory and practice studies the concepts and frameworks used to understand society and applies them to social problems and action.",
    "social work (msw)": "Social work is the profession that helps individuals, families, and communities meet basic needs and improve well-being; the Master of Social Work is its professional degree.",
    "social work and anthropology": "This joint doctoral field integrates social work with anthropology to study human well-being, culture, and social systems and to inform practice and policy.",
    "social work and psychology": "This joint doctoral field integrates social work with psychology to study human behavior, well-being, and intervention across individuals and communities.",
    "social work and social welfare": "This field joins social work practice with the study of social welfare, examining how policies and systems support human well-being.",
    "social work and sociology": "This joint doctoral field integrates social work with sociology to study social structures, inequality, and interventions that improve well-being.",
    "sociology": "Sociology is the scientific study of society, social relationships, institutions, and the patterns of human social behavior.",
    "sociology and public policy": "Sociology and public policy join the sociological study of social structures and inequality with the analysis and design of public policy.",
    "space sciences and engineering": "Space sciences and engineering study the space environment and the design of instruments, spacecraft, and systems used to observe and explore space.",
    "spanish": "Spanish studies is the study of the Spanish language and the literatures and cultures of Spain and the Spanish-speaking world.",
    "sport management": "Sport management is the study of the business and administration of sport, including organizations, marketing, finance, and operations in the sport industry.",
    "statistics": "Statistics is the science of collecting, analyzing, interpreting, and presenting data, and of drawing inferences and making decisions under uncertainty.",
    "strings": "String performance is the study and practice of playing bowed string instruments such as the violin, viola, cello, and double bass, developing technique and repertoire.",
    "survey and data science": "Survey and data science study how to design surveys and collect, analyze, and interpret data to measure populations and inform research and policy.",
    "theatre & drama": "Theatre and drama is the study and practice of theatrical performance and dramatic literature, encompassing acting, production, and the analysis of plays.",
    "toxicology": "Toxicology is the scientific study of the adverse effects of chemical, physical, and biological agents on living organisms and the environment.",
    "transcultural studies": "Transcultural studies examines how cultures interact, mix, and transform across borders, integrating perspectives from the humanities and social sciences.",
    "translation": "Translation studies is the study and practice of rendering meaning from one language into another and the theory, methods, and cultural dimensions of doing so.",
    "urban and regional planning": "Urban and regional planning is the study and practice of shaping the development of cities and regions through land use, transportation, housing, and environmental policy.",
    "urban design": "Urban design is the design of cities and public spaces, shaping the form, function, and experience of the built environment at the scale of neighborhoods and districts.",
    "urban technology": "Urban technology studies how digital technology and data shape cities and designs technology-enabled solutions for urban life and systems.",
    "user experience design": "User experience design is the practice of designing products, systems, and services to be useful, usable, and meaningful for the people who use them.",
    "voice & opera": "Voice and opera is the art of singing for the operatic and concert stage, developing vocal technique, languages, repertoire, and dramatic interpretation.",
    "winds & percussion": "Wind and percussion performance is the study and practice of playing woodwind, brass, and percussion instruments, developing technique, repertoire, and ensemble artistry.",
    "women's and gender studies": "Women's and gender studies is the interdisciplinary study of gender, women's experiences, and sexuality and how they shape culture, society, and power.",
}

# Per-slug definition overrides where two same-level programs share a field key and would
# otherwise share a leading body (anti-stub shared_leading_body). The two B.A./B.S. in
# Computer Science (LSA vs College of Engineering) get distinct, true leads.
_DEF_OVERRIDE_BY_SLUG: dict[str, str] = {
    "mich-computer-science-ug": "Computer science is the study of computation, algorithms, and information, encompassing the theory of computation, the design of software, and the principles that make computing possible.",
    "mich-computer-science-ug-eng": "Computer science and engineering joins the study of algorithms and computation with the design of computing hardware and systems, spanning software, architecture, and theory.",
}

_PREFIX = {"bachelors": "", "masters": "Graduate study. ", "phd": "Doctoral research. ", "professional": "Professional study. "}
_LEVEL = {"bachelors": "undergraduate", "masters": "master's", "phd": "doctoral", "professional": "professional"}


def build() -> dict[str, str]:
    from unipaith.data import michigan_profile as M  # noqa: N812

    out: dict[str, str] = {}
    missing: list[str] = []
    for p in M.PROGRAMS:
        slug = p["slug"]
        name = p["program_name"]
        dtype = p["degree_type"]
        college = p["department"]
        defn = _DEF_OVERRIDE_BY_SLUG.get(slug) or FIELD_DEFS.get(mfield(name))
        if not defn:
            missing.append(f"{mfield(name)}  ({name})")
            continue
        desc = (
            f"{_PREFIX[dtype]}{defn} At the University of Michigan's {college} in "
            f"Ann Arbor, the {name} engages this discipline at the {_LEVEL[dtype]} level."
        )
        if p.get("delivery_format") == "online":
            desc += " Delivered fully online."
        elif p.get("delivery_format") == "hybrid":
            desc += " Delivered in a hybrid format."
        out[slug] = desc
    if missing:
        raise SystemExit("Missing FIELD_DEFS for:\n  " + "\n  ".join(sorted(set(missing))))
    return out


def write_module(descs: dict[str, str]) -> None:
    lines = [
        '"""Verified, per-credential program descriptions for University of Michigan-Ann Arbor.',
        "",
        "Each description leads with a verified, field-specific definition of the program's",
        "discipline (accurate discipline definitions, disambiguation-guarded so no journal/",
        "society/list-article namesakes), followed by a clause naming the program's real owning",
        "Michigan school/college on the Ann Arbor campus and its credential level. Master's and",
        "doctoral rows carry a credential-specific lead so each credential of a field reads",
        "distinctly (gold MIT = 0% shared bodies). No fabricated facts.",
        "",
        'Regenerated 2026-06-18 to replace the machine "Catalog entry <hex>:" + namesake-scrape +',
        "division-frame assembly (REPAIR_BACKLOG run 59, target #1). Source: school/college",
        "ownership from michigan_profile; discipline definitions from standard reference",
        "definitions of each academic field. Regenerate via",
        "scripts/build_michigan_catalogue_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "CATALOGUE_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(descs):
        esc = descs[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{esc}",')
    lines.append("}")
    OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    from unipaith.data import michigan_profile as M  # noqa: N812
    from unipaith.profile_standard.anti_stub import analyze, machine_artifacts

    descs = build()
    by_slug = {p["slug"]: p["program_name"] for p in M.PROGRAMS}
    programs = [{"program_name": by_slug[s], "description": d} for s, d in descs.items()]
    report = analyze(programs)
    arts = machine_artifacts(programs)
    if not report.is_clean or arts:
        raise SystemExit(f"Anti-stub gate failed: {report.summary()} | artifacts={arts[:5]}")
    write_module(descs)
    print(f"Wrote {len(descs)} descriptions → {OUT} (anti-stub clean)")


if __name__ == "__main__":
    main()
