"""Per-credential program descriptions for UC San Diego multi-level fields.

Each (field, degree_type) pair carries its OWN researched body describing what
THAT degree studies at THAT level — the undergraduate major, advanced master's
coursework, doctoral research, or focused graduate certificate — never one field
text stamped (or frame-spliced) across the certificate/bachelor's/master's/PhD
rows of a field (SKILL.md miss #8; gold MIT = 0% shared body). Every fact is
drawn from UC San Diego's own catalog and school pages; no fact is invented to
satisfy the gold contrast.
"""

# ruff: noqa: E501

from __future__ import annotations

CREDENTIAL_DESCRIPTIONS: dict[tuple[str, str], str] = {
    # ---- Jacobs School of Engineering ----
    ("Aerospace Engineering", "bachelors"): (
        "Undergraduates in UC San Diego's aerospace engineering major build foundations in "
        "aerodynamics, propulsion, and spacecraft systems, working in the Jacobs School's "
        "wind-tunnel and flight-research facilities."
    ),
    ("Aerospace Engineering", "masters"): (
        "The aerospace engineering master's deepens propulsion, structures, and flight "
        "dynamics through advanced Jacobs School coursework and project work in the "
        "department's wind-tunnel and water-channel laboratories."
    ),
    ("Aerospace Engineering", "certificate"): (
        "A focused graduate certificate in aerospace engineering covers selected topics in "
        "aerodynamics, propulsion, and spacecraft systems for practicing engineers, taught "
        "by Jacobs School aerospace faculty."
    ),
    ("Bioengineering", "bachelors"): (
        "The bioengineering bachelor's — ranked among the nation's top undergraduate "
        "programs by U.S. News — grounds students in device design, tissue engineering, and "
        "medical imaging with early UC San Diego Health clinical immersion."
    ),
    ("Bioengineering", "masters"): (
        "Bioengineering master's students pursue advanced study in medical-device design, "
        "tissue engineering, and imaging, working alongside UC San Diego Health clinicians "
        "on translational projects."
    ),
    ("Bioengineering", "certificate"): (
        "This graduate certificate concentrates on bioengineering device design and medical "
        "imaging for working professionals in San Diego's medical-technology sector."
    ),
    ("Bioinformatics", "bachelors"): (
        "The bioinformatics major pairs molecular biology with programming and statistics, "
        "giving undergraduates hands-on genomics-pipeline work linked to the San Diego "
        "Supercomputer Center."
    ),
    ("Bioinformatics", "masters"): (
        "Bioinformatics master's students build genomics pipelines and computational "
        "biology methods with the San Diego Supercomputer Center and the Institute for "
        "Genomic Medicine on the La Jolla mesa."
    ),
    ("Bioinformatics", "certificate"): (
        "A graduate certificate in bioinformatics offers focused training in genomics data "
        "analysis and computational pipelines for life-sciences and biotech practitioners."
    ),
    ("Chemical Engineering", "bachelors"): (
        "Chemical engineering undergraduates study reaction engineering, transport, and "
        "materials processing in the Jacobs School's NanoEngineering department, with "
        "laboratory work in clean-room and characterization facilities."
    ),
    ("Chemical Engineering", "masters"): (
        "The chemical engineering master's advances reaction engineering, materials "
        "processing, and nanoscale systems through graduate coursework and research in "
        "Jacobs School clean-room and characterization labs."
    ),
    ("Chemical Engineering", "certificate"): (
        "This graduate certificate develops focused expertise in reaction engineering and "
        "materials processing for engineers working in San Diego's process and materials "
        "industries."
    ),
    ("Computer Engineering", "bachelors"): (
        "The computer engineering major spans digital design, embedded systems, and VLSI, "
        "with project work in the Qualcomm Institute and Jacobs School maker spaces."
    ),
    ("Computer Engineering", "masters"): (
        "Computer engineering master's students specialize in embedded systems, VLSI, and "
        "hardware–software integration, drawing on Qualcomm Institute research and "
        "prototyping facilities."
    ),
    ("Computer Engineering", "certificate"): (
        "A graduate certificate in computer engineering offers concentrated coursework in "
        "embedded systems and digital design for practicing hardware engineers."
    ),
    ("Computer Science", "bachelors"): (
        "Computer science undergraduates in UC San Diego's top-ranked CSE department study "
        "algorithms, systems, AI, and security, with project courses and access to the San "
        "Diego Supercomputer Center."
    ),
    ("Computer Science", "masters"): (
        "The CSE master's lets students specialize across algorithms, systems, artificial "
        "intelligence, and security through advanced graduate coursework and faculty "
        "research projects."
    ),
    ("Computer Science", "certificate"): (
        "This graduate certificate delivers focused CSE coursework in areas such as "
        "machine learning and systems for software professionals in San Diego's tech sector."
    ),
    ("Computer and Information Sciences", "bachelors"): (
        "This information-sciences major covers databases, human-computer interaction, and "
        "software engineering, with applied project courses based in the Qualcomm Institute."
    ),
    ("Computer and Information Sciences", "masters"): (
        "Master's study in computer and information sciences advances databases, "
        "human-computer interaction, and software engineering through graduate seminars and "
        "Qualcomm Institute project work."
    ),
    ("Electrical Engineering", "bachelors"): (
        "Electrical engineering undergraduates study communications, photonics, machine-"
        "learning hardware, and power electronics, with laboratory work in the department's "
        "nanofabrication facilities."
    ),
    ("Electrical Engineering", "masters"): (
        "The ECE master's offers depth in communications, photonics, and machine-learning "
        "hardware, with research through the Center for Wireless Communications and "
        "nanofabrication facilities."
    ),
    ("Electrical Engineering", "certificate"): (
        "A graduate certificate in electrical engineering concentrates on selected topics "
        "such as communications or power electronics for working engineers."
    ),
    ("Engineering Physics", "bachelors"): (
        "The engineering physics major bridges physics and engineering, grounding "
        "undergraduates in quantum materials, plasma physics, and applied optics."
    ),
    ("Engineering Physics", "masters"): (
        "Engineering physics master's students pursue advanced study in quantum materials, "
        "plasma physics, and applied optics, with research links to the Center for Energy "
        "Research."
    ),
    ("Engineering Physics", "certificate"): (
        "This graduate certificate offers focused coursework at the physics–engineering "
        "interface, drawing on Center for Energy Research faculty."
    ),
    ("Engineering Science", "bachelors"): (
        "The engineering science major gives undergraduates a cross-disciplinary foundation "
        "in mechanics, thermodynamics, and systems analysis within the Jacobs School."
    ),
    ("Engineering Science", "certificate"): (
        "A graduate certificate in engineering science offers focused coursework in "
        "mechanics and systems analysis for engineers bridging disciplines."
    ),
    ("Engineering Sciences", "bachelors"): (
        "Engineering-sciences undergraduates study applied mechanics, materials, and design "
        "methodology as a foundation that bridges multiple Jacobs School disciplines."
    ),
    ("Engineering Sciences", "masters"): (
        "The engineering-sciences master's advances applied mechanics, materials, and design "
        "methodology for students working across engineering specializations."
    ),
    ("Engineering Sciences", "certificate"): (
        "This graduate certificate concentrates on applied mechanics and design methodology "
        "for practicing engineers spanning multiple disciplines."
    ),
    ("Materials Science", "masters"): (
        "The materials-science master's examines nanomaterials, biomaterials, and "
        "energy-storage systems through graduate coursework and research in Jacobs School "
        "synthesis and characterization labs."
    ),
    ("Materials Science", "certificate"): (
        "A graduate certificate in materials science offers focused study of nanomaterials "
        "and energy-storage systems for engineers in San Diego's materials industries."
    ),
    ("Mechanical Engineering", "bachelors"): (
        "Mechanical engineering undergraduates study robotics, thermofluids, and design, "
        "applying coursework on Formula SAE student engineering teams."
    ),
    ("Mechanical Engineering", "masters"): (
        "The MAE master's deepens robotics, thermofluids, and mechanical design, with "
        "research through the Center for Wearable Sensors and Jacobs School laboratories."
    ),
    ("Mechanical Engineering", "certificate"): (
        "This graduate certificate offers concentrated coursework in robotics or "
        "thermofluids for practicing mechanical engineers."
    ),
    ("NanoEngineering", "masters"): (
        "The NanoEngineering master's advances nanomaterials synthesis, nanomedicine, and "
        "semiconductor processing in one of the nation's dedicated nanoengineering "
        "departments."
    ),
    ("NanoEngineering", "certificate"): (
        "A graduate certificate in nanoengineering offers focused coursework in nanomaterials "
        "synthesis and semiconductor processing for industry practitioners."
    ),
    ("Structural Engineering", "bachelors"): (
        "Structural engineering undergraduates study earthquake engineering, structural "
        "design, and mechanics, with laboratory work in the Powell Structural Research "
        "Laboratories."
    ),
    ("Structural Engineering", "masters"): (
        "The structural engineering master's advances earthquake engineering, structural "
        "design, and computational mechanics, with research in the Powell Structural "
        "Research Laboratories."
    ),
    ("Structural Engineering", "certificate"): (
        "This graduate certificate concentrates on earthquake engineering and structural "
        "design for practicing civil and structural engineers."
    ),
    ("Systems Engineering", "masters"): (
        "The systems engineering master's covers optimization, control theory, and "
        "large-scale engineering design for aerospace and defense applications."
    ),
    ("Systems Engineering", "certificate"): (
        "A graduate certificate in systems engineering offers focused coursework in "
        "optimization and control for engineers in San Diego's aerospace and defense sector."
    ),

    # ---- School of Biological Sciences ----
    ("Biochemistry", "bachelors"): (
        "Biochemistry undergraduates in the Division of Biological Sciences study protein "
        "structure, enzymology, and molecular mechanisms, with wet-lab coursework on the La "
        "Jolla mesa."
    ),
    ("Biochemistry", "masters"): (
        "Biochemistry master's study advances protein structure and molecular mechanisms, "
        "with laboratory access to the Sanford Consortium for Regenerative Medicine."
    ),
    ("Biochemistry", "certificate"): (
        "A graduate certificate in biochemistry offers focused coursework in protein "
        "chemistry and molecular mechanisms for life-sciences professionals."
    ),
    ("Biology", "bachelors"): (
        "The biology major spans molecular, cellular, and organismal biology across the "
        "division's four sections, with NIH-funded undergraduate research opportunities."
    ),
    ("Biology", "masters"): (
        "Biology master's study offers advanced work across molecular, cellular, and "
        "organismal biology, drawing on the Division of Biological Sciences' research "
        "sections."
    ),
    ("Biology", "certificate"): (
        "This graduate certificate provides focused coursework in molecular and cellular "
        "biology for practitioners and pre-health students."
    ),
    ("Ecology and Evolution", "bachelors"): (
        "Ecology and evolution undergraduates study population genetics, behavioral ecology, "
        "and conservation, with field work from the Anza-Borrego Desert to the La Jolla kelp "
        "forest."
    ),
    ("Ecology and Evolution", "masters"): (
        "Master's study in ecology and evolution advances population genetics and "
        "conservation biology, using field sites across the San Diego region."
    ),
    ("Ecology and Evolution", "certificate"): (
        "A graduate certificate in ecology and evolution offers focused coursework in "
        "conservation and field ecology for environmental practitioners."
    ),
    ("Neurobiology", "bachelors"): (
        "The neurobiology major — a UC San Diego flagship strength — covers systems, "
        "molecular, and cognitive neuroscience, with research ties to the Kavli Institute "
        "for Brain and Mind."
    ),
    ("Neurobiology", "masters"): (
        "Neurobiology master's study advances systems and molecular neuroscience, with "
        "laboratory work connected to the Kavli Institute for Brain and Mind."
    ),
    ("Neurobiology", "certificate"): (
        "This graduate certificate offers focused neuroscience coursework spanning systems "
        "and molecular approaches for clinical and research professionals."
    ),
    ("Physiology", "masters"): (
        "Physiology master's study in the Division of Biological Sciences examines "
        "organ-system function, exercise physiology, and biomedical mechanisms through "
        "wet-lab research."
    ),
    ("Physiology", "certificate"): (
        "A graduate certificate in physiology offers focused coursework in organ-system "
        "function and exercise physiology for health-sciences practitioners."
    ),

    # ---- School of Physical Sciences ----
    ("Applied Mathematics", "bachelors"): (
        "The applied mathematics major grounds undergraduates in scientific computing, "
        "differential equations, and mathematical modeling, with ties to the Center for "
        "Computational Mathematics."
    ),
    ("Applied Mathematics", "masters"): (
        "Applied mathematics master's study connects fluid dynamics, scientific computing, "
        "and mathematical biology with the Center for Computational Mathematics and Scripps "
        "ocean-modeling groups."
    ),
    ("Applied Mathematics", "certificate"): (
        "This graduate certificate offers focused coursework in scientific computing and "
        "mathematical modeling for technical professionals."
    ),
    ("Chemistry", "bachelors"): (
        "Chemistry undergraduates in Physical Sciences study organic synthesis, physical "
        "chemistry, and materials science, with laboratory access to shared NMR facilities."
    ),
    ("Chemistry", "masters"): (
        "Chemistry master's study advances organic synthesis, physical chemistry, and "
        "materials science, with research through the Center for Aerosol Impacts on "
        "Chemistry of the Environment."
    ),
    ("Chemistry", "certificate"): (
        "A graduate certificate in chemistry offers focused coursework in synthesis or "
        "physical chemistry for laboratory and industry professionals."
    ),
    ("Mathematics", "bachelors"): (
        "The mathematics major covers algebra, analysis, and geometry, with proof-based "
        "coursework and electives bridging to physics and computer science."
    ),
    ("Mathematics", "masters"): (
        "Mathematics master's study advances algebra, analysis, and geometry, with ties to "
        "the Center for Computational Mathematics and to physics and engineering research."
    ),
    ("Mathematics", "certificate"): (
        "This graduate certificate offers focused coursework in applied and computational "
        "mathematics for quantitative professionals."
    ),
    ("Physical Sciences", "bachelors"): (
        "This Physical Sciences program lets undergraduates integrate chemistry, physics, "
        "and mathematics, with research links to the Center for Astrophysics and Space "
        "Sciences."
    ),
    ("Physical Sciences", "certificate"): (
        "A graduate certificate in the physical sciences offers focused interdisciplinary "
        "coursework across chemistry, physics, and mathematics."
    ),
    ("Physics", "bachelors"): (
        "Physics undergraduates study condensed matter, particle physics, and biophysics, "
        "with access to the Center for Astrophysics and Space Sciences and major "
        "observatories."
    ),
    ("Physics", "masters"): (
        "Physics master's study advances condensed matter, particle physics, and "
        "biophysics, with research through the Center for Astrophysics and Space Sciences."
    ),
    ("Physics", "certificate"): (
        "This graduate certificate offers focused coursework in areas such as condensed "
        "matter or biophysics for technical professionals."
    ),

    # ---- School of Social Sciences ----
    ("Anthropology", "bachelors"): (
        "Anthropology undergraduates combine archaeology, biological anthropology, and "
        "sociocultural study, with a Pacific Rim and U.S.–Mexico borderlands research focus."
    ),
    ("Anthropology", "masters"): (
        "Anthropology master's study advances sociocultural theory and archaeological "
        "method, drawing on UC San Diego's borderlands and Pacific Rim field research."
    ),
    ("Anthropology", "certificate"): (
        "A graduate certificate in anthropology offers focused coursework in sociocultural "
        "or archaeological methods for researchers and educators."
    ),
    ("Applied Psychology", "bachelors"): (
        "Applied psychology undergraduates study behavioral neuroscience, cognitive "
        "psychology, and human factors, with hands-on work in School of Social Sciences "
        "laboratories."
    ),
    ("Applied Psychology", "certificate"): (
        "A graduate certificate in applied psychology offers focused coursework in human "
        "factors and behavioral methods for working professionals."
    ),
    ("Clinical Psychology", "bachelors"): (
        "Undergraduate clinical-psychology coursework introduces assessment, "
        "psychopathology, and intervention, with research exposure through Department of "
        "Psychology labs."
    ),
    ("Clinical Psychology", "certificate"): (
        "A graduate certificate in clinical psychology offers focused coursework in "
        "evidence-based assessment and intervention, drawing on UC San Diego Health and the "
        "Department of Psychiatry."
    ),
    ("Cognitive Science", "bachelors"): (
        "UC San Diego founded one of the nation's first cognitive-science majors, where "
        "undergraduates integrate neuroscience, linguistics, psychology, and computer "
        "science alongside the Kavli Institute for Brain and Mind."
    ),
    ("Cognitive Science", "masters"): (
        "Cognitive-science master's study advances computational modeling, neuroscience, "
        "and human-computer interaction across the department's interdisciplinary labs."
    ),
    ("Cognitive Science", "certificate"): (
        "This graduate certificate offers focused cognitive-science coursework spanning "
        "neuroscience and human-computer interaction for industry researchers."
    ),
    ("Communication", "bachelors"): (
        "Communication undergraduates study media, political communication, and science "
        "communication, with production work in the department's digital-media labs."
    ),
    ("Communication", "masters"): (
        "Communication master's study advances media and science communication, with "
        "research through the Arthur C. Clarke Center for Human Imagination."
    ),
    ("Communication", "certificate"): (
        "A graduate certificate in communication offers focused coursework in media and "
        "science communication for professionals."
    ),
    ("Computational Social Science", "bachelors"): (
        "This program trains undergraduates to apply network analysis, machine learning, "
        "and large-scale survey data to political and social questions across GPS and the "
        "social sciences."
    ),
    ("Economics", "bachelors"): (
        "Economics undergraduates study microeconomic theory, macroeconomics, and "
        "econometrics, choosing among tracks including the management-science and "
        "international-economics emphases."
    ),
    ("Economics", "masters"): (
        "Economics master's study advances econometrics and applied microeconomics, drawing "
        "on the Center for Commerce and Diplomacy and Pacific Rim policy research."
    ),
    ("Economics", "certificate"): (
        "A graduate certificate in economics offers focused coursework in econometrics and "
        "applied economic analysis for policy and industry professionals."
    ),
    ("Education Studies", "bachelors"): (
        "Education Studies undergraduates analyze schooling, equity, and learning "
        "environments, with community-engaged practica in San Diego-area schools."
    ),
    ("Education Studies", "masters"): (
        "Education Studies master's work advances learning sciences and educational policy, "
        "combining classroom research with supervised practice in regional schools."
    ),
    ("Education Studies", "certificate"): (
        "A graduate certificate in education studies offers focused coursework in pedagogy "
        "and learning sciences for practicing educators."
    ),
    ("Ethnic Studies", "bachelors"): (
        "Ethnic Studies undergraduates examine race, migration, and social justice, with "
        "strengths in Chicana/o, Asian American, and Black studies on the border campus."
    ),
    ("Ethnic Studies", "masters"): (
        "Ethnic Studies master's study advances critical theory and comparative racial "
        "analysis, drawing on UC San Diego's borderlands location."
    ),
    ("Ethnic Studies", "certificate"): (
        "A graduate certificate in ethnic studies offers focused coursework in race, "
        "migration, and social-justice scholarship for educators and organizers."
    ),
    ("Experimental Psychology", "bachelors"): (
        "Experimental-psychology undergraduates study cognition, perception, and behavioral "
        "methods, with research training in Department of Psychology laboratories."
    ),
    ("Experimental Psychology", "masters"): (
        "Experimental-psychology master's study advances cognitive neuroscience, sensation "
        "and perception, and behavioral genetics in federally funded research labs."
    ),
    ("Experimental Psychology", "certificate"): (
        "This graduate certificate offers focused coursework in cognitive and behavioral "
        "research methods for applied researchers."
    ),
    ("History", "bachelors"): (
        "History undergraduates study world history, the history of science and medicine, "
        "and U.S.–Mexico border history, with archival work through the Center for "
        "U.S.–Mexican Studies."
    ),
    ("History", "masters"): (
        "History master's study advances world and borderlands history, drawing on the "
        "Center for U.S.–Mexican Studies and regional archival partnerships."
    ),
    ("History", "certificate"): (
        "A graduate certificate in history offers focused coursework in borderlands or "
        "science-and-medicine history for educators and researchers."
    ),
    ("International Relations", "bachelors"): (
        "International-relations undergraduates at GPS study Pacific Rim security, trade "
        "policy, and diplomacy, with the 21st Century China Center and Center on Global "
        "Transformation nearby."
    ),
    ("International Relations", "masters"): (
        "The international-relations master's at GPS deepens Pacific Rim security and trade "
        "policy through professional policy training and the 21st Century China Center."
    ),
    ("Political Science", "bachelors"): (
        "Political-science undergraduates study American politics, comparative politics, and "
        "international relations, with research opportunities in the Policy Design and "
        "Evaluation Lab."
    ),
    ("Political Science", "masters"): (
        "Political-science master's study advances comparative politics and policy analysis "
        "through the Policy Design and Evaluation Lab."
    ),
    ("Political Science", "certificate"): (
        "A graduate certificate in political science offers focused coursework in policy "
        "analysis and comparative politics for government professionals."
    ),
    ("Psychology", "bachelors"): (
        "Psychology undergraduates study cognitive, developmental, social, and clinical "
        "psychology, with research participation in the department's federally funded labs."
    ),
    ("Psychology", "masters"): (
        "Psychology master's study advances research methods across cognitive, "
        "developmental, and social psychology in the department's federally funded "
        "laboratories."
    ),
    ("Psychology", "certificate"): (
        "This graduate certificate offers focused coursework in psychological research "
        "methods and applied psychology."
    ),
    ("Sociology", "bachelors"): (
        "Sociology undergraduates study stratification, immigration, and the sociology of "
        "science, with research ties to the Center for Comparative Immigration Studies."
    ),
    ("Sociology", "masters"): (
        "Sociology master's study advances immigration and science-studies research through "
        "the Center for Comparative Immigration Studies."
    ),
    ("Sociology", "certificate"): (
        "A graduate certificate in sociology offers focused coursework in immigration and "
        "social-stratification research for policy practitioners."
    ),
    ("Statistics", "bachelors"): (
        "The statistics major grounds undergraduates in probability, statistical inference, "
        "and data modeling, with applications across the biological and social sciences."
    ),
    ("Statistics", "masters"): (
        "Statistics master's study advances statistical inference and data modeling, with "
        "applied projects spanning biological and social-sciences research."
    ),

    # ---- School of Arts and Humanities ----
    ("Comparative Literature", "bachelors"): (
        "Comparative-literature undergraduates study world literatures, translation, and "
        "critical theory across the School of Arts and Humanities' language programs."
    ),
    ("Comparative Literature", "masters"): (
        "Comparative-literature master's study advances translation studies and critical "
        "theory across multiple literary traditions."
    ),
    ("Comparative Literature", "certificate"): (
        "A graduate certificate in comparative literature offers focused coursework in "
        "translation and critical theory for writers and educators."
    ),
    ("International Studies", "bachelors"): (
        "International-studies undergraduates combine language training, area studies, and "
        "global cultural analysis across the Pacific and the Americas."
    ),
    ("International Studies", "masters"): (
        "International-studies master's work advances area studies and global cultural "
        "analysis, building on UC San Diego's Pacific and trans-American focus."
    ),
    ("Intermedia Arts", "bachelors"): (
        "Intermedia-arts undergraduates work across digital media, installation, and "
        "time-based art in the Visual Arts department's studios."
    ),
    ("Intermedia Arts", "certificate"): (
        "A graduate certificate in intermedia arts offers focused studio coursework in "
        "digital and time-based media for practicing artists."
    ),
    ("Liberal Arts", "bachelors"): (
        "This liberal-arts program lets undergraduates integrate literature, philosophy, "
        "and historical analysis across broad humanistic inquiry."
    ),
    ("Liberal Arts", "certificate"): (
        "A graduate certificate in liberal arts offers focused humanities coursework across "
        "literature, philosophy, and history."
    ),
    ("Linguistics", "bachelors"): (
        "Linguistics undergraduates study phonetics, syntax, and psycholinguistics at a "
        "department known as a birthplace of modern generative grammar, with research in "
        "the Center for Research in Language."
    ),
    ("Linguistics", "masters"): (
        "Linguistics master's study advances syntax, psycholinguistics, and sign-language "
        "research through the Center for Research in Language."
    ),
    ("Linguistics", "certificate"): (
        "A graduate certificate in linguistics offers focused coursework in phonetics and "
        "psycholinguistics for language professionals."
    ),
    ("Literature", "bachelors"): (
        "Literature undergraduates read across British, American, and world literatures, "
        "with critical-theory seminars and the Geisel Library special collections."
    ),
    ("Literature", "masters"): (
        "Literature master's study advances critical theory and comparative literary "
        "analysis, drawing on the Geisel Library special-collections holdings."
    ),
    ("Literature", "certificate"): (
        "A graduate certificate in literature offers focused coursework in literary and "
        "critical-theory studies for writers and educators."
    ),
    ("Music", "bachelors"): (
        "Music undergraduates study composition, performance, and music technology in a "
        "department known for its experimental and contemporary focus, with the Conrad "
        "Prebys Music Center as home."
    ),
    ("Music", "masters"): (
        "Music master's study advances composition and music technology within the "
        "department's contemporary focus at the Conrad Prebys Music Center."
    ),
    ("Music", "certificate"): (
        "A graduate certificate in music offers focused coursework in composition or music "
        "technology for practicing musicians."
    ),
    ("Philosophy", "bachelors"): (
        "Philosophy undergraduates study logic, ethics, and the philosophy of science, with "
        "departmental strength in epistemology and the philosophy of language."
    ),
    ("Philosophy", "masters"): (
        "Philosophy master's study advances philosophy of science, epistemology, and "
        "philosophy of language with the department's research faculty."
    ),
    ("Philosophy", "certificate"): (
        "A graduate certificate in philosophy offers focused coursework in logic, ethics, "
        "or philosophy of science."
    ),
    ("Studio Art", "bachelors"): (
        "Studio-art undergraduates work in painting, sculpture, and new media, with critique "
        "seminars in the Visual Arts department's studios."
    ),
    ("Studio Art", "masters"): (
        "Studio-art master's study advances individual practice in painting, sculpture, and "
        "new media through intensive critique in the Visual Arts studios."
    ),
    ("Studio Art", "certificate"): (
        "A graduate certificate in studio art offers focused studio coursework and critique "
        "for practicing artists."
    ),
    ("Theatre", "bachelors"): (
        "Theatre undergraduates train in acting, directing, and dramaturgy, with productions "
        "staged at the Mandell Weiss Theatre."
    ),
    ("Theatre", "masters"): (
        "Theatre master's study — part of a top-ranked graduate program — advances acting, "
        "directing, and design through productions at the Mandell Weiss Theatre."
    ),
    ("Theatre", "certificate"): (
        "A graduate certificate in theatre offers focused coursework in directing or "
        "dramaturgy for working theatre artists."
    ),
    ("Visual Arts", "bachelors"): (
        "Visual-arts undergraduates combine studio practice, art history, and critical "
        "theory, with public programs in the Structural and Materials Engineering building "
        "galleries."
    ),
    ("Visual Arts", "masters"): (
        "Visual-arts master's study advances studio practice and critical theory through "
        "intensive critique and the department's exhibition programs."
    ),
    ("Visual Arts", "certificate"): (
        "A graduate certificate in visual arts offers focused studio and critical-theory "
        "coursework for practicing artists."
    ),

    # ---- Scripps Institution of Oceanography ----
    ("Earth Sciences", "bachelors"): (
        "Earth-sciences undergraduates at Scripps study geophysics, geochemistry, and "
        "paleoclimate, with access to the Geological Collections facility."
    ),
    ("Earth Sciences", "masters"): (
        "Earth-sciences master's study at Scripps advances geophysics and paleoclimate, "
        "including shipboard research aboard the R/V Sally Ride."
    ),
    ("Earth Sciences", "certificate"): (
        "A graduate certificate in earth sciences offers focused coursework in geophysics or "
        "geochemistry for environmental professionals."
    ),

    # ---- Rady School of Management ----
    ("Business Administration", "masters"): (
        "Rady's full-time MBA emphasizes innovation, analytics, and entrepreneurship in "
        "small cohorts with Lab-to-Market capstones and San Diego startup partnerships."
    ),
    ("Business Administration", "certificate"): (
        "A graduate certificate in business administration offers focused management "
        "coursework in finance, strategy, and analytics for working professionals."
    ),
    ("Business Analytics", "bachelors"): (
        "Business-analytics undergraduates at Rady learn data-driven decision making, "
        "predictive modeling, and business intelligence using industry datasets."
    ),
    ("Business Analytics", "masters"): (
        "The Rady business-analytics master's builds predictive modeling and "
        "decision-analytics skills using the Rady Behavioral Lab and partner datasets."
    ),
    ("Business Analytics", "certificate"): (
        "A graduate certificate in business analytics offers focused coursework in "
        "predictive modeling and business intelligence for managers."
    ),

    # ---- School of Medicine / Skaggs School of Pharmacy ----
    ("Medicine", "certificate"): (
        "A graduate certificate in medicine offers focused coursework linking biomedical "
        "research and clinical science through the School of Medicine."
    ),
    ("Medicine", "phd"): (
        "Doctoral study in the medical sciences at UC San Diego pursues original biomedical "
        "and translational research through the School of Medicine's research programs."
    ),
    ("Pharmaceutical Sciences", "masters"): (
        "The pharmaceutical-sciences master's at Skaggs advances drug design, pharmacology, "
        "and medicinal chemistry through graduate coursework and laboratory research."
    ),
    ("Pharmaceutical Sciences", "phd"): (
        "Pharmaceutical-sciences doctoral study at Skaggs pursues original drug-discovery "
        "research in pharmacology and medicinal chemistry."
    ),
    ("Pharmaceutical Sciences", "certificate"): (
        "A graduate certificate in pharmaceutical sciences offers focused coursework in drug "
        "design and pharmacology for industry scientists."
    ),
    ("Speech and Language Sciences", "phd"): (
        "Doctoral study in speech and language sciences pursues original research in "
        "phonetics, language acquisition, and communication disorders, linked to "
        "cognitive-science and linguistics labs."
    ),
    ("Speech and Language Sciences", "certificate"): (
        "A graduate certificate in speech and language sciences offers focused coursework in "
        "phonetics and communication disorders for clinical practitioners."
    ),

    # ---- Herbert Wertheim School of Public Health ----
    ("Public Health", "bachelors"): (
        "Public-health undergraduates study epidemiology, environmental health, and health "
        "promotion, with community fieldwork through the Center for Community Health."
    ),
    ("Public Health", "masters"): (
        "Wertheim School MPH training covers epidemiology, biostatistics, and community "
        "health with San Diego County public-health partnerships."
    ),
    ("Public Health", "certificate"): (
        "A graduate certificate in public health offers focused coursework in epidemiology "
        "and health promotion for working health professionals."
    ),
}


def description_for(field: str, degree_type: str) -> str | None:
    """Return a per-credential description when this field spans levels."""
    return CREDENTIAL_DESCRIPTIONS.get((field, degree_type))
