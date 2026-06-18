"""Field-specific program description clauses for Princeton University.

Each entry states something concrete about what Princeton's program in that field
covers — never a credential/school classification stub. Sources: Princeton University
Undergraduate Admission (admission.princeton.edu/academics/degrees-departments), the
Office of the Dean of the Faculty academic divisions page (dof.princeton.edu),
individual department program pages (e.g. cs.princeton.edu, orfe.princeton.edu,
spia.princeton.edu, architecture.princeton.edu, molbio.princeton.edu,
astrophysics.princeton.edu, aas.princeton.edu, nes.princeton.edu, eas.princeton.edu,
fit.princeton.edu, spo.princeton.edu), the Undergraduate Announcement field-of-study
pages (ua.princeton.edu/fields-study), and Graduate School degree requirements
(gradschool.princeton.edu).
"""

# ruff: noqa: E501

FIELD_DESCRIPTIONS: dict[str, str] = {
    "Anthropology": (
        "Princeton anthropology combines sociocultural ethnography, biological anthropology, "
        "and archaeology with long-running field programs and museum collections study."
    ),
    "Applied Mathematics": (
        "Princeton's Program in Applied and Computational Mathematics (PACM) trains students "
        "in modeling, numerical analysis, and scientific computing tied to ORFE and physics research."
    ),
    "Architectural Sciences and Technology": (
        "Graduate research in building science, environmental systems, and digital fabrication "
        "within Princeton's School of Architecture and its design-technology labs."
    ),
    "Architecture": (
        "Princeton's School of Architecture runs design studios with architectural history and "
        "theory — the undergraduate A.B. is a liberal-arts path; the NAAB-accredited M.Arch. "
        "prepares students for licensure."
    ),
    "Area Studies": (
        "Regional concentrations — including Near Eastern, East Asian, African, and Latin American "
        "studies — combine language training with history and politics across the humanities division."
    ),
    "Astronomy and Astrophysics": (
        "Princeton astrophysical sciences spans observational cosmology, exoplanets, and "
        "gravitational-wave astronomy with access to Peyton Hall observatories and national "
        "telescope partnerships."
    ),
    "Atmospheric Sciences and Meteorology": (
        "Atmospheric and climate dynamics research through Princeton's Geosciences department "
        "and the High Meadows Environmental Institute's climate-science faculty."
    ),
    "Biochemistry, Biophysics and Molecular Biology": (
        "Princeton's Molecular Biology department covers genetics, structural biology, and "
        "quantitative cell biology with NIH-funded labs across the natural-sciences division."
    ),
    "Biological/Biosystems Engineering": (
        "Chemical and biological engineering at SEAS applies transport phenomena and reaction "
        "engineering to biotechnology, energy, and sustainable materials."
    ),
    "Biomathematics, Bioinformatics, and Computational Biology": (
        "Quantitative biology through PACM and Molecular Biology — genomics pipelines, "
        "statistical genetics, and computational neuroscience on Princeton's research campus."
    ),
    "Chemical Engineering": (
        "SEAS chemical and biological engineering spans reaction engineering, transport phenomena, "
        "and materials for energy and biotechnology applications."
    ),
    "Chemistry": (
        "Princeton chemistry runs organic, inorganic, physical, and chemical-biology groups "
        "with shared instrumentation in the Frick Chemistry Laboratory."
    ),
    "Civil Engineering": (
        "Civil and environmental engineering at SEAS covers structures, hydrology, and "
        "environmental systems with field work tied to the Andlinger Center for Energy and the Environment."
    ),
    "Classics and Classical Languages, Literatures, and Linguistics": (
        "Princeton Classics combines Greek and Latin philology with papyrology and "
        "archaeological fieldwork — one of the oldest classics departments in the United States."
    ),
    "Computer Science": (
        "Princeton computer science — the university's largest major — spans theory, systems, "
        "AI, and machine learning through SEAS with close ties to the Center for Statistics "
        "and Machine Learning."
    ),
    "Demography": (
        "Graduate demography through Princeton's Office of Population Research (OPR) — fertility, "
        "mortality, migration, and population-health research with global field sites."
    ),
    "Ecology and Evolutionary Biology": (
        "Ecology and evolutionary biology at Princeton combines field ecology, evolutionary genetics, "
        "and conservation with research at the Princeton Environmental Institute and global field stations."
    ),
    "Economics": (
        "Princeton economics is empirically rigorous — microeconomics, macroeconomics, and "
        "econometrics with faculty whose research spans finance, development, and public economics."
    ),
    "Electrical, Electronics, and Communications Engineering": (
        "Electrical and computer engineering at SEAS covers circuits, photonics, and networked "
        "systems; the one-year M.Eng. is coursework-based for practicing engineers."
    ),
    "Engineering Physics": (
        "Engineering physics coursework at SEAS bridges applied physics with electrical and "
        "mechanical engineering for students pursuing quantitative device and systems design."
    ),
    "English Language and Literature, General": (
        "Princeton English combines literary history, criticism, and creative writing with "
        "small seminars and the Firestone Library's special collections."
    ),
    "Ethnic, Cultural Minority, Gender, and Group Studies": (
        "Princeton's Department of African American Studies examines the historic achievements "
        "and struggles of African-descended people in the United States and their relationship "
        "to African and African-descended people worldwide, through history, literature, and the "
        "social sciences."
    ),
    "East Asian Studies": (
        "Princeton East Asian Studies trains students in the literature, history, anthropology, "
        "and media and cultural studies of China, Korea, and Japan across premodern and "
        "contemporary contexts, paired with intensive study of an East Asian language."
    ),
    "Near Eastern Studies": (
        "Princeton's Department of Near Eastern Studies pairs competence in a Near Eastern "
        "language — Arabic, Hebrew, Persian, or Turkish — with study of the history, literature, "
        "religion, law, and politics of the ancient, medieval, and modern Near East."
    ),
    "French and Italian": (
        "Princeton's Department of French and Italian offers four tracks spanning French and "
        "Italian language, literature, and culture, with the option to combine the language with "
        "another discipline or a creative art and study abroad."
    ),
    "Spanish and Portuguese": (
        "Princeton's Department of Spanish and Portuguese studies the literatures, cultures, "
        "societies, and politics of the Spanish- and Portuguese-speaking worlds across four "
        "tracks, from single-language study to interdisciplinary and creative-arts paths."
    ),
    "Fine and Studio Arts": (
        "Art and Archaeology at Princeton pairs studio practice in painting, photography, and "
        "sculpture with art-history study and the Princeton University Art Museum collections."
    ),
    "Geological and Earth Sciences/Geosciences": (
        "Princeton Geosciences covers geology, geophysics, and paleoclimate with field camps, "
        "isotope geochemistry labs, and climate research through the High Meadows Environmental Institute."
    ),
    "Germanic Languages, Literatures, and Linguistics": (
        "Princeton German department trains students in German language, literature, and "
        "intellectual history from the medieval period through contemporary culture."
    ),
    "History": (
        "Princeton history spans every region and period — from ancient to contemporary — with "
        "emphasis on archival research and the Shelby Cullom Davis Center for historical studies."
    ),
    "Linguistic, Comparative, and Related Language Studies and Services": (
        "Princeton linguistics examines syntax, semantics, phonetics, and language acquisition "
        "with ties to cognitive science and the Program in Linguistics faculty."
    ),
    "Mathematics": (
        "Princeton mathematics covers pure and applied analysis, algebra, geometry, and "
        "number theory — home to the National Research Council's top-ranked graduate program."
    ),
    "Mechanical Engineering": (
        "Mechanical and aerospace engineering at SEAS spans fluid mechanics, robotics, "
        "propulsion, and materials with research in the Composites Manufacturing Laboratory."
    ),
    "Multi/Interdisciplinary Studies, Other": (
        "Princeton's independent concentration allows undergraduates to design a custom major "
        "combining courses across divisions with faculty-supervised junior and senior theses."
    ),
    "Music": (
        "Princeton music combines performance, composition, and musicology with the Woolworth "
        "Center for Musical Studies and the Richardson Auditorium concert series."
    ),
    "Natural Resources Conservation and Research": (
        "Environmental and conservation research through Princeton's High Meadows Environmental "
        "Institute linking ecology, policy, and sustainable-development field projects."
    ),
    "Neurobiology and Neurosciences": (
        "Princeton neuroscience spans molecular, cellular, and systems levels — from neural "
        "circuits to cognitive neuroscience through the Princeton Neuroscience Institute."
    ),
    "Operations Research": (
        "Operations research and financial engineering (ORFE) applies optimization, probability, "
        "and statistics to finance, networks, and data science — one of Princeton's signature "
        "quantitative majors."
    ),
    "Philosophy": (
        "Princeton philosophy emphasizes logic, ethics, metaphysics, and the history of philosophy "
        "with a leading graduate program and the Center for Human Values."
    ),
    "Physics": (
        "Princeton physics spans particle theory, condensed matter, and biophysics with the "
        "Princeton Plasma Physics Laboratory and Institute for Advanced Study collaborations nearby."
    ),
    "Political Science and Government": (
        "Princeton's Politics department covers American politics, comparative politics, "
        "international relations, and political theory with the Bobst Center for Peace and Justice."
    ),
    "Public Policy Analysis": (
        "SPIA's policy curriculum trains undergraduates and MPA candidates in quantitative "
        "policy analysis, economics, and leadership for public service — fully funded for MPA students."
    ),
    "Religion/Religious Studies": (
        "Princeton religion examines scriptures, theology, and religious history across traditions "
        "with the Center for the Study of Religion and interdisciplinary humanities ties."
    ),
    "Research and Experimental Psychology": (
        "Princeton psychology covers cognitive, social, developmental, and systems neuroscience "
        "with the Princeton Neuroscience Institute and laboratory-based junior independent work."
    ),
    "Romance Languages, Literatures, and Linguistics": (
        "French, Italian, and Spanish language and literature at Princeton with study-abroad "
        "programs and the Humanities Council's cross-cultural events."
    ),
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": (
        "Princeton Slavic languages covers Russian, Polish, and Czech literature and culture "
        "with the Program in Russian, East European, and Eurasian Studies."
    ),
    "Sociology": (
        "Princeton sociology examines social inequality, organizations, and culture with "
        "quantitative and ethnographic methods and the Office of Population Research affiliations."
    ),
    "Teacher Education and Professional Development, Specific Levels and Methods": (
        "Princeton does not operate a standalone teacher-certification program; education-policy "
        "coursework appears through SPIA and the Program in Teacher Preparation for select students."
    ),
}

