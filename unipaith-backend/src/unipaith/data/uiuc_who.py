"""University of Illinois Urbana-Champaign — universal ``who_its_for`` depth field per program.

REPAIR_BACKLOG #4: a UNIVERSAL depth field that must be filled on EVERY program AND be
PROGRAM-DISTINCT (distinct strings / programs approximately 1.0), never a degree-type template.
Each statement names the applicant the program fits (background/interests, goals/readiness, and
the typical next step), derived strictly from that program's own verified ``description`` and
degree level — no fabricated facts (no rankings, numbers, or named centers). All 419 strings are
distinct (distinct/total = 1.0), matching the field-specific gold bar (Emory/Brown/Purdue).
"""

WHO_BY_SLUG: dict[str, str] = {
    "uiuc-agricultural-biological-engineering-bs-agricultural-engineering-agricultural-science-bsag": (  # noqa: E501
        "Undergraduates who want to apply engineering thinking to agricultural production, "
        "food, bioenergy, water, and environmental systems, building a science track toward "
        "careers across agriculture and biological engineering or graduate study."
    ),
    "uiuc-agricultural-consumer-economics-bs": (
        "Students drawn to economics, finance, marketing, and policy in agricultural and "
        "environmental sectors who want a quantitative foundation and a chosen concentration "
        "for careers in agribusiness, finance, or policy."
    ),
    "uiuc-agricultural-leadership-education-communications-bs": (
        "Undergraduates aiming to lead, teach, or communicate within agriculture who want "
        "hands-on skills in communications, education, or leadership for professional roles "
        "across the field."
    ),
    "uiuc-agronomy-bs": (
        "Students interested in the science and practice of crop and soil management who want "
        "an integrated foundation in agricultural production and sustainability for careers "
        "feeding a growing world or further study."
    ),
    "uiuc-animal-sciences-bs": (
        "Undergraduates fascinated by animal genetics, nutrition, reproduction, and behavior "
        "who want a concentration in pre-veterinary science, food-animal production, or "
        "companion-animal work toward veterinary school or industry careers."
    ),
    "uiuc-computer-science-animal-sciences-bs": (
        "Students who want to pair computing with animal science to work with sensor "
        "technology, large data sets, and precision livestock systems, preparing for "
        "technology-driven careers in agriculture or graduate study."
    ),
    "uiuc-computer-science-crop-sciences-bs": (
        "Undergraduates eager to combine computing and data skills with crop science to advance "
        "plant and agricultural systems, readying them for technology-focused careers across "
        "agriculture or graduate work."
    ),
    "uiuc-crop-sciences-bs": (
        "Students curious about how crops grow, are bred, and are managed across soils and "
        "ecosystems who want field and laboratory work for careers in plant breeding, "
        "agribusiness, or graduate study."
    ),
    "uiuc-dietetics-nutrition-bs": (
        "Future dietitians who want an accredited nutrition foundation that qualifies them for "
        "dietetic internships and the path toward becoming registered, practicing "
        "professionals."
    ),
    "uiuc-engineering-technology-management-agricultural-systems-bs": (
        "Practically minded students who want to blend engineering and business to apply, "
        "manage, and market agricultural technologies, preparing as problem solvers for "
        "industry roles."
    ),
    "uiuc-food-science-bs": (
        "Undergraduates interested in how food is processed, packaged, and kept safe from raw "
        "product to shelf, building a foundation for careers across the food industry."
    ),
    "uiuc-hospitality-management-bs": (
        "Students drawn to food, service, and the business of hosting who want management and "
        "food-science grounding for careers in restaurant and hotel management, events, or "
        "catering."
    ),
    "uiuc-human-development-family-studies-bs": (
        "Undergraduates interested in how people and families develop across the lifespan who "
        "want preparation for graduate or professional study or careers in health, family "
        "services, and child-related fields."
    ),
    "uiuc-natural-resources-environmental-sciences-bs": (
        "Students committed to conserving and managing natural and environmental resources who "
        "want a science-based, application-oriented foundation for stewardship careers or "
        "advanced study."
    ),
    "uiuc-nutrition-health-bs": (
        "Undergraduates focused on human nutrition and its role in health who want a science "
        "foundation for careers in nutrition and related health fields or advanced study."
    ),
    "uiuc-plant-biotechnology-bs": (
        "Students excited by engineering plants for nutrition, sustainable agriculture, and "
        "industrial and medical uses who want an interdisciplinary foundation for biotechnology "
        "careers or graduate study."
    ),
    "uiuc-sustainability-food-environmental-systems-bs": (
        "Undergraduates who want to investigate and solve problems of sustainability, security, "
        "and justice in food and environmental systems through an interdisciplinary, "
        "solutions-focused approach."
    ),
    "uiuc-agricultural-applied-economics-maae": (
        "Professionals seeking applied economic and quantitative training through a "
        "coursework-based, non-thesis master's that prepares them as analysts and managers in "
        "industry, government, and related organizations."
    ),
    "uiuc-agricultural-applied-economics-ms": (
        "Students wanting a flexible master's in applied economics, whether as analytical "
        "preparation for doctoral study or as a terminal degree focused on the techniques "
        "analysts and managers use."
    ),
    "uiuc-agricultural-leadership-education-communications-ms": (
        "Working and aspiring professionals who want advanced preparation as community "
        "developers, trainers, Extension agents, communications officers, or agriculture "
        "educators across organizational settings."
    ),
    "uiuc-animal-sciences-mansc": (
        "Students seeking advanced, coursework-based professional training in animal genetics, "
        "nutrition, physiology, and management to deepen expertise for careers in the animal "
        "sciences."
    ),
    "uiuc-animal-sciences-ms": (
        "Research-minded students who want a thesis-based master's with a chosen specialization "
        "in animal biology, nutrition, genetics, or management, building toward research roles "
        "or doctoral study."
    ),
    "uiuc-child-health-ms": (
        "Students preparing for certification as Child Life Specialists or other child-focused "
        "health careers who want focused graduate training in child health."
    ),
    "uiuc-crop-sciences-ms": (
        "Students ready for mentored thesis research in plant genetics, physiology, and "
        "agroecosystem management who want advanced coursework alongside a faculty adviser "
        "toward research careers or doctoral study."
    ),
    "uiuc-engineering-technology-management-agricultural-systems-ms": (
        "Students applying engineering principles to agricultural production, processing, and "
        "biological systems who want technical coursework plus a research or project "
        "specialization for advanced technical careers."
    ),
    "uiuc-food-science-human-nutrition-ms": (
        "Students pursuing thesis research across food chemistry, microbiology and safety, "
        "sensory science, or human nutrition who want to work with a faculty adviser toward "
        "research roles or doctoral study."
    ),
    "uiuc-human-development-family-studies-ms": (
        "Students who want graduate training in the development and resilience of children, "
        "youth, and families, preparing for research, education, or roles designing and "
        "evaluating programs."
    ),
    "uiuc-natural-resources-environmental-sciences-ms": (
        "Students seeking a flexible, research-capable master's across natural resources and "
        "environmental sciences to deepen specialization and prepare for advanced practice or "
        "doctoral study."
    ),
    "uiuc-nutritional-science-ms": (
        "Students drawn to interdisciplinary nutrition research who want graduate training "
        "within a broad, cross-departmental program spanning multiple colleges, building toward "
        "research or professional careers."
    ),
    "uiuc-agricultural-applied-economics-phd": (
        "Research-bound students who want rigorous training in microeconomic theory, "
        "econometrics, and quantitative methods applied to agriculture, food, environment, and "
        "policy, completing an original dissertation for academic or research careers."
    ),
    "uiuc-animal-sciences-phd": (
        "Doctoral candidates pursuing original dissertation research in animal genetics, "
        "nutrition, physiology, and reproduction, preparing for research leadership in "
        "academia, industry, or government."
    ),
    "uiuc-crop-sciences-phd": (
        "Doctoral students committed to original research in plant breeding and genetics, crop "
        "physiology, weed science, or agroecology who want independent scholarship and "
        "publication toward research careers."
    ),
    "uiuc-engineering-technology-management-agricultural-systems": (
        "Research-focused students who want a doctorate integrating coursework and original "
        "research in agricultural systems engineering and management, preparing for scholarly "
        "and research leadership."
    ),
    "uiuc-food-science-human-nutrition-phd": (
        "Doctoral students centered on independent dissertation research in food chemistry and "
        "engineering, microbiology and safety, or molecular and community nutrition, building a "
        "publication record for research leadership."
    ),
    "uiuc-human-development-family-studies-phd": (
        "Research-bound students who want doctoral training in the development and resilience "
        "of diverse children, youth, and families using qualitative, quantitative, and mixed "
        "methods toward careers as researchers and educators."
    ),
    "uiuc-natural-resources-environmental-sciences-phd": (
        "Doctoral students taking a systems-level approach to environmental stewardship who "
        "want dissertation research in ecology and conservation, soil and water resources, or "
        "human dimensions of the environment."
    ),
    "uiuc-nutritional-science-phd": (
        "Research-bound students who want flexible, individualized doctoral training in "
        "nutritional sciences, with options to combine medical, public-health, or dietetics "
        "credentials, toward research careers."
    ),
    "uiuc-community-health-bs": (
        "Undergraduates focused on health care and health behavior who want preparation as "
        "community health practitioners and a foundation for health-related careers and further "
        "study."
    ),
    "uiuc-interdisciplinary-health-sciences-bs": (
        "Students who want to combine biology and health sciences with whole-person well-being, "
        "preparing for entry into graduate or professional programs in physical therapy, "
        "occupational therapy, medicine, or nursing."
    ),
    "uiuc-kinesiology-bs": (
        "Undergraduates interested in human movement who want a broad foundation spanning the "
        "sciences and liberal arts for careers in health, fitness, sport, and education or "
        "advanced and professional study."
    ),
    "uiuc-public-health-bs": (
        "Students who want to address pressing population-health challenges locally and "
        "globally, choosing a concentration and building the knowledge and skills to lead in "
        "public health."
    ),
    "uiuc-recreation-sport-tourism-bs": (
        "Undergraduates drawn to recreation, sport, and tourism who want a concentration-based "
        "foundation in this long-established program for careers managing leisure and sport "
        "services."
    ),
    "uiuc-speech-hearing-science-bs": (
        "Students interested in human speech, language, swallowing, hearing, and balance who "
        "want the theoretical and clinical background needed for graduate study in the field."
    ),
    "uiuc-community-health-ms": (
        "Students who want to plan, deliver, and evaluate programs that improve population "
        "health, applying epidemiology and health-behavior theory through coursework, "
        "fieldwork, and a chosen specialization."
    ),
    "uiuc-epidemiology-mph": (
        "Students who want strong analytical training to study the distribution and "
        "determinants of disease, combining public-health coursework with an applied practice "
        "experience toward epidemiology careers."
    ),
    "uiuc-health-administration-mha": (
        "Students preparing to become healthcare managers and administrators who want the "
        "knowledge and skills to lead within the complex U.S. healthcare system."
    ),
    "uiuc-health-technology-ms": (
        "Students who want to develop, test, and apply technologies that promote health, "
        "support rehabilitation, and improve independence, preparing as health-technology "
        "professionals working with end users."
    ),
    "uiuc-kinesiology-ms": (
        "Students seeking advanced graduate study in human movement and physical activity, "
        "whether as professional specialization or as preparation for doctoral research."
    ),
    "uiuc-public-health-mph": (
        "Students drawn to an interdisciplinary field rooted in science and social justice who "
        "want to identify needs, craft solutions, and implement change that protects and "
        "improves population health."
    ),
    "uiuc-recreation-sport-tourism-ms": (
        "Students who want a master's in recreation, sport, and tourism as either a terminal "
        "professional credential or a first step toward doctoral study."
    ),
    "uiuc-speech-hearing-science-ma": (
        "Students training to become speech-language pathologists who want coursework in "
        "language, phonology, voice, fluency, and dysphagia paired with supervised clinical "
        "practicum to assess and treat communication and swallowing disorders."
    ),
    "uiuc-community-health-phd": (
        "Research-bound students who want doctoral training in the determinants of population "
        "health and the design of programs and policies that prevent disease, drawing on "
        "epidemiology and health-systems research."
    ),
    "uiuc-kinesiology-phd": (
        "Doctoral students who want advanced study and original research across exercise "
        "physiology, biomechanics, and motor control to become researchers in human movement "
        "and physical activity."
    ),
    "uiuc-recreation-sport-tourism-phd": (
        "Research-focused students who want to develop as researchers and educators studying "
        "leisure behavior and the management of recreation, tourism, and sport systems."
    ),
    "uiuc-speech-hearing-science-phd": (
        "Research-bound students who want original research into communication, communication "
        "disorders, and dysphagia, joining faculty laboratories and completing advanced study "
        "toward research careers."
    ),
    "uiuc-audiology-aud": (
        "Students pursuing the clinical practitioner path in audiology who want professional "
        "doctoral training to specialize in hearing and balance care."
    ),
    "uiuc-accountancy-bs": (
        "Undergraduates who want to pair technical accounting, assurance, taxation, and data "
        "analytics with professional skills in communication and decision-making for careers "
        "across accounting and business."
    ),
    "uiuc-accountancy-data-science-bs": (
        "Students who want to supplement an accounting foundation with data science, combining "
        "accountancy with statistics, computing, and mathematics for analytics-driven "
        "accounting and business careers."
    ),
    "uiuc-business-data-science-bs": (
        "Undergraduates who want to extend a business foundation with data science, blending "
        "business administration with statistics, computing, and mathematics for "
        "analytics-focused business careers."
    ),
    "uiuc-finance-bs": (
        "Students interested in how firms, governments, and individuals acquire and manage "
        "funds who want a foundation in financial decision-making for careers in finance."
    ),
    "uiuc-finance-data-science-bs": (
        "Undergraduates who want a finance foundation paired with strong quantitative and data "
        "skills, drawing on statistics, computer science, and mathematics, and are aiming "
        "toward analytical roles in financial services or further study at the intersection of "
        "finance and data."
    ),
    "uiuc-information-systems-bs": (
        "Undergraduates who want to bridge business and technology and are comfortable "
        "navigating increasingly digitized organizations, building toward careers helping "
        "companies adopt and manage information systems."
    ),
    "uiuc-management-business-bs": (
        "Undergraduates drawn to leadership and innovation who want to analyze and solve the "
        "people, organizational, and market problems businesses face day to day, headed toward "
        "management roles across organizations."
    ),
    "uiuc-marketing-bs": (
        "Undergraduates interested in how goods and services reach consumers who want to study "
        "the development, decisions, and delivery behind marketing, building toward careers "
        "managing marketing activities for organizations."
    ),
    "uiuc-operations-management-bs": (
        "Undergraduates interested in how organizations produce and deliver, preparing for "
        "careers in manufacturing and service management, operations strategy consulting, "
        "purchasing and supply, project management, and quality management."
    ),
    "uiuc-supply-chain-bs": (
        "Undergraduates curious about how materials, information, and finances flow from "
        "sourcing to the customer who want data-driven training in procurement, logistics, "
        "operations, and analytics, headed toward careers designing and managing global supply "
        "chains."
    ),
    "uiuc-accountancy-mas": (
        "Accounting graduates with a U.S. bachelor's in accountancy who want a focused one-year "
        "master's, choosing a concentration in taxation or financial reporting and assurance to "
        "deepen professional accounting expertise."
    ),
    "uiuc-accountancy-ms": (
        "Aspiring accounting professionals who want advanced, specialized training in "
        "accountancy, with the flexibility to complete the degree on campus or online before "
        "moving into accounting practice."
    ),
    "uiuc-accountancy-imsa-ms": (
        "Working professionals and accounting-bound students who want a fully online master's "
        "in accountancy that builds advanced expertise on a flexible, remote schedule."
    ),
    "uiuc-business-administration-online-mba": (
        "Working professionals seeking a flexible, fully online MBA who want broad graduate "
        "management training to advance or pivot their careers without leaving the workforce."
    ),
    "uiuc-business-analytics-ms": (
        "Professionally minded students who want to master contemporary analytics for "
        "identifying and solving business problems, with on-campus or online study and "
        "coursework in managing, analyzing, and communicating data."
    ),
    "uiuc-finance-ms": (
        "Practitioners in finance-related roles who want a focused 15-month master's to deepen "
        "their finance expertise and advance their careers in the field."
    ),
    "uiuc-financial-engineering-ms": (
        "Quantitatively strong students who want to apply mathematics, statistics, computing, "
        "and machine learning to financial markets and products, preparing for technical roles "
        "in finance."
    ),
    "uiuc-management-ms": (
        "Practitioners leading or moving toward leading teams, units, or organizations who want "
        "a general management foundation with the option to specialize in a focused area."
    ),
    "uiuc-management-imsm-ms": (
        "Working professionals who want a flexible, fully online general management master's "
        "with room to specialize, while leading teams, units, or organizations."
    ),
    "uiuc-technology-management-ms": (
        "Professionals in technology-driven enterprises who want to manage the dynamic "
        "environment of tech-based companies, pairing core business topics with the challenges "
        "specific to firms that depend on technology."
    ),
    "uiuc-accountancy-phd": (
        "Research-bound students who want to pursue original scholarship in accountancy, "
        "building toward an academic career through advanced coursework and a doctoral thesis "
        "developed with a faculty advisory committee."
    ),
    "uiuc-business-administration-phd": (
        "Research-minded students who want in-depth doctoral training and teaching preparation "
        "in a chosen business area such as marketing, organizational behavior, management "
        "science, information systems, or strategic management, headed toward academic careers."
    ),
    "uiuc-finance-phd": (
        "Research-bound students who want rigorous doctoral training in finance, advancing "
        "through qualifying examinations and original research toward a scholarly career in the "
        "field."
    ),
    "uiuc-medicine-md": (
        "Future physicians who want a professional, four-year MD program that integrates "
        "engineering concepts with the traditional foundations of medicine, preparing for "
        "careers in clinical practice and medical innovation."
    ),
    "uiuc-computer-science-education-bs": (
        "Undergraduates who want to combine computing with teaching and learning through a "
        "flexible joint major, preparing for careers in either computer science or education."
    ),
    "uiuc-early-childhood-education-bs": (
        "Undergraduates who want to teach children from birth through grade two, combining "
        "child development, literacy and numeracy methods, and inclusive practice with "
        "supervised clinical experience on the path to licensure."
    ),
    "uiuc-elementary-education-bs": (
        "Undergraduates who want to teach grades one through six across the core subjects, "
        "pairing literacy, math, science, and social-studies methods with extensive supervised "
        "placements and earning an Illinois teaching license."
    ),
    "uiuc-learning-education-studies-bs": (
        "Undergraduates drawn to education beyond the licensed classroom who want to work in "
        "training and development, education technology, policy, or community programs, "
        "studying how people learn across settings alongside applied, career-focused "
        "coursework."
    ),
    "uiuc-middle-grades-education-bs": (
        "Undergraduates who want to teach grades five through eight, balancing subject-matter "
        "depth with the developmental needs of early adolescents through content specialization "
        "and supervised placements toward Illinois licensure."
    ),
    "uiuc-secondary-education-bs": (
        "Undergraduates who want to teach grades nine through twelve and are ready to "
        "specialize in a content concentration such as mathematics, completing coursework "
        "toward licensure as a high school teacher."
    ),
    "uiuc-special-education-bs": (
        "Undergraduates with prior experience supporting individuals with disabilities who want "
        "to teach students from kindergarten through age 22, preparing as licensed special "
        "education teachers."
    ),
    "uiuc-curriculum-instruction-edm": (
        "Experienced teachers who want to grow as reflective practitioners and instructional "
        "leaders, deepening applied pedagogy in subject-matter teaching, learning, and "
        "curriculum design."
    ),
    "uiuc-curriculum-instruction-ma": (
        "Teachers moving toward scholarly or research-oriented work who want a master's in "
        "curriculum and instruction with a research core and a thesis or research project in "
        "teaching, learning, and curriculum."
    ),
    "uiuc-curriculum-instruction-ms": (
        "Educators who want a research-focused master's in curriculum and instruction, pairing "
        "curriculum coursework with empirical and quantitative methods and culminating in a "
        "research thesis."
    ),
    "uiuc-early-childhood-education-edm": (
        "Teachers and specialists who want advanced preparation in the learning and development "
        "of young children, focusing on developmentally appropriate curriculum, family "
        "engagement, and early-grades instruction."
    ),
    "uiuc-education-policy-organization-leadership-edm": (
        "Professionals who want to lead and improve educational institutions through study of "
        "governance, administration, policy, leadership, higher education, and human resource "
        "development."
    ),
    "uiuc-education-policy-organization-leadership-ma": (
        "Students pursuing scholarship or doctoral study who want a research-oriented master's "
        "analyzing education systems, their governance, and the leadership of schools and "
        "postsecondary institutions."
    ),
    "uiuc-educational-psychology-edm": (
        "Educators and practitioners who want to apply the science of learning, development, "
        "motivation, and measurement to schools, building toward roles in teaching, evaluation, "
        "and educational support."
    ),
    "uiuc-educational-psychology-ma": (
        "Students moving toward research or doctoral work who want a scholarly master's in "
        "educational psychology, emphasizing research methods and the study of learning, "
        "development, motivation, and measurement."
    ),
    "uiuc-educational-psychology-ms": (
        "Students who want a research-focused master's studying how people learn and develop, "
        "pairing coursework in cognition, assessment, and statistics with empirical research "
        "training."
    ),
    "uiuc-elementary-education-edm": (
        "Practicing teachers who want to strengthen their classroom practice and integrated "
        "curriculum knowledge for teaching reading, mathematics, science, and social studies "
        "across the elementary grades."
    ),
    "uiuc-mental-health-counseling-ms": (
        "Students preparing to become mental health counselors who want a two-year, "
        "face-to-face program grounded in psychological science, cultural diversity, and "
        "applied practice across the lifespan, including a clinical placement."
    ),
    "uiuc-secondary-education-edm": (
        "Practicing secondary teachers who want to build advanced disciplinary pedagogy and "
        "curriculum expertise for instructing adolescents at the middle and high school levels."
    ),
    "uiuc-special-education-edm": (
        "Educators who want advanced licensure and specialization in special education across "
        "emphases such as infancy and early childhood, learning and behavior specialist "
        "preparation, and inclusive teaching."
    ),
    "uiuc-curriculum-instruction-edd": (
        "Experienced educators who want to advance research and leadership in teaching, "
        "learning, and curriculum, preparing as scholarly practitioners for leadership in "
        "teacher-preparation institutions, state agencies, and school districts."
    ),
    "uiuc-curriculum-instruction-phd": (
        "Research-bound students who want to conduct original research on teaching, learning, "
        "and curriculum, preparing for careers as researchers in universities and research "
        "settings."
    ),
    "uiuc-education-policy-organization-leadership-edd": (
        "Experienced professionals who want to lead and improve educational institutions and "
        "systems through applied research on problems of practice, headed toward leadership "
        "roles in schools and agencies."
    ),
    "uiuc-education-policy-organization-leadership-phd": (
        "Research-bound students who want to investigate how policy, governance, and leadership "
        "shape educational institutions, advancing through rigorous methods and an original "
        "dissertation toward academic and policy careers."
    ),
    "uiuc-educational-psychology-phd": (
        "Research-bound students who want to advance the science of learning, human "
        "development, measurement, and motivation through advanced quantitative and qualitative "
        "methods and an original dissertation."
    ),
    "uiuc-special-education-phd": (
        "Research-focused students who want an individualized doctoral course of study in "
        "special education, working closely with an advisor and engaging in research toward a "
        "scholarly career."
    ),
    "uiuc-aerospace-engineering-bs": (
        "Undergraduates fascinated by flight and space who want a foundation in aerodynamics, "
        "propulsion, structures, and dynamics and control, applying it in a year-long senior "
        "capstone designing aircraft and spacecraft against an industry challenge."
    ),
    "uiuc-agricultural-biological-engineering-bs": (
        "Undergraduates who want to apply engineering science to agriculture, food, bioenergy, "
        "water, and biological systems, combining fundamentals, design, and laboratory work in "
        "a professionally accredited program."
    ),
    "uiuc-bioengineering-bs": (
        "Undergraduates who want to apply engineering to human health and the life sciences, "
        "pairing a strong foundation in biology, math, and engineering with design coursework "
        "to develop diagnostics, devices, and therapies."
    ),
    "uiuc-chemical-engineering-bs": (
        "Undergraduates strong in the basic sciences who want to build from chemistry, physics, "
        "and mathematics into the fundamentals of chemical engineering such as mass and energy "
        "balances and thermodynamics, headed toward engineering practice."
    ),
    "uiuc-civil-engineering-bs": (
        "Undergraduates who want to apply science and computational tools to society's biggest "
        "challenges, from clean air and safe water to protecting communities from natural "
        "hazards, preparing for careers in civil and environmental engineering."
    ),
    "uiuc-computer-engineering-bs": (
        "Undergraduates drawn to building computing technologies from chips to networks who "
        "want to design scalable, trustworthy computing systems, pairing hardware and software "
        "foundations toward engineering careers."
    ),
    "uiuc-computer-science-bs": (
        "Undergraduates who want a deep foundation in algorithms, systems, software, and "
        "theory, with the flexibility to apply computing across domains from graphics and "
        "machine learning to security and computational science."
    ),
    "uiuc-computer-science-bioengineering-bs": (
        "Undergraduates who want to join computational methods with bioengineering to analyze "
        "biomedical data, model biological systems, and design diagnostic and therapeutic "
        "technologies, through a blended major spanning both fields."
    ),
    "uiuc-computer-science-physics-bs": (
        "Undergraduates who want to combine computing with the quantitative study of physical "
        "systems, using computational methods to extend physics beyond what pen and paper "
        "allow."
    ),
    "uiuc-electrical-engineering-bs": (
        "Undergraduates interested in the technologies of energy and information who want a "
        "broad, solid foundation in mathematics and physics, preparing for careers driving "
        "electrical engineering innovation."
    ),
    "uiuc-engineering-mechanics-bs": (
        "Undergraduates who want rigorous training in the principles of mechanics that underpin "
        "design across industries such as materials, energy, biotechnology, civil, and "
        "aerospace, building strong mathematical and scientific foundations."
    ),
    "uiuc-engineering-physics-bs": (
        "Undergraduates who want to bridge fundamental physics and mathematics with engineering "
        "design, pairing a deep physics core with engineering coursework toward emerging "
        "technology."
    ),
    "uiuc-environmental-engineering-bs": (
        "Undergraduates who want to use science and computational tools to ensure clean air, "
        "safe water, and sanitation and to design systems for sustainable environmental "
        "resource management, preparing for environmental engineering careers."
    ),
    "uiuc-industrial-engineering-bs": (
        "Undergraduates drawn to improving integrated systems of people, materials, "
        "information, energy, and equipment who want to analyze, develop, and evaluate "
        "processes, building toward careers optimizing how organizations operate."
    ),
    "uiuc-innovation-leadership-engineering-entrepreneurship-bs": (
        "Grainger engineering undergraduates who want to pair technical training with the "
        "skills to identify problems, lead, and turn ideas into ventures, aiming toward "
        "innovation- and startup-driven engineering careers."
    ),
    "uiuc-materials-science-engineering-bs": (
        "Undergraduates fascinated by how materials are processed and why their properties "
        "behave as they do, building a foundation in designing and developing new materials for "
        "careers across engineering industries or graduate study."
    ),
    "uiuc-materials-science-engineering-data-science-bs": (
        "Undergraduates drawn to both the structure-property foundations of materials and "
        "computational thinking, who want a blended degree that applies data science to "
        "materials problems before careers spanning engineering and analytics."
    ),
    "uiuc-mechanical-engineering-bs": (
        "Undergraduates curious about how forces act on solids and fluids and how machines "
        "interact with their environments, building a broad foundation for engineering careers "
        "across nearly every industry."
    ),
    "uiuc-neural-engineering-bs": (
        "Undergraduates drawn to the meeting point of neuroscience and engineering who want "
        "training in electrical and imaging systems, molecular and cellular engineering, and "
        "computational data science, headed toward engineering careers or further study at the "
        "brain-technology frontier."
    ),
    "uiuc-nuclear-plasma-radiological-engineering-bs": (
        "Undergraduates interested in energy production, plasma processing, fusion, and the "
        "medical and safety uses of radiation, building a foundation across these complementary "
        "disciplines for engineering careers or graduate study."
    ),
    "uiuc-nuclear-plasma-radiological-engineering-data-science-bs": (
        "Undergraduates who want the nuclear, plasma, and radiological engineering foundation "
        "joined with computing, mathematics, and statistics, preparing for data-driven "
        "engineering careers across energy and radiological fields."
    ),
    "uiuc-physics-bs": (
        "Undergraduates seeking the fundamental laws governing matter, energy, space, and time, "
        "who want a deep conceptual and mathematical foundation through coursework and research "
        "before careers in industry or graduate study."
    ),
    "uiuc-systems-engineering-design-bs": (
        "Undergraduates who think about how parts fit into a whole and want an "
        "interdisciplinary blend of basic sciences, engineering analysis, and design, with the "
        "flexibility of a secondary field, headed toward broad engineering careers."
    ),
    "uiuc-aerospace-engineering-ms": (
        "Engineers ready for advanced study in aerodynamics, propulsion, structures, flight "
        "mechanics, and autonomy, choosing thesis research with a faculty group or a non-thesis "
        "path toward professional practice."
    ),
    "uiuc-agricultural-biological-engineering-ms": (
        "Engineers focused on food, bioenergy, water, and biological systems who want advanced "
        "coursework and research, with an optional computational science concentration, toward "
        "technical or research careers."
    ),
    "uiuc-bioengineering-meng": (
        "Engineers aiming to translate bioengineering into industry, who want technical depth "
        "alongside regulatory, business, and project-management skills built through team "
        "projects with healthcare and medical-device partners."
    ),
    "uiuc-bioengineering-ms": (
        "Engineers seeking advanced bioengineering training who can choose mentored laboratory "
        "research in areas like biomedical imaging and cellular engineering, or a "
        "coursework-focused non-thesis path toward technical careers."
    ),
    "uiuc-biomedical-image-computing-ms": (
        "Students who want to combine biomedical imaging science with machine learning, gaining "
        "rigorous training in imaging systems, computational imaging, and analysis for an "
        "industry career."
    ),
    "uiuc-chemical-engineering-ms": (
        "Chemical engineers considering a terminal master's who want advanced specialization, "
        "with the professionally oriented Chemical Engineering Leadership track available for "
        "industry-bound study."
    ),
    "uiuc-chemical-engineering-leadership-meng": (
        "Chemical engineers whose primary aim is a professional career in industry or "
        "government, who want a professionally oriented master's rather than a research-focused "
        "one."
    ),
    "uiuc-civil-engineering-ms": (
        "Civil engineers seeking advanced study across the field's many specialized areas "
        "through departmental and joint programs, preparing for technical practice or further "
        "graduate research."
    ),
    "uiuc-computer-science-ms": (
        "Computer scientists who want advanced coursework joined with thesis research in areas "
        "like systems, artificial intelligence, theory, and human-computer interaction, "
        "preparing for advanced technical and research roles."
    ),
    "uiuc-computer-science-mcs": (
        "Computer scientists seeking a research master's that can be earned en route to a PhD "
        "or as a terminal degree, deepening expertise in a long-established department."
    ),
    "uiuc-computer-science-online-mcs": (
        "Working professionals and remote learners who want a fully online master's in computer "
        "science, gaining advanced expertise on a flexible schedule for technical careers."
    ),
    "uiuc-electrical-computer-engineering-meng": (
        "Electrical and computer engineers who want to extend the depth or breadth of their "
        "technical knowledge through a professionally oriented degree, heading into industry "
        "practice."
    ),
    "uiuc-electrical-computer-engineering-ms": (
        "Electrical and computer engineers seeking advanced specialization, with the option to "
        "focus on computational science and engineering, toward technical or research careers."
    ),
    "uiuc-engineering-meng": (
        "Engineers bound for industry or government rather than doctoral study, who want an "
        "interdisciplinary concentration that combines technical coursework with applied "
        "project work."
    ),
    "uiuc-environmental-engineering-civil-engineering-ms": (
        "Engineers focused on protecting and restoring air, water, and land through treatment, "
        "pollution control, and sustainable infrastructure, who want advanced specialization "
        "toward professional practice."
    ),
    "uiuc-industrial-engineering-ms": (
        "Engineers who want to design and improve complex systems of people, processes, and "
        "resources using optimization, operations research, and human factors, advancing toward "
        "technical careers."
    ),
    "uiuc-materials-engineering-meng": (
        "Engineers seeking a professionally oriented master's in materials engineering for "
        "industry-focused practice."
    ),
    "uiuc-materials-science-engineering-ms": (
        "Engineers who want advanced study of how processing controls the structure and "
        "properties of metals, ceramics, polymers, and electronic materials, with an optional "
        "computational concentration, toward technical or research roles."
    ),
    "uiuc-mechanical-engineering-ms": (
        "Mechanical engineers seeking advanced study on campus or online, building "
        "specialization for technical careers or as a step toward doctoral work."
    ),
    "uiuc-mechanical-engineering-meng": (
        "Mechanical engineers who want a coursework-based, non-thesis master's with advanced "
        "knowledge and experiential opportunities, choosing tracks such as design, "
        "manufacturing, or controls and robotics for industry practice."
    ),
    "uiuc-nuclear-plasma-radiological-engineering-ms": (
        "Engineers focused on fission and fusion energy, plasma science, and radiological and "
        "medical uses of radiation, who want advanced coursework and research, with an optional "
        "computational concentration."
    ),
    "uiuc-physics-ms": (
        "Physicists seeking graduate study that deepens their command of the field, as advanced "
        "specialization or a step toward doctoral research."
    ),
    "uiuc-teaching-physics-ms": (
        "Aspiring and current physics educators who want graduate training focused on teaching, "
        "building advanced subject mastery and pedagogy for the classroom."
    ),
    "uiuc-systems-entrepreneurial-engineering-ms": (
        "Engineers who want to join the modeling and design of large engineered systems with "
        "technology management and entrepreneurship, advancing toward leadership and "
        "venture-minded technical careers."
    ),
    "uiuc-theoretical-applied-mechanics-ms": (
        "Students seeking advanced study in theoretical and applied mechanics, as "
        "specialization in its own right or preparation before applying to the doctoral "
        "program."
    ),
    "uiuc-aerospace-engineering-phd": (
        "Research-bound engineers ready to complete an original dissertation across "
        "computational and experimental aerodynamics, propulsion, structures, and space "
        "systems, with a faculty adviser, toward academic or research careers."
    ),
    "uiuc-agricultural-biological-engineering-phd": (
        "Research-bound engineers who want to develop original work across food, bioenergy, "
        "water, and biological systems through dissertation research, teaching, and seminars, "
        "with an optional computational concentration."
    ),
    "uiuc-bioengineering-phd": (
        "Doctoral researchers drawn to interdisciplinary laboratories spanning engineering and "
        "medicine, pursuing original dissertation work in areas like biomedical imaging, "
        "regenerative engineering, and computational biology toward research careers."
    ),
    "uiuc-chemical-engineering-phd": (
        "Research-bound students with a strong chemistry and chemical engineering background "
        "who want to pursue an advanced doctoral degree, toward careers in research."
    ),
    "uiuc-civil-engineering-phd": (
        "Research-bound engineers seeking doctoral work across the field's many specialized "
        "areas through departmental programs, preparing for academic and research careers."
    ),
    "uiuc-computer-science-phd": (
        "Doctoral candidates ready to conduct original research at the frontier of computing, "
        "advised within groups spanning systems, AI and machine learning, theory, programming "
        "languages, and security, toward research and academic careers."
    ),
    "uiuc-electrical-computer-engineering-phd": (
        "Research-bound students entering with a master's or directly from a bachelor's, who "
        "pursue advanced doctoral research under faculty mentorship toward academic and "
        "research careers."
    ),
    "uiuc-environmental-engineering-civil-engineering-phd": (
        "Research-bound engineers advancing the science of protecting air, water, and land, "
        "from remediation to sustainable infrastructure and environmental systems, through "
        "original dissertation work."
    ),
    "uiuc-industrial-engineering-phd": (
        "Doctoral researchers advancing the optimization, operations-research, and "
        "human-factors science of complex production and service systems, choosing traditional "
        "or direct doctoral paths toward research careers."
    ),
    "uiuc-materials-science-engineering-phd": (
        "Research-bound students probing the structure-property-processing relationships of "
        "metals, ceramics, polymers, and electronic and biological materials through "
        "dissertation research, toward academic and research careers."
    ),
    "uiuc-mechanical-engineering-phd": (
        "Research-bound engineers entering with a master's or directly from a bachelor's, "
        "pursuing original doctoral research in mechanical engineering toward academic and "
        "research careers."
    ),
    "uiuc-nuclear-plasma-radiological-engineering-phd": (
        "Research-bound engineers advancing fission and fusion energy, plasma science, and "
        "radiological applications through dissertation research and seminars, with an optional "
        "computational concentration."
    ),
    "uiuc-physics-phd": (
        "Doctoral physicists seeking outstanding research opportunities in an "
        "interdisciplinary, integrated approach to graduate training, toward academic and "
        "research careers."
    ),
    "uiuc-systems-entrepreneurial-engineering-phd": (
        "Research-bound students uniting systems engineering with technology management and "
        "entrepreneurship through original dissertation work, choosing traditional or direct "
        "doctoral paths toward research careers."
    ),
    "uiuc-theoretical-applied-mechanics-phd": (
        "Research-bound students seeking a rigorous, distinctive doctoral curriculum in "
        "theoretical and applied mechanics with structured core and breadth coursework, "
        "pursuing original dissertation research."
    ),
    "uiuc-architectural-studies-bs": (
        "Undergraduates building a strong foundation in design, technology, and architectural "
        "history as preparation to enter a professional master of architecture degree."
    ),
    "uiuc-foundation": (
        "Incoming art and design students, including those entering undeclared, who complete a "
        "shared first-year curriculum after portfolio review before specializing in a major."
    ),
    "uiuc-art-education-bfa": (
        "Undergraduates who want to combine studio art training with preparation to teach, "
        "building the foundation to bring art education into the classroom."
    ),
    "uiuc-computer-science-music-bs": (
        "Undergraduates who want to join computer science with music to pursue music "
        "technology, advance music composition, and explore new avenues of expression, "
        "preparing for careers and advanced study at that intersection."
    ),
    "uiuc-dance-bfa": (
        "Undergraduates seeking intensive dance training, multicultural movement practice, and "
        "close faculty mentorship to enter the professional dance world as performers and "
        "informed citizens."
    ),
    "uiuc-dance-ba": (
        "Undergraduates who want an integrated, individualized study of dance with room for "
        "interdisciplinary art-making and a second major or minor alongside their training."
    ),
    "uiuc-graphic-design-bfa": (
        "Undergraduates preparing for professional practice in visual communications, with "
        "studio work spanning typography, image making, design history, and research methods."
    ),
    "uiuc-industrial-design-bfa": (
        "Undergraduates drawn to a human-centered, experiential approach to creating innovative "
        "products and services, building studio skills for a career designing products."
    ),
    "uiuc-jazz-performance-bmus": (
        "Undergraduate instrumentalists and vocalists who want focused conservatory-style "
        "training on their major instrument, from saxophone to voice, toward careers as jazz "
        "performers."
    ),
    "uiuc-landscape-architecture-bla": (
        "Undergraduates pursuing professional training in landscape architecture through "
        "studio-based work toward a career in the field."
    ),
    "uiuc-lyric-theatre-bma": (
        "Undergraduate singer-actors who want interdisciplinary training that blends music with "
        "dance and theatre, choosing a performance or creative concentration toward careers on "
        "the lyric stage."
    ),
    "uiuc-music-ba": (
        "Musically grounded undergraduates who want a flexible music degree with room for "
        "secondary and complementary fields of study, leaving the door open to careers that "
        "blend music with other interests or to further study."
    ),
    "uiuc-music-composition-bmus": (
        "Undergraduate musicians drawn to writing and analyzing music who want focused training "
        "in composition or music theory, preparing for creative careers or graduate work in "
        "composition."
    ),
    "uiuc-music-education-bme": (
        "Aspiring music teachers who want undergraduate preparation to lead instruction in "
        "pre-kindergarten through twelfth-grade classrooms, headed toward licensed careers in "
        "school music education."
    ),
    "uiuc-musicology-bmus": (
        "Undergraduates who want to unite academic study with musical training and are curious "
        "about music as culture and history, building toward graduate study in musicology or "
        "ethnomusicology."
    ),
    "uiuc-music-open-studies-bmus": (
        "Self-directed undergraduate musicians who want to shape a degree around an individual "
        "interest such as world music, piano pedagogy, music technology, sound engineering, or "
        "theatre alongside core music study."
    ),
    "uiuc-studio-art-basa": (
        "Undergraduates who want to study art, design, and art history within a broad liberal "
        "program, combining studio practice with the wider research and teaching of the "
        "university."
    ),
    "uiuc-studio-art-bfasa": (
        "Undergraduates committed to a single studio concentration who want focused, "
        "professional preparation in their chosen area of art practice."
    ),
    "uiuc-sustainable-design-bs": (
        "Design-minded undergraduates interested in the environment who want an "
        "interdisciplinary path toward building sustainable communities through products, "
        "buildings, neighborhoods, landscapes, and cities."
    ),
    "uiuc-theatre-bfa": (
        "Undergraduates seeking conservatory-style theatre training inside a research "
        "university, with concentrations across acting, design, and theatre technology and "
        "production, building professional skills through studios and staged productions."
    ),
    "uiuc-urban-studies-planning-ba": (
        "Undergraduates who care about the quality of life in cities and regions and want both "
        "technical skills and a broad liberal foundation for careers or graduate study in "
        "planning."
    ),
    "uiuc-architectural-studies-ms": (
        "Architecture graduates and professionals from allied fields who want advanced research "
        "skills and a specialized focus to engage environmental design at a deeper level."
    ),
    "uiuc-architecture-march": (
        "Students pursuing graduate architecture education who want the professional "
        "preparation of a Master of Architecture for practice in the field."
    ),
    "uiuc-art-design-mfa": (
        "Practicing artists and designers seeking terminal, professional-level training in a "
        "chosen field such as design for responsible innovation, industrial design, or studio "
        "art."
    ),
    "uiuc-art-education-edm": (
        "Art teachers, supervisors, and prospective educators who want advanced professional "
        "study to strengthen their practice in schools or prepare for further work in the "
        "field."
    ),
    "uiuc-art-education-ma": (
        "Students drawn to research in art education who want advanced study toward careers in "
        "schools, museums, and community settings or as a foundation for doctoral work."
    ),
    "uiuc-dance-mfa": (
        "Dance artists pursuing terminal training in choreographing, performing, teaching, and "
        "community building, preparing for professional careers and creative leadership in "
        "dance."
    ),
    "uiuc-industrial-design-mdes": (
        "Designers seeking a STEM-designated, professionally oriented master's who want to "
        "advance in the industrial design profession."
    ),
    "uiuc-landscape-architecture-mla": (
        "Students entering the landscape architecture profession who want studio-based, "
        "professional training to design outdoor environments from the individual site to the "
        "region, integrating ecology, planning, and design."
    ),
    "uiuc-music-mmus": (
        "Musicians seeking advanced graduate study in music who want to deepen their artistry "
        "and specialization beyond the undergraduate level."
    ),
    "uiuc-music-education-mme": (
        "Certified music teachers who want advanced study to continue their careers as public "
        "school music educators or move into music administration."
    ),
    "uiuc-sustainable-urban-design-msud": (
        "Designers and planners focused on cities who want studio and research training in "
        "sustainable urban form, shaping the public realm for environmental performance, "
        "livability, and resilience."
    ),
    "uiuc-theatre-ma": (
        "Students drawn to theatre history, theory, and dramatic literature who want scholarly "
        "graduate study as preparation for doctoral work or careers in arts education and "
        "administration."
    ),
    "uiuc-theatre-mfa": (
        "Theatre practitioners seeking the terminal studio credential, with specializations "
        "across acting, design, and stage and production management, in intensive, "
        "production-centered training."
    ),
    "uiuc-urban-planning-mup": (
        "Students preparing for professional planning practice who want training for public "
        "service across government, private consulting, and the nonprofit sector."
    ),
    "uiuc-architecture-phd": (
        "Scholars aiming at research careers in academia, industry, or government who want "
        "doctoral training in architecture across focus areas such as history and theory, "
        "environment and technology, health and wellbeing, and urbanism."
    ),
    "uiuc-art-education-phd": (
        "Advanced graduate students drawn to scholarship and research in art education who want "
        "doctoral coursework spanning art education and related disciplines across the "
        "university."
    ),
    "uiuc-landscape-architecture-phd": (
        "Researchers in landscape architecture who want doctoral study toward scholarly inquiry "
        "and academic careers in the field."
    ),
    "uiuc-music-dma": (
        "Accomplished performers who want to combine artistic and academic interests at the "
        "doctoral level, pursuing the highest comprehensive training in musical practice."
    ),
    "uiuc-music-education-phd": (
        "Researchers seeking a terminal degree in music education with a strong background and "
        "interest in inquiry, preparing for scholarly and academic careers in the field."
    ),
    "uiuc-musicology-phd": (
        "Doctoral students whose interests lie in research on the history of music, systematic "
        "musicology, or ethnomusicology, headed toward scholarship and university teaching."
    ),
    "uiuc-regional-planning-phd": (
        "Doctoral students who design an individualized course of theory, methods, and "
        "specialization with their advisers, preparing for careers of advanced research and "
        "teaching in planning."
    ),
    "uiuc-theatre-phd": (
        "Scholars headed for research and university teaching in theatre history, theory, and "
        "performance studies through advanced seminars and a dissertation."
    ),
    "uiuc-artist-diploma-music": (
        "Performers at the highest level of artistic accomplishment in keyboard, voice, or "
        "orchestral and band instruments who want a focused, performance-centered credential "
        "demonstrated by an exceptional entrance audition."
    ),
    "uiuc-information-sciences-bs": (
        "Undergraduates drawn to the knowledge economy who want preparation for a wide range of "
        "information-professional careers in a technology-centered job market."
    ),
    "uiuc-information-sciences-data-science-bs": (
        "Undergraduates who pair an interest in information professions with data work, "
        "building information-science foundations alongside data skills for careers in the "
        "knowledge economy."
    ),
    "uiuc-bioinformatics-ms": (
        "Graduate students at the meeting point of biology and computing who want to manage and "
        "analyze large biological data sets, with a concentration in areas such as genomics or "
        "health, for careers applying informatics to life-science problems."
    ),
    "uiuc-game-development-ms": (
        "Students aiming for professional game studios and game-adjacent industries who want "
        "technical training and practical experience with game-related skills increasingly in "
        "demand."
    ),
    "uiuc-information-management-ms": (
        "Working professionals seeking graduate study in information management; note that "
        "admissions to this program are currently suspended."
    ),
    "uiuc-library-information-science-ms": (
        "Students preparing for careers in libraries and information work who want an "
        "ALA-accredited master's available on campus or online."
    ),
    "uiuc-informatics-phd": (
        "Doctoral students who want interdisciplinary research training in informatics, guided "
        "by an advisory and dissertation committee through an individualized program of study."
    ),
    "uiuc-information-science-phd": (
        "Research-bound doctoral students in information sciences who want substantial graduate "
        "coursework and a thesis toward scholarly and academic careers."
    ),
    "uiuc-actuarial-science-bslas": (
        "Quantitatively minded undergraduates interested in risk and finance who want an "
        "interdisciplinary blend of mathematics, statistics, and financial economics to prepare "
        "for the actuarial profession or careers in quantitative finance and risk management."
    ),
    "uiuc-african-american-studies-balas": (
        "Undergraduates who want to systematically explore the life, culture, and history of "
        "African American peoples and their African Diaspora connections across historical, "
        "political, social, and artistic dimensions."
    ),
    "uiuc-anthropology-balas": (
        "Undergraduates curious about humans across time and space who want a broad, globally "
        "minded discipline that integrates biological and cultural study drawing on the natural "
        "sciences, social sciences, humanities, and arts."
    ),
    "uiuc-art-history-balas": (
        "Undergraduates fascinated by the visual and built world who want a broad historical "
        "and cultural education as sound preparation for graduate study toward museum work or "
        "college-level teaching."
    ),
    "uiuc-art-art-history-bfa": (
        "Undergraduates who want to combine art history with studio and design practice in a "
        "single course of study, pairing scholarly and creative work."
    ),
    "uiuc-asian-american-studies-balas": (
        "Undergraduates who want to deepen their understanding of Asian American histories, "
        "experiences, and contemporary social issues through an interdisciplinary major as part "
        "of a liberal education."
    ),
    "uiuc-astronomy-bslas": (
        "Undergraduates fascinated by the cosmos who want a flexible program grounded in "
        "physical science and mathematics, preparing for technical or professional careers "
        "requiring that foundation."
    ),
    "uiuc-astronomy-data-science-bslas": (
        "Undergraduates drawn to astronomy and its massive data sets who want modern "
        "computational and statistical methods, data curation, and ethics alongside core "
        "astronomy, preparing for graduate study and data-intensive careers."
    ),
    "uiuc-astrophysics-bslas": (
        "Undergraduates who want to apply the methods and principles of physics to understand "
        "the universe, building advanced astronomy and physics coursework toward graduate study "
        "in astronomy, physics, and the planetary sciences."
    ),
    "uiuc-atmospheric-sciences-bslas": (
        "Undergraduates interested in weather, climate, and the atmosphere who want preparation "
        "for careers spanning meteorology, environmental science, climate, remote sensing, "
        "broadcast, and atmospheric chemistry."
    ),
    "uiuc-biochemistry-bs": (
        "Pre-health and life-science undergraduates who want to study the molecular processes "
        "of living systems at the interface of biology and chemistry, combining laboratory "
        "technique with research experience."
    ),
    "uiuc-chemical-engineering-data-science-bs": (
        "Undergraduates who want to join the chemical engineering core with data science, "
        "applying chemistry, thermodynamics, transport, and reaction engineering alongside "
        "computational methods to process design and operation."
    ),
    "uiuc-chemistry-bslas": (
        "Undergraduates who want a flexible liberal-arts path through chemistry's organic, "
        "inorganic, physical, analytical, and biological branches, with classroom and "
        "laboratory study and room for undergraduate research."
    ),
    "uiuc-chemistry-bs": (
        "Undergraduates committed to chemistry who want the specialized, professionally "
        "certified track with a deeper core in the chemical subdisciplines and undergraduate "
        "research, preparing for chemistry careers or graduate study."
    ),
    "uiuc-classics-balas": (
        "Undergraduates drawn to the languages, literatures, and material cultures of ancient "
        "Greece and Rome who want a broad, deep liberal-arts education that sharpens critical "
        "thinking for varied career paths."
    ),
    "uiuc-communication-balas": (
        "Undergraduates who want a sophisticated understanding of communication across public "
        "and private life, from the workplace and public policy to health care and personal "
        "interactions."
    ),
    "uiuc-comparative-literature": (
        "Undergraduates who want to engage two or more literary and cultural traditions in "
        "their original languages, mastering critical interpretation and aesthetic analysis "
        "across cultures."
    ),
    "uiuc-computer-science-anthropology-bslas": (
        "Undergraduates curious about how culture, biology, and technology shape one another "
        "who want to pair computer science with anthropology, using computational tools and "
        "algorithms to analyze data from field sites and online communities."
    ),
    "uiuc-computer-science-astronomy-bs": (
        "Undergraduates who want to apply computing to astronomical problems such as data "
        "visualization, data mining, astrophysical simulation, and image processing, building "
        "an interdisciplinary foundation in both fields."
    ),
    "uiuc-computer-science-chemistry-bslas": (
        "Undergraduates fascinated by both coding and chemistry who want to apply computing, "
        "AI, and machine learning to chemical and biochemical systems and molecular design, "
        "aiming toward computational chemistry roles or graduate study."
    ),
    "uiuc-computer-science-economics-bslas": (
        "Undergraduates drawn to markets and data who want to build the programming and "
        "algorithmic skills to analyze large economic datasets, heading into data-driven "
        "economics, fintech, or further study."
    ),
    "uiuc-computer-science-geography-geographic-information-science-bslas": (
        "Undergraduates interested in maps, spatial data, and high-performance computing who "
        "want advanced programming skills for geospatial problems, pointing toward GIS, "
        "geospatial analytics, or graduate work."
    ),
    "uiuc-computer-science-linguistics-bslas": (
        "Undergraduates intrigued by language, cognition, and machine learning who want a "
        "strong computing foundation paired with rigorous linguistic training, leading toward "
        "computational linguistics and natural-language work or graduate study."
    ),
    "uiuc-computer-science-philosophy-bslas": (
        "Undergraduates who enjoy both rigorous reasoning and programming, wanting to pair "
        "computer science with philosophical inquiry into the questions technology raises, "
        "headed toward tech, ethics-focused roles, or graduate study."
    ),
    "uiuc-creative-writing-balas": (
        "Undergraduates serious about writing fiction, poetry, or creative nonfiction who want "
        "intensive workshops and close literary study, building toward a writing portfolio and "
        "creative or publishing-related careers."
    ),
    "uiuc-earth-society-environmental-sustainability-bslas": (
        "Undergraduates interested in how earth systems, society, and environmental change "
        "intersect who want an integrated natural- and social-science foundation; note this "
        "major is closing to new admissions as it transitions to the Environmental "
        "Sustainability degree."
    ),
    "uiuc-east-asian-languages-cultures-balas": (
        "Undergraduates drawn to the languages and cultures of East Asia who want deep "
        "linguistic and cultural training, preparing for careers in education, business, "
        "international relations, journalism, or the arts."
    ),
    "uiuc-econometrics-quantitative-economics-bslas": (
        "Quantitatively minded undergraduates who want a rigorous blend of econometrics, "
        "statistics, mathematics, and computing to answer economic questions with data, heading "
        "toward analytics, research, or graduate economics."
    ),
    "uiuc-economics-balas": (
        "Undergraduates curious about how economies, markets, and policy work who want a "
        "customizable foundation in economic theory and data analysis, preparing for business, "
        "policy, or further study."
    ),
    "uiuc-english-balas": (
        "Undergraduates who love reading closely and writing well, wanting to sharpen critical "
        "analysis and interpretation across texts and contexts, with paths into law, "
        "communications, education, or graduate study."
    ),
    "uiuc-environmental-sustainability-bslas": (
        "Undergraduates committed to environmental challenges who want to combine earth-system "
        "science with the social sciences and a chosen focus area, preparing for "
        "sustainability, environmental, or policy careers."
    ),
    "uiuc-french-balas": (
        "Undergraduates who enjoy French language, literature, and culture and want to read, "
        "write, and think critically in a global context, building toward international, "
        "cultural, or further academic work."
    ),
    "uiuc-teaching-french-ba": (
        "Undergraduates preparing to teach French who want grounding in second-language "
        "acquisition, linguistics, and pedagogy to design inclusive instruction, heading toward "
        "licensed classroom teaching."
    ),
    "uiuc-gender-womens-studies-balas": (
        "Undergraduates interested in how gender shapes social, political, economic, and "
        "cultural life who want a rigorously interdisciplinary education, preparing for "
        "advocacy, public-facing, or graduate work."
    ),
    "uiuc-geography-geographic-information-science-balas": (
        "Undergraduates drawn to the human and social side of geography who want to study "
        "social organization and its environmental consequences, heading toward planning, "
        "policy, or further study."
    ),
    "uiuc-geography-geographic-information-science-bslas": (
        "Undergraduates interested in geography and geographic information science who want a "
        "science-oriented, course-intensive foundation in spatial study, preparing for GIS, "
        "environmental, or analytical careers."
    ),
    "uiuc-geology-bslas": (
        "Undergraduates curious about the earth who want a flexible, liberal-arts-grounded path "
        "through geology that pairs the science with broader study, opening options across "
        "science, education, or graduate work."
    ),
    "uiuc-geology-bs": (
        "Undergraduates aiming at professional or graduate work in the earth sciences who want "
        "a specialized, rigorous curriculum in geology, geophysics, and environmental geology, "
        "heading toward environmental careers or graduate study."
    ),
    "uiuc-teaching-german-ba": (
        "Undergraduates preparing to teach German who want a multidisciplinary study of the "
        "language and culture leading to Illinois teacher licensure and classroom careers."
    ),
    "uiuc-germanic-studies-balas": (
        "Undergraduates drawn to German or Scandinavian languages and cultures who want "
        "literature, intellectual history, and language proficiency in a chosen concentration, "
        "preparing for business, cultural, or research paths."
    ),
    "uiuc-global-studies-balas": (
        "Undergraduates passionate about global issues and societies who want interdisciplinary "
        "research, writing, and language and cultural competency, preparing for international, "
        "policy, or graduate work."
    ),
    "uiuc-history-balas": (
        "Undergraduates who like investigating the past and arguing from evidence who want "
        "strong research and analytical training, opening paths into law, government, policy, "
        "education, media, and beyond."
    ),
    "uiuc-individual-plans-study": (
        "Self-directed undergraduates whose interests cross existing majors who want to design "
        "an original, individualized course of study within the liberal arts and sciences."
    ),
    "uiuc-integrative-biology-bslas": (
        "Undergraduates fascinated by how life works from molecules to ecosystems who want "
        "broad organismal and ecological training, preparing for research, health, or graduate "
        "science careers."
    ),
    "uiuc-honors": (
        "Strong undergraduates in integrative biology who want an enriched, more demanding "
        "course of study across scales of life, building toward research, health professions, "
        "or graduate science."
    ),
    "uiuc-interdisciplinary-studies-balas": (
        "Undergraduates with cross-cutting interests who want to pursue a chosen concentration "
        "spanning multiple fields, declared early in their studies, toward a tailored "
        "liberal-arts path."
    ),
    "uiuc-italian-balas": (
        "Undergraduates interested in Italy and the Mediterranean who want an interdisciplinary "
        "study of Italian language, history, culture, and literature in a global context, "
        "heading toward cultural, international, or further study."
    ),
    "uiuc-latin-american-studies-balas": (
        "Undergraduates drawn to Latin America who want to combine language study with history, "
        "politics, culture, and society in a self-designed program, preparing for "
        "international, policy, or graduate work."
    ),
    "uiuc-latina-latino-studies-balas": (
        "Undergraduates interested in Latina/o experiences in the United States who want a "
        "broad, multidisciplinary grounding in theory and research, preparing for "
        "community-facing, advocacy, or graduate work."
    ),
    "uiuc-liberal-studies-bls": (
        "Adult and returning students completing a degree who want to explore subjects across "
        "campus while building a strong liberal-arts foundation with advisor-guided coursework."
    ),
    "uiuc-linguistics-balas": (
        "Undergraduates curious about how language is structured, used, and changes who want "
        "empirical, theoretical training in its social and cognitive foundations, heading "
        "toward language-related careers or graduate study."
    ),
    "uiuc-linguistics-teaching-english-second-language-tesl-balas": (
        "Undergraduates interested in how English is learned as an additional language and how "
        "to teach it who want grounding in linguistics and assessment across proficiency "
        "levels, preparing for language-teaching careers."
    ),
    "uiuc-mathematics-bslas": (
        "Undergraduates who enjoy abstract and applied problem-solving who want a strong "
        "mathematical core plus a concentration to broaden or specialize, opening paths into "
        "analytical careers or graduate study."
    ),
    "uiuc-mathematics-computer-science-bslas": (
        "Undergraduates who like rigorous mathematics and computing who want to pair "
        "mathematical problem-solving with practical CS techniques, building flexible skills "
        "for technical careers or graduate work."
    ),
    "uiuc-molecular-cellular-biology-bslas": (
        "Pre-health and future life-science researchers who want thorough preparation across "
        "molecular biology, genetics, microbiology, cellular biology, and biochemistry before "
        "medical or graduate school."
    ),
    "uiuc-molecular-cellular-biology-data-science-bslas": (
        "Undergraduates drawn to both the bench and the dataset who want an integrated "
        "foundation in molecular and cellular biology and data science, preparing for "
        "computational life-science roles or graduate study."
    ),
    "uiuc-neuroscience-bslas": (
        "Undergraduates fascinated by how the brain works who want training spanning molecular "
        "and cellular biology through neurophysiology and systems, preparing for health "
        "professions, neuroscience research, or graduate school."
    ),
    "uiuc-philosophy-balas": (
        "Undergraduates drawn to fundamental questions about knowledge, ethics, and existence "
        "who want rigorous training in reasoning and argument, opening paths into law, public "
        "life, or graduate study."
    ),
    "uiuc-political-science-balas": (
        "Undergraduates interested in politics, government, and public affairs who want focused "
        "study in a chosen concentration, preparing for law, policy, public service, or further "
        "study."
    ),
    "uiuc-portuguese-balas": (
        "Undergraduates drawn to Brazil and the Portuguese-speaking world who want language and "
        "cultural study that connects the Americas, the Global South, and Lusophone Africa and "
        "Asia, preparing for international or further work."
    ),
    "uiuc-psychology-bslas": (
        "Undergraduates curious about mind and behavior who want a broad, research-focused "
        "curriculum, whether as a liberal-arts focus or preparation for graduate or "
        "professional school."
    ),
    "uiuc-religion-balas": (
        "Undergraduates interested in religious traditions, ideas, and practices across "
        "cultures and history who want humanities-grounded training in critical thinking and "
        "analysis, opening varied professional and graduate paths."
    ),
    "uiuc-russian-east-european-eurasian-studies-balas": (
        "Undergraduates drawn to Russia, Eastern Europe, and Eurasia who want an "
        "interdisciplinary study of this complex world region, preparing for international, "
        "policy, or graduate work."
    ),
    "uiuc-slavic-studies-balas": (
        "Undergraduates interested in Slavic languages, literatures, and cultures who want "
        "focused concentration study with advanced language and extensive literature and "
        "culture coursework, heading toward cultural or further study."
    ),
    "uiuc-sociology-balas": (
        "Undergraduates who want to understand how society works and drive social change, "
        "studying inequalities or global sociology, and preparing for research, public-service, "
        "or graduate paths."
    ),
    "uiuc-spanish-balas": (
        "Undergraduates who want advanced Spanish proficiency and intercultural understanding "
        "to connect across cultures, opening meaningful personal and professional paths or "
        "further study."
    ),
    "uiuc-teaching-spanish-ba": (
        "Undergraduates preparing to become pK-12 Spanish teachers who want focused training in "
        "language and pedagogy, heading directly toward licensed classroom teaching."
    ),
    "uiuc-statistics-bslas": (
        "Undergraduates who like modeling and making sense of data who want training in "
        "statistical and computing tools to make predictions and decisions under uncertainty, "
        "preparing for analytics careers or graduate study."
    ),
    "uiuc-statistics-computer-science-bslas": (
        "Undergraduates who want a strong computing foundation paired with advanced statistics, "
        "building skills for data-intensive technical careers or graduate work."
    ),
    "uiuc-actuarial-science-ms": (
        "Graduates with quantitative undergraduate backgrounds who want professional and "
        "advanced actuarial training plus experiential learning to launch actuarial careers."
    ),
    "uiuc-african-studies-ma": (
        "Graduate students seeking an interdisciplinary, area-studies grounding in Africa with "
        "intensive African-language training, preparing for research, professional, or doctoral "
        "work."
    ),
    "uiuc-anthropology-ma": (
        "Graduate students who want to deepen anthropological expertise, whether as a first "
        "step toward the doctorate or to apply the field to a related area, culminating in a "
        "thesis or equivalent paper."
    ),
    "uiuc-applied-mathematics-ms": (
        "Graduates aiming for careers in applied mathematics or preparation for doctoral study "
        "who want advanced, application-oriented mathematical training."
    ),
    "uiuc-art-history-ma": (
        "Graduate students preparing for college teaching, museum work, or doctoral study who "
        "want advanced background in the history of art, typically building on undergraduate "
        "study in the field."
    ),
    "uiuc-astronomy-ms": (
        "Graduate students seeking broad-based training in modern astrophysics and astronomy, "
        "often as a step toward doctoral research."
    ),
    "uiuc-atmospheric-sciences-ms": (
        "Graduate students focused on meteorology, climate, and computational analysis who want "
        "advanced coursework in the atmospheric sciences, preparing for professional or "
        "doctoral work."
    ),
    "uiuc-biochemistry-ms": (
        "Graduate students pursuing advanced molecular coursework and laboratory training in "
        "biochemistry, typically as progress within the doctoral program in molecular and "
        "cellular biology."
    ),
    "uiuc-teaching-biological-science-ms": (
        "Educators and prospective biology teachers seeking advanced preparation in the "
        "teaching of biological science; note that admissions are suspended effective Spring "
        "2027."
    ),
    "uiuc-biology-ms": (
        "Graduate students who want broad advanced training across the biological sciences, "
        "preparing for research, professional, or teaching careers."
    ),
    "uiuc-biophysics-quantitative-biology-ms": (
        "Scientifically grounded students who want to apply physics, mathematics, and "
        "computation to molecular and cellular biology through advanced quantitative "
        "coursework, often as a step toward doctoral research."
    ),
    "uiuc-cell-developmental-biology-ms": (
        "Life-science graduates seeking advanced coursework and laboratory work in molecular "
        "genetics and development, whether building toward doctoral research or strengthening "
        "their footing for further study."
    ),
    "uiuc-chemistry-ms": (
        "Chemistry graduates wanting focused, often one-year graduate coursework to deepen "
        "their training before professional work or further study."
    ),
    "uiuc-teaching-chemistry-ms": (
        "Current and prospective secondary and community-college chemistry teachers who want to "
        "pair advanced chemistry content with pedagogy to strengthen their classroom practice."
    ),
    "uiuc-classics-ma": (
        "Students drawn to the languages, literatures, and civilizations of ancient Greece and "
        "Rome who want advanced study in Greek, Latin, or both, with an option to explore the "
        "medieval world."
    ),
    "uiuc-communication-ma": (
        "Students interested in how people communicate across organizations, relationships, "
        "health, and technology who want to design an individualized research program in "
        "communication."
    ),
    "uiuc-comparative-literature-ma": (
        "Multilingual readers passionate about literature across languages and traditions who "
        "want rigorous comparative study spanning more than one foreign language alongside "
        "English."
    ),
    "uiuc-creative-writing-mfa": (
        "Emerging writers committed to fiction or poetry who want sustained, workshop-based "
        "study to develop their craft toward a serious writing life."
    ),
    "uiuc-cyberGIS-geospatial-data-science-ms": (
        "Technically minded students fascinated by geospatial data, high-performance computing, "
        "and AI who want advanced training in CyberGIS for data-driven careers across science "
        "and industry."
    ),
    "uiuc-east-asian-languages-cultures-ma": (
        "Students with strong language preparation in East Asian languages and cultures who "
        "want graduate study to deepen their expertise toward doctoral work or culturally "
        "engaged careers."
    ),
    "uiuc-ecology-evolution-conservation-biology-ms": (
        "Students passionate about biodiversity, evolution, and protecting the natural world "
        "who want flexible, interdepartmental graduate study in ecology and conservation "
        "biology."
    ),
    "uiuc-economics-ms": (
        "Students with a strong quantitative background in economics who want advanced graduate "
        "training in theory and methods, often as preparation for doctoral study or analytical "
        "careers."
    ),
    "uiuc-english-ma": (
        "Readers and writers eager to study English, American, and Anglophone literature, "
        "language, and film beyond the undergraduate level, whether advancing toward the PhD or "
        "deepening their expertise."
    ),
    "uiuc-entomology-ms": (
        "Students fascinated by insects and their biology who want mentored graduate study and "
        "laboratory training as a foundation for research or scientific careers."
    ),
    "uiuc-environmental-geology-ms": (
        "Working professionals and earth-science graduates who want a flexible, fully online "
        "master's with an individualized capstone in environmental geology to advance applied "
        "careers."
    ),
    "uiuc-european-union-studies-ma": (
        "Students interested in Europe's politics, languages, and institutions who want "
        "interdisciplinary area study toward careers in policy, international affairs, or "
        "further graduate work."
    ),
    "uiuc-evolution-ecology-behavior-ms": (
        "Students drawn to how organisms evolve, interact, and behave who want graduate "
        "training across evolution, ecology, and physiology as a base for research or "
        "scientific roles."
    ),
    "uiuc-french-ma": (
        "Advanced students of French language and culture who want specialized graduate study "
        "in French studies, applied linguistics, or related areas, often toward doctoral work "
        "or teaching."
    ),
    "uiuc-geography-ma": (
        "Students with a strong background in geography or related fields who want advanced "
        "graduate study of place, people, and environment toward research or applied careers."
    ),
    "uiuc-geography-ms": (
        "Students grounded in physical geography and GIS who want quantitative, methods-focused "
        "graduate training in geography for technical and research-oriented work."
    ),
    "uiuc-geology-ms": (
        "Earth-science students choosing between a thesis path for research and an applied, "
        "non-thesis track aimed at professional work in environmental, engineering, or applied "
        "geophysics fields."
    ),
    "uiuc-german-ma": (
        "Students of German language and culture who want to build advanced proficiency and "
        "literary and cultural analysis for teaching, research, or further graduate study."
    ),
    "uiuc-global-studies-ms": (
        "Students focused on global affairs, gender equity, and international security who want "
        "an interdisciplinary master's spanning global studies and policy for internationally "
        "engaged careers."
    ),
    "uiuc-health-communication-ms": (
        "Healthcare professionals working full time who want a fully online, asynchronous "
        "master's in health communication to strengthen their practice without leaving the job."
    ),
    "uiuc-history-ma": (
        "Students committed to historical research and analysis who, often within a doctoral "
        "path, earn the master's as an early milestone toward advanced scholarship."
    ),
    "uiuc-integrative-biology-ms": (
        "Biology students wanting a focused, one-year, course-based degree across organismal, "
        "ecological, and evolutionary biology as preparation for professional roles or further "
        "study."
    ),
    "uiuc-italian-ma": (
        "Students passionate about Italian language and culture who want a strong linguistic, "
        "cultural, and critical foundation for specialized work or teaching Italian as a second "
        "language."
    ),
    "uiuc-latin-american-studies-ma": (
        "Students engaged with Latin America who want interdisciplinary area and language "
        "study, including Indigenous languages such as Quechua, for regionally focused careers "
        "or further study."
    ),
    "uiuc-teaching-latin-ma": (
        "Classicists who want to teach Latin and Roman culture at the secondary or college "
        "level, combining Latin scholarship with pedagogy and classroom preparation."
    ),
    "uiuc-teaching-english-second-language-ma": (
        "Students whose interests lie in language pedagogy and related research who want "
        "graduate study of English structure and second-language teaching toward careers "
        "educating English learners."
    ),
    "uiuc-linguistics-ma": (
        "Students pursuing the study of language at an advanced level who earn the master's "
        "along the doctoral path as a milestone in their linguistics training."
    ),
    "uiuc-mathematics-ms": (
        "Mathematically strong students who want flexible advanced coursework as preparation "
        "for industry roles or for doctoral study in mathematics."
    ),
    "uiuc-teaching-mathematics-ms": (
        "Students who want to teach mathematics at the high school or community-college level "
        "and seek focused graduate preparation, completed in about eighteen months, in "
        "mathematics teaching."
    ),
    "uiuc-microbiology-ms": (
        "Students fascinated by microorganisms in disease, ecology, and biotechnology who want "
        "advanced coursework and laboratory work in microbiology as a foundation for research "
        "or further study."
    ),
    "uiuc-molecular-cellular-biology-ms": (
        "Students seeking a non-thesis, course-based degree to deepen molecular and cellular "
        "biology training before professional or graduate school or careers in industry, "
        "government, or academia."
    ),
    "uiuc-molecular-integrative-physiology-ms": (
        "Students interested in how cells, tissues, and organ systems function who want core "
        "physiology coursework and laboratory experience as preparation for advanced study."
    ),
    "uiuc-philosophy-ma": (
        "Students pursuing rigorous philosophical study who, within a doctoral path, earn the "
        "master's after completing the program's first stage on the way to advanced "
        "scholarship."
    ),
    "uiuc-plant-biology-ms": (
        "Students studying plant structure, function, ecology, and evolution who want mentored "
        "research through thesis or non-thesis paths, with the option to join an "
        "interdepartmental ecology program."
    ),
    "uiuc-policy-economics-ms": (
        "Students who want a strong, applied foundation in economic theory and statistical "
        "methods, with emphasis on micro, macro, and econometrics, for policy and analytical "
        "careers."
    ),
    "uiuc-political-science-ma": (
        "Students of politics and government who want advanced graduate study, with teaching "
        "experience valued especially for those aiming toward college teaching and academic "
        "careers."
    ),
    "uiuc-portuguese-ma": (
        "Students of Portuguese language and culture who want graduate study toward doctoral "
        "work, with the option to concentrate in second-language acquisition and teacher "
        "education."
    ),
    "uiuc-predictive-analytics-risk-management-ms": (
        "Quantitatively inclined students who want advanced analytical and modeling skills for "
        "risk-management careers across insurance, consulting, investment, healthcare, banking, "
        "and financial services."
    ),
    "uiuc-psychological-science-ms": (
        "Students seeking hands-on research experience paired with advanced courses in "
        "experimental techniques, working closely with a faculty mentor in a two-year, "
        "in-person program."
    ),
    "uiuc-psychology-ms": (
        "Students within the doctoral program who earn the master's as a research milestone "
        "rather than as preparation for a standalone professional position."
    ),
    "uiuc-religion-ma": (
        "Students drawn to the academic study of religion who want graduate research grounded "
        "in rich library resources, with teaching valued as part of their scholarly "
        "preparation."
    ),
    "uiuc-russian-east-european-eurasian-studies-ma": (
        "Students focused on Russia, Eastern Europe, and Eurasia who want interdisciplinary "
        "area study and primary-source research, including work in the languages of the region."
    ),
    "uiuc-slavic-languages-literatures-ma": (
        "Students seeking advanced competence in Russian or another Slavic language and its "
        "literatures and cultures, as preparation for doctoral work or careers requiring deep "
        "regional expertise."
    ),
    "uiuc-sociology-ma": (
        "Students pursuing the study of society who earn the master's as an intermediate step "
        "within the doctoral program on the way to advanced research."
    ),
    "uiuc-south-asian-middle-eastern-studies-ma": (
        "Students focused on South Asia or the Middle East who want language and area-studies "
        "preparation for doctoral work or careers requiring regional and language expertise."
    ),
    "uiuc-spanish-ma": (
        "Students who want to advance their command of Hispanic literatures, cultures, and "
        "linguistics through coursework spanning peninsular and Latin American study and "
        "second-language acquisition."
    ),
    "uiuc-statistics-ms": (
        "Quantitatively strong students who want advanced training in mathematical and applied "
        "statistics, with consulting or collaborative research experience, as preparation for "
        "analytical careers."
    ),
    "uiuc-translation-interpreting-ma": (
        "Multilingual students who want professional graduate training in translation and "
        "interpreting, with specializations spanning professional, literary, and applied work."
    ),
    "uiuc-weather-climate-risk-analytics-ms": (
        "Professionals in atmospheric science and related fields who want an online, applied "
        "master's focused on weather and climate risk and analytics for advanced practice."
    ),
    "uiuc-anthropology-phd": (
        "Research-bound students of human cultures, societies, and the past who want doctoral "
        "training and dissertation work in anthropology toward scholarship and academic "
        "careers."
    ),
    "uiuc-art-history-phd": (
        "Students aiming for scholarship and university teaching who want doctoral training and "
        "original dissertation research across periods and regions of art and architectural "
        "history."
    ),
    "uiuc-astronomy-phd": (
        "Research-driven students of astrophysics who want individually designed doctoral "
        "programs in close contact with faculty, working toward original research at the "
        "frontier of the field."
    ),
    "uiuc-atmospheric-sciences-phd": (
        "Students drawn to research on the atmosphere, from chemistry and aerosols to climate "
        "modeling and cloud physics, who want doctoral training toward scientific careers and "
        "applications."
    ),
    "uiuc-biochemistry-phd": (
        "Research-focused students who want to pursue original dissertation work across "
        "structural biology, enzymology, gene regulation, and molecular biophysics within a "
        "broad network of laboratories."
    ),
    "uiuc-biology-phd": (
        "Research-bound biologists drawn to areas such as animal behavior, conservation, "
        "ecology, evolution, genetics, and physiology who want doctoral training toward "
        "scientific scholarship."
    ),
    "uiuc-biophysics-quantitative-biology-phd": (
        "Research-driven scientists who want to join laboratories using physical and "
        "computational methods to study molecular machines, cellular dynamics, and biological "
        "systems through doctoral research."
    ),
    "uiuc-cell-developmental-biology-phd": (
        "Research-bound students fascinated by how cells function and organisms develop who "
        "want to pursue dissertation work in eukaryotic cell biology, developmental biology, or "
        "molecular genetics, headed toward academic or research careers in the life sciences."
    ),
    "uiuc-chemistry-phd": (
        "Doctoral-minded chemists who want to specialize deeply in an area such as analytical, "
        "organic, inorganic, materials, physical chemistry, or chemical biology and complete "
        "original research over roughly five years toward careers in research, academia, or "
        "industry."
    ),
    "uiuc-classical-philology-phd": (
        "Classics scholars with a master's-level foundation who want advanced study of both "
        "Greek and Latin and original dissertation research, headed toward university teaching "
        "and research in the ancient world."
    ),
    "uiuc-communication-phd": (
        "Researchers with strong communication training and a master's degree who want to "
        "investigate human communication in depth, preparing for academic and research careers "
        "in the field."
    ),
    "uiuc-comparative-literature-phd": (
        "Scholars drawn to literature across languages and traditions who want advanced "
        "graduate coursework and dissertation research, headed toward university teaching and "
        "research in comparative literary study."
    ),
    "uiuc-east-asian-languages-cultures-phd": (
        "Students concentrating on China, Japan, or Korea who want doctoral specialization in "
        "culture, language acquisition, or language pedagogy, headed toward research and "
        "teaching careers in East Asian studies."
    ),
    "uiuc-ecology-evolution-conservation-biology-phd": (
        "Researchers studying biological diversity and its conservation across populations, "
        "species, and ecosystems who want individualized, cross-departmental doctoral training "
        "toward careers in ecological and conservation research."
    ),
    "uiuc-economics-phd": (
        "Quantitatively rigorous students ready to master microeconomics, macroeconomics, and "
        "econometrics at the doctoral level and produce original research, headed toward "
        "academic, research, or policy careers in economics."
    ),
    "uiuc-english-phd": (
        "Students of literature committed to the doctorate from the outset who want advanced "
        "graduate study and original scholarship, preparing for academic and research careers "
        "in English."
    ),
    "uiuc-entomology-phd": (
        "Students fascinated by insects, from beginners to the well-versed, who want a strong "
        "foundation in basic biology and specialized research skills, headed toward "
        "doctoral-level careers in entomological research."
    ),
    "uiuc-evolution-ecology-behavior-phd": (
        "Doctoral students of organismal biology who want to build expertise across evolution, "
        "ecology, behavior, and physiology, preparing for research careers studying living "
        "systems."
    ),
    "uiuc-french-phd": (
        "Advanced students of French language, literature, and culture who want graduate "
        "specialization and original dissertation research, headed toward academic and research "
        "careers in French studies."
    ),
    "uiuc-geography-phd": (
        "Researchers ready to design an individualized program around geographic questions, "
        "complete original projects, and qualify for doctoral candidacy, preparing for academic "
        "and research careers in geography."
    ),
    "uiuc-geology-phd": (
        "Earth-science researchers prepared to carry out original geological investigation "
        "through preliminary and final oral examinations and a dissertation, headed toward "
        "research and academic careers in geology."
    ),
    "uiuc-german-phd": (
        "Scholars of German language, literature, and culture across periods and critical "
        "approaches who want to center original dissertation research, preparing for academic "
        "and research careers."
    ),
    "uiuc-history-phd": (
        "Students committed to the doctorate in history who want advanced graduate coursework "
        "and original archival research, headed toward university teaching and research "
        "careers."
    ),
    "uiuc-italian-phd": (
        "Students drawn to Italian Studies, Mediterranean Studies, and related fields who want "
        "doctoral training as researchers, completing coursework and original research toward "
        "an academic career."
    ),
    "uiuc-linguistics-phd": (
        "Students of language structure and analysis who want grounding in major areas of "
        "linguistic theory and method and training to become independent researchers in one or "
        "more subfields."
    ),
    "uiuc-mathematics-phd": (
        "Mathematically motivated students who want to explore advanced areas such as algebra, "
        "analysis, topology, or number theory and write and defend a dissertation, headed "
        "toward research and academic careers."
    ),
    "uiuc-microbiology-phd": (
        "Researchers drawn to microbial genetics, physiology, host-pathogen interaction, or "
        "microbial ecology who want dissertation research, teaching, and peer-reviewed "
        "publication, preparing for careers in microbiological research."
    ),
    "uiuc-molecular-integrative-physiology-phd": (
        "Students interested in how living systems function from cells to whole organisms who "
        "want core coursework, laboratory rotations, and dissertation research, headed toward "
        "research careers in physiology and related sciences."
    ),
    "uiuc-neuroscience-phd": (
        "Students of the brain and nervous system who want an individually tailored program "
        "built around a major and two minor areas of concentration, preparing for research "
        "careers in neuroscience."
    ),
    "uiuc-philosophy-phd": (
        "Students committed to doctoral study in philosophy who want sustained advanced "
        "training and original scholarship, headed toward academic and research careers in the "
        "discipline."
    ),
    "uiuc-plant-biology-phd": (
        "Researchers drawn to plant molecular biology, physiology, ecology, evolution, or "
        "systematics who want original dissertation research, preparing for academic and "
        "research careers in the plant sciences."
    ),
    "uiuc-political-science-phd": (
        "Students of politics and government ready for full-time doctoral study, advanced "
        "coursework, and a defended dissertation, headed toward academic, research, and policy "
        "careers in political science."
    ),
    "uiuc-portuguese-phd": (
        "Students drawn to advanced doctoral research in Portuguese studies; note that this "
        "program is not currently accepting applications, with admissions suspended as of Fall "
        "2023."
    ),
    "uiuc-psychology-phd": (
        "Students pursuing an area of specialization in psychology who want rigorous graduate "
        "coursework and original research toward the doctorate, headed toward academic and "
        "research careers."
    ),
    "uiuc-slavic-languages-literatures-phd": (
        "Scholars of Russian and other Slavic literatures, cultures, and linguistics who want "
        "advanced seminars, teaching, and original dissertation research, preparing for "
        "university research and teaching careers in Slavic studies."
    ),
    "uiuc-sociology-phd": (
        "Students drawn to a small, cohesive program with close faculty mentoring who want "
        "grounding in theory and methods plus ongoing professional development, headed toward "
        "doctoral research careers in sociology."
    ),
    "uiuc-spanish-phd": (
        "Researchers in Hispanic and Luso-Brazilian literatures and cultures or in Hispanic "
        "linguistics and second-language acquisition who want advanced seminars, teaching, and "
        "a dissertation, preparing for university careers."
    ),
    "uiuc-statistics-phd": (
        "Students ready to build deep theoretical and methodological expertise in statistics "
        "through coursework, qualifying examinations, and original research, headed toward "
        "leadership in research, teaching, and collaboration across academia, industry, and "
        "research settings."
    ),
    "uiuc-master-laws-llm": (
        "Lawyers and professionals, including foreign-educated students, who want an "
        "introduction to the U.S. legal system and the chance to specialize in an area of "
        "academic or professional interest, advancing their legal careers."
    ),
    "uiuc-master-studies-msl": (
        "Professionals who hold a bachelor's degree and want focused graduate study of law "
        "without pursuing a practicing law degree, building legal literacy for their careers."
    ),
    "uiuc-science-law-jsd": (
        "Accomplished legal scholars with strong analytic and research ability who want "
        "extended study, research, and scholarly writing, primarily preparing for academic "
        "careers in law."
    ),
    "uiuc-law-jd": (
        "Students ready to pursue a three-year professional legal education that blends "
        "doctrinal law, theoretical perspectives, and real-world skills, headed toward careers "
        "as practicing attorneys."
    ),
    "uiuc-human-resources-industrial-relations-mhrir": (
        "Students drawn to human resources and labor relations who want a professional master's "
        "foundation for careers in the field, or a stepping stone toward doctoral study in law "
        "and related professional areas."
    ),
    "uiuc-human-resources-industrial-relations-phd": (
        "Research-oriented students of labor and employment relations who want "
        "interdisciplinary, in-residence doctoral training, typically headed toward teaching "
        "and research careers at business or industrial relations schools."
    ),
    "uiuc-advertising-bs": (
        "Undergraduates curious about how advertising shapes business, culture, and the "
        "products and media we consume who want to learn brand strategy and communication, "
        "building a foundation for careers in the advertising field."
    ),
    "uiuc-computer-science-advertising-bs": (
        "Undergraduates who want a career in advertising with a strong technology focus, "
        "combining computing and data science with advertising coursework toward roles at the "
        "intersection of the two fields."
    ),
    "uiuc-journalism-bs": (
        "Undergraduates who want to report on the people, ideas, and events of a democratic "
        "society and learn reporting, writing, editing, producing, and multimedia skills, "
        "building a foundation for careers in journalism."
    ),
    "uiuc-media-ba": (
        "Undergraduates who want a well-rounded, interdisciplinary education across "
        "advertising, journalism, and media and cinema studies, building a flexible foundation "
        "for careers in the media industry."
    ),
    "uiuc-media-cinema-studies-bs": (
        "Undergraduates interested in media, film, and visual culture who want skills for the "
        "media, information, and creative industries, with chances for original research, media "
        "production, and internships toward careers in those fields."
    ),
    "uiuc-sports-media-ba": (
        "Undergraduates passionate about sports who want an interdisciplinary education in "
        "sports media, building a foundation for careers as broadcasters, public relations and "
        "strategic communication professionals, or content creators."
    ),
    "uiuc-advertising-ms": (
        "Students who want advanced, strategy-focused study of advertising grounded in consumer "
        "insight, media, and campaign research, building professional expertise in effective "
        "communication."
    ),
    "uiuc-journalism-ms": (
        "Students who want professional journalism training for roles across news outlets, "
        "nonprofits, higher education, and government communication, where strong journalistic "
        "skills are valued."
    ),
    "uiuc-strategic-brand-communication-ms": (
        "Working professionals who want an online master's in strategic brand communication "
        "within an advertising department, advancing their expertise in building and managing "
        "brands."
    ),
    "uiuc-communications-media-phd": (
        "Researchers drawn to interdisciplinary study of communication and media across "
        "advertising, journalism, and media and cinema studies who want doctoral training "
        "toward academic and research careers."
    ),
    "uiuc-social-work-bsw": (
        "Undergraduates committed to helping others who want a professional foundation in "
        "social work, available through traditional or upper-level completer paths, preparing "
        "for entry into the field."
    ),
    "uiuc-leadership-social-change": (
        "Educators and professionals who want graduate preparation in leadership and social "
        "change for careers as academic professionals, adult educators, corporate trainers, "
        "policy analysts, or administrators."
    ),
    "uiuc-social-work-msw": (
        "Students pursuing professional social work practice who want a CSWE-accredited "
        "master's available on campus or online, preparing for careers as practicing social "
        "workers."
    ),
    "uiuc-social-work-phd": (
        "Research-oriented students who enter with an MSW or other master's and want "
        "interdisciplinary doctoral training across social welfare policy and social work "
        "scholarship, headed toward research and academic careers."
    ),
    "uiuc-applied-veterinary-sciences-mvs": (
        "Professionals in the animal health industry who want to sharpen critical thinking and "
        "broaden their knowledge through a versatile applied master's, advancing their careers "
        "in the field."
    ),
    "uiuc-medical-science-comparative-biosciences-ms": (
        "Students interested in the biology of animals and humans across physiology, "
        "pharmacology, toxicology, neuroscience, and reproductive biology who want "
        "research-centered graduate training in comparative biosciences."
    ),
    "uiuc-livestock-systems-health-mvs": (
        "Working professionals focused on food-producing animals who want an applied, roughly "
        "two-year professional master's, building critical-thinking skills for careers in "
        "specialized clinical practice and industry."
    ),
    "uiuc-medical-science-pathobiology-ms": (
        "Students drawn to complex problems in human and animal health at the cellular, host, "
        "and population levels who want research-centered graduate training, preparing for "
        "careers in academia, industry, and public health."
    ),
    "uiuc-clinical-medicine-ms": (
        "Veterinarians who want advanced coursework and mentored research in clinical specialty "
        "areas such as surgery and internal medicine, preparing for research and teaching "
        "careers in clinical veterinary medicine."
    ),
    "uiuc-medical-science-comparative-biosciences-phd": (
        "Research-bound students of animal and human biology across physiology, pharmacology, "
        "toxicology, neuroscience, and reproductive biology who want doctoral training toward "
        "research and academic careers in comparative biosciences."
    ),
    "uiuc-medical-science-pathobiology-phd": (
        "Researchers drawn to specialties such as epidemiology, infectious diseases, "
        "immunology, virology, or pathology who want doctoral training in pathobiology, "
        "preparing for research careers in human and animal health."
    ),
    "uiuc-veterinary-medicine-dvm": (
        "Students committed to becoming veterinarians who want a clinically focused "
        "professional curriculum that prepares broadly trained graduates to enter a wide range "
        "of veterinary fields."
    ),
}
