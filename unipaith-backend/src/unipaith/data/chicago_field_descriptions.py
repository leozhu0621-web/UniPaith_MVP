"""Field-specific program description clauses for the University of Chicago.

Each entry states something concrete about what UChicago's program in that field covers —
never a credential/school classification stub. Sources: UChicago College Catalog
(collegecatalog.uchicago.edu), department and division program pages (economics.uchicago.edu,
cs.uchicago.edu, stat.uchicago.edu, biologicalsciences.uchicago.edu, pme.uchicago.edu),
Chicago Booth (chicagobooth.edu), Harris School of Public Policy (harris.uchicago.edu),
Law School (law.uchicago.edu), Pritzker School of Medicine (pritzker.uchicago.edu),
Crown Family School (crownschool.uchicago.edu), Divinity School (divinity.uchicago.edu),
MPCS (masters.cs.uchicago.edu), CIR (cir.uchicago.edu), MAPSS (mapss.uchicago.edu),
and MAPH (maph.uchicago.edu).
"""

# ruff: noqa: E501

FIELD_DESCRIPTIONS: dict[str, str] = {
    "Anthropology": (
        "Archaeological fieldwork, sociocultural ethnography, and linguistic anthropology "
        "with the Oriental Institute collections and long-running Chicago ethnographic "
        "field schools."
    ),
    "Applied Mathematics": (
        "Mathematical modeling, numerical analysis, and scientific computing applied to "
        "physics, economics, and data science across the Division of the Physical Sciences."
    ),
    "Area Studies": (
        "Regional concentrations — East Asia, Latin America, Middle East, and South Asia — "
        "combining language study with history and politics through the Center for East "
        "Asian Studies and related area centers."
    ),
    "Astronomy and Astrophysics": (
        "Observatory-based astrophysics and theoretical cosmology through the Department "
        "of Astronomy and Astrophysics and ties to Yerkes Observatory and Fermilab "
        "partnerships."
    ),
    "Biochemistry and Molecular Biology": (
        "Protein biochemistry, enzymology, and molecular mechanisms in the Division of "
        "the Biological Sciences with research labs adjacent to the Pritzker School of "
        "Medicine."
    ),
    "Biochemistry, Biophysics and Molecular Biology": (
        "Structural biology, biophysics, and molecular mechanisms spanning chemistry and "
        "the Biological Sciences Division's NIH-funded research institutes."
    ),
    "Biological Sciences": (
        "Integrative life-sciences study — genetics, ecology, and neurobiology — across "
        "the Division of the Biological Sciences with undergraduate research in campus "
        "and medical-center labs."
    ),
    "Biology, General": (
        "Core biology spanning molecular, organismal, and evolutionary science within the "
        "College's Biological Sciences major and the Gordon Center for Integrative Science."
    ),
    "Biomathematics, Bioinformatics, and Computational Biology": (
        "Computational genomics, statistical genetics, and systems biology linking "
        "mathematics, computer science, and the Biological Sciences Division."
    ),
    "Cell Biology": (
        "Cell-cycle regulation, signaling, and developmental mechanisms in graduate "
        "labs across the Biological Sciences Division and the Ben May Department for "
        "Cancer Research."
    ),
    "Cell/Cellular Biology and Anatomical Sciences": (
        "Microscopy-intensive cell biology and anatomical sciences coursework feeding "
        "into the Biological Sciences major and Pritzker-adjacent research labs."
    ),
    "Chemistry": (
        "Organic, inorganic, physical, and theoretical chemistry in a department whose "
        "faculty include Nobel laureates, with shared facilities in the Gordon Center "
        "for Integrative Science."
    ),
    "Cinema and Media Studies": (
        "Film history, media theory, and documentary practice through the Department of "
        "Cinema and Media Studies and screenings at the Doc Films student cinema."
    ),
    "Classics": (
        "Greek and Latin philology, ancient history, and archaeology with the Oriental "
        "Institute and one of the nation's oldest classics faculties."
    ),
    "Classics and Classical Languages, Literatures, and Linguistics": (
        "Greek, Latin, and classical-civilization coursework with papyrology and museum "
        "study through the Oriental Institute and Regenstein Library collections."
    ),
    "Clinical, Counseling and Applied Psychology": (
        "Clinical science and applied psychology bridging the Department of Psychology "
        "and the Crown Family School's evidence-based practice training."
    ),
    "Committee on International Relations": (
        "The oldest graduate international-relations program in the United States, "
        "combining political theory, security studies, and area expertise in a "
        "faculty-governed committee within the Division of the Social Sciences."
    ),
    "Computational Biology": (
        "Genomics pipelines, machine-learning for biology, and quantitative modeling "
        "through the Biological Sciences Division and the Center for Data and Computing."
    ),
    "Computer Science": (
        "Algorithms, systems, AI, and programming languages in a department whose "
        "faculty span theory and applications, with the MPCS professional master's "
        "alongside the Ph.D. program."
    ),
    "Computer and Information Sciences, General": (
        "Broad computing foundations — programming, data structures, and information "
        "systems — within the Department of Computer Science and the College Core."
    ),
    "Crown Family School of Social Work, Policy, and Practice": (
        "Clinical social work, welfare policy, and community practice through Crown "
        "Family School's A.M. program with field placements across Chicago."
    ),
    "Design and Applied Arts": (
        "Visual communication, interaction design, and creative practice in the Media "
        "Arts, Data and Design (MADD) program and Logan Center studios."
    ),
    "Division of the Humanities": (
        "Graduate humanities study — literature, philosophy, history, and the arts — "
        "anchored by the Franke Institute for the Humanities and Regenstein Library "
        "special collections."
    ),
    "Division of the Social Sciences": (
        "Graduate training in economics, sociology, political science, and related "
        "fields in the home division of the Chicago schools of economics and sociology."
    ),
    "Drama/Theatre Arts and Stagecraft": (
        "Acting, directing, dramaturgy, and stagecraft through Theater and Performance "
        "Studies and productions in the Reva and David Logan Center for the Arts."
    ),
    "East Asian Languages and Civilizations": (
        "Chinese, Japanese, and Korean language and cultural history with the Center "
        "for East Asian Studies and study-abroad pathways in East Asia."
    ),
    "East Asian Languages, Literatures, and Linguistics": (
        "Chinese, Japanese, and Korean language and literary scholarship in the "
        "Department of East Asian Languages and Civilizations."
    ),
    "Ecology and Evolution": (
        "Field ecology, evolutionary genetics, and population biology through the "
        "Department of Ecology and Evolution and the Chicago Botanic Garden partnership."
    ),
    "Ecology, Evolution, Systematics, and Population Biology": (
        "Evolutionary genomics, systematics, and conservation biology in the Ecology "
        "and Evolution department with access to the Field Museum collections."
    ),
    "Economics": (
        "Microeconomics, macroeconomics, and econometrics in the tradition of the "
        "Chicago school, with the Becker Friedman Institute for Research in Economics "
        "on campus."
    ),
    "Education": (
        "Urban schooling, curriculum, and teacher preparation through the Urban "
        "Teacher Education Program and partnerships with Chicago Public Schools."
    ),
    "English Language and Literature": (
        "Literary history, criticism, and creative writing from medieval to contemporary "
        "periods in the English Language and Literature department."
    ),
    "English Language and Literature, General": (
        "Literary analysis, poetics, and the writing workshops of the English department "
        "with the Special Collections Research Center at Regenstein Library."
    ),
    "Environment, Geography and Urbanization": (
        "Urban environmental change, spatial analysis, and policy through the "
        "Environmental and Urban Studies program and the Mansueto Institute for "
        "Urban Innovation."
    ),
    "Environmental and Urban Studies": (
        "Interdisciplinary study of cities, climate, and environmental justice combining "
        "geography, policy, and the Core's social-sciences foundations."
    ),
    "Environmental/Natural Resources Management and Policy": (
        "Resource governance, sustainability policy, and environmental economics linking "
        "Environmental and Urban Studies with Harris public-policy coursework."
    ),
    "Ethnic, Cultural Minority, Gender, and Group Studies": (
        "African and African American, Latin American, and gender-studies scholarship "
        "through the Center for the Study of Race, Politics, and Culture and related "
        "College programs."
    ),
    "Film/Video and Photographic Arts": (
        "Documentary filmmaking, photography, and media arts practice in Cinema and "
        "Media Studies and the Logan Center's production facilities."
    ),
    "Finance and Financial Management Services": (
        "Corporate finance, asset pricing, and econometric finance through Chicago Booth "
        "coursework and the Polsky Center for Entrepreneurship and Innovation."
    ),
    "Fine and Studio Arts": (
        "Painting, sculpture, printmaking, and new-media studio practice in Visual Arts "
        "and the Logan Center for the Arts."
    ),
    "Gender and Sexuality Studies": (
        "Feminist theory, LGBTQ+ studies, and gender history through the Center for the "
        "Study of Gender and Sexuality and affiliated faculty across the College."
    ),
    "Genetics": (
        "Mendelian and molecular genetics, genomics, and genetic epidemiology in the "
        "Biological Sciences Division with ties to the Institute for Genomics and Systems "
        "Biology."
    ),
    "Geography": (
        "Human and urban geography, GIS, and spatial data science through the Committee "
        "on Geographical Sciences and the Mansueto Institute."
    ),
    "Geography and Cartography": (
        "Cartography, remote sensing, and spatial analysis in graduate geography "
        "coursework within the Division of the Social Sciences."
    ),
    "Geological and Earth Sciences/Geosciences": (
        "Planetary geology, paleoclimate, and earth-system science through the Department "
        "of the Geophysical Sciences and campus isotope geochemistry labs."
    ),
    "Geophysical Sciences": (
        "Atmospheric dynamics, oceanography, and geochemistry in the Geophysical "
        "Sciences department — UChicago's home for earth and planetary science."
    ),
    "Germanic Languages, Literatures, and Linguistics": (
        "German language, literature, and intellectual history from medieval through "
        "contemporary periods in the Department of Germanic Studies."
    ),
    "Germanic Studies": (
        "German literature, philosophy, and cultural history with strengths in critical "
        "theory and the Committee on Social Thought's interdisciplinary seminars."
    ),
    "Harris School of Public Policy": (
        "Data-driven policy analysis grounded in economics and statistics — Harris's "
        "signature approach to training quantitative public leaders."
    ),
    "History": (
        "Global and U.S. history from ancient to modern eras with the Special Collections "
        "Research Center and the Nicholson Center for British Studies."
    ),
    "Humanities": (
        "Interdisciplinary humanities study through the Core curriculum, the Franke "
        "Institute, and the one-year MAPH degree in the Division of the Humanities."
    ),
    "Information Science": (
        "Data management, information policy, and human–computer interaction bridging "
        "computer science, statistics, and the Center for Data and Computing."
    ),
    "Information Science/Studies": (
        "Human-centered computing, data ethics, and information systems within the "
        "Department of Computer Science and CDAC research initiatives."
    ),
    "International Relations": (
        "Security studies, international political economy, and diplomatic history "
        "through the Committee on International Relations and political-science faculty."
    ),
    "International Relations and National Security Studies": (
        "Grand strategy, security policy, and area expertise in CIR and political-science "
        "graduate fields within the Division of the Social Sciences."
    ),
    "Law": (
        "Constitutional law, corporate law, and public-interest clinics shaped by the "
        "Law School's influential law-and-economics tradition on the Hyde Park campus."
    ),
    "Legal Research and Advanced Professional Studies": (
        "Advanced legal scholarship, LL.M. specializations, and interdisciplinary "
        "law-and-policy study at the University of Chicago Law School."
    ),
    "Legal Studies": (
        "Constitutional theory, law-and-society, and jurisprudence for undergraduates "
        "without a J.D., drawing on Law School faculty and the Core's social-sciences "
        "foundations."
    ),
    "Liberal Arts and Sciences, General Studies and Humanities": (
        "The College Core curriculum — humanities, civilization studies, and the arts — "
        "before students declare a major in the Division of the Humanities or related "
        "fields."
    ),
    "Linguistic, Comparative, and Related Language Studies and Services": (
        "Phonetics, syntax, semantics, and field linguistics in the Department of "
        "Linguistics with experimental labs and typological research."
    ),
    "Linguistics": (
        "Formal linguistics, phonology, and language acquisition in a department known "
        "for empirical and theoretical work on human language."
    ),
    "Marketing": (
        "Consumer behavior, market analytics, and brand strategy through Chicago Booth "
        "marketing coursework and behavioral-science research centers."
    ),
    "Master of Arts Program in the Humanities": (
        "MAPH — a one-year interdisciplinary M.A. across literature, philosophy, and the "
        "arts with creative-writing and digital-humanities options in the Franke "
        "Institute community."
    ),
    "Master of Arts Program in the Social Sciences": (
        "MAPSS — a one-year interdisciplinary M.A. across economics, sociology, and "
        "political science, preparing students for doctoral study and applied research."
    ),
    "Mathematics": (
        "Pure and applied mathematics — algebra, analysis, geometry, and probability — "
        "in a department with the Enrico Fermi Institute and strong ties to economics "
        "and physics."
    ),
    "Media Arts and Design": (
        "Creative coding, data visualization, and digital media in the Media Arts, Data "
        "and Design (MADD) major housed in the Logan Center for the Arts."
    ),
    "Medieval Studies": (
        "Interdisciplinary medieval history, literature, and art with manuscript study "
        "through the Special Collections Research Center and the Medieval Studies "
        "workshop."
    ),
    "Medieval and Renaissance Studies": (
        "Graduate medieval and Renaissance scholarship combining history, literature, "
        "and art history within the Division of the Humanities."
    ),
    "Microbiological Sciences and Immunology": (
        "Microbial pathogenesis, immunology, and virology in Biological Sciences labs "
        "with infectious-disease research ties to the Pritzker School of Medicine."
    ),
    "Microbiology": (
        "Bacterial genetics, microbial ecology, and host–pathogen interaction in graduate "
        "microbiology fields across the Biological Sciences Division."
    ),
    "Middle/Near Eastern and Semitic Languages, Literatures, and Linguistics": (
        "Arabic, Hebrew, and ancient Near Eastern languages with philology and archaeology "
        "through Near Eastern Languages and Civilizations and the Oriental Institute."
    ),
    "Music": (
        "Music history, theory, and performance in the Department of Music with concerts "
        "in Mandel Hall and the Logan Center."
    ),
    "Natural Resources Conservation and Research": (
        "Conservation biology and environmental science through Environmental and Urban "
        "Studies and ecology field work with the Chicago Botanic Garden."
    ),
    "Near Eastern Languages and Civilizations": (
        "Arabic, Hebrew, Persian, and ancient Near Eastern texts with the Oriental "
        "Institute's archaeological collections and field projects."
    ),
    "Neurobiology and Neurosciences": (
        "Neural circuits, cognitive neuroscience, and neurodegeneration research in "
        "psychology, biology, and the Grossman Institute for Neuroscience."
    ),
    "Neuroscience": (
        "Interdisciplinary neuroscience spanning molecular, cognitive, and computational "
        "approaches through the undergraduate Neuroscience major and Grossman Institute."
    ),
    "Nutrition Sciences": (
        "Human nutrition, metabolism, and diet-related disease through Biological "
        "Sciences coursework and ties to the Pritzker School of Medicine."
    ),
    "Nutritional Science": (
        "Nutritional biochemistry and public-health dietetics linking biology and "
        "policy-oriented study in the Biological Sciences Division."
    ),
    "Organismal Biology and Anatomy": (
        "Comparative anatomy, physiology, and organismal biology within the Biological "
        "Sciences major and the BSCD research institutes."
    ),
    "Philosophy": (
        "Logic, ethics, philosophy of science, and political philosophy in a department "
        "central to the analytic tradition and the Committee on Social Thought."
    ),
    "Physical Sciences": (
        "Graduate physical-sciences training spanning physics, chemistry, astronomy, "
        "and geophysical sciences in the Division of the Physical Sciences."
    ),
    "Physical Sciences, General": (
        "Broad physical-sciences preparation — physics, chemistry, and earth science — "
        "within the College before specialization in a Physical Sciences department."
    ),
    "Physics": (
        "Experimental and theoretical physics — particle, condensed matter, and "
        "astrophysics — through the Enrico Fermi Institute and ties to Argonne National "
        "Laboratory."
    ),
    "Physiology, Pathology and Related Sciences": (
        "Human physiology, disease mechanisms, and pathobiology linking Biological "
        "Sciences coursework to Pritzker School of Medicine research labs."
    ),
    "Political Science": (
        "American politics, comparative politics, international relations, and political "
        "theory in a department known for rational-choice and institutional analysis."
    ),
    "Political Science and Government": (
        "Empirical political science, formal theory, and public-law study in the "
        "Department of Political Science within the Division of the Social Sciences."
    ),
    "Pritzker School of Medicine": (
        "A small M.D. class with a strong emphasis on research, Pritzker's four-year "
        "curriculum integrates basic science with clinical training at the University "
        "of Chicago Medical Center."
    ),
    "Pritzker School of Molecular Engineering": (
        "Engineering at the molecular scale — quantum devices, immunoengineering, and "
        "advanced materials — in the nation's first school devoted to molecular "
        "engineering, with Argonne and Fermilab partnerships."
    ),
    "Psychology": (
        "Cognitive, developmental, social, and behavioral neuroscience in the Department "
        "of Psychology with the Grossman Institute for Neuroscience."
    ),
    "Public Health": (
        "Population health, epidemiology, and health policy through certificate and "
        "graduate pathways linking Biological Sciences and Harris policy coursework."
    ),
    "Public Health Sciences": (
        "Biostatistics, epidemiology, and health-services research in graduate fields "
        "across the Biological Sciences Division and medical-center institutes."
    ),
    "Public Policy Analysis": (
        "Quantitative policy evaluation, microeconomics, and data analysis — the analytic "
        "core shared by Harris's MPP and the College's Public Policy Studies major."
    ),
    "Public Policy Studies": (
        "Undergraduate policy analysis combining economics, statistics, and political "
        "science with Harris faculty and Chicago field placements."
    ),
    "Radio, Television, and Digital Communication": (
        "Broadcast history, digital media, and journalism practice through Cinema and "
        "Media Studies and the Logan Center's media-production facilities."
    ),
    "Research and Experimental Psychology": (
        "Graduate experimental psychology — perception, cognition, and behavioral "
        "neuroscience — in the Department of Psychology's Ph.D. program."
    ),
    "Rhetoric and Composition/Writing Studies": (
        "Academic writing, argumentation, and composition pedagogy through the Writing "
        "Program and the Core's humanities writing sequences."
    ),
    "Romance Languages and Literatures": (
        "French, Italian, Spanish, and Portuguese language and literary scholarship in "
        "the Department of Romance Languages and Literatures."
    ),
    "Romance Languages, Literatures, and Linguistics": (
        "Romance philology, literary theory, and linguistics spanning French, Italian, "
        "and Iberian traditions in the Division of the Humanities."
    ),
    "Science, Technology and Society": (
        "History of science, technology ethics, and science policy through the Science, "
        "Technology, and Society program and the Institute on the Formation of Knowledge."
    ),
    "Slavic Languages and Literatures": (
        "Russian, Polish, and East European language and literature with the Special "
        "Collections Research Center's Slavic holdings."
    ),
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": (
        "Slavic philology, literary history, and Baltic languages in the Department of "
        "Slavic Languages and Literatures."
    ),
    "Social Sciences": (
        "Interdisciplinary social-science study through the Core, MAPSS, and the "
        "Division of the Social Sciences' economics, sociology, and political-science "
        "departments."
    ),
    "Social Sciences, General": (
        "Broad social-science foundations — economics, sociology, and political science "
        "— within the College Core and MAPSS interdisciplinary curriculum."
    ),
    "Social Sciences, Other": (
        "Specialized social-science topics and interdisciplinary methods across the "
        "Division of the Social Sciences and the Becker Friedman Institute."
    ),
    "Sociology": (
        "Social stratification, urban sociology, and organizations in the home of the "
        "Chicago school of sociology and the Department of Sociology."
    ),
    "Statistics": (
        "Probability, statistical inference, and data science in the Department of "
        "Statistics — foundational to campus econometrics, biostatistics, and MPCS "
        "coursework."
    ),
    "Sustainability Studies": (
        "Climate solutions, urban sustainability, and environmental justice through "
        "Environmental and Urban Studies and the Mansueto Institute."
    ),
    "Teacher Education and Professional Development, Specific Levels and Methods": (
        "Classroom practice and Illinois certification through the Urban Teacher Education "
        "Program's residency model in Chicago schools."
    ),
    "The University of Chicago Booth School of Business": (
        "Discipline-based business education with the most flexible curriculum among top "
        "MBA programs — foundation courses, the LEAD experiential program, and "
        "thirteen-plus concentrations."
    ),
    "The University of Chicago Law School": (
        "A top-ranked J.D. program distinguished by law-and-economics, rigorous Socratic "
        "instruction, and interdisciplinary ties to Booth and Harris."
    ),
    "Theater and Performance Studies": (
        "Performance theory, acting, and dramaturgy in the Department of Theater and "
        "Performance Studies with productions at the Logan Center."
    ),
    "University of Chicago Divinity School": (
        "The academic study of religion, theology, and ministry in an ecumenical divinity "
        "school with the Martin Marty Center for the Public Understanding of Religion."
    ),
    "Visual Arts": (
        "Studio art, photography, and new media in the Department of Visual Arts and "
        "the Logan Center galleries."
    ),
    "Visual and Performing Arts, Other": (
        "Interdisciplinary visual and performing-arts study across Visual Arts, Music, "
        "Theater and Performance Studies, and the Logan Center."
    ),
    "Writing": (
        "Creative nonfiction, fiction, and poetry workshops through the English "
        "department's Creative Writing program and MAPH writing options."
    ),
}

