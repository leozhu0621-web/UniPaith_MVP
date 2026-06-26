"""Duke University — universal ``who_its_for`` depth field per program.

REPAIR_BACKLOG #4 (SKILL miss #8): a UNIVERSAL depth field that must be filled on EVERY
program AND be PROGRAM-DISTINCT (distinct strings / programs approximately 1.0), never a
degree-type template keyed on credential alone. Each statement names the applicant the
program fits — background/interests, goals/readiness, and the typical next step — derived
strictly from that program's own field and degree level. No fabricated facts (no rankings,
numbers, or named centers), matching the field-specific gold bar (Emory/Brown/Purdue/Rice).
All strings are distinct (distinct/total = 1.0). The bachelor's and the doctoral row of one
field read differently because an A.B. survey and a funded dissertation study different
things — a researched statement says so.
"""

from __future__ import annotations

WHO_BY_SLUG: dict[str, str] = {
    # ── Trinity College of Arts & Sciences — A.B. (bachelor's) ──
    "duke-african-and-african-american-studies-ab": (
        "Undergraduates who want to study the histories, politics, and cultural production of "
        "Africa and the African diaspora, building interdisciplinary grounding for law, public "
        "service, education, or graduate work in the humanities and social sciences."
    ),
    "duke-art-history-ab": (
        "Students drawn to the visual record of human culture who want to learn to read objects, "
        "buildings, and images across periods, preparing for museums, conservation, arts "
        "writing, or graduate study in art history."
    ),
    "duke-visual-arts-ab": (
        "Undergraduates who want to make art — painting, sculpture, photography, or new media — "
        "in a studio-intensive program, building a portfolio for an MFA, a creative career, or "
        "interdisciplinary work that pairs studio practice with another field."
    ),
    "duke-visual-and-media-studies-ab": (
        "Students who want to analyze film, photography, and digital media critically while "
        "producing their own, suited to careers in media, curation, or criticism and to graduate "
        "study in visual culture."
    ),
    "duke-asian-and-middle-eastern-studies-ab": (
        "Undergraduates committed to the languages, literatures, and societies of Asia and the "
        "Middle East who want regional and linguistic depth for diplomacy, business, journalism, "
        "or area-studies graduate work."
    ),
    "duke-biology-ab": (
        "Students fascinated by living systems from molecules to ecosystems who want a broad "
        "laboratory and field foundation, whether they are headed toward medical school, "
        "graduate research, biotechnology, or conservation."
    ),
    "duke-biophysics-ab": (
        "Undergraduates who want to apply physics and quantitative methods to biological "
        "questions, building the interdisciplinary rigor that prepares them for graduate research "
        "in biophysics, medicine, or computational life science."
    ),
    "duke-brazilian-and-global-portuguese-ab": (
        "Students drawn to the Portuguese-speaking world — Brazil, Portugal, and lusophone "
        "Africa — who want language fluency and cultural literacy for careers in international "
        "work, the arts, or graduate study."
    ),
    "duke-chemistry-ab": (
        "Undergraduates curious about how matter reacts and transforms who want hands-on training "
        "across organic, inorganic, and physical chemistry, whether their goal is medical school, "
        "a chemistry PhD, or research in industry."
    ),
    "duke-classical-civilization-ab": (
        "Students captivated by the ancient Greek and Roman worlds who want to study their "
        "literature, history, art, and archaeology in translation, building humanistic depth for "
        "law, teaching, or graduate work."
    ),
    "duke-classical-languages-ab": (
        "Undergraduates who want to read Greek and Latin in the original and engage ancient texts "
        "directly, preparing for graduate study in classics, philology, or careers that reward "
        "rigorous language and analytical training."
    ),
    "duke-computational-media-ab": (
        "Students who want to work where code meets creative media — games, interactive art, and "
        "digital storytelling — building technical and design skills for careers in media "
        "technology or further study at the art-and-computing boundary."
    ),
    "duke-computer-science-ab": (
        "Undergraduates who enjoy problem-solving with code and want a foundation across "
        "algorithms, systems, and theory, preparing for software engineering, technical roles in "
        "any industry, or graduate study in computing."
    ),
    "duke-cultural-anthropology-ab": (
        "Students curious about how people make meaning across societies who want ethnographic "
        "and theoretical training to study culture, power, and difference, useful for global "
        "careers, public service, or graduate anthropology."
    ),
    "duke-dance-ab": (
        "Undergraduates who want to study dance as both performance and scholarship — technique, "
        "choreography, and history together — preparing for performance, arts education, or "
        "interdisciplinary work in the body and movement."
    ),
    "duke-earth-and-climate-sciences-ab": (
        "Students who want to understand how the Earth and its climate work, from deep-time "
        "geology to present-day climate change, building fieldwork and data skills for "
        "environmental, energy, or geoscience careers and graduate study."
    ),
    "duke-economics-ab": (
        "Undergraduates who want to analyze how individuals, firms, and markets make decisions "
        "using theory and data, preparing for finance, consulting, policy, or graduate study in "
        "economics and the social sciences."
    ),
    "duke-english-ab": (
        "Students who love close reading and clear writing and want to study literature across "
        "periods and genres, building interpretive and analytical skills for law, publishing, "
        "education, or graduate work in English."
    ),
    "duke-environmental-sciences-and-policy-ab": (
        "Undergraduates motivated by environmental challenges who want to pair natural-science "
        "grounding with policy analysis, preparing for environmental management, advocacy, or "
        "graduate study spanning science and governance."
    ),
    "duke-evolutionary-anthropology-ab": (
        "Students interested in human and primate evolution, anatomy, and behavior who want a "
        "biological-anthropology foundation for research, medicine, or graduate study in human "
        "biology and evolution."
    ),
    "duke-french-and-francophone-studies-ab": (
        "Undergraduates who want fluency in French and deep engagement with the literatures and "
        "cultures of France and the francophone world, suited to international careers, the arts, "
        "or graduate study."
    ),
    "duke-gender-sexuality-and-feminist-studies-ab": (
        "Students who want to analyze gender and sexuality across culture, politics, and history "
        "through feminist and queer theory, building critical grounding for law, advocacy, health, "
        "or graduate work in the humanities and social sciences."
    ),
    "duke-german-ab": (
        "Undergraduates drawn to the German language and to German thought, literature, and film "
        "who want cultural and linguistic depth for careers in international work, the arts, or "
        "graduate study."
    ),
    "duke-global-cultural-studies-ab": (
        "Students who want to read literature and culture across borders and languages through "
        "critical theory, building comparative and analytical skills for the arts, media, or "
        "graduate work in cultural studies."
    ),
    "duke-global-health-ab": (
        "Undergraduates committed to health equity who want to study the biological, social, and "
        "policy dimensions of health worldwide, preparing for medicine, public health, or careers "
        "addressing global health disparities."
    ),
    "duke-history-ab": (
        "Students who want to investigate the past through evidence and argument across regions "
        "and eras, building research and writing skills for law, public service, education, or "
        "graduate study in history."
    ),
    "duke-international-comparative-studies-ab": (
        "Undergraduates focused on global affairs who want to combine regional expertise, "
        "language, and comparative analysis of politics and culture, preparing for diplomacy, "
        "international development, or graduate work."
    ),
    "duke-italian-and-european-studies-ab": (
        "Students drawn to Italy and modern Europe who want to pair Italian fluency with the "
        "study of European history, art, and politics, suited to international careers, the arts, "
        "or graduate study."
    ),
    "duke-linguistics-ab": (
        "Undergraduates fascinated by how language works — its sounds, structure, and meaning — "
        "who want analytical training in linguistic theory and data, preparing for careers in "
        "technology, education, or graduate study in linguistics."
    ),
    "duke-marine-science-and-conservation-ab": (
        "Students passionate about oceans and coastal ecosystems who want field and laboratory "
        "training in marine biology and conservation, preparing for environmental work, policy, "
        "or graduate research in marine science."
    ),
    "duke-mathematics-ab": (
        "Undergraduates who love rigorous proof and abstract structure and want a strong "
        "foundation in pure and applied mathematics, whether they aim for graduate study, "
        "quantitative careers, or further work in the sciences."
    ),
    "duke-medieval-and-renaissance-studies-ab": (
        "Students captivated by the European Middle Ages and Renaissance who want "
        "interdisciplinary study of their literature, art, religion, and history, building "
        "humanistic depth for "
        "teaching, museums, or graduate work."
    ),
    "duke-music-ab": (
        "Undergraduates who want to study music as performer, composer, and scholar — theory, "
        "history, and practice together — preparing for performance, arts careers, or graduate "
        "study in music."
    ),
    "duke-neuroscience-ab": (
        "Students fascinated by the brain and behavior who want an interdisciplinary foundation "
        "spanning molecular, systems, and cognitive neuroscience, preparing for medicine, "
        "graduate research, or careers in the neural sciences."
    ),
    "duke-philosophy-ab": (
        "Undergraduates who enjoy rigorous argument about knowledge, ethics, and reality who want "
        "training in logic and the history of ideas, building analytical skills for law, policy, "
        "or graduate study in philosophy."
    ),
    "duke-physics-ab": (
        "Students driven to understand nature's fundamental laws who want a rigorous foundation in "
        "classical and modern physics, preparing for graduate research, engineering, or "
        "quantitative technical careers."
    ),
    "duke-political-science-ab": (
        "Undergraduates who want to analyze government, institutions, and political behavior using "
        "theory and data, preparing for law, public service, policy, or graduate study in "
        "political science."
    ),
    "duke-psychology-ab": (
        "Students curious about mind and behavior who want a scientific foundation in cognition, "
        "development, and social psychology, preparing for careers in health, business, or "
        "education and for graduate study in psychology."
    ),
    "duke-public-policy-studies-ab": (
        "Undergraduates who want to understand and shape public decisions, combining economics, "
        "politics, ethics, and analysis, preparing for government, nonprofits, law, or graduate "
        "study in policy."
    ),
    "duke-religious-studies-ab": (
        "Students who want to study the world's religious traditions, texts, and practices "
        "analytically and comparatively, building humanistic and cross-cultural literacy for law, "
        "service, or graduate work."
    ),
    "duke-romance-studies-ab": (
        "Undergraduates drawn to the Romance languages and their literatures who want comparative "
        "study across French, Italian, Spanish, and Portuguese traditions, suited to "
        "international careers or graduate study."
    ),
    "duke-russian-ab": (
        "Students who want fluency in Russian and engagement with Russian literature, history, and "
        "culture, preparing for international work, journalism, security, or graduate study in "
        "Slavic fields."
    ),
    "duke-slavic-and-eurasian-studies-ab": (
        "Undergraduates focused on Russia, Eastern Europe, and Eurasia who want interdisciplinary "
        "regional study with language, preparing for diplomacy, security, journalism, or graduate "
        "work on the region."
    ),
    "duke-spanish-latin-american-and-latino-a-studies-ab": (
        "Students who want Spanish fluency and deep study of the cultures of Spain, Latin America, "
        "and U.S. Latino/a communities, suited to careers in education, health, public service, "
        "or graduate study."
    ),
    "duke-sociology-ab": (
        "Undergraduates who want to analyze how societies, institutions, and inequality shape "
        "human life, building research and data skills for careers in policy, business, law, or "
        "graduate study in sociology."
    ),
    "duke-statistical-science-ab": (
        "Undergraduates who want to turn data into evidence, learning probability, modeling, and "
        "statistical computing, preparing for data-science roles, quantitative careers, or "
        "graduate study in statistics."
    ),
    "duke-theater-studies-ab": (
        "Students who want to study theater as artists and scholars — acting, directing, design, "
        "and dramatic literature together — preparing for the stage, arts careers, or graduate "
        "work in theater."
    ),
    "duke-data-science-mathematics-and-computer-science-ab": (
        "Undergraduates who want the mathematical and computational core of data science, "
        "combining rigorous math with programming and algorithms, preparing for data-intensive "
        "careers or graduate study in quantitative fields."
    ),
    "duke-linguistics-and-computer-science-ab": (
        "Students drawn to language and computation alike who want to study linguistic structure "
        "and build the programming skills behind natural-language technology, preparing for work "
        "in computational linguistics or graduate study."
    ),
    "duke-program-ii-self-designed-major-ab": (
        "Intellectually independent undergraduates whose interests cross departmental lines and "
        "who want to design and pursue their own coherent interdisciplinary course of study "
        "toward a self-defined academic or professional goal."
    ),
    # ── Pratt School of Engineering — B.S.E. ──
    "duke-biomedical-engineering-bse": (
        "Undergraduates who want to engineer solutions to problems in medicine and biology — "
        "devices, imaging, biomaterials — combining engineering rigor with the life sciences for "
        "careers in medtech, research, or medical school."
    ),
    "duke-civil-engineering-bse": (
        "Students who want to design and build the infrastructure people depend on — structures, "
        "transportation, and water systems — preparing for engineering practice, licensure, or "
        "graduate study in civil engineering."
    ),
    "duke-electrical-and-computer-engineering-bse": (
        "Undergraduates fascinated by electronics, computing hardware, and signals who want a "
        "foundation spanning circuits, systems, and software, preparing for engineering roles in "
        "technology or graduate study."
    ),
    "duke-environmental-engineering-bse": (
        "Students who want to engineer cleaner water, air, and energy systems, applying chemistry "
        "and engineering to environmental challenges, preparing for environmental engineering "
        "practice or graduate study."
    ),
    "duke-mechanical-engineering-bse": (
        "Undergraduates drawn to how machines and energy systems work who want a foundation in "
        "mechanics, thermodynamics, and design, preparing for engineering careers across "
        "industries or graduate study."
    ),
    "duke-interdisciplinary-engineering-and-applied-science-ideas-bse": (
        "Students who want to define an engineering path that crosses traditional disciplines, "
        "pairing a strong engineering core with a self-designed concentration aimed at an "
        "emerging or interdisciplinary problem area."
    ),
    # ── The Fuqua School of Business ──
    "duke-daytime-mba-ms": (
        "Early- and mid-career professionals who want a full-time, immersive MBA to pivot or "
        "accelerate into general management, consulting, finance, or technology leadership, with "
        "an emphasis on collaborative, team-based learning."
    ),
    "duke-accelerated-daytime-mba-ms": (
        "Candidates who already hold a graduate business or quantitative degree and want to earn "
        "the full-time MBA on a compressed timeline, moving quickly into management roles without "
        "repeating foundational coursework."
    ),
    "duke-weekend-executive-mba-ms": (
        "Experienced working managers who want to earn an MBA without leaving their jobs, "
        "attending in a weekend format designed to apply leadership and strategy learning "
        "immediately within their current organizations."
    ),
    "duke-master-of-management-studies-foundations-of-business-ms": (
        "Recent graduates from non-business backgrounds who want a one-year foundation in core "
        "business skills — accounting, finance, marketing, and analytics — to launch into "
        "early-career analyst and associate roles."
    ),
    "duke-master-in-business-climate-and-sustainability-mbcs-ms": (
        "Professionals and recent graduates who want to lead at the intersection of business and "
        "the climate transition, building management skills focused on sustainability strategy, "
        "decarbonization, and the green economy."
    ),
    "duke-master-of-quantitative-management-business-analytics-ms": (
        "Analytically minded recent graduates who want to translate data into business decisions, "
        "building skills in statistics, modeling, and analytics for careers as data-driven "
        "analysts and consultants."
    ),
    "duke-msqm-business-analytics-online-ms": (
        "Working professionals who want to earn a quantitative business-analytics credential "
        "online while employed, strengthening their data and decision-modeling skills without "
        "pausing their careers."
    ),
    "duke-msqm-health-analytics-online-ms": (
        "Healthcare professionals and analysts who want to apply business analytics specifically "
        "to health systems and data, building online the quantitative skills to improve care "
        "delivery, operations, and outcomes."
    ),
    "duke-phd-in-business-administration-phd": (
        "Scholars aiming for research and faculty careers in management who want funded doctoral "
        "training in a business discipline — finance, marketing, operations, strategy, or "
        "organizational behavior — culminating in original research."
    ),
    # ── Duke University School of Law ──
    "duke-juris-doctor-jd-prof": (
        "Aspiring lawyers who want a rigorous professional legal education preparing them for the "
        "bar and for practice across litigation, transactional, public-interest, and policy "
        "careers."
    ),
    "duke-master-of-laws-llm-ms": (
        "Lawyers trained outside the United States who want a one-year graduate degree in U.S. and "
        "international law to deepen expertise, qualify for bar examinations, or advance global "
        "legal careers."
    ),
    "duke-jd-llm-in-international-and-comparative-law-prof": (
        "Law students who want to combine the J.D. with focused graduate training in international "
        "and comparative law, preparing for cross-border practice, diplomacy, or global "
        "public-interest work."
    ),
    "duke-jd-llm-in-law-and-entrepreneurship-prof": (
        "Law students who want to pair the J.D. with training at the intersection of law and "
        "business formation, preparing to advise startups, venture investors, and entrepreneurs."
    ),
    "duke-doctor-of-juridical-science-sjd-phd": (
        "Experienced legal scholars, typically with an LL.M., who want the law school's most "
        "advanced research degree to produce a substantial dissertation and pursue academic legal "
        "careers."
    ),
    "duke-master-of-judicial-studies-mjs-ms": (
        "Sitting judges who want a graduate degree grounded in social-science research methods to "
        "strengthen their analysis of the law, courts, and judicial decision-making."
    ),
    # ── Duke University School of Medicine ──
    "duke-doctor-of-medicine-md-prof": (
        "Students committed to becoming physicians who want a medical education that pairs early "
        "clinical training with a dedicated year of scholarly research, preparing for residency "
        "and academic medicine."
    ),
    "duke-medical-scientist-training-program-md-phd-phd": (
        "Aspiring physician-scientists who want combined, funded M.D.–Ph.D. training to lead "
        "careers bridging laboratory research and clinical medicine in academic and translational "
        "settings."
    ),
    "duke-doctor-of-physical-therapy-dpt-prof": (
        "Students who want to become licensed physical therapists, seeking clinical doctoral "
        "training in movement science, rehabilitation, and patient care across the lifespan."
    ),
    "duke-occupational-therapy-doctorate-otd-prof": (
        "Students preparing to become occupational therapists who want entry-level doctoral "
        "training to help people of all abilities participate in the daily activities that matter "
        "to them."
    ),
    "duke-physician-assistant-program-mhs-ms": (
        "Health-focused candidates who want to become physician assistants through the "
        "profession's founding model of training, preparing for team-based clinical practice "
        "across medical "
        "specialties."
    ),
    "duke-master-of-biomedical-sciences-mbs-ms": (
        "Recent graduates strengthening their candidacy for medical or health-professional school "
        "who want a focused master's in foundational biomedical sciences and academic skills."
    ),
    "duke-master-of-biostatistics-ms": (
        "Quantitatively minded graduates who want to design and analyze biomedical and clinical "
        "studies, building statistical and computing skills for careers in research, pharma, or "
        "public health."
    ),
    "duke-master-of-health-sciences-in-clinical-research-online-ms": (
        "Practicing clinicians and research staff who want online training in clinical-research "
        "design, biostatistics, and trial methods to lead or contribute to patient-centered "
        "studies while working."
    ),
    "duke-master-of-science-in-medical-physics-ms": (
        "Physics and engineering graduates who want to apply physics to medicine — imaging, "
        "radiation therapy, and dosimetry — preparing for clinical medical-physics practice and "
        "board certification."
    ),
    "duke-master-of-science-in-population-health-sciences-ms": (
        "Health professionals and graduates who want to study the drivers of health across "
        "populations, building epidemiologic and analytic skills for research, policy, or "
        "health-system improvement."
    ),
    "duke-master-of-management-in-clinical-informatics-mmci-ms": (
        "Clinicians and health-IT professionals who want to lead the use of data and information "
        "systems in healthcare, combining management and informatics to improve care delivery and "
        "operations."
    ),
    # ── Duke University School of Nursing ──
    "duke-master-of-nursing-mn-pre-licensure-ms": (
        "Career-changers with a bachelor's in another field who want an accelerated path to become "
        "registered nurses, earning licensure-eligible nursing preparation at the master's level."
    ),
    "duke-master-of-science-in-nursing-msn-ms": (
        "Registered nurses who want to advance into specialized and advanced-practice roles — "
        "nurse practitioner, leadership, or informatics — building graduate clinical and "
        "systems expertise."
    ),
    "duke-doctor-of-nursing-practice-dnp-prof": (
        "Advanced-practice nurses who want the terminal practice doctorate to lead evidence-based "
        "improvement of patient care, translating research into clinical and health-system "
        "practice."
    ),
    "duke-doctor-of-nursing-practice-nurse-anesthesia-prof": (
        "Critical-care registered nurses who want doctoral preparation to become certified "
        "registered nurse anesthetists, mastering the science and practice of anesthesia care."
    ),
    "duke-phd-in-nursing-phd": (
        "Nurses aiming for research and faculty careers who want funded doctoral training to "
        "generate nursing science, conducting original research on health, care, and outcomes."
    ),
    # ── Nicholas School of the Environment ──
    "duke-master-of-environmental-management-mem-ms": (
        "Graduates and professionals who want to manage environmental problems with science and "
        "policy together — from ecosystems to energy and climate — preparing for careers in "
        "agencies, NGOs, and the private sector."
    ),
    "duke-master-of-forestry-mf-ms": (
        "Students focused on forests and natural-resource management who want professional "
        "training in forest ecology, silviculture, and policy for careers managing forested "
        "landscapes."
    ),
    "duke-duke-environmental-leadership-mem-del-mem-online-ms": (
        "Mid-career environmental professionals who want to earn the environmental-management "
        "master's largely online while working, building leadership and policy skills without "
        "leaving their jobs."
    ),
    # ── Sanford School of Public Policy ──
    "duke-master-of-public-policy-mpp-ms": (
        "Aspiring policy analysts who want rigorous training in economics, statistics, and policy "
        "analysis to design and evaluate programs in government, nonprofits, and the private "
        "sector."
    ),
    "duke-master-of-international-development-policy-midp-ms": (
        "Professionals working on global development who want graduate training in development "
        "economics and policy to lead programs addressing poverty, governance, and growth in "
        "lower- and middle-income countries."
    ),
    "duke-master-of-public-affairs-mpa-ms": (
        "Experienced practitioners who want a flexible public-affairs master's to sharpen "
        "leadership, analysis, and management skills for advancement in public-service and "
        "mission-driven organizations."
    ),
    "duke-master-of-national-security-policy-mnsp-ms": (
        "Professionals and graduates focused on security who want specialized policy training in "
        "defense, intelligence, and international security to advance in national-security "
        "careers."
    ),
    # ── Duke Divinity School ──
    "duke-master-of-divinity-mdiv-ms": (
        "Candidates preparing for ordained ministry and pastoral leadership who want comprehensive "
        "theological, biblical, and practical formation for service in churches and communities."
    ),
    "duke-master-of-theological-studies-mts-ms": (
        "Students who want rigorous academic study of theology and religion — as preparation for "
        "doctoral work, teaching, or informed lay leadership — without a primary focus on "
        "ordination."
    ),
    "duke-master-of-arts-in-christian-practice-ms": (
        "Working ministers and lay leaders who want graduate study connecting theology to "
        "practice, deepening their vocation in congregational, nonprofit, or community settings."
    ),
    "duke-master-of-theology-thm-ms": (
        "Students who already hold a theological degree and want a year of advanced, focused study "
        "in a chosen area as a bridge to doctoral work or specialized ministry."
    ),
    "duke-doctor-of-ministry-dmin-prof": (
        "Experienced ministry leaders who want a professional doctorate to strengthen their "
        "practice through advanced theological reflection and a project rooted in their own "
        "ministry context."
    ),
    "duke-doctor-of-theology-thd-phd": (
        "Scholars called to theological research and teaching who want a funded research doctorate "
        "integrating academic theology with the life and practices of the church."
    ),
    # ── Pratt School of Engineering — professional master's ──
    "duke-master-of-engineering-in-ai-for-product-innovation-ms": (
        "Engineers and technical graduates who want to build and deploy machine-learning–driven "
        "products, pairing applied AI skills with management and innovation training for "
        "industry roles."
    ),
    "duke-master-of-science-in-biomedical-engineering-ms": (
        "Engineering and science graduates who want advanced, research-oriented training in "
        "biomedical engineering — devices, imaging, or biomaterials — preparing for industry R&D "
        "or doctoral study."
    ),
    "duke-master-of-engineering-in-civil-engineering-ms": (
        "Civil-engineering graduates who want a practice-focused master's to deepen technical "
        "expertise in structures, environment, or infrastructure and advance toward professional "
        "leadership."
    ),
    "duke-master-of-science-in-electrical-and-computer-engineering-ms": (
        "Electrical- and computer-engineering graduates who want advanced study in areas such as "
        "signal processing, hardware, or machine learning, preparing for technical industry roles "
        "or a PhD."
    ),
    "duke-master-of-engineering-management-ms": (
        "Engineers and scientists who want to move into technical leadership, pairing their "
        "technical foundation with management, finance, and product skills for roles managing "
        "people and projects."
    ),
    "duke-master-of-engineering-in-cybersecurity-ms": (
        "Computing and engineering graduates who want applied training in securing systems, "
        "networks, and data, preparing for cybersecurity engineering and security-leadership "
        "roles."
    ),
    "duke-master-of-engineering-in-financial-technology-ms": (
        "Quantitatively strong graduates who want to work at the intersection of finance and "
        "engineering, building the computing and modeling skills behind modern financial "
        "technology."
    ),
    "duke-master-of-science-in-mechanical-engineering-and-materials-science-ms": (
        "Mechanical-engineering and materials graduates who want advanced study in mechanics, "
        "energy, or materials, preparing for industry research and development or doctoral work."
    ),
    # ── The Graduate School — Ph.D. (biomedical) ──
    "duke-biochemistry-grad-phd": (
        "Scientists who want funded doctoral research on the molecular machinery of life — protein "
        "structure, enzymes, and metabolism — preparing for careers in academic, biotech, or "
        "pharmaceutical research."
    ),
    "duke-biology-grad-phd": (
        "Researchers who want a funded biology doctorate to pursue original investigation across "
        "organisms and systems, from genetics to ecology, toward faculty or research careers."
    ),
    "duke-biostatistics-grad-phd": (
        "Quantitative scientists who want doctoral training to develop statistical methods for "
        "biomedical research, preparing for faculty, industry, or research-leadership careers in "
        "biostatistics."
    ),
    "duke-cell-and-molecular-biology-grad-phd": (
        "Scientists who want funded doctoral research on how cells function at the molecular "
        "level, from signaling to gene regulation, toward careers in biomedical research."
    ),
    "duke-cell-biology-grad-phd": (
        "Researchers focused on the architecture and behavior of cells who want doctoral training "
        "in cell biology — membranes, organelles, and cell division — for academic or industry "
        "research careers."
    ),
    "duke-cognitive-neuroscience-grad-phd": (
        "Scientists who want to study how the brain gives rise to perception, memory, and "
        "decision-making, pursuing funded doctoral research bridging neuroscience and cognition."
    ),
    "duke-computational-biology-and-bioinformatics-grad-phd": (
        "Quantitatively skilled researchers who want to use computation and large biological data "
        "to answer questions in genomics and systems biology, toward careers in computational "
        "life science."
    ),
    "duke-developmental-and-stem-cell-biology-grad-phd": (
        "Scientists fascinated by how organisms build and renew themselves who want funded "
        "doctoral research in development and stem-cell biology for academic or "
        "regenerative-medicine "
        "careers."
    ),
    "duke-ecology-grad-phd": (
        "Researchers who want doctoral training to study how organisms interact with each other "
        "and their environment, pursuing field and quantitative research toward careers in "
        "ecology and conservation."
    ),
    "duke-genetics-and-genomics-grad-phd": (
        "Scientists who want funded doctoral research on heredity and genome function across "
        "organisms, using genetic and genomic tools toward careers in research and medicine."
    ),
    "duke-immunology-grad-phd": (
        "Researchers drawn to how the immune system defends and misfires who want doctoral "
        "training in immunology toward careers in academic, biotech, or therapeutic research."
    ),
    "duke-integrated-toxicology-and-environmental-health-grad-phd": (
        "Scientists who want to study how environmental exposures affect biological systems and "
        "health, pursuing funded doctoral research bridging toxicology and environmental health."
    ),
    "duke-molecular-cancer-biology-grad-phd": (
        "Researchers focused on the molecular basis of cancer who want funded doctoral training in "
        "tumor biology and signaling toward careers advancing cancer research and therapy."
    ),
    "duke-molecular-genetics-and-microbiology-grad-phd": (
        "Scientists drawn to microbes and gene function who want doctoral research in molecular "
        "genetics and microbiology — from pathogens to host interactions — for research careers."
    ),
    "duke-neurobiology-grad-phd": (
        "Researchers who want funded doctoral training to study the nervous system from molecules "
        "to circuits, pursuing experimental neuroscience toward academic or research careers."
    ),
    "duke-pharmacology-grad-phd": (
        "Scientists interested in how drugs act on biological systems who want doctoral research "
        "in pharmacology and drug discovery toward academic, biotech, or pharmaceutical careers."
    ),
    "duke-population-health-sciences-grad-phd": (
        "Researchers who want funded doctoral training to study health determinants and outcomes "
        "across populations, developing epidemiologic and analytic methods for academic or policy "
        "research."
    ),
    "duke-medical-physics-grad-phd": (
        "Physicists who want doctoral research applying physics to medical imaging and radiation "
        "therapy, preparing for research and clinical-academic careers in medical physics."
    ),
    # ── The Graduate School — Ph.D. (humanities) ──
    "duke-art-art-history-and-visual-studies-grad-phd": (
        "Scholars who want funded doctoral training in the history and theory of art and visual "
        "culture, pursuing original research toward careers in academia, museums, or curation."
    ),
    "duke-classical-studies-grad-phd": (
        "Researchers devoted to the ancient Mediterranean who want doctoral study of Greek and "
        "Latin texts, history, and material culture toward scholarly and teaching careers in "
        "classics."
    ),
    "duke-english-grad-phd": (
        "Scholars of literature who want funded doctoral training in literary history, theory, and "
        "criticism, producing original research toward faculty careers in English."
    ),
    "duke-german-studies-grad-phd": (
        "Researchers in German thought, literature, and culture who want doctoral study and "
        "original scholarship toward academic careers in German studies and the humanities."
    ),
    "duke-literature-grad-phd": (
        "Scholars drawn to comparative literature and critical theory who want funded doctoral "
        "training across languages and media toward research and teaching careers in the "
        "humanities."
    ),
    "duke-music-grad-phd": (
        "Researchers and composers who want doctoral study in musicology, theory, ethnomusicology, "
        "or composition, pursuing original scholarship or creative work toward academic careers."
    ),
    "duke-philosophy-grad-phd": (
        "Scholars who want funded doctoral training in rigorous philosophical research across "
        "areas such as ethics, metaphysics, and the history of philosophy, toward faculty "
        "careers."
    ),
    "duke-religion-grad-phd": (
        "Researchers who want doctoral study of religious traditions, texts, and practices using "
        "humanistic and social-scientific methods, toward scholarly and teaching careers in "
        "religion."
    ),
    "duke-romance-studies-grad-phd": (
        "Scholars of the Romance languages and their literatures who want funded doctoral training "
        "and original research across French, Italian, Spanish, and lusophone traditions toward "
        "academic careers."
    ),
    # ── The Graduate School — Ph.D. (natural sciences) ──
    "duke-chemistry-grad-phd": (
        "Scientists who want funded doctoral research across organic, inorganic, physical, and "
        "biological chemistry, producing original work toward academic, government, or industry "
        "research careers."
    ),
    "duke-computer-science-grad-phd": (
        "Researchers who want a funded computer-science doctorate to pursue original work in areas "
        "such as AI, theory, systems, and security toward academic and industry-research careers."
    ),
    "duke-earth-and-climate-sciences-grad-phd": (
        "Scientists who want doctoral research on Earth systems and climate, from geology to "
        "atmospheric and ocean processes, toward academic, government, or environmental research "
        "careers."
    ),
    "duke-marine-science-and-conservation-grad-phd": (
        "Researchers committed to oceans and coastal systems who want funded doctoral training in "
        "marine science and conservation toward academic, agency, or NGO research careers."
    ),
    "duke-materials-science-and-engineering-grad-phd": (
        "Engineers and scientists who want doctoral research designing and understanding new "
        "materials, from electronics to biomaterials, toward research-and-development careers."
    ),
    "duke-mathematics-grad-phd": (
        "Mathematicians who want a funded doctorate to pursue original research in pure or applied "
        "mathematics toward academic, government, or quantitative-industry careers."
    ),
    "duke-physics-grad-phd": (
        "Physicists who want funded doctoral research across areas such as condensed matter, "
        "high-energy, and biophysics, producing original work toward academic and research "
        "careers."
    ),
    "duke-statistical-science-grad-phd": (
        "Researchers who want doctoral training to develop statistical theory and methods, "
        "including Bayesian and computational approaches, toward faculty or research-science "
        "careers."
    ),
    # ── The Graduate School — Ph.D. (engineering) ──
    "duke-biomedical-engineering-grad-phd": (
        "Engineers who want funded doctoral research at the interface of engineering and medicine "
        "— devices, imaging, and biomaterials — toward academic or industry research careers."
    ),
    "duke-civil-and-environmental-engineering-grad-phd": (
        "Engineers who want doctoral research on infrastructure and environmental systems, from "
        "structures to water and sustainability, toward academic, agency, or industry research "
        "careers."
    ),
    "duke-electrical-and-computer-engineering-grad-phd": (
        "Engineers who want a funded ECE doctorate to pursue original research in areas such as "
        "signals, hardware, photonics, or machine learning toward research careers."
    ),
    "duke-mechanical-engineering-and-materials-science-grad-phd": (
        "Engineers who want doctoral research in mechanics, energy, dynamics, or materials, "
        "producing original work toward academic and advanced-industry research careers."
    ),
    # ── The Graduate School — Ph.D. (social sciences) ──
    "duke-cultural-anthropology-grad-phd": (
        "Scholars who want funded doctoral training in ethnographic and theoretical research on "
        "culture, power, and difference, toward academic and applied research careers in "
        "anthropology."
    ),
    "duke-economics-grad-phd": (
        "Researchers who want a funded economics doctorate to develop theory and empirical methods "
        "across micro, macro, and applied fields toward academic, policy, or research careers."
    ),
    "duke-environmental-policy-grad-phd": (
        "Researchers who want doctoral training combining environmental science with policy and "
        "economics, producing original work on environmental governance toward academic and "
        "policy-research careers."
    ),
    "duke-history-grad-phd": (
        "Scholars who want funded doctoral training in archival and interpretive historical "
        "research across regions and periods, producing original scholarship toward faculty "
        "careers."
    ),
    "duke-political-science-grad-phd": (
        "Researchers who want a funded political-science doctorate to study institutions, "
        "behavior, and international relations with theory and data toward academic and research "
        "careers."
    ),
    "duke-psychology-and-neuroscience-grad-phd": (
        "Scientists who want funded doctoral research on mind, brain, and behavior spanning "
        "cognitive, developmental, social, and systems approaches, toward academic and research "
        "careers."
    ),
    "duke-sociology-grad-phd": (
        "Researchers who want doctoral training to study social structure, networks, and "
        "inequality with rigorous methods, producing original research toward academic and "
        "applied careers in sociology."
    ),
}
