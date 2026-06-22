"""Field-specific program description clauses for Cornell University.

Each entry states something concrete about what Cornell's program in that field
covers — never a credential/school classification stub, and only Cornell's OWN
verified units (no peer-institution landmarks). Sources: Cornell school and
department program pages (cornell.edu, as.cornell.edu, cals.cornell.edu,
engineering.cornell.edu / duffield.cornell.edu, johnson.cornell.edu,
sha.cornell.edu, ilr.cornell.edu, aap.cornell.edu, bowers.cornell.edu,
publicpolicy.cornell.edu, lawschool.cornell.edu, vet.cornell.edu,
astro.cornell.edu, physics.cornell.edu, chemistry.cornell.edu, cnf.cornell.edu,
pma.cornell.edu, einaudi.cornell.edu, philosophy.cornell.edu).

De-contamination pass (2026-06-19, cornelldecontam1): the prior build copied peer
institutions' descriptions and find-replaced the campus token, leaving foreign
academic units (from Penn, Berkeley, and Johns Hopkins) and Penn Vet's clinical
center wrongly attributed to Cornell rows. Every foreign unit has been replaced
with Cornell's own verified unit or a true generic clause, allowlist-checked
against Cornell's published org chart (REPAIR_BACKLOG CRITICAL #1; SKILL miss #8
allowlist).
"""

# ruff: noqa: E501