SLUG_DESCRIPTIONS: dict[str, str] = {
    "uchicago-mba": (
        "A rigorous, discipline-based program built on the most flexible curriculum among "
        "the top business schools, requiring only a short foundation plus the experiential "
        "LEAD program before students design their own path across thirteen-plus "
        "concentrations."
    ),
    "uchicago-mpp": (
        "Harris's flagship degree, training students to use economics, statistics, and "
        "data analysis to solve public problems."
    ),
    "uchicago-jd": (
        "The Law School's three-year professional degree, shaped by the school's "
        "influential law-and-economics tradition."
    ),
    "uchicago-md": (
        "Pritzker's four-year M.D. program, distinguished by a small class size and a "
        "strong emphasis on research."
    ),
    "uchicago-social-work-am": (
        "Crown Family School's professional degree preparing clinical and administrative "
        "social-work practitioners."
    ),
    "uchicago-divinity-mdiv": (
        "The Divinity School's professional degree in the academic study and practice of "
        "religion and ministry."
    ),
    "uchicago-molecular-engineering-bs": (
        "The nation's first undergraduate major in the field, applying engineering at the "
        "molecular scale across quantum, materials, water, and immunoengineering."
    ),
    "uchicago-mpcs": (
        "A professional master's spanning software, systems, machine learning, and "
        "applications, with immersive and part-time options."
    ),
    "uchicago-statistics-ms": (
        "Graduate training in statistical theory, methodology, and computation in the "
        "Department of Statistics."
    ),
    "uchicago-cir-ma": (
        "The oldest graduate program of its kind in the United States, awarding the M.A. "
        "in international relations."
    ),
    "uchicago-mapss-ma": (
        "A one-year interdisciplinary M.A. across the social sciences, preparing students "
        "for doctoral study and applied research."
    ),
    "uchicago-maph-ma": (
        "A one-year interdisciplinary M.A. across the humanities and the arts, with "
        "creative-writing and digital-studies options."
    ),
}