# CIP / federal field titles → canonical FIELD_DESCRIPTIONS keys.
FIELD_ALIASES: dict[str, str] = {
    "Fine and Studio Arts": "Fine and Studio Arts",
    "Political Science and Government": "Political Science and Government",
    "Research and Experimental Psychology": "Research and Experimental Psychology",
    "English Language and Literature, General": "English Language and Literature, General",
    "Geological and Earth Sciences/Geosciences": "Geological and Earth Sciences/Geosciences",
    "Neurobiology and Neurosciences": "Neurobiology and Neurosciences",
    "Ecology, Evolution, Systematics, and Population Biology": (
        "Ecology and Evolutionary Biology"
    ),
    "Biochemistry, Biophysics and Molecular Biology": (
        "Biochemistry, Biophysics and Molecular Biology"
    ),
    "Mechanical Engineering": "Mechanical Engineering",
    "Operations Research": "Operations Research",
    "Electrical, Electronics, and Communications Engineering": (
        "Electrical, Electronics, and Communications Engineering"
    ),
}

# Per-slug overrides where the program-specific fact differs from the field default.
SLUG_DESCRIPTIONS: dict[str, str] = {
    "princeton-architecture-bs": (
        "Princeton's B.A. in Architecture blends design studios with architectural history, "
        "theory, and urbanism within the humanities division — a liberal-arts path that "
        "feeds leading M.Arch. and Ph.D. programs rather than conferring NAAB licensure."
    ),
    "princeton-architecture-ms": (
        "Princeton's NAAB-accredited professional Master of Architecture (M.Arch.) is a "
        "studio-centered degree for students pursuing architectural licensure — typically "
        "three years for students without a pre-professional background, with a rigorous "
        "sequence in design, building technology, and history/theory."
    ),
    "princeton-chemical-engineering-ms": (
        "The M.S.E. in Chemical and Biological Engineering is a research-based graduate "
        "degree — typically 1.5–2 years — grounded in transport, thermodynamics, and "
        "reaction engineering with thesis research in energy, bioengineering, and materials."
    ),
    "princeton-civil-engineering-ms": (
        "The M.S.E. in Civil and Environmental Engineering is a research-based graduate "
        "degree spanning structures, environmental systems, hydrology, and sustainable "
        "infrastructure — typically completed within two years of residence."
    ),
    "princeton-electrical-electronics-and-communications-engineering-ms": (
        "Princeton's M.Eng. in Electrical and Computer Engineering is a one-year, "
        "coursework-based master's for practicing engineers — ECE does not offer an "
        "M.S.E.; candidates must demonstrate external financial support."
    ),
    "princeton-mechanical-engineering-ms": (
        "The M.S.E. in Mechanical and Aerospace Engineering is a research-based graduate "
        "degree in dynamics, fluid mechanics, robotics, and materials — typically "
        "completed within two years with faculty-supervised thesis research."
    ),
    "princeton-computer-science-bs": (
        "Princeton's flagship and largest major — computer science, offered as both "
        "the A.B. and the B.S.E., spanning theory, systems, AI and machine learning."
    ),
    "princeton-public-affairs-mpa": (
        "The two-year Master in Public Affairs — a fully-funded graduate degree in "
        "policy analysis and leadership for public service through SPIA."
    ),
}