FIELD_DESCRIPTIONS: dict[str, str] = {
    'Aerospace, Aeronautical, and Astronautical/Space Engineering': (
        "Cornell Sibley School aerospace coursework covers orbital mechanics, propulsion, and autonomous flight with ties to Cornell's nanosatellite labs."
    ),
    'Agricultural Business and Management': (
        "Dyson School applied economics and management covers agribusiness finance, "
        "food-industry strategy, and policy with CALS field research across New York State."
    ),
    'Agricultural Engineering': (
        "Engineering design for irrigation, precision agriculture, and biological systems drawing on Cornell's bioengineering and environmental-engineering labs."
    ),
    'Agriculture, General': (
        "CALS agriculture foundations span crop and soil science, sustainable farming, and Cornell's land-grant extension network across New York State."
    ),
    'Allied Health Diagnostic, Intervention, and Treatment Professions': (
        "Weill Cornell allied-health pathways prepare clinical technologists and diagnostic specialists within New York City's academic medical center."
    ),
    'Animal Sciences': (
        'CALS animal science covers livestock production, nutrition, genetics, and welfare with research at the Cornell University animal science teaching barns.'
    ),
    'Anthropology': (
        'Arts and Sciences anthropology combines archaeological field schools, biological anthropology, and sociocultural ethnography with the Cornell Institute of Archaeology and Material Studies and global research sites.'
    ),
    'Apparel and Textiles': (
        'Human Ecology fiber science and apparel design combines material testing, sustainable textiles, and industry partnerships through the Cornell Costume and Textile Collection.'
    ),
    'Applied Horticulture and Horticultural Business Services': (
        'CALS horticulture coursework combines greenhouse management, plant breeding, and viticulture with Finger Lakes field sites and Cornell AgriTech.'
    ),
    'Applied Mathematics': (
        "Applied mathematics at Cornell spans modeling, numerical analysis, "
        "and scientific computing applied to engineering, finance, and biology, with graduate ties to the Center for Applied Mathematics."
    ),
    'Archeology': (
        'Classical and Near Eastern archaeology at Arts and Sciences includes field seasons, material-studies labs, and interdisciplinary work with art history and anthropology.'
    ),
    'Architectural History, Criticism, and Conservation': (
        'AAP architectural history examines built heritage, preservation theory, and field documentation with Ithaca and New York City studio projects.'
    ),
    'Architectural Sciences and Technology': (
        "AAP building-science coursework covers environmental controls, digital fabrication, and performance simulation in Cornell's design research labs."
    ),
    'Architecture': (
        "AAP architecture combines design studios, history and theory, and building technology in one of the nation's oldest professional architecture programs, with Ithaca urban-design field work."
    ),
    'Architecture and Related Services, Other': (
        "AAP interdisciplinary design studies span urbanism, digital fabrication, and environmental systems in Cornell's Rome and New York City programs."
    ),
    'Area Studies': (
        'Regional specializations — East Asia, Latin America, the Middle East, and South Asia — combine language immersion with political and cultural scholarship in the College of Arts and Sciences, coordinated through the Mario Einaudi Center for International Studies.'
    ),
    'Astronomy and Astrophysics': (
        'Observational and theoretical astrophysics through the Cornell Center for Astrophysics and Planetary Science and the Cornell-led CCAT Observatory (Fred Young Submillimeter Telescope).'
    ),
    'Atmospheric Sciences and Meteorology': (
        "Earth and environmental science coursework at Arts and Sciences examines climate dynamics, atmospheric chemistry, and earth-system modeling with Cornell's climate research groups."
    ),
    'Behavioral Sciences': (
        'Interdisciplinary behavioral science at Arts and Sciences examines cognition, decision making, and policy-relevant experiments linking psychology and the social sciences.'
    ),
    'Biochemistry, Biophysics and Molecular Biology': (
        'Biochemistry and biophysics at Arts and Sciences and the Weill Institute for Cell and Molecular Biology studies protein structure, enzymology, and molecular mechanisms in NIH-funded Cornell labs.'
    ),
    'Biological and Physical Sciences': (
        'CALS biological and physical sciences integrates chemistry, physics, and life-sciences foundations for pre-professional and research-track students.'
    ),
    'Biological/Biosystems Engineering': (
        'Cornell biological engineering integrates CALS life sciences with Duffield Engineering design for agricultural, environmental, and biomedical systems.'
    ),
    'Biology, General': (
        'Arts and Sciences biology spans genetics, cell biology, ecology, and neurobiology with undergraduate research in campus life-sciences institutes and the Weill Cornell research network.'
    ),
    'Biomathematics, Bioinformatics, and Computational Biology': (
        "Computational biology training pairs genomics pipelines, statistical genetics, "
        "and systems biology across Arts and Sciences, Cornell Engineering, and Weill "
        "Cornell precision-medicine initiatives."
    ),
    'Biomedical/Medical Engineering': (
        'Cornell biomedical engineering integrates device design, imaging, and tissue engineering with clinical collaboration at Weill Cornell Medicine in New York City.'
    ),
    'Botany/Plant Biology': (
        'Plant physiology, ecology, and evolutionary biology with field work at Cornell Botanic Gardens and CALS agricultural research stations.'
    ),
    'Business Administration, Management and Operations': (
        "Johnson School doctoral study in management spans organizational behavior, strategy, marketing, operations, and managerial economics, drawing on the school's analytics and entrepreneurship faculty."
    ),
    'Cell/Cellular Biology and Anatomical Sciences': (
        'Cell biology at Arts and Sciences and the Weill Institute for Cell and Molecular Biology focuses on signaling, developmental biology, and microscopy methods in cancer and immunology research labs.'
    ),
    'Chemical Engineering': (
        "The Robert Frederick Smith School of Chemical and Biomolecular Engineering spans reaction engineering, materials, and bioprocess design with ties to Cornell's energy and biotechnology research."
    ),
    'Chemistry': (
        "Cornell's Department of Chemistry and Chemical Biology runs organic, inorganic, physical, and chemical-biology research groups, several with joint appointments at Weill Cornell Medicine."
    ),
    'City/Urban, Community, and Regional Planning': (
        'AAP city and regional planning covers housing policy, transportation, and urban design with Ithaca and New York City field studios in the Department of City and Regional Planning.'
    ),
    'Civil Engineering': (
        'Civil and systems engineering at Cornell Engineering emphasizes infrastructure resilience, transportation systems, and urban hydrology.'
    ),
    'Classics and Classical Languages, Literatures, and Linguistics': (
        'Greek and Latin language, ancient history, and philology at Arts and Sciences with manuscript resources and Mediterranean archaeology ties.'
    ),
    'Communication and Media Studies': (
        "Cornell's Department of Communication in CALS covers media effects, science communication, and digital culture with social-scientific research labs."
    ),
    'Community Organization and Advocacy': (
        'Brooks School and ILR community-organizing coursework examines grassroots mobilization, policy advocacy, and labor-community coalitions.'
    ),
    'Computer Science': (
        "Cornell Bowers College computing covers algorithms, systems, AI, and theory "
        "with research groups spanning Cornell Engineering, the Cornell AI Institute, "
        "and robotics labs on campus."
    ),
    'Computer and Information Sciences, General': (
        "Broad computing foundations — programming, data structures, and information systems — within Cornell's Bowers College of Computing and Information Science."
    ),
    'Computer/Information Technology Administration and Management': (
        "Bowers College IT management spans enterprise systems, cybersecurity policy, and data governance for Cornell's computing and information-science students."
    ),
    'Culinary Arts and Related Services': (
        'SHA hospitality coursework includes culinary management, restaurant operations, and food-service entrepreneurship in Nolan School labs.'
    ),
    'Dance': (
        "Cornell's Department of Performing and Media Arts teaches dance technique, composition, and performance in the Schwartz Center for the Performing Arts."
    ),
    'Design and Applied Arts': (
        "AAP and Arts and Sciences design coursework spans visual communication, interaction design, and creative practice in Cornell's studio and fabrication facilities."
    ),
    'Drama/Theatre Arts and Stagecraft': (
        "Arts and Sciences theatre arts in the Department of Performing and Media Arts combines acting, directing, dramaturgy, and technical production with performances in the Schwartz Center."
    ),
    'East Asian Languages, Literatures, and Linguistics': (
        'Chinese, Japanese, and Korean language and cultural studies at Arts and Sciences with the East Asia Program and study-abroad pathways.'
    ),
    'Ecology, Evolution, Systematics, and Population Biology': (
        "Field ecology, evolutionary genomics, and conservation biology at Arts and Sciences with research at Cornell Botanic Gardens natural areas and global field-station partnerships."
    ),
    'Economics': (
        'Arts and Sciences and Johnson economics is empirically rigorous — faculty research spans health, trade, development, and behavioral economics.'
    ),
    'Education, General': (
        'Graduate education programs at Cornell target urban reform, special education, and evidence-based teaching in Ithaca partner districts.'
    ),
    'Electrical, Electronics, and Communications Engineering': (
        "Cornell Engineering electrical and systems engineering spans signal processing, photonics, and communications with Cornell's medical-device and robotics research groups."
    ),
    'Engineering Mechanics': (
        'Solid mechanics, fluid dynamics, and computational mechanics at Cornell Engineering support aerospace and biomedical device research.'
    ),
    'Engineering Physics': (
        'Applied physics for engineering — quantum devices, plasmas, and materials — bridging the Duffield College of Engineering and the physics department.'
    ),
    'Engineering, General': (
        "Cross-disciplinary engineering master's and doctoral study spanning Cornell Engineering's departments and research centers."
    ),
    'Engineering, Other': (
        'Flexible engineering pathways at Cornell Engineering let students combine design, computing, and lab research before declaring a specialized major.'
    ),
    'English Language and Literature, General': (
        "Arts and Sciences English in the Department of Literatures in English combines literary history, creative writing, and rhetoric with Cornell's M.F.A. program and Ithaca's literary community."
    ),
    'Environmental Design': (
        'AAP environmental design integrates landscape architecture, ecological planning, and sustainable site design with Ithaca urban greening projects.'
    ),
    'Environmental/Environmental Health Engineering': (
        'Air and water quality, exposure science, and environmental health engineering linking civil and environmental engineering with public-health research.'
    ),
    'Environmental/Natural Resources Management and Policy': (
        "CALS natural-resources policy analysis covers GIS, forest and water governance, "
        "and climate adaptation through Cornell Cooperative Extension."
    ),
    'Ethnic, Cultural Minority, Gender, and Group Studies': (
        'Arts and Sciences programs in Africana studies, gender and sexuality, and ethnic studies examine race, diaspora, and social justice with Ithaca community research.'
    ),
    'Film/Video and Photographic Arts': (
        "Arts and Sciences cinema and media studies in the Department of Performing and Media Arts covers production, documentary, and media theory with Cornell's media labs and Ithaca film internships."
    ),
    'Fine and Studio Arts': (
        'Arts and Sciences fine arts combines drawing, painting, printmaking, and new media with the Herbert F. Johnson Museum of Art and Ithaca gallery culture.'
    ),
    'Food Science and Technology': (
        "CALS food science spans sensory evaluation, food microbiology, and product development in Cornell's pilot plant and dairy-processing facilities."
    ),
    'Foods, Nutrition, and Related Services': (
        'Human Ecology nutrition science covers dietetics, community health, and metabolic research with Cornell Cooperative Extension outreach.'
    ),
    'Genetics': (
        'Genomics and genetic-analysis training at Arts and Sciences connects to the Department of Molecular Biology and Genetics and the Weill Institute for Cell and Molecular Biology.'
    ),
    'Geological and Earth Sciences/Geosciences': (
        "Earth and environmental science at Arts and Sciences studies climate, geophysics, and planetary surfaces with Cornell's paleontology and geochemistry research groups."
    ),
    'Germanic Languages, Literatures, and Linguistics': (
        'German language, literature, and culture at Arts and Sciences includes Berlin study-abroad and European intellectual-history coursework.'
    ),
    'Health Professions and Related Clinical Sciences, Other': (
        'Interdisciplinary clinical-science coursework at Weill Cornell Medicine spans specialized health disciplines with hospital and lab research access.'
    ),
    'Historic Preservation and Conservation': (
        'AAP preservation studies combine documentation, materials conservation, and heritage policy with field work across upstate New York.'
    ),
    'History': (
        "Arts and Sciences history spans American, European, global, and science-and-medicine specialties with the Cornell History Department's archival and museum partnerships."
    ),
    'Hospitality Administration/Management': (
        "The Nolan School of Hotel Administration — the world's first four-year hospitality degree — covers finance, real estate, and service operations with Statler Hotel practicum experience."
    ),
    'Housing and Human Environments': (
        'Human Ecology design and environmental analysis examines interior environments, housing policy, and sustainable building systems.'
    ),
    'Human Development, Family Studies, and Related Services': (
        "Human Ecology human development spans lifespan psychology, family policy, and Cornell's Bronfenbrenner Center for Translational Research."
    ),
    'Human Development': (
        "Human Ecology human development spans lifespan psychology, family policy, and Cornell's Bronfenbrenner Center for Translational Research."
    ),
    'Human Resources Management and Services': (
        'ILR and Johnson management coursework covers organizational behavior, talent strategy, and labor relations with Ithaca corporate and nonprofit placements.'
    ),
    'Industrial Production Technologies/Technicians': (
        'Cornell Engineering and CALS production technology coursework covers manufacturing processes, automation, and quality systems.'
    ),
    'International Agriculture': (
        "CALS international agriculture examines global food systems, development economics, and field research through Cornell's land-grant mission abroad."
    ),
    'Landscape Architecture': (
        "Site design, ecological planning, and urban landscapes in CALS landscape architecture studios — the only accredited landscape architecture program in the Ivy League — with Cornell Botanic Gardens field sites."
    ),
    'Law': (
        "Cornell Law School's J.D. and advanced legal-degree programs emphasize cross-disciplinary study and a small, collegial, clinic-rich curriculum."
    ),
    'Legal Research and Advanced Professional Studies': (
        'Cornell Law School LL.M. and advanced legal-study programs combine doctrinal coursework with cross-disciplinary legal research.'
    ),
    'Liberal Arts and Sciences, General Studies and Humanities': (
        'Arts and Sciences general studies pathways satisfy College distribution requirements across humanities, social sciences, and natural sciences for flexible degree plans.'
    ),
    'Linguistic, Comparative, and Related Language Studies and Services': (
        "Arts and Sciences linguistics covers phonetics, syntax, sociolinguistics, and computational language science with ties to Cornell's Bowers College of Computing and Information Science."
    ),
    'Management Sciences and Quantitative Methods': (
        'Johnson operations and decision-science coursework emphasizes optimization, stochastic modeling, and analytics for finance and consulting careers.'
    ),
    'Materials Engineering': (
        "Cornell Engineering materials science studies biomaterials, nanomaterials, and characterization with the Cornell NanoScale Facility (CNF) and Cornell Center for Materials Research (CCMR)."
    ),
    'Mathematics': (
        'Pure and applied mathematics at Arts and Sciences spans analysis, algebra, probability, and mathematical biology with small upper-level seminars.'
    ),
    'Mechanical Engineering': (
        'Cornell Engineering mechanical engineering and applied mechanics emphasizes design, robotics, fluid mechanics, and energy systems in the Sibley School of Mechanical and Aerospace Engineering.'
    ),
    'Medieval and Renaissance Studies': (
        "Arts and Sciences medieval studies combines Latin paleography, art history, and Cornell's world-renowned rare-book library collections."
    ),
    'Microbiological Sciences and Immunology': (
        'Microbiology and immunology at Arts and Sciences and Weill Cornell studies pathogens, host defense, and vaccine science in Cornell research labs.'
    ),
    'Multi/Interdisciplinary Studies, Other': (
        'Custom interdisciplinary majors combining methods from multiple Cornell colleges under College of Arts and Sciences advising.'
    ),
    'Music': (
        'Arts and Sciences music combines musicology, theory, and performance with Ithaca orchestra partnerships and campus ensemble opportunities.'
    ),
    'Natural Resources Conservation and Research': (
        "Cornell's CALS Department of Natural Resources and the Environment studies conservation biology, fisheries and wildlife, environmental policy, and sustainability with field research across New York State and the Cornell Botanic Gardens natural areas."
    ),
    'Neurobiology and Neurosciences': (
        'Cornell neuroscience spans cellular, cognitive, and systems levels across the Department of Neurobiology and Behavior, Cornell Neurotech, and Weill Cornell Medicine.'
    ),
    'Nuclear Engineering': (
        "Nuclear energy systems, radiation detection, and fusion research in Cornell's nuclear science and engineering program and national-lab partnerships."
    ),
    'Nutrition Sciences': (
        'Human nutrition, metabolic biology, and public-health dietetics through the Division of Nutritional Sciences and metabolic biology research.'
    ),
    'Operations Research': (
        "Optimization, stochastic modeling, and analytics in Cornell's School of Operations Research and Information Engineering (ORIE)."
    ),
    'Operations Research and Engineering': (
        "Undergraduate ORIE training in optimization, probability, and data-driven decision models within Cornell Engineering's School of Operations Research and Information Engineering."
    ),
    'Operations Research and Information Engineering': (
        "Graduate and doctoral ORIE training in optimization, stochastic modeling, financial engineering, and analytics at Cornell's School of Operations Research and Information Engineering."
    ),
    'Pharmacology and Toxicology': (
        'Pharmacology at Weill Cornell and Arts and Sciences studies drug mechanisms, chemical biology, and toxicology adjacent to Cornell drug-discovery pipelines.'
    ),
    'Philosophy': (
        "Arts and Sciences philosophy in the Sage School of Philosophy emphasizes logic, ethics, metaphysics, and philosophy of science, and edits The Philosophical Review."
    ),
    'Physics': (
        "Arts and Sciences physics covers condensed matter, particle physics, and biophysics with faculty in Cornell's Laboratory of Atomic and Solid State Physics (LASSP)."
    ),
    'Physiology, Pathology and Related Sciences': (
        'Human physiology, disease mechanisms, and pathobiology in molecular and integrative biology research labs.'
    ),
    'Plant Sciences': (
        "CALS plant sciences spans crop genetics, horticulture, and microbial biology "
        "with field stations and Cornell AgriTech research facilities."
    ),
    'Political Science and Government': (
        'Arts and Sciences political science combines American politics, comparative methods, and international relations with the Mario Einaudi Center for International Studies and Cornell in Washington.'
    ),
    'Psychology, General': (
        'Arts and Sciences psychology is among the largest majors, with research tracks in cognitive, developmental, social, and clinical science in campus psychology labs.'
    ),
    'Public Health': (
        "Cornell's Master of Public Health program spans epidemiology, biostatistics, and health policy with Weill Cornell Medicine population-health research."
    ),
    'Public Policy Analysis': (
        'Cornell Jeb E. Brooks School of Public Policy programs analyze housing, education, and health policy with the Cornell Institute for Public Affairs and Ithaca practitioner faculty.'
    ),
    'Real Estate': (
        "Johnson's real-estate program combines finance, development, and urban economics with Ithaca and New York City market case studies."
    ),
    'Religion/Religious Studies': (
        "Arts and Sciences religious studies examines world religions, theology, and religion-and-culture across an interdisciplinary program with global faculty."
    ),
    'Research and Experimental Psychology': (
        "Laboratory-based psychology at Arts and Sciences uses behavioral, cognitive, and neuroscience methods in Cornell's psychology department research institutes."
    ),
    'Rhetoric and Composition/Writing Studies': (
        "Arts and Sciences writing and rhetoric courses support the John S. Knight Institute for Writing in the Disciplines and professional communication across fields."
    ),
    'Romance Languages, Literatures, and Linguistics': (
        "French, Spanish, and Italian language and literature at Arts and Sciences include study-abroad and translation workshops through Cornell's language departments."
    ),
    'Science, Technology and Society': (
        "Arts and Sciences STS examines science policy, ethics, and the social dimensions of technology with Cornell's science-and-technology studies faculty."
    ),
    'Slavic, Baltic and Albanian Languages, Literatures, and Linguistics': (
        'Russian and East European language and literature at Arts and Sciences includes study-abroad and cultural-history coursework.'
    ),
    'Social Sciences, General': (
        'Arts and Sciences interdisciplinary social-science foundations span economics, sociology, and government before students declare a major.'
    ),
    'Social Sciences, Other': (
        'Interdisciplinary social-science coursework at Arts and Sciences integrates policy analysis, urban studies, and community-engaged research.'
    ),
    'Sociology': (
        'Arts and Sciences sociology examines urban inequality, health disparities, and social networks with Ithaca community-based research and the Cornell Population Center.'
    ),
    'Statistics': (
        'Arts and Sciences and Johnson statistics training covers inference, Bayesian methods, and high-dimensional data for finance, biostatistics, and data-science careers.'
    ),
    'Sustainability Studies': (
        "Interdisciplinary sustainability coursework spans CALS, AAP design studios, "
        "and the Cornell Atkinson Center for Sustainability research initiatives."
    ),
    'Systems Engineering': (
        "Cornell Engineering systems engineering models complex health-care, transportation, and defense systems in the Systems Engineering program's research groups."
    ),
    'Veterinary Biomedical and Clinical Sciences': (
        'Cornell Vet biomedical sciences covers comparative pathology, infectious disease, and translational research at the College of Veterinary Medicine.'
    ),
    'Veterinary Medicine': (
        "Cornell Vet's D.V.M. curriculum moves from animal health sciences to extensive clinical training at the Cornell University Hospital for Animals in Ithaca."
    ),
    'Visual and Performing Arts, Other': (
        "AAP and Arts and Sciences visual and performing arts span studio practice, critical theory, and Cornell's Schwartz Center for the Performing Arts."
    ),
    'Zoology/Animal Biology': (
        'CALS and Arts and Sciences zoology examines animal behavior, ecology, and evolutionary biology with Cornell Lab of Ornithology research access.'
    ),
}