FIELD_ALIASES: dict[str, str] = {
    # CIP / IPEDS comma variants → canonical FIELD_DESCRIPTIONS keys
    "Biology General": "Biology, General",
    "Biochemistry Biophysics and Molecular Biology": "Biochemistry, Biophysics and Molecular Biology",
    "Biomathematics Bioinformatics and Computational Biology": "Biomathematics, Bioinformatics, and Computational Biology",
    "Clinical Counseling and Applied Psychology": "Clinical, Counseling and Applied Psychology",
    "Computer and Information Sciences General": "Computer and Information Sciences, General",
    "East Asian Languages Literatures and Linguistics": "East Asian Languages, Literatures, and Linguistics",
    "Ecology Evolution Systematics and Population Biology": "Ecology, Evolution, Systematics, and Population Biology",
    "English Language and Literature General": "English Language and Literature, General",
    "Ethnic Cultural Minority Gender and Group Studies": "Ethnic, Cultural Minority, Gender, and Group Studies",
    "Germanic Languages Literatures and Linguistics": "Germanic Languages, Literatures, and Linguistics",
    "Liberal Arts and Sciences General Studies and Humanities": "Liberal Arts and Sciences, General Studies and Humanities",
    "Linguistic Comparative and Related Language Studies and Services": "Linguistic, Comparative, and Related Language Studies and Services",
    "Middle/Near Eastern and Semitic Languages Literatures and Linguistics": (
        "Middle/Near Eastern and Semitic Languages, Literatures, and Linguistics"
    ),
    "Classics and Classical Languages Literatures and Linguistics": (
        "Classics and Classical Languages, Literatures, and Linguistics"
    ),
    "Physiology Pathology and Related Sciences": "Physiology, Pathology and Related Sciences",
    "Romance Languages Literatures and Linguistics": "Romance Languages, Literatures, and Linguistics",
    "Slavic Baltic and Albanian Languages Literatures and Linguistics": (
        "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics"
    ),
    "Social Sciences General": "Social Sciences, General",
    "Social Sciences Other": "Social Sciences, Other",
    "Teacher Education and Professional Development Specific Levels and Methods": (
        "Teacher Education and Professional Development, Specific Levels and Methods"
    ),
    "Visual and Performing Arts Other": "Visual and Performing Arts, Other",
    "Radio Television and Digital Communication": "Radio, Television, and Digital Communication",
    "Physical Sciences General": "Physical Sciences, General",
    # UChicago department / school name variants
    "Crown Family School of Social Work Policy and Practice": (
        "Crown Family School of Social Work, Policy, and Practice"
    ),
    "Environment Geography and Urbanization": "Environment, Geography and Urbanization",
    "Social Work": "Crown Family School of Social Work, Policy, and Practice",
    "Business Administration, Management and Operations": (
        "The University of Chicago Booth School of Business"
    ),
    "Psychology, General": "Psychology",
    "Biological Sciences": "Biological Sciences",
    "Public Policy Studies": "Public Policy Studies",
    "Legal Professions and Studies, Other": "Legal Studies",
    "Non-Professional Legal Studies": "Legal Studies",
    "Health Professions (CIP 51.12)": "Pritzker School of Medicine",
    "Science Technology and Society": "Science, Technology and Society",
    "Master of Arts Program in the Social Sciences (MAPSS)": (
        "Master of Arts Program in the Social Sciences"
    ),
    "Master of Arts Program in the Humanities (MAPH)": (
        "Master of Arts Program in the Humanities"
    ),
}
