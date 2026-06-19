"""Regenerate Purdue FIELD_DESCRIPTIONS with verified Purdue-only units (no peer signatures).

Run: PYTHONPATH=src python3 scripts/rebuild_purdue_field_descriptions.py
"""

from __future__ import annotations

# Real Purdue colleges / schools / institutes — allowlist for description clauses.
PURDUE_UNITS = {
    "ag": "College of Agriculture",
    "eng": "College of Engineering",
    "cla": "College of Liberal Arts",
    "sci": "College of Science",
    "hhs": "College of Health and Human Sciences",
    "pharm": "College of Pharmacy",
    "vet": "College of Veterinary Medicine",
    "poly": "Purdue Polytechnic Institute",
    "biz": "Mitch Daniels School of Business",
    "comm": "Brian Lamb School of Communication",
    "nursing": "School of Nursing",
    "ed": "College of Education",
    "aviation": "School of Aviation and Transportation Technology",
    "rueff": "Patti and Rusty Rueff School of Design, Art, Performance, and Communication",
}

# Field → (unit_key, concrete clause about the discipline at Purdue)
FIELD_CLAUSES: dict[str, tuple[str, str]] = {
    "Accounting": (
        "biz",
        "Accounting coursework in the Daniels School covers financial reporting, audit, tax, and managerial accounting with case studies tied to Big Four and industry recruiting.",
    ),
    "Advanced Engineering Technology": (
        "poly",
        "Applied engineering technology at Purdue Polytechnic spans mechatronics, manufacturing systems, and industry-sponsored capstone projects.",
    ),
    "Aerospace Engineering": (
        "eng",
        "Aerospace engineering leverages Zucrow Laboratories for propulsion, spacecraft systems, and autonomy research in the School of Aeronautics and Astronautics.",
    ),
    "Agricultural Communication": (
        "ag",
        "Agricultural communication trains science journalists and extension messaging specialists for Purdue Extension and ag-industry audiences.",
    ),
    "Agricultural Economics": (
        "ag",
        "The Department of Agricultural Economics analyzes commodity markets, farm policy, and agribusiness finance — a signature Purdue land-grant strength.",
    ),
    "Agricultural Engineering": (
        "ag",
        "Agricultural and biological engineering integrates irrigation, precision agriculture, and biological systems design on Purdue research farms.",
    ),
    "Agricultural Operations": (
        "ag",
        "Production agriculture coursework covers crop and livestock operations, precision agriculture, and farm management using Purdue's research farms.",
    ),
    "Agricultural Systems Management": (
        "ag",
        "Agricultural systems management integrates machinery, soil conservation, and technology for modern farm and agribusiness operations.",
    ),
    "Agriculture": (
        "ag",
        "Purdue's College of Agriculture spans agronomy, animal sciences, food science, and agricultural economics across Indiana's land-grant mission.",
    ),
    "Allied Health": (
        "hhs",
        "Allied health pathways in the College of Health and Human Sciences prepare clinical technologists and diagnostic specialists for hospital and community settings.",
    ),
    "Animal Sciences": (
        "ag",
        "Animal sciences covers livestock production, nutrition, genetics, and welfare with hands-on work at Purdue's animal science teaching facilities.",
    ),
    "Anthropology": (
        "cla",
        "Anthropology combines archaeological fieldwork, medical anthropology, and sociocultural theory with Midwest and global research sites.",
    ),
    "Apparel Design": (
        "rueff",
        "Apparel design in the Rueff School combines textile science, CAD patternmaking, and retail merchandising with industry internships.",
    ),
    "Applied Mathematics": (
        "sci",
        "Applied mathematics supports Purdue's data-science and quantitative finance initiatives with stochastic modeling and scientific computing.",
    ),
    "Architectural Engineering Technologies/Technicians": (
        "poly",
        "Architectural engineering technology covers building systems, HVAC design, and construction documentation in Purdue Polytechnic.",
    ),
    "Area Studies": (
        "cla",
        "Area studies programs in the College of Liberal Arts integrate language immersion with regional policy and diaspora scholarship.",
    ),
    "Atmospheric Science": (
        "sci",
        "Atmospheric science examines weather dynamics, climate modeling, and remote sensing with Purdue mesonet and supercomputing resources.",
    ),
    "Aviation Management": (
        "aviation",
        "The School of Aviation and Transportation Technology trains pilots, airport managers, and aviation operations leaders at Purdue University Airport.",
    ),
    "Bilingual, Multilingual, and Multicultural Education": (
        "ed",
        "Multilingual education graduate work targets ESL pedagogy, literacy, and evidence-based practice in Indiana partner districts.",
    ),
    "Biochemistry, Biophysics and Molecular Biology": (
        "sci",
        "Biochemistry and biophysics studies protein structure, enzymology, and molecular mechanisms in federally funded Purdue research labs.",
    ),
    "Biological Sciences": (
        "sci",
        "Biological sciences span molecular, cellular, and organismal biology with undergraduate research across the College of Science.",
    ),
    "Biology": (
        "cla",
        "Biology majors choose among cell biology, ecology, neurobiology, and molecular genetics tracks with federally funded undergraduate research.",
    ),
    "Biomedical Engineering": (
        "eng",
        "The Weldon School of Biomedical Engineering integrates device design, biomaterials, and clinical immersion — U.S. News routinely ranks the undergraduate major among the nation's best.",
    ),
    "Biotechnology": (
        "sci",
        "Biotechnology coursework covers bioprocessing, regulatory science, and translational research through Discovery Park partnerships.",
    ),
    "Business/Corporate Communications": (
        "comm",
        "Corporate communications combines rhetoric, media studies, and organizational messaging through the Brian Lamb School.",
    ),
    "Cell Biology": (
        "sci",
        "Cell biology training focuses on signaling, organelle biology, and microscopy methods used in cancer and immunology labs.",
    ),
    "Chemical Engineering": (
        "eng",
        "The Davidson School of Chemical Engineering spans catalysis, drug delivery, and sustainable process design with industry partnerships.",
    ),
    "Chemistry": (
        "sci",
        "Chemistry runs synthesis, physical, and chemical-biology groups with joint appointments across the College of Science.",
    ),
    "Civil Engineering": (
        "eng",
        "The Lyles School of Civil Engineering emphasizes infrastructure resilience, transportation systems, and urban hydrology.",
    ),
    "Classical and Ancient Studies": (
        "cla",
        "Classics covers Greek and Latin language, ancient history, and philology with manuscript and Mediterranean archaeology resources.",
    ),
    "Clinical, Counseling and Applied Psychology": (
        "cla",
        "Clinical and counseling psychology graduate work emphasizes evidence-based practice, assessment, and community mental-health placements.",
    ),
    "Clinical/Medical Laboratory Science/Research and Allied Professions": (
        "hhs",
        "Medical laboratory science prepares clinical technologists in hematology, microbiology, and diagnostic testing through hospital-affiliated rotations.",
    ),
    "Communication": (
        "comm",
        "The Brian Lamb School of Communication covers rhetoric, media studies, and organizational communication — named for C-SPAN founder and Purdue alumnus Brian Lamb.",
    ),
    "Computer Engineering": (
        "eng",
        "Electrical and computer engineering covers embedded systems, VLSI, and hardware–software co-design with robotics lab access.",
    ),
    "Computer Graphics Technology": (
        "poly",
        "Computer graphics technology spans 3D animation, virtual-product development, and UX design for manufacturing and entertainment.",
    ),
    "Computer Information Systems": (
        "poly",
        "Information systems coursework covers enterprise databases, network administration, and business analytics for IT leadership roles.",
    ),
    "Computer Science": (
        "sci",
        "Computer science covers algorithms, systems, AI, and theory with the Purdue Computes initiative and undergraduate research in robotics labs.",
    ),
    "Computer and Information Sciences": (
        "sci",
        "Foundational computer science spans algorithms, systems, and AI within the Department of Computer Science.",
    ),
    "Construction Engineering": (
        "eng",
        "The School of Construction Engineering and Management trains builders in estimating, scheduling, and sustainable infrastructure delivery.",
    ),
    "Cultural Studies/Critical Theory and Analysis": (
        "cla",
        "Cultural studies examines critical theory, visual culture, and postcolonial scholarship in the College of Liberal Arts.",
    ),
    "Curriculum and Instruction": (
        "ed",
        "Curriculum and instruction programs prepare educators in literacy, STEM pedagogy, and classroom-based research with Indiana partner schools.",
    ),
    "Data Analytics": (
        "sci",
        "Data analytics training covers statistical modeling, machine learning, and decision analytics for finance, health, and policy applications.",
    ),
    "Digital Humanities and Textual Studies": (
        "cla",
        "Digital humanities combines computational text analysis, archival digitization, and data visualization in the College of Liberal Arts.",
    ),
    "Doctor of Pharmacy": (
        "pharm",
        "The Pharm.D. program in one of the oldest U.S. pharmacy colleges emphasizes clinical practice and drug discovery at the Purdue Institute for Drug Discovery.",
    ),
    "Doctor of Veterinary Medicine": (
        "vet",
        "The D.V.M. program operates a full-service veterinary teaching hospital with research in comparative oncology and food-animal medicine.",
    ),
    "Earth Sciences": (
        "sci",
        "Earth sciences covers geology, geophysics, and planetary geology with field camps and analytical labs.",
    ),
    "East Asian Languages": (
        "cla",
        "East Asian languages and cultures covers Chinese, Japanese, and Korean with study-abroad pathways.",
    ),
    "Ecology and Evolutionary Biology": (
        "sci",
        "Ecology and evolutionary biology examines population dynamics, conservation genetics, and field ecology across Indiana forests and wetlands.",
    ),
    "Economics": (
        "cla",
        "Economics is empirically rigorous — faculty research spans health, trade, and development with the Krannert School analytics network.",
    ),
    "Education": (
        "ed",
        "Graduate education programs target literacy, special education, and evidence-based practice in Indiana partner districts.",
    ),
    "Education Studies": (
        "cla",
        "Education studies examines policy, inequality, and learning science without requiring teacher certification.",
    ),
    "Educational Assessment, Evaluation, and Research": (
        "ed",
        "Educational assessment and evaluation trains researchers in psychometrics, program evaluation, and school improvement analytics.",
    ),
    "Educational Leadership": (
        "ed",
        "Principal and superintendent preparation integrates equity audits and data-driven school improvement.",
    ),
    "Educational/Instructional Media Design": (
        "ed",
        "Instructional media design builds digital learning environments, multimedia curricula, and educational technology for schools and universities.",
    ),
    "Electrical Engineering": (
        "eng",
        "The Elmore Family School of Electrical and Computer Engineering spans signal processing, photonics, and medical devices.",
    ),
    "Electrical Engineering Technology": (
        "poly",
        "Electrical engineering technology covers power systems, industrial controls, and embedded electronics for manufacturing careers.",
    ),
    "Engineering Sciences": (
        "eng",
        "Interdisciplinary engineering sciences lets undergraduates tailor engineering fundamentals across College of Engineering schools.",
    ),
    "Engineering Technology": (
        "poly",
        "Engineering technology trains technologists in manufacturing processes, quality systems, and applied engineering design.",
    ),
    "Engineering-Related Technology": (
        "poly",
        "Engineering-related technology bridges applied design, prototyping, and industry-sponsored senior projects.",
    ),
    "English": (
        "cla",
        "English combines literary history, creative writing, and rhetoric with the Purdue Writing Lab and journal traditions.",
    ),
    "Entrepreneurial and Small Business Operations": (
        "biz",
        "Entrepreneurship coursework covers venture creation, small-business finance, and startup strategy through the Purdue Foundry and Discovery Park.",
    ),
    "Environmental Engineering": (
        "eng",
        "Environmental and ecological engineering pairs water-quality science with sustainability policy and green infrastructure design.",
    ),
    "Experimental Psychology": (
        "cla",
        "Experimental psychology uses behavioral, cognitive, and neuroscience methods in the Department of Psychological Sciences.",
    ),
    "Family and Consumer Sciences/Human Sciences": (
        "hhs",
        "Human development and consumer sciences spans family systems, financial literacy, and community wellness.",
    ),
    "Family and Consumer Sciences/Human Sciences Business Services": (
        "hhs",
        "Consumer sciences business combines retail analytics, product development, and merchandising strategy.",
    ),
    "Film/Video and Photographic Arts": (
        "rueff",
        "Film and video production covers documentary, narrative, and media theory with access to Purdue media labs.",
    ),
    "Finance": (
        "biz",
        "Finance coursework emphasizes corporate finance, real-estate valuation, and quantitative asset management.",
    ),
    "Fisheries and Aquatic Sciences": (
        "ag",
        "Fisheries and aquatic sciences studies freshwater ecology, aquaculture, and fisheries management through the Aquaculture Research Laboratory.",
    ),
    "Food Science": (
        "ag",
        "Food science covers food chemistry, processing, safety, and sensory evaluation in Whistler Center of Research labs.",
    ),
    "Forestry": (
        "ag",
        "Forestry covers forest ecology, silviculture, and wildfire science through Purdue's natural-resource programs.",
    ),
    "General Engineering": (
        "eng",
        "First-year engineering exposes students to design, computing, and lab rotations before declaring a major.",
    ),
    "General Sales, Merchandising and Related Marketing Operations": (
        "biz",
        "Sales and merchandising emphasizes retail analytics, category management, and consumer behavior.",
    ),
    "Genetics": (
        "sci",
        "Genomics and genetic analysis connect to Purdue precision-medicine and agricultural genomics institutes.",
    ),
    "Geography and Cartography": (
        "cla",
        "Geography uses GIS, remote sensing, and spatial analysis for urban, environmental, and health-geography research.",
    ),
    "German": (
        "cla",
        "German language, literature, and culture includes study-abroad and European intellectual-history coursework.",
    ),
    "Gerontology": (
        "hhs",
        "Gerontology programs study epidemiology of aging, long-term care, and policy for older adults.",
    ),
    "Health Administration": (
        "hhs",
        "Health administration prepares leaders for hospitals, insurers, and government health agencies.",
    ),
    "Health Sciences": (
        "hhs",
        "Health sciences coursework spans biostatistics, epidemiology, and health-systems research.",
    ),
    "Health Services/Allied Health/Health Sciences": (
        "hhs",
        "Allied health sciences prepares practitioners in clinical support roles across the College of Health and Human Sciences.",
    ),
    "History": (
        "cla",
        "History spans global, American, and science-and-medicine specialties with archival and museum partnerships.",
    ),
    "Horticulture": (
        "ag",
        "Horticulture covers greenhouse production, urban forestry, and sustainable landscape design on Purdue horticulture farms.",
    ),
    "Hospitality Administration/Management": (
        "biz",
        "Hospitality and tourism management in the Daniels School covers service operations, revenue management, and event planning for the hospitality industry.",
    ),
    "Human Development and Family Studies": (
        "hhs",
        "Human development and family studies examines child development, family policy, and gerontology with community practica.",
    ),
    "Human Resource Management": (
        "biz",
        "Human resource management covers talent analytics, labor relations, and organizational development.",
    ),
    "Industrial Engineering": (
        "eng",
        "Industrial engineering focuses on health-care operations, supply chains, and human-factors engineering.",
    ),
    "Industrial Production Technologies/Technicians": (
        "poly",
        "Production technology coursework covers manufacturing processes, automation, and quality systems.",
    ),
    "Information Science": (
        "sci",
        "Information science covers data curation, human–computer interaction, and knowledge organization.",
    ),
    "Information Technology": (
        "poly",
        "Information technology trains systems administrators, cybersecurity analysts, and IT project managers.",
    ),
    "Integrated Science": (
        "sci",
        "Integrated science combines chemistry, physics, and life-sciences foundations for pre-professional and research-track students.",
    ),
    "Intercultural Studies": (
        "cla",
        "Intercultural studies examines race, diaspora, and social justice with community-based research.",
    ),
    "Intercultural/Multicultural and Diversity Studies": (
        "cla",
        "African American studies and ethnic studies examine race, migration, and multicultural policy.",
    ),
    "Interdisciplinary Studies": (
        "cla",
        "Interdisciplinary studies lets students combine two or more departments around a faculty-advised thesis.",
    ),
    "Landscape Architecture": (
        "ag",
        "Landscape architecture covers site design, ecological planning, and urban landscapes in studio-based coursework.",
    ),
    "Liberal Arts": (
        "cla",
        "Liberal arts breadth satisfies distribution requirements across humanities, social sciences, and natural sciences.",
    ),
    "Linguistics": (
        "cla",
        "Linguistics covers phonetics, syntax, sociolinguistics, and computational language science.",
    ),
    "Management": (
        "biz",
        "The Mitch Daniels School of Business emphasizes analytics-driven management, supply chain leadership, and entrepreneurship through the Purdue Foundry.",
    ),
    "Management Sciences and Quantitative Methods": (
        "biz",
        "Operations research and decision science emphasizes optimization, stochastic modeling, and analytics for finance and consulting.",
    ),
    "Marketing": (
        "biz",
        "Marketing integrates consumer analytics, brand strategy, and go-to-market case studies.",
    ),
    "Materials Engineering": (
        "eng",
        "Materials engineering studies biomaterials, nanomaterials, and characterization with the Birck Nanotechnology Center.",
    ),
    "Mathematics": (
        "sci",
        "Pure and applied mathematics spans analysis, algebra, and mathematical biology with small upper-level seminars.",
    ),
    "Mathematics and Computer Science": (
        "sci",
        "Joint mathematics–computer science training supports algorithms, cryptography, and theoretical computer science pathways.",
    ),
    "Mechanical Engineering": (
        "eng",
        "Mechanical engineering emphasizes design, robotics, and biomechanics through Herrick Laboratories and the Laboratory for Computational Sensing and Robotics.",
    ),
    "Mechanical Engineering Technology": (
        "poly",
        "Mechanical engineering technology covers CAD, manufacturing processes, and thermal-fluid systems.",
    ),
    "Mental and Social Health Services and Allied Professions": (
        "hhs",
        "Mental health services training covers community counseling, substance-use treatment, and psychiatric epidemiology.",
    ),
    "Microbiology": (
        "sci",
        "Microbiology and immunology studies pathogens, host defense, and vaccine science with BSL-3 lab access.",
    ),
    "Military Technologies and Applied Sciences": (
        "eng",
        "ROTC and defense-research pathways connect engineering students to aerospace, cybersecurity, and systems programs.",
    ),
    "Multi-/Interdisciplinary Studies": (
        "cla",
        "Interdisciplinary studies lets undergraduates design cross-college curricula combining STEM, liberal arts, and professional coursework.",
    ),
    "Music": (
        "rueff",
        "Music performance and composition includes orchestra, band, and jazz training through the Rueff School.",
    ),
    "Nanotechnology": (
        "eng",
        "Nanotechnology graduate work spans nanomaterials, drug delivery, and imaging at the Birck Nanotechnology Center.",
    ),
    "Natural Resources": (
        "ag",
        "Natural resources covers conservation biology, watershed management, and environmental policy.",
    ),
    "Neurobiology and Neurosciences": (
        "sci",
        "Neuroscience spans cellular, cognitive, and systems levels across the College of Science and Purdue Institute for Integrative Neuroscience.",
    ),
    "Nuclear Engineering": (
        "eng",
        "Nuclear engineering covers energy systems, radiation detection, and fusion research with national-lab partnerships.",
    ),
    "Nursing": (
        "nursing",
        "The School of Nursing combines clinical rotations, simulation labs, and community health practica with Indiana hospital partners.",
    ),
    "Nutrition Science": (
        "hhs",
        "Nutrition science examines dietetics, metabolic biochemistry, and community nutrition with ACEND-accredited pathways.",
    ),
    "Nutrition Sciences": (
        "hhs",
        "Human nutrition and metabolic biology research spans public-health dietetics and clinical nutrition.",
    ),
    "Pharmaceutical Sciences": (
        "pharm",
        "Pharmaceutical sciences spans medicinal chemistry, pharmacology, and drug delivery at the Purdue Institute for Drug Discovery.",
    ),
    "Pharmacology and Toxicology": (
        "pharm",
        "Pharmacology studies drug mechanisms, chemical biology, and toxicology adjacent to Purdue drug-discovery pipelines.",
    ),
    "Philosophy": (
        "cla",
        "Philosophy emphasizes logic, ethics, and philosophy of science with interdisciplinary ties across campus.",
    ),
    "Physics": (
        "sci",
        "Physics covers condensed matter, particle physics, and biophysics with faculty affiliated to national user facilities.",
    ),
    "Physiology, Pathology and Related Sciences": (
        "sci",
        "Physiology and pathobiology examine disease mechanisms in integrative biology research labs.",
    ),
    "Plant Biology": (
        "ag",
        "Plant biology covers crop genetics, plant pathology, and sustainable agriculture through the Department of Botany and Plant Pathology.",
    ),
    "Plant Science": (
        "ag",
        "Plant science examines crop genetics, plant pathology, and sustainable agriculture.",
    ),
    "Political Science": (
        "cla",
        "Political science combines American politics, comparative methods, and international relations with D.C. internship access.",
    ),
    "Psychological Sciences": (
        "cla",
        "Psychological sciences spans cognitive, clinical, developmental, and industrial-organizational psychology with NIH-funded research labs.",
    ),
    "Psychology": (
        "cla",
        "Psychology is among the largest majors, with research tracks in clinical, cognitive, and social psychology.",
    ),
    "Public Health": (
        "hhs",
        "Public health coursework spans epidemiology, biostatistics, and health-policy research in the College of Health and Human Sciences.",
    ),
    "Religious Studies": (
        "cla",
        "Religious studies examines world religions, theology, and religion-and-culture across global traditions.",
    ),
    "Rhetoric and Composition/Writing Studies": (
        "cla",
        "Writing and rhetoric courses support the Purdue Writing Lab and professional communication across disciplines.",
    ),
    "Romance Languages": (
        "cla",
        "French, Spanish, and Italian language and literature include study-abroad and translation workshops.",
    ),
    "Science, Technology and Society": (
        "cla",
        "Science, technology, and society examines science policy, ethics, and the social dimensions of technology.",
    ),
    "Slavic Languages": (
        "cla",
        "Russian and East European language and literature includes study-abroad and cultural-history coursework.",
    ),
    "Social Sciences": (
        "cla",
        "Social sciences distribution spans economics, sociology, and political science with quantitative-methods requirements.",
    ),
    "Sociology": (
        "cla",
        "Sociology examines urban inequality, health disparities, and social networks with community-based research.",
    ),
    "Soil Science": (
        "ag",
        "Soil science examines soil fertility, precision agriculture, and environmental quality on Indiana research farms.",
    ),
    "Special Education": (
        "ed",
        "Special education programs train teachers for inclusive classrooms and autism-spectrum interventions.",
    ),
    "Speech, Language, and Hearing Sciences": (
        "hhs",
        "Speech, language, and hearing sciences prepares audiologists and speech-language pathologists with clinical practica.",
    ),
    "Sports, Kinesiology, and Physical Education/Fitness": (
        "hhs",
        "Kinesiology and movement science covers exercise physiology, motor learning, and youth-sports policy.",
    ),
    "Statistics": (
        "sci",
        "Statistics training covers inference, Bayesian methods, and high-dimensional data for biostatistics careers.",
    ),
    "Systems Science and Theory": (
        "eng",
        "Systems engineering coursework models complex networks in health care, infrastructure, and policy using operations-research methods.",
    ),
    "Teacher Education (Levels and Methods)": (
        "ed",
        "Teacher preparation programs lead to Indiana licensure with classroom placements in Tippecanoe County partner schools.",
    ),
    "Teacher Education (Subject Areas)": (
        "ed",
        "Subject-area teacher education pairs content majors with pedagogy coursework and supervised student teaching.",
    ),
    "Theatre": (
        "rueff",
        "Theatre arts combines acting, directing, dramaturgy, and technical production with campus performances.",
    ),
    "Veterinary Biomedical Sciences": (
        "vet",
        "Veterinary biomedical sciences covers infectious disease, comparative oncology, and translational animal health.",
    ),
    "Veterinary Medicine": (
        "vet",
        "The D.V.M. curriculum moves from animal health sciences to extensive clinical training at the veterinary teaching hospital.",
    ),
    "Veterinary Technology": (
        "vet",
        "Veterinary technology trains credentialed technicians in clinical nursing, diagnostic imaging, and laboratory procedures.",
    ),
    "Visual Arts": (
        "rueff",
        "Fine arts combines drawing, painting, printmaking, and new media with studio critiques and gallery culture.",
    ),
    "Visual Communication Design": (
        "rueff",
        "Visual communication design covers branding, typography, and interactive media with industry portfolio reviews.",
    ),
    "Zoology/Animal Biology": (
        "sci",
        "Zoology examines animal behavior, ecology, and evolutionary biology with field and lab research.",
    ),
}