SLUG_DESCRIPTIONS: dict[str, str] = {
    'cornell-applied-economics-bs': (
        "Applied economics and management — the Dyson School's AACSB-accredited undergraduate business degree, grounded in applied economics."
    ),
    'cornell-biology-bs': (
        'Biological sciences — a college-spanning major in genetics, cell and molecular biology, ecology and physiology (offered jointly with CALS).'
    ),
    'cornell-biomedical-sciences-bs': (
        'Biological and biomedical sciences in CALS — from molecular and organismal biology to applied life-science fields.'
    ),
    'cornell-business-administration-ms': (
        "A specialized management master's in the Johnson School covering business administration, analytics and management."
    ),
    'cornell-computer-science-bs': (
        "Cornell's flagship computing major — offered as the B.S. (College of Engineering) and the B.A. (College of Arts and Sciences), spanning theory, systems, AI and machine learning, taught through the Bowers College of Computing and Information Science."
    ),
    'cornell-computer-science-ms': (
        "The graduate Computer Science master's in the Bowers College, covering advanced systems, theory, artificial intelligence and applications."
    ),
    'cornell-dvm': (
        "The College of Veterinary Medicine's four-year D.V.M. — a top-ranked professional program in veterinary clinical and biomedical science."
    ),
    'cornell-economics-bs': (
        'Micro, macro, econometrics and economic policy in the College of Arts and Sciences.'
    ),
    'cornell-electrical-computer-eng-bs': (
        'Electrical and computer engineering — circuits, signals, devices, computer systems and communications.'
    ),
    'cornell-electrical-computer-eng-ms': (
        "The research master's in electrical and computer engineering, across devices, systems, signal processing and communications."
    ),
    'cornell-emba-americas': (
        'A hybrid Executive MBA delivered through weekend courses with synchronous online instruction plus residential sessions, for working professionals across the Americas.'
    ),
    'cornell-emha-online': (
        "The Sloan Program's Executive Master of Health Administration — a blended 18-month degree mixing synchronous and asynchronous online coursework with on-campus intensives, for working health-care leaders."
    ),
    'cornell-empa-online': (
        "The Brooks School's Executive Master of Public Administration — an 18-month blended program for working public-sector and nonprofit professionals."
    ),
    'cornell-engineering-management-meng-online': (
        'A hybrid Master of Engineering in Engineering Management combining online coursework with annual one-week on-campus intensive sessions.'
    ),
    'cornell-hotel-administration-bs': (
        "Hospitality administration — the Nolan School's flagship undergraduate degree, the original four-year collegiate hospitality program."
    ),
    'cornell-human-development-bs': (
        'Human development — the science of development across the lifespan, in the College of Human Ecology.'
    ),
    'cornell-ilr-bs': (
        "Industrial and labor relations — the ILR School's interdisciplinary undergraduate degree in work, labor markets, HR and organizations."
    ),
    'cornell-ilr-ms': (
        "The ILR School's graduate degree in human resources and labor relations (Master of Industrial and Labor Relations)."
    ),
    'cornell-information-science-bs': (
        'Information science — the study of computing in social, technical and design contexts, from data science to human-computer interaction.'
    ),
    'cornell-information-science-ms': (
        "The graduate Information Science master's, spanning data science, human-computer interaction and the social study of computing."
    ),
    'cornell-jd': (
        "Cornell Law School's three-year Juris Doctor — a small, collegial professional law degree emphasizing lawyering in the best sense."
    ),
    'cornell-legal-studies-ms-online': (
        "Cornell Law School's fully online Master of Science in Legal Studies — legal reasoning and frameworks for professionals who do not intend to practice law."
    ),
    'cornell-march': (
        "The College of Architecture, Art, and Planning's professional Master of Architecture (M.Arch I), a STEM-designated accredited degree."
    ),
    'cornell-mathematics-bs': (
        "Cornell mathematics spans pure and applied analysis, algebra, geometry, "
        "probability, and logic with graduate ties to the Center for Applied Mathematics."
    ),
    'cornell-mba': (
        "Cornell's flagship Two-Year MBA at the Samuel Curtis Johnson Graduate School of Management — a full-time residential program in Ithaca with semester-long immersions, a summer internship, and elective access across Cornell's graduate schools and Cornell Tech in New York City."
    ),
    'cornell-md': (
        "Weill Cornell Medicine's four-year M.D. — the New York City medical degree of Cornell University, taught alongside its biomedical graduate school."
    ),
    'cornell-mechanical-eng-bs': (
        'Mechanical engineering — mechanics, thermal-fluids, dynamics and controls, materials and design.'
    ),
    'cornell-meng-ms': (
        "The professional Master of Engineering — a course-based, one-year degree across Cornell Engineering's fields, with an engineering project."
    ),
    'cornell-mpa-ms': (
        'The Cornell Institute for Public Affairs MPA — a two-year, multidisciplinary professional degree in public and nonprofit policy and management.'
    ),
    'cornell-operations-research-ms': (
        'Operations research and information engineering — optimization, applied probability, statistics and financial engineering.'
    ),
    'cornell-political-science-bs': (
        'Government — American politics, comparative politics, international relations and political theory.'
    ),
    'cornell-systems-eng-ms': (
        'Systems engineering — the design, modeling and management of complex engineered systems.'
    ),
}
