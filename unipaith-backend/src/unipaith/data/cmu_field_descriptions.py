"""Field-specific program description clauses for Carnegie Mellon University.

Each entry states something concrete about what CMU's program in that field covers —
never a credential/school classification stub. Sources: CMU school and department
program pages (cmu.edu/admission, csd.cmu.edu, ml.cmu.edu, lti.cmu.edu, ri.cmu.edu,
hcii.cmu.edu, s3d.cmu.edu, compbio.cmu.edu, engineering.cmu.edu, mcs.cmu.edu,
dietrich.cmu.edu, cfa.cmu.edu, tepper.cmu.edu, heinz.cmu.edu, africa.engineering.cmu.edu,
cmist.cmu.edu, privacy.cs.cmu.edu, cyLab).
"""

# ruff: noqa: E501

SLUG_DESCRIPTIONS: dict[str, str] = {
    # ===== School of Computer Science =====
    "cmu-cs-bs": (
        "Spans algorithms, systems, programming languages, and AI theory in CMU's U.S. News "
        "#1-ranked Computer Science Department with undergraduate research in SCS labs."
    ),
    "cmu-ai-bs": (
        "The nation's first dedicated undergraduate AI degree, combining machine learning, "
        "NLP, computer vision, and robotics coursework across SCS institutes."
    ),
    "cmu-compbio-bs": (
        "Integrates genomics, structural biology, and machine-learning methods through the "
        "Ray and Stephanie Lane Computational Biology Department's wet-lab and compute pipelines."
    ),
    "cmu-hci-bs": (
        "Trains user-centered design, usability evaluation, and interaction prototyping in "
        "the Human-Computer Interaction Institute's studio and research settings."
    ),
    "cmu-robotics-bs": (
        "Undergraduate robotics study through the Robotics Institute — founded in 1979 — "
        "covering manipulation, perception, and autonomous systems."
    ),
    "cmu-mscs": (
        "A research-oriented master's spanning SCS areas from systems and theory to AI, "
        "with access to the Machine Learning Department and Robotics Institute."
    ),
    "cmu-cs-phd": (
        "Doctoral research across CMU's top-ranked CS areas including programming languages, "
        "systems, theory, graphics, and human–computer interaction."
    ),
    "cmu-ms-ml": (
        "Core and elective coursework in statistical learning, deep learning, and "
        "optimization through the world's first academic Machine Learning Department (2006)."
    ),
    "cmu-ml-phd": (
        "Ph.D. research in probabilistic modeling, reinforcement learning, and large-scale "
        "learning systems within the pioneering Machine Learning Department."
    ),
    "cmu-mlt": (
        "LTI training in speech recognition, machine translation, information retrieval, "
        "and dialogue systems with project-based NLP and speech labs."
    ),
    "cmu-miis": (
        "Applied language-technology curriculum pairing search engines, question answering, "
        "and multilingual NLP with industry-style capstone projects."
    ),
    "cmu-mcds": (
        "Large-scale data pipelines, distributed systems, and analytics engineering for "
        "scientific and web-scale datasets through the LTI's MCDS track."
    ),
    "cmu-msaii": (
        "Entrepreneurship and product development around AI systems — from model building "
        "to startup formation — in the LTI's innovation-focused master's."
    ),
    "cmu-lti-phd": (
        "Doctoral work in computational linguistics, speech, IR, and machine learning for "
        "language at the Language Technologies Institute."
    ),
    "cmu-msr": (
        "Graduate robotics spanning perception, planning, control, and field robotics "
        "within the Robotics Institute's research ecosystem."
    ),
    "cmu-mrsd": (
        "Team-based product development for commercial robotic systems — hardware, software, "
        "and systems integration — in the MRSD professional program."
    ),
    "cmu-mscv": (
        "Computer vision and machine perception coursework covering 3-D reconstruction, "
        "object recognition, and visual learning at the Robotics Institute."
    ),
    "cmu-robotics-phd": (
        "Doctoral research in autonomous vehicles, legged locomotion, human–robot "
        "collaboration, and field robotics at the Robotics Institute."
    ),
    "cmu-mhci": (
        "A one-year professional master's in interaction design, user research, and "
        "prototyping through HCII's studio-based curriculum and industry capstone."
    ),
    "cmu-msle": (
        "Learning engineering and educational technology design — analytics, tutoring "
        "systems, and instructional design — through the METALS program at HCII."
    ),
    "cmu-hci-phd": (
        "Doctoral study of social computing, accessibility, design methods, and "
        "human-centered AI in the Human-Computer Interaction Institute."
    ),
    "cmu-mse": (
        "Professional software-engineering practice covering architecture, quality, "
        "requirements, and team delivery in the Software and Societal Systems Department."
    ),
    "cmu-mse-online": (
        "The same studio- and project-based software-engineering curriculum as the on-campus "
        "MSE, delivered remotely for working engineers."
    ),
    "cmu-msit-privacy": (
        "Privacy-by-design engineering, data governance, and risk analysis aligned with "
        "CMU's Privacy Engineering program and CyLab security research."
    ),
    "cmu-se-phd": (
        "Empirical and design-oriented doctoral research on software architecture, "
        "developer productivity, and dependable systems in S3D."
    ),
    "cmu-societal-computing-phd": (
        "Doctoral work on algorithmic fairness, platform governance, misinformation, and "
        "the societal impacts of computing in S3D's Societal Computing group."
    ),
    "cmu-ms-compbio": (
        "Graduate training in computational genomics, structural bioinformatics, and "
        "statistical genetics through Lane Computational Biology."
    ),
    "cmu-compbio-phd": (
        "Ph.D. research integrating high-throughput biology, structural methods, and "
        "machine learning for disease and evolution questions."
    ),
    "cmu-ms-automated-science": (
        "Robot-assisted biological experimentation and closed-loop lab automation for "
        "systems biology through the Automated Science master's."
    ),
    # ===== College of Engineering =====
    "cmu-cheme-bs": (
        "Process design, transport phenomena, and reaction engineering with CMU strengths "
        "in process systems and sustainable chemical manufacturing."
    ),
    "cmu-civil-bs": (
        "Infrastructure, structural analysis, and civil systems with CMU's emphasis on "
        "smart cities and resilient built environments."
    ),
    "cmu-environ-bs": (
        "Water quality, environmental systems, and sustainability engineering within "
        "Civil & Environmental Engineering's green-infrastructure research."
    ),
    "cmu-ece-bs": (
        "Circuits, signals, embedded systems, and computer engineering with access to "
        "CMU's robotics, AI, and hardware–software co-design labs."
    ),
    "cmu-mse-bs": (
        "Materials processing, characterization, and computational materials science in "
        "CMU's cross-disciplinary materials research community."
    ),
    "cmu-meche-bs": (
        "Thermodynamics, fluid mechanics, and mechanical design with ties to CMU "
        "robotics, energy systems, and advanced manufacturing."
    ),
    "cmu-bme-bs": (
        "An additional major pairing engineering fundamentals with neural engineering, "
        "medical devices, and Pittsburgh medical-center collaborations."
    ),
    "cmu-ms-ece": (
        "Graduate ECE spanning communications, signal processing, robotics hardware, and "
        "VLSI with Silicon Valley and Pittsburgh research options."
    ),
    "cmu-ms-se-sv": (
        "Software-engineering master's delivered at CMU Silicon Valley, emphasizing "
        "product development in the Bay Area tech ecosystem."
    ),
    "cmu-msaie-ece": (
        "AI-engineering coursework applied to sensing, edge inference, and intelligent "
        "embedded systems within Electrical & Computer Engineering."
    ),
    "cmu-ece-phd": (
        "Doctoral research in wireless systems, computer architecture, control, and "
        "hardware for robotics and AI at ECE."
    ),
    "cmu-ms-meche": (
        "Coursework-based mechanical engineering covering energy, manufacturing, and "
        "design with CMU's robotics and thermal-systems labs."
    ),
    "cmu-ms-meche-research": (
        "Research-track mechanical engineering thesis work in biomechanics, combustion, "
        "or advanced manufacturing at MechE."
    ),
    "cmu-ms-meche-advanced": (
        "Advanced-study MechE master's for depth in thermal fluids, design, or controls "
        "without a full research thesis requirement."
    ),
    "cmu-msaie-meche": (
        "Applies machine learning and AI methods to mechanical systems — prognostics, "
        "design optimization, and intelligent manufacturing."
    ),
    "cmu-meche-phd": (
        "Ph.D. research in energy conversion, micro/nano mechanics, bio-inspired design, "
        "and robotics mechanics at MechE."
    ),
    "cmu-ms-cee": (
        "Graduate civil engineering in structures, geotechnics, and environmental systems "
        "with Pittsburgh urban-infrastructure projects."
    ),
    "cmu-ms-cee-research": (
        "Research-oriented CEE master's with thesis work in hydrology, structural health "
        "monitoring, or sustainable infrastructure."
    ),
    "cmu-msaie-civil": (
        "AI methods for civil infrastructure — predictive maintenance, smart sensing, and "
        "data-driven structural assessment."
    ),
    "cmu-ms-cce": (
        "Combines civil engineering with computing for infrastructure informatics, GIS, "
        "and sensor-network monitoring of built systems."
    ),
    "cmu-cee-phd": (
        "Doctoral study of climate-resilient infrastructure, water resources, and "
        "computational mechanics in Civil & Environmental Engineering."
    ),
    "cmu-ms-cheme": (
        "Applied-study chemical engineering covering process optimization, energy, and "
        "bioprocess design for industry roles."
    ),
    "cmu-mche": (
        "Practice-oriented Master of Chemical Engineering emphasizing process design, "
        "safety, and plant-scale engineering."
    ),
    "cmu-ms-cse": (
        "Computational systems engineering — modeling, simulation, and optimization of "
        "complex chemical and energy processes."
    ),
    "cmu-msaie-cheme": (
        "AI and data-driven methods for chemical process control, materials discovery, "
        "and pharmaceutical manufacturing."
    ),
    "cmu-ms-btpe": (
        "Biotechnology and pharmaceutical engineering spanning bioprocessing, drug "
        "formulation, and GMP-scale production design."
    ),
    "cmu-cheme-phd": (
        "Ph.D. research in catalysis, electrochemical energy, process systems, and "
        "computational reaction engineering at ChemE."
    ),
    "cmu-ms-matsci": (
        "Coursework master's in materials processing, mechanical behavior, and "
        "characterization techniques for industry careers."
    ),
    "cmu-ms-matsci-research": (
        "Research-track materials science thesis in alloys, polymers, or electronic "
        "materials with CMU's shared fabrication facilities."
    ),
    "cmu-ms-cmse": (
        "Computational materials modeling — DFT, molecular dynamics, and ML for materials "
        "discovery — in MSE's simulation labs."
    ),
    "cmu-matsci-phd": (
        "Doctoral work on energy-storage materials, additive manufacturing, and "
        "nanostructured materials at MSE."
    ),
    "cmu-ms-bme": (
        "Research master's in neural engineering, medical imaging, or tissue interfaces "
        "with UPMC and Pittsburgh health-system partners."
    ),
    "cmu-ms-bme-applied": (
        "Applied biomedical engineering covering device design, regulatory pathways, and "
        "clinical translation without a research thesis."
    ),
    "cmu-bme-phd": (
        "Ph.D. research in brain–machine interfaces, cardiovascular devices, and "
        "computational physiology at CMU BME."
    ),
    "cmu-ms-epp": (
        "Engineering & Public Policy analysis of energy systems, climate policy, and "
        "technology risk using quantitative decision models."
    ),
    "cmu-epp-phd": (
        "Doctoral research on energy transitions, innovation policy, and engineering "
        "ethics through EPP's interdisciplinary methods."
    ),
    "cmu-msin": (
        "Information Networking Institute training in distributed systems, cloud "
        "architecture, and large-scale network operations."
    ),
    "cmu-msis": (
        "Hands-on information-security curriculum aligned with CMU's CyLab and CERT "
        "Division expertise in vulnerability analysis and incident response."
    ),
    "cmu-msaie-is": (
        "AI-engineering methods for threat detection, secure ML, and adversarial "
        "robustness within the Information Networking Institute."
    ),
    "cmu-msit-is": (
        "Bicoastal information-security master's splitting time between Pittsburgh and "
        "Silicon Valley with CyLab-affiliated faculty."
    ),
    "cmu-msmite": (
        "Mobile and IoT engineering — embedded connectivity, edge computing, and "
        "device security — in INI's bicoastal format."
    ),
    "cmu-miips": (
        "Integrated Innovation Institute product-development studio combining engineering, "
        "design, and business for new product and service launches."
    ),
    "cmu-miips-online": (
        "Remote version of MIIPS' cross-functional innovation curriculum for global "
        "product-development teams."
    ),
    "cmu-mssm": (
        "Software-management hybrid program for product leaders covering agile delivery, "
        "roadmapping, and SaaS business models."
    ),
    "cmu-ms-etim": (
        "Engineering & Technology Innovation Management on technology commercialization, "
        "venture creation, and R&D portfolio strategy."
    ),
    "cmu-africa-msece": (
        "CMU-Africa ECE master's in Kigali training engineers for continental "
        "infrastructure, telecom, and embedded-systems needs."
    ),
    "cmu-africa-msit": (
        "Information-technology master's at CMU-Africa focused on scalable systems for "
        "East African public-sector and industry applications."
    ),
    "cmu-africa-mseai": (
        "Engineering AI master's at CMU-Africa applying machine learning to agriculture, "
        "health, and resource challenges across the continent."
    ),
    # ===== Mellon College of Science =====
    "cmu-biosci-bs": (
        "Molecular, cellular, and organismal biology with CMU's quantitative and "
        "computational life-sciences research culture."
    ),
    "cmu-neuro-bs": (
        "Neuroscience undergraduate study spanning cognitive, systems, and molecular "
        "levels with ties to CMU's BrainHub initiative."
    ),
    "cmu-chem-bs": (
        "Synthesis, physical chemistry, and chemical biology with access to CMU "
        "spectroscopy and materials-characterization facilities."
    ),
    "cmu-math-bs": (
        "Pure and applied mathematical sciences — analysis, algebra, probability, and "
        "discrete math — feeding CMU's CS and ML ecosystem."
    ),
    "cmu-compfin-bs": (
        "Undergraduate computational finance combining stochastic calculus, programming, "
        "and markets coursework with the MSCF pipeline."
    ),
    "cmu-physics-bs": (
        "Experimental and theoretical physics including condensed matter, particle "
        "physics, and cosmology on CMU's Oakland campus."
    ),
    "cmu-ms-qbb": (
        "Quantitative biology and bioinformatics master's integrating statistics, "
        "genomics pipelines, and high-throughput data analysis."
    ),
    "cmu-biosci-phd": (
        "Ph.D. research in cell biology, microbiology, and developmental genetics with "
        "CMU's collaborative life-sciences labs."
    ),
    "cmu-chem-phd": (
        "Doctoral chemistry research in catalysis, spectroscopy, and chemical biology "
        "with interdisciplinary MCS collaborations."
    ),
    "cmu-physics-phd": (
        "Graduate physics spanning condensed-matter theory, cosmology, and particle "
        "experiments including McWilliams Center astrophysics."
    ),
    "cmu-astro-phd": (
        "Astronomy and astrophysics doctoral work at the McWilliams Center for Cosmology "
        "on dark energy, galaxies, and gravitational waves."
    ),
    "cmu-ms-modern-physics": (
        "Coursework master's in modern physics covering quantum mechanics, statistical "
        "mechanics, and contemporary research topics."
    ),
    "cmu-math-phd": (
        "Ph.D. research in analysis, logic, combinatorics, and applied mathematics within "
        "CMU's top-ranked mathematical sciences department."
    ),
    "cmu-da-math": (
        "Doctor of Arts focused on mathematical exposition, teaching, and scholarship "
        "rather than a traditional research-only Ph.D."
    ),
    "cmu-aco-phd": (
        "Algorithms, Combinatorics, and Optimization joint Ph.D. spanning Math, Tepper, "
        "and CS on discrete optimization and graph theory."
    ),
    "cmu-ms-das": (
        "Data Analytics for Science master's teaching Python, statistics, and ML for "
        "domain scientists across MCS disciplines."
    ),
    # ===== Dietrich College of Humanities and Social Sciences =====
    "cmu-econ-bs": (
        "Microeconomics, econometrics, and policy analysis with CMU's quantitative "
        "tradition and behavioral-economics research groups."
    ),
    "cmu-creative-writing-ba": (
        "Workshop-based fiction, poetry, and creative nonfiction in Dietrich's English "
        "department with Pittsburgh literary community ties."
    ),
    "cmu-professional-writing-ba": (
        "Technical communication, documentation, and professional rhetoric for science, "
        "policy, and industry writing careers."
    ),
    "cmu-history-ba": (
        "Social and political history with archival research methods and CMU's strengths "
        "in science-and-technology history."
    ),
    "cmu-global-studies-ba": (
        "Transnational politics, development, and cultural analysis drawing on History "
        "and CMIST security-policy perspectives."
    ),
    "cmu-ir-bs": (
        "International relations and politics through CMIST — security studies, "
        "technology policy, and grand-strategy coursework."
    ),
    "cmu-linguistics-ba": (
        "Formal linguistics, phonetics, and computational language science bridging "
        "Dietrich and SCS language-technology research."
    ),
    "cmu-philosophy-ba": (
        "Analytic philosophy, logic, and ethics with CMU's renowned strengths in "
        "formal epistemology and philosophy of science."
    ),
    "cmu-logic-computation-bs": (
        "Interdisciplinary logic, computability, and formal methods linking Philosophy, "
        "Math, and Computer Science foundations."
    ),
    "cmu-psychology-bs": (
        "Cognitive, developmental, and social psychology with CMU's experiment-based "
        "training and brain-imaging collaborations."
    ),
    "cmu-cognitive-science-bs": (
        "Mind, brain, and computation integrating psychology, linguistics, neuroscience, "
        "and AI models of cognition."
    ),
    "cmu-decision-science-bs": (
        "Behavioral decision research, judgment under uncertainty, and policy-relevant "
        "experiments in Social and Decision Sciences."
    ),
    "cmu-statistics-bs": (
        "Probability, inference, and data visualization with CMU's cross-college "
        "statistics faculty linking Dietrich and MCS."
    ),
    "cmu-stats-ml-bs": (
        "Joint statistics and machine-learning curriculum bridging Dietrich's Statistical "
        "Data Science group and the ML Department."
    ),
    "cmu-information-systems-bs": (
        "Undergraduate IS combines technology, organizations, and analytics — a precursor "
        "to Heinz's information-systems management tradition."
    ),
    "cmu-mads": (
        "Applied Data Science master's teaching Python, causal inference, and ML for "
        "social-science and industry analytics roles."
    ),
    "cmu-ms-statistics": (
        "Graduate statistics covering linear models, Bayesian methods, and high-dimensional "
        "inference with research or applied tracks."
    ),
    "cmu-statistics-phd": (
        "Ph.D. research in statistical theory, nonparametrics, and data-science methods "
        "at CMU's Statistics & Data Science department."
    ),
    "cmu-stats-ml-phd": (
        "Joint doctoral training in statistical learning theory, Bayesian ML, and "
        "large-scale inference across Stats and the ML Department."
    ),
    "cmu-cert-fds-online": (
        "Online graduate certificate in data-science foundations — programming, statistics, "
        "and visualization — from CMU's Statistics & Data Science faculty."
    ),
    "cmu-psychology-phd": (
        "Doctoral psychology spanning cognitive science, developmental, and social "
        "research with CMU's experiment and neuroimaging labs."
    ),
    "cmu-cogneuro-phd": (
        "Cognitive neuroscience Ph.D. linking brain imaging, computational modeling, and "
        "behavioral experiments at CMU Psychology."
    ),
    "cmu-ma-gcat": (
        "Global communication and applied translation training for multilingual media, "
        "localization, and cross-cultural messaging."
    ),
    "cmu-ma-lcs": (
        "Literary and cultural studies master's examining texts, media, and cultural "
        "theory with interdisciplinary Dietrich seminars."
    ),
    "cmu-mapw": (
        "Professional writing master's in technical communication, content strategy, and "
        "UX writing for technology and science organizations."
    ),
    "cmu-phd-rhetoric": (
        "Doctoral rhetoric research on argument, digital discourse, and science "
        "communication in Dietrich English."
    ),
    "cmu-phd-lcs": (
        "Ph.D. in literary and cultural studies with archival, theoretical, and "
        "digital-humanities methods in English."
    ),
    "cmu-history-phd": (
        "History doctoral work in social, political, and science-and-technology history "
        "with Pittsburgh archival resources."
    ),
    "cmu-philosophy-phd": (
        "Graduate philosophy emphasizing logic, formal epistemology, ethics, and "
        "philosophy of mind at CMU's analytic tradition."
    ),
    "cmu-ms-lcm": (
        "Logic, Computation, and Methodology master's in formal logic, proof theory, and "
        "philosophy-of-mathematics foundations."
    ),
    "cmu-bdr-phd": (
        "Behavioral Decision Research Ph.D. on judgment, heuristics, and policy "
        "experiments in Social and Decision Sciences."
    ),
    "cmu-ma-alsla": (
        "Applied linguistics and second-language acquisition for ESL pedagogy, language "
        "assessment, and classroom research."
    ),
    "cmu-mits": (
        "Information Technology Strategy master's through CMIST on cyber policy, "
        "emerging technology, and national-security strategy."
    ),
    "cmu-msstair": (
        "Security, Technology, and International Relations combining CMIST policy analysis "
        "with technical cybersecurity foundations."
    ),
    "cmu-mint": (
        "Neural Technologies master's from the Neuroscience Institute on brain–machine "
        "interfaces, neuroimaging tools, and neural-device engineering."
    ),
    "cmu-pnc-phd": (
        "Neural Computation Ph.D. integrating machine learning, neurophysiology, and "
        "computational models of brain function."
    ),
    "cmu-psn-phd": (
        "Systems Neuroscience doctoral research on circuits, behavior, and neural dynamics "
        "at CMU's Neuroscience Institute."
    ),
    "cmu-comp-cultural-phd": (
        "Computational Cultural Studies Ph.D. applying NLP, network analysis, and digital "
        "archives to literature and media corpora."
    ),
    "cmu-alsla-phd": (
        "Doctoral applied linguistics on language pedagogy, bilingualism, and "
        "corpus-based second-language research."
    ),
    # ===== College of Fine Arts =====
    "cmu-barch": (
        "NAAB-accredited architecture studio sequence with CMU's technology-forward "
        "design labs and urban Pittsburgh context."
    ),
    "cmu-art-bfa": (
        "Studio art across painting, sculpture, and new media with CFA's Wiegand Gallery "
        "and interdisciplinary technology collaborations."
    ),
    "cmu-design-bdes": (
        "Undergraduate communication and industrial design emphasizing research-through-"
        "making and human-centered product systems."
    ),
    "cmu-drama-bfa": (
        "Conservatory training in acting, musical theatre, and production with CMU Drama's "
        "professional summer-stock and industry showcases."
    ),
    "cmu-music-bfa": (
        "Performance-focused music study in CFA's School of Music with Pittsburgh Symphony "
        "and chamber-music partnerships."
    ),
    "cmu-music-technology-bs": (
        "Music and Technology combines acoustics, DSP, and computer music with SCS and CFA "
        "recording and synthesis labs."
    ),
    "cmu-march": (
        "Professional architecture master's with advanced studios in sustainable design, "
        "computational fabrication, and urban systems."
    ),
    "cmu-maad": (
        "Advanced Architectural Design post-professional studio research in experimental "
        "form, robotics, and material systems."
    ),
    "cmu-ms-msrsd": (
        "Regenerative and Sustainable Design master's on net-zero buildings, ecological "
        "materials, and climate-adaptive architecture."
    ),
    "cmu-mud": (
        "Urban Design master's addressing transit-oriented development, public space, and "
        "Pittsburgh post-industrial revitalization."
    ),
    "cmu-arch-phd": (
        "Architecture Ph.D. on design theory, history, and building-science research in "
        "CMU's technology-integrated architecture culture."
    ),
    "cmu-art-mfa": (
        "MFA studio practice with graduate critiques, solo exhibitions, and cross-media "
        "experimentation in CFA's School of Art."
    ),
    "cmu-mdes": (
        "Design for Interactions master's in service design, UX, and social innovation "
        "through CMU Design's research-through-making studios."
    ),
    "cmu-ma-design": (
        "Research-oriented MA Design exploring design theory, ethnography, and speculative "
        "futures before professional MDes work."
    ),
    "cmu-design-phd": (
        "Transition Design doctoral research on long-horizon societal change, wicked "
        "problems, and systemic design interventions."
    ),
    "cmu-drama-mfa-directing": (
        "MFA directing with season productions, new-play development, and CMU Drama's "
        "professional theatre partnerships."
    ),
    "cmu-drama-mfa-writing": (
        "Dramatic writing MFA developing plays, screenplays, and episodic scripts through "
        "workshops and staged readings."
    ),
    "cmu-drama-mfa-design": (
        "Production-design MFA in scenery, costumes, lighting, and media for live "
        "performance and immersive theatre."
    ),
    "cmu-mm": (
        "Master of Music in performance, composition, or conducting with conservatory "
        "ensembles and recital requirements."
    ),
    "cmu-ms-music-tech": (
        "Music & Technology graduate work in audio engineering, music information retrieval, "
        "and interactive sound systems."
    ),
    "cmu-mm-music-ed": (
        "Music Education master's combining pedagogy, ensemble leadership, and "
        "community-music partnerships in Pittsburgh schools."
    ),
    "cmu-mscd": (
        "Computational Design master's applying scripting, generative design, and "
        "fabrication robotics to architectural form-finding."
    ),
    "cmu-msbpd": (
        "Building Performance & Diagnostics on post-occupancy evaluation, energy modeling, "
        "and forensic building-systems analysis."
    ),
    "cmu-msaecm": (
        "Architecture-Engineering-Construction Management integrating BIM, project "
        "delivery, and capital-project analytics."
    ),
    "cmu-ddes": (
        "Doctor of Design practitioner-scholar doctorate advancing design knowledge through "
        "built work and applied research."
    ),
    # ===== Tepper School of Business =====
    "cmu-mba": (
        "Full-time MBA rooted in Tepper's management-science tradition — optimization, "
        "analytics, and data-driven leadership with experiential strategy labs."
    ),
    "cmu-mba-online": (
        "Online Hybrid MBA delivering Tepper's analytics-heavy core with Access Weekend "
        "immersions and the same quantitative curriculum."
    ),
    "cmu-msba": (
        "Business Analytics master's combining machine learning, prescriptive analytics, "
        "and capstone consulting with Pittsburgh industry partners."
    ),
    "cmu-msba-online": (
        "Online MSBA teaching Python, SQL, and ML for marketing, operations, and finance "
        "analytics from Tepper faculty."
    ),
    "cmu-msm": (
        "MS in Management for non-business graduates covering finance, strategy, and "
        "analytics before career pivot or MBA prep."
    ),
    "cmu-mspm": (
        "Joint SCS–Tepper product-management master's on agile development, roadmapping, "
        "and go-to-market for technology products."
    ),
    "cmu-mscf": (
        "Computational Finance — stochastic calculus, C++ pricing engines, and markets — "
        "with Pittsburgh and New York City trading-floor immersions."
    ),
    "cmu-tepper-phd": (
        "Business Administration Ph.D. in accounting, finance, marketing, OB, or operations "
        "with Tepper's quantitative research culture."
    ),
    # ===== Heinz College of Information Systems and Public Policy =====
    "cmu-mism": (
        "Information Systems Management on enterprise architecture, IT strategy, and "
        "analytics in Heinz's 16-month Pittsburgh program."
    ),
    "cmu-mism-bida": (
        "MISM Business Intelligence & Data Analytics track emphasizing warehouses, "
        "visualization, and large-scale business data pipelines."
    ),
    "cmu-msit-online": (
        "Online MSIT for IT leaders covering cloud migration, cybersecurity governance, "
        "and digital transformation from Heinz faculty."
    ),
    "cmu-msispm": (
        "Information Security Policy & Management bridging technical security with risk "
        "governance and executive decision-making at Heinz."
    ),
    "cmu-aim": (
        "Artificial Intelligence Systems Management on deploying ML in organizations — "
        "MLOps, ethics, and AI product strategy at Heinz."
    ),
    "cmu-heinz-ism-phd": (
        "Ph.D. in Information Systems & Management researching digital platforms, "
        "health IT, and data-driven organizational change."
    ),
    "cmu-msppm": (
        "Public Policy & Management on evidence-based policy, program evaluation, and "
        "Heinz's intelligent-action analytics tradition."
    ),
    "cmu-msppm-da": (
        "MSPPM Data Analytics track applying statistics and ML to housing, education, and "
        "social-policy datasets for government decisions."
    ),
    "cmu-msppm-dc": (
        "Washington, D.C. MSPPM cohort studying federal policy, regulation, and legislative "
        "process with Capitol Hill internships."
    ),
    "cmu-mshca": (
        "Health Care Analytics on claims data, clinical informatics, and predictive models "
        "for hospital and payer organizations."
    ),
    "cmu-mmm": (
        "Medical Management for physician leaders on health-system operations, quality "
        "metrics, and value-based care strategy."
    ),
    "cmu-mpm": (
        "Public Management for nonprofit and government executives on budgeting, stakeholder "
        "engagement, and performance measurement."
    ),
    "cmu-heinz-ppm-phd": (
        "Public Policy & Management Ph.D. on urban policy, education reform, and "
        "computational social science for civic outcomes."
    ),
    "cmu-mam": (
        "Arts Management on venue operations, cultural policy, fundraising, and audience "
        "development for museums and performing arts."
    ),
    "cmu-meim": (
        "Entertainment Industry Management split between Pittsburgh and Los Angeles on "
        "film, TV, and games business strategy."
    ),
}