PEER_DENYLIST = [
    "Wharton", "SAS", "Perelman", "Writing Seminars", "Chesapeake", "Kelly Writers House",
    "McCormick", "Weill", "CALS", "Bloomberg", "Mailman", "Peabody", "Nolan School",
    "STScI", "APL", "UC Botanical", "Hutchins Center", "Berman Institute", "SEAS",
    "CUIMC", "New Bolton Center", "Rausser", "Blake Garden", "Mahoney Institute",
    "East West Lafayette", "Purdue Lab of Ornithology", "Purdue Review", "Purdue Museum",
    "Purdue Hospital", "Purdue Business School", "Purdue Psychiatry", "Purdue Kennedy",
    "Purdue Gene Therapy", "Purdue CIS", "Purdue Public Health", "VMD curriculum",
]

if __name__ == "__main__":
    missing = set()
    from unipaith.data.purdue_profile import PROGRAMS  # noqa: WPS433 — script entry

    for spec in PROGRAMS:
        field = spec.get("_field_name") or spec.get("program_name", "")
        if field not in FIELD_CLAUSES:
            missing.add(field)
    if missing:
        print("Missing clauses for:", sorted(missing)[:10], "...")
    else:
        print(f"All {len(PROGRAMS)} program fields covered by {len(FIELD_CLAUSES)} clauses")
