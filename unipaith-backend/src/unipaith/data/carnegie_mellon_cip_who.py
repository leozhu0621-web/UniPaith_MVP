"""Carnegie Mellon University — matcher-core ``cip_code`` + universal ``who_its_for``.

REPAIR_BACKLOG #1 (``cip_code`` starvation) and #4a (``who_its_for`` 0%), SKILL miss #2
(matcher-core fields) and miss #8 (universal depth field). The base ``carnegie_mellon_profile``
catalog (180 real, field-specific programs) shipped both fields null:

* ``cip_code`` — the CIP join key the CPEF matcher uses to resolve a program's field to
  ``ref_majors`` + the field-66 vocabulary. Every program here carries a verified NCES
  CIP-2020 6-digit code keyed by slug. The less-common / 2020-new codes were confirmed
  against the NCES CIP user site and DHS STEM list (AI 11.0102, Robotics 14.4201,
  Data Science 30.7001, Business Analytics 30.7102, Music Technology 50.0913,
  Language Interpretation and Translation 16.0103, Rhetoric and Composition 23.1304,
  Financial Mathematics 27.0305, Medical Informatics 51.2706, Human Computer Interaction
  30.3101, Sustainable Design/Architecture 04.0403). Every code is also present in the repo's
  own CIP vocabulary (``data/reference/ref_majors.jsonl``), the table the matcher resolves
  against. No guesses — a genuinely uncodeable program would be omitted with a reason, but
  every CMU field is codeable.

* ``who_its_for`` — a UNIVERSAL depth field: a field-specific, program-DISTINCT 1-2
  sentence statement of the applicant each program fits (background/interest, goal or
  readiness, typical next step), derived strictly from that program's own field + credential
  level. A bachelor's survey, a professional master's, and a funded research doctorate of the
  same field read differently because they serve different applicants. No fabricated facts
  (no rankings, numbers, or named centers), matching the field-specific gold bar
  (Brown/Emory/Purdue/Rice/UW-Madison). All strings are distinct (distinct/total = 1.0).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# CIP6_BY_SLUG — verified NCES CIP-2020 6-digit code per program.
# ---------------------------------------------------------------------------
CIP6_BY_SLUG: dict[str, str] = {
    # ── School of Computer Science ──
    "cmu-cs-bs": "11.0701",
    "cmu-ai-bs": "11.0102",
    "cmu-compbio-bs": "26.1104",
    "cmu-hci-bs": "30.3101",
    "cmu-robotics-bs": "14.4201",
    "cmu-mscs": "11.0701",
    "cmu-cs-phd": "11.0701",
    "cmu-ms-ml": "11.0102",
    "cmu-ml-phd": "11.0102",
    "cmu-mlt": "11.0701",
    "cmu-miis": "11.0701",
    "cmu-mcds": "30.7001",
    "cmu-msaii": "11.0102",
    "cmu-lti-phd": "11.0701",
    "cmu-msr": "14.4201",
    "cmu-mrsd": "14.4201",
    "cmu-mscv": "11.0701",
    "cmu-robotics-phd": "14.4201",
    "cmu-mhci": "30.3101",
    "cmu-msle": "11.0104",
    "cmu-hci-phd": "30.3101",
    "cmu-mse": "14.0903",
    "cmu-mse-online": "14.0903",
    "cmu-msit-privacy": "11.1003",
    "cmu-se-phd": "14.0903",
    "cmu-societal-computing-phd": "11.0104",
    "cmu-ms-compbio": "26.1104",
    "cmu-compbio-phd": "26.1104",
    "cmu-ms-automated-science": "26.1104",
    # ── College of Engineering ──
    "cmu-cheme-bs": "14.0701",
    "cmu-civil-bs": "14.0801",
    "cmu-environ-bs": "14.1401",
    "cmu-ece-bs": "14.1001",
    "cmu-mse-bs": "14.1801",
    "cmu-meche-bs": "14.1901",
    "cmu-bme-bs": "14.0501",
    "cmu-ms-ece": "14.1001",
    "cmu-ms-se-sv": "14.0903",
    "cmu-msaie-ece": "14.1001",
    "cmu-ece-phd": "14.1001",
    "cmu-ms-meche": "14.1901",
    "cmu-ms-meche-research": "14.1901",
    "cmu-ms-meche-advanced": "14.1901",
    "cmu-msaie-meche": "14.1901",
    "cmu-meche-phd": "14.1901",
    "cmu-ms-cee": "14.0801",
    "cmu-ms-cee-research": "14.0801",
    "cmu-msaie-civil": "14.0801",
    "cmu-ms-cce": "14.0801",
    "cmu-cee-phd": "14.0801",
    "cmu-ms-cheme": "14.0701",
    "cmu-mche": "14.0701",
    "cmu-ms-cse": "14.2701",
    "cmu-msaie-cheme": "14.0701",
    "cmu-ms-btpe": "14.0701",
    "cmu-cheme-phd": "14.0701",
    "cmu-ms-matsci": "14.1801",
    "cmu-ms-matsci-research": "14.1801",
    "cmu-ms-cmse": "14.1801",
    "cmu-matsci-phd": "14.1801",
    "cmu-ms-bme": "14.0501",
    "cmu-ms-bme-applied": "14.0501",
    "cmu-bme-phd": "14.0501",
    "cmu-ms-epp": "14.0101",
    "cmu-epp-phd": "14.0101",
    "cmu-msin": "11.0901",
    "cmu-msis": "11.1003",
    "cmu-msaie-is": "11.1003",
    "cmu-msit-is": "11.1003",
    "cmu-msmite": "14.1001",
    "cmu-miips": "14.0101",
    "cmu-miips-online": "14.0101",
    "cmu-mssm": "52.1201",
    "cmu-ms-etim": "15.1501",
    "cmu-africa-msece": "14.1001",
    "cmu-africa-msit": "11.0103",
    "cmu-africa-mseai": "11.0102",
    # ── Mellon College of Science ──
    "cmu-biosci-bs": "26.0101",
    "cmu-neuro-bs": "26.1501",
    "cmu-chem-bs": "40.0501",
    "cmu-math-bs": "27.0101",
    "cmu-compfin-bs": "27.0305",
    "cmu-physics-bs": "40.0801",
    "cmu-ms-qbb": "26.1103",
    "cmu-biosci-phd": "26.0101",
    "cmu-chem-phd": "40.0501",
    "cmu-physics-phd": "40.0801",
    "cmu-astro-phd": "40.0202",
    "cmu-ms-modern-physics": "40.0801",
    "cmu-math-phd": "27.0101",
    "cmu-da-math": "27.0101",
    "cmu-aco-phd": "27.0101",
    "cmu-ms-das": "30.7001",
    # ── Dietrich College of Humanities and Social Sciences ──
    "cmu-econ-bs": "45.0601",
    "cmu-creative-writing-ba": "23.1302",
    "cmu-professional-writing-ba": "23.1303",
    "cmu-history-ba": "54.0101",
    "cmu-global-studies-ba": "30.2001",
    "cmu-ir-bs": "45.0901",
    "cmu-linguistics-ba": "16.0102",
    "cmu-philosophy-ba": "38.0101",
    "cmu-logic-computation-bs": "38.0101",
    "cmu-psychology-bs": "42.0101",
    "cmu-cognitive-science-bs": "30.2501",
    "cmu-decision-science-bs": "52.1301",
    "cmu-statistics-bs": "27.0501",
    "cmu-stats-ml-bs": "27.0501",
    "cmu-information-systems-bs": "11.0401",
    "cmu-mads": "30.7001",
    "cmu-ms-statistics": "27.0501",
    "cmu-statistics-phd": "27.0501",
    "cmu-stats-ml-phd": "27.0501",
    "cmu-cert-fds-online": "30.7001",
    "cmu-psychology-phd": "42.0101",
    "cmu-cogneuro-phd": "26.1501",
    "cmu-ma-gcat": "16.0103",
    "cmu-ma-lcs": "23.1401",
    "cmu-mapw": "23.1303",
    "cmu-phd-rhetoric": "23.1304",
    "cmu-phd-lcs": "23.1401",
    "cmu-history-phd": "54.0101",
    "cmu-philosophy-phd": "38.0101",
    "cmu-ms-lcm": "38.0101",
    "cmu-bdr-phd": "42.0101",
    "cmu-ma-alsla": "16.0105",
    "cmu-mits": "52.1201",
    "cmu-msstair": "45.0901",
    "cmu-mint": "26.1501",
    "cmu-pnc-phd": "26.1501",
    "cmu-psn-phd": "26.1501",
    "cmu-comp-cultural-phd": "23.1401",
    "cmu-alsla-phd": "16.0105",
    # ── College of Fine Arts ──
    "cmu-barch": "04.0201",
    "cmu-art-bfa": "50.0702",
    "cmu-design-bdes": "50.0401",
    "cmu-drama-bfa": "50.0501",
    "cmu-music-bfa": "50.0901",
    "cmu-music-technology-bs": "50.0913",
    "cmu-march": "04.0201",
    "cmu-maad": "04.0201",
    "cmu-ms-msrsd": "04.0403",
    "cmu-mud": "04.0301",
    "cmu-arch-phd": "04.0201",
    "cmu-art-mfa": "50.0702",
    "cmu-mdes": "50.0401",
    "cmu-ma-design": "50.0401",
    "cmu-design-phd": "50.0401",
    "cmu-drama-mfa-directing": "50.0501",
    "cmu-drama-mfa-writing": "50.0504",
    "cmu-drama-mfa-design": "50.0502",
    "cmu-mm": "50.0903",
    "cmu-ms-music-tech": "50.0913",
    "cmu-mm-music-ed": "13.1312",
    "cmu-mscd": "04.0201",
    "cmu-msbpd": "04.0902",
    "cmu-msaecm": "52.2001",
    "cmu-ddes": "04.0201",
    # ── Tepper School of Business ──
    "cmu-mba": "52.0201",
    "cmu-mba-online": "52.0201",
    "cmu-msba": "30.7102",
    "cmu-msba-online": "30.7102",
    "cmu-msm": "52.0201",
    "cmu-mspm": "52.0201",
    "cmu-mscf": "52.0801",
    "cmu-tepper-phd": "52.0201",
    # ── Heinz College of Information Systems and Public Policy ──
    "cmu-mism": "52.1201",
    "cmu-mism-bida": "52.1201",
    "cmu-msit-online": "11.0103",
    "cmu-msispm": "11.1003",
    "cmu-aim": "52.1201",
    "cmu-heinz-ism-phd": "52.1201",
    "cmu-msppm": "44.0501",
    "cmu-msppm-da": "44.0501",
    "cmu-msppm-dc": "44.0501",
    "cmu-mshca": "51.2706",
    "cmu-mmm": "51.0701",
    "cmu-mpm": "44.0401",
    "cmu-heinz-ppm-phd": "44.0501",
    "cmu-mam": "50.1001",
    "cmu-meim": "50.1001",
}


# ---------------------------------------------------------------------------
# WHO_BY_SLUG — program-DISTINCT "Who it's for" (distinct/total = 1.0).
# ---------------------------------------------------------------------------
WHO_BY_SLUG: dict[str, str] = {
    # ── School of Computer Science ──
    "cmu-cs-bs": (
        "Undergraduates who want a rigorous, theory-forward foundation in algorithms, "
        "systems, and software and expect to head into software engineering, research, or "
        "graduate study in computing."
    ),
    "cmu-ai-bs": (
        "Students set on building intelligent systems from the ground up — machine learning, "
        "perception, and decision-making — who want a dedicated AI major rather than a CS "
        "concentration, aiming at AI engineering or research roles."
    ),
    "cmu-compbio-bs": (
        "Undergraduates fluent in both biology and programming who want to model living "
        "systems and analyze genomic and molecular data, pointing toward computational biology "
        "research, biotech, or a doctorate."
    ),
    "cmu-hci-bs": (
        "Students who care as much about people as about code and want to design and evaluate "
        "interactive technology, preparing for UX, product, or interaction-design careers."
    ),
    "cmu-robotics-bs": (
        "Hands-on builders drawn to autonomous machines who want to combine perception, "
        "control, and mechanical design, aiming at robotics engineering or graduate research."
    ),
    "cmu-mscs": (
        "Computing graduates and working engineers who want advanced, research-informed depth "
        "in algorithms and systems to move into senior technical roles or a research track."
    ),
    "cmu-cs-phd": (
        "Aspiring computer-science researchers with strong theory and systems preparation who "
        "want a funded doctorate and a future in academia or an industrial research lab."
    ),
    "cmu-ms-ml": (
        "Quantitatively strong graduates who want to specialize deeply in machine-learning "
        "methods and theory, headed for ML engineering, applied-science, or research-adjacent "
        "roles."
    ),
    "cmu-ml-phd": (
        "Researchers committed to advancing the foundations of machine learning who want a "
        "funded doctorate and a career inventing new methods in academia or research labs."
    ),
    "cmu-mlt": (
        "Graduates fascinated by language and computation who want to build systems for "
        "translation, speech, and natural-language understanding, aiming at NLP engineering or "
        "research."
    ),
    "cmu-miis": (
        "Engineering-minded students who want to build end-to-end intelligent information "
        "systems that retrieve, reason over, and act on data, headed for applied AI and "
        "search-systems roles."
    ),
    "cmu-mcds": (
        "Technically strong graduates who want to engineer large-scale data pipelines and "
        "machine-learning systems, preparing for data-engineering and applied data-science "
        "careers."
    ),
    "cmu-msaii": (
        "Builders who want to ship real AI products, pairing machine-learning depth with "
        "innovation and entrepreneurship, aiming at AI product and venture-building roles."
    ),
    "cmu-lti-phd": (
        "Researchers in natural-language processing, speech, and information retrieval who want "
        "a funded doctorate and a path to academic or industrial language-technology research."
    ),
    "cmu-msr": (
        "Graduates with a strong robotics or engineering base who want research-grade depth in "
        "perception, manipulation, and autonomy, often as a step toward a PhD or an R&D role."
    ),
    "cmu-mrsd": (
        "Engineers who want to lead the development of complete robotic products, blending "
        "technical depth with systems integration and project leadership for industry."
    ),
    "cmu-mscv": (
        "Graduates focused specifically on visual perception who want to master image and video "
        "understanding, headed for computer-vision engineering and applied-research roles."
    ),
    "cmu-robotics-phd": (
        "Future robotics scholars who want a funded doctorate to push the science of autonomous "
        "machines, aiming at faculty positions or advanced industrial research."
    ),
    "cmu-mhci": (
        "Career-changers and recent graduates who want an intensive, project-based path into "
        "user-experience research and design, headed straight for UX and product roles."
    ),
    "cmu-msle": (
        "People who want to design technology and data systems that improve how students learn, "
        "bridging learning science and engineering for edtech and learning-analytics work."
    ),
    "cmu-hci-phd": (
        "Researchers who want to study and invent new forms of human-computer interaction at a "
        "doctoral level, preparing for academic or research-lab careers."
    ),
    "cmu-mse": (
        "Practicing engineers who want to master large-scale software design, architecture, and "
        "team leadership, moving toward senior and technical-lead roles."
    ),
    "cmu-mse-online": (
        "Working software professionals who need the flexibility of a fully online degree to "
        "deepen their engineering practice without leaving their jobs."
    ),
    "cmu-msit-privacy": (
        "Technologists who want to engineer systems that protect personal data, combining "
        "software skills with privacy law and policy for privacy-engineering roles."
    ),
    "cmu-se-phd": (
        "Researchers committed to the science of building software at scale who want a funded "
        "doctorate and a future in academic or industrial software-engineering research."
    ),
    "cmu-societal-computing-phd": (
        "Scholars who want to study how computing systems shape society, pairing technical depth "
        "with social science for research on technology's human impact."
    ),
    "cmu-ms-compbio": (
        "Graduates who want advanced computational and quantitative methods for biology and "
        "genomics, preparing for biotech, pharma, or doctoral research."
    ),
    "cmu-compbio-phd": (
        "Researchers at the intersection of computation and the life sciences who want a funded "
        "doctorate to develop new methods for biological discovery."
    ),
    "cmu-ms-automated-science": (
        "Scientists and engineers who want to automate experimentation with robotics and machine "
        "learning, aiming at high-throughput, AI-driven research roles in the life sciences."
    ),
    # ── College of Engineering ──
    "cmu-cheme-bs": (
        "Undergraduates drawn to chemistry and process design who want to turn molecules into "
        "products and energy at scale, heading into chemical, energy, or materials industries."
    ),
    "cmu-civil-bs": (
        "Students who want to design and build the bridges, buildings, and infrastructure that "
        "communities depend on, preparing for civil-engineering practice or graduate study."
    ),
    "cmu-environ-bs": (
        "Engineers motivated by clean water, air, and climate who want to design systems that "
        "protect the environment and public health."
    ),
    "cmu-ece-bs": (
        "Undergraduates fascinated by circuits, signals, and computing hardware who want broad "
        "depth across electrical and computer engineering for industry or research."
    ),
    "cmu-mse-bs": (
        "Students curious about why materials behave as they do who want to design the metals, "
        "polymers, and semiconductors behind new technologies."
    ),
    "cmu-meche-bs": (
        "Hands-on undergraduates who want to design machines, energy systems, and mechanical "
        "products, preparing for engineering practice across many industries."
    ),
    "cmu-bme-bs": (
        "Students pairing engineering with the life sciences who want to build medical devices "
        "and biotechnologies, often alongside another engineering major."
    ),
    "cmu-ms-ece": (
        "Electrical and computer-engineering graduates who want advanced, customizable depth "
        "across hardware, software, and systems for senior technical roles."
    ),
    "cmu-ms-se-sv": (
        "Software engineers who want a Silicon Valley-based, industry-immersed master's that "
        "blends technical depth with startup and product experience."
    ),
    "cmu-msaie-ece": (
        "Electrical and computer engineers who want to specialize in the hardware and systems "
        "that power AI, from accelerators to embedded intelligence."
    ),
    "cmu-ece-phd": (
        "Future scholars in electrical and computer engineering who want a funded doctorate "
        "spanning devices, systems, and computing for academic or industrial research."
    ),
    "cmu-ms-meche": (
        "Mechanical-engineering graduates who want advanced coursework and design depth to move "
        "into specialized industry roles or further study."
    ),
    "cmu-ms-meche-research": (
        "Mechanical engineers who want a thesis-driven, research-intensive master's as a bridge "
        "toward a doctorate or an R&D career."
    ),
    "cmu-ms-meche-advanced": (
        "Practicing mechanical engineers who want flexible advanced study to deepen expertise in "
        "a chosen specialization without a research thesis."
    ),
    "cmu-msaie-meche": (
        "Mechanical engineers who want to apply artificial intelligence to design, manufacturing, "
        "and control, aiming at AI-driven engineering roles."
    ),
    "cmu-meche-phd": (
        "Researchers in mechanics, energy, and design who want a funded doctorate and a future "
        "advancing mechanical engineering in academia or industry."
    ),
    "cmu-ms-cee": (
        "Civil and environmental engineering graduates who want advanced professional depth in "
        "infrastructure, water, or sustainability for industry practice."
    ),
    "cmu-ms-cee-research": (
        "Civil and environmental engineers who want a research-focused master's with a thesis as "
        "preparation for a doctorate or an R&D role."
    ),
    "cmu-msaie-civil": (
        "Civil engineers who want to bring artificial intelligence to infrastructure, sensing, "
        "and the built environment, aiming at smart-infrastructure roles."
    ),
    "cmu-ms-cce": (
        "Engineers who want to combine civil-infrastructure expertise with computing and data, "
        "preparing for the digital transformation of the built environment."
    ),
    "cmu-cee-phd": (
        "Future scholars of infrastructure, environment, and sustainability who want a funded "
        "doctorate and a research career in civil and environmental engineering."
    ),
    "cmu-ms-cheme": (
        "Chemical-engineering graduates who want an applied, industry-oriented master's with a "
        "practicum to step into process and product engineering roles."
    ),
    "cmu-mche": (
        "Chemical engineers who want a focused professional master's to deepen practice and "
        "advance into senior process-engineering positions."
    ),
    "cmu-ms-cse": (
        "Engineers who want to master computation, modeling, and optimization for chemical and "
        "process systems, aiming at simulation-driven engineering roles."
    ),
    "cmu-msaie-cheme": (
        "Chemical engineers who want to apply machine learning to molecules, processes, and "
        "materials discovery, headed for AI-enabled process roles."
    ),
    "cmu-ms-btpe": (
        "Engineers focused on the manufacture of biologics and pharmaceuticals who want depth in "
        "bioprocessing and pharmaceutical engineering for the biotech industry."
    ),
    "cmu-cheme-phd": (
        "Researchers in reaction engineering, energy, and soft matter who want a funded doctorate "
        "and a career advancing chemical engineering."
    ),
    "cmu-ms-matsci": (
        "Materials-engineering graduates who want advanced study of structure, processing, and "
        "properties to move into materials industry or research."
    ),
    "cmu-ms-matsci-research": (
        "Materials engineers who want a thesis-based, research-intensive master's as a step "
        "toward a doctorate or an R&D laboratory."
    ),
    "cmu-ms-cmse": (
        "Engineers who want to design materials through simulation and machine learning, aiming "
        "at computational materials and informatics roles."
    ),
    "cmu-matsci-phd": (
        "Future scholars of materials science who want a funded doctorate to discover and design "
        "the materials behind emerging technologies."
    ),
    "cmu-ms-bme": (
        "Biomedical-engineering graduates who want a research-oriented master's in medical "
        "devices, imaging, or biomechanics on the way to a doctorate or R&D role."
    ),
    "cmu-ms-bme-applied": (
        "Engineers who want an applied, industry-facing biomedical master's with a practicum to "
        "step directly into the medical-technology sector."
    ),
    "cmu-bme-phd": (
        "Researchers bridging engineering and medicine who want a funded doctorate to advance "
        "biomedical devices, imaging, and therapies."
    ),
    "cmu-ms-epp": (
        "Engineers and scientists who want to work where technology meets policy, analyzing "
        "energy, environment, and technology decisions for government, industry, or think tanks."
    ),
    "cmu-epp-phd": (
        "Researchers who want a funded doctorate combining engineering analysis with public "
        "policy to study technology's role in society's biggest challenges."
    ),
    "cmu-msin": (
        "Engineers who want deep expertise in networking, distributed systems, and connected "
        "infrastructure, preparing for systems and network engineering roles."
    ),
    "cmu-msis": (
        "Technically strong graduates who want to specialize in securing systems and networks, "
        "headed for security-engineering and information-security careers."
    ),
    "cmu-msaie-is": (
        "Security-minded engineers who want to apply artificial intelligence to threat detection "
        "and defense, aiming at AI-driven cybersecurity roles."
    ),
    "cmu-msit-is": (
        "Working professionals who want a bicoastal, industry-connected master's in information "
        "security that combines technical depth with applied practice."
    ),
    "cmu-msmite": (
        "Engineers drawn to mobile and connected-device technology who want depth in embedded "
        "systems and the Internet of Things for industry roles."
    ),
    "cmu-miips": (
        "Cross-disciplinary builders who want to lead the creation of new products and services, "
        "combining engineering, design, and business for innovation roles."
    ),
    "cmu-miips-online": (
        "Working professionals who want the integrated product-innovation curriculum in a "
        "flexible online format while staying in their current roles."
    ),
    "cmu-mssm": (
        "Engineers and technical professionals who want to lead software organizations, blending "
        "engineering depth with management for software-leadership roles."
    ),
    "cmu-ms-etim": (
        "Engineers who want to manage technology, innovation, and new ventures, aiming at "
        "technical management and product-strategy positions."
    ),
    "cmu-africa-msece": (
        "Engineers based in or focused on Africa who want rigorous electrical and computer "
        "engineering training to drive the continent's technology sector."
    ),
    "cmu-africa-msit": (
        "Technology professionals advancing Africa's digital economy who want applied "
        "information-technology depth for engineering and product roles."
    ),
    "cmu-africa-mseai": (
        "Engineers building Africa's AI capacity who want a hands-on master's in engineering "
        "artificial intelligence for applied and entrepreneurial work."
    ),
    # ── Mellon College of Science ──
    "cmu-biosci-bs": (
        "Undergraduates fascinated by living systems from molecules to organisms who want a "
        "strong base for medicine, biotech, or graduate research."
    ),
    "cmu-neuro-bs": (
        "Students drawn to the brain and behavior who want an interdisciplinary base in the "
        "biology of the nervous system, pointing toward medicine or neuroscience research."
    ),
    "cmu-chem-bs": (
        "Undergraduates who love understanding matter at the molecular level and want a rigorous "
        "chemistry foundation for industry, medicine, or graduate study."
    ),
    "cmu-math-bs": (
        "Students who enjoy abstraction and proof and want a deep mathematics foundation for "
        "research, quantitative careers, or graduate study."
    ),
    "cmu-compfin-bs": (
        "Quantitatively gifted undergraduates who want to apply mathematics and computing to "
        "markets and risk, aiming at quantitative finance roles."
    ),
    "cmu-physics-bs": (
        "Undergraduates curious about the fundamental laws of nature who want a strong physics "
        "base for research, engineering, or graduate study."
    ),
    "cmu-ms-qbb": (
        "Life scientists and quantitative graduates who want master's-level training in "
        "bioinformatics and quantitative biology for biotech or doctoral study."
    ),
    "cmu-biosci-phd": (
        "Researchers in molecular, cellular, and computational biology who want a funded "
        "doctorate and a future in life-science research."
    ),
    "cmu-chem-phd": (
        "Aspiring chemistry researchers who want a funded doctorate to investigate synthesis, "
        "materials, or biological chemistry in academia or industry."
    ),
    "cmu-physics-phd": (
        "Future physicists who want a funded doctorate to pursue research in fields from "
        "condensed matter to particle and biological physics."
    ),
    "cmu-astro-phd": (
        "Researchers drawn to the cosmos who want a funded doctorate studying galaxies, "
        "cosmology, and astrophysical phenomena."
    ),
    "cmu-ms-modern-physics": (
        "Physics graduates who want focused advanced coursework in contemporary physics as a "
        "bridge to doctoral study or technical careers."
    ),
    "cmu-math-phd": (
        "Future mathematicians who want a funded doctorate to do original research in pure or "
        "applied mathematics."
    ),
    "cmu-da-math": (
        "Mathematicians who want a doctorate emphasizing teaching and the scholarship of "
        "mathematics, aiming at college and university faculty careers."
    ),
    "cmu-aco-phd": (
        "Researchers drawn to discrete mathematics who want a funded doctorate in algorithms, "
        "combinatorics, and optimization across math, CS, and operations research."
    ),
    "cmu-ms-das": (
        "Scientists and analysts who want to apply data science to scientific data, preparing "
        "for research-data and analytics roles in science-driven organizations."
    ),
    # ── Dietrich College of Humanities and Social Sciences ──
    "cmu-econ-bs": (
        "Undergraduates who want to analyze how people, markets, and policy interact, preparing "
        "for careers in finance, consulting, government, or graduate economics."
    ),
    "cmu-creative-writing-ba": (
        "Students who want to develop their voice in fiction, poetry, or nonfiction while "
        "building broad humanities skills for writing and media careers."
    ),
    "cmu-professional-writing-ba": (
        "Undergraduates who want to write clearly for organizations and audiences, preparing for "
        "technical writing, communications, and content roles."
    ),
    "cmu-history-ba": (
        "Students drawn to how social and political forces shaped the past who want strong "
        "research and argument skills for law, policy, or graduate study."
    ),
    "cmu-global-studies-ba": (
        "Undergraduates interested in globalization, culture, and transnational issues who want "
        "an interdisciplinary base for careers in international affairs or development."
    ),
    "cmu-ir-bs": (
        "Students focused on world politics, security, and diplomacy who want analytical and "
        "policy skills for foreign service, government, or international organizations."
    ),
    "cmu-linguistics-ba": (
        "Undergraduates fascinated by how language works who want to study its structure and use, "
        "pointing toward research, language technology, or graduate study."
    ),
    "cmu-philosophy-ba": (
        "Students who want to reason carefully about knowledge, ethics, and mind, building "
        "analytical skills valued in law, policy, and many graduate fields."
    ),
    "cmu-logic-computation-bs": (
        "Undergraduates drawn to formal reasoning who want to study logic at the meeting point of "
        "philosophy, mathematics, and computer science."
    ),
    "cmu-psychology-bs": (
        "Students curious about mind and behavior who want a science-grounded psychology base for "
        "health, research, or applied behavioral careers."
    ),
    "cmu-cognitive-science-bs": (
        "Undergraduates who want to study how minds compute and learn across psychology, "
        "neuroscience, and computer science, aiming at cognitive research or AI."
    ),
    "cmu-decision-science-bs": (
        "Students who want to understand and improve how people and organizations make decisions, "
        "blending economics, psychology, and statistics for analytics and policy work."
    ),
    "cmu-statistics-bs": (
        "Undergraduates who want to reason from data with rigor, preparing for analytics, data "
        "science, or graduate study in statistics."
    ),
    "cmu-stats-ml-bs": (
        "Students who want statistics tightly integrated with machine learning, aiming at "
        "data-science and modeling roles or graduate study."
    ),
    "cmu-information-systems-bs": (
        "Undergraduates who want to connect technology, data, and business, preparing for "
        "product, consulting, and information-systems careers."
    ),
    "cmu-mads": (
        "Graduates and professionals who want applied, project-based data-science training to "
        "move into analytics and machine-learning roles."
    ),
    "cmu-ms-statistics": (
        "Quantitatively strong graduates who want advanced statistical theory and methods for "
        "data-science careers or doctoral study."
    ),
    "cmu-statistics-phd": (
        "Future statisticians who want a funded doctorate to develop new statistical methodology "
        "for research in academia or industry."
    ),
    "cmu-stats-ml-phd": (
        "Researchers at the boundary of statistics and machine learning who want a funded joint "
        "doctorate advancing the theory and practice of learning from data."
    ),
    "cmu-cert-fds-online": (
        "Working professionals who want to build a verified foundation in data-science methods "
        "online before advancing or applying to a full graduate program."
    ),
    "cmu-psychology-phd": (
        "Researchers in cognitive, social, or developmental psychology who want a funded "
        "doctorate and a future in behavioral-science research."
    ),
    "cmu-cogneuro-phd": (
        "Scientists studying how the brain gives rise to cognition who want a funded doctorate "
        "combining psychology and neuroscience."
    ),
    "cmu-ma-gcat": (
        "Multilingual graduates who want professional skills in cross-cultural communication and "
        "translation for global organizations and language-services careers."
    ),
    "cmu-ma-lcs": (
        "Humanities graduates who want advanced study of literature and culture, preparing for "
        "doctoral work, teaching, or writing and editorial careers."
    ),
    "cmu-mapw": (
        "Graduates who want to become expert professional and technical writers, advancing into "
        "communications, content-strategy, and documentation leadership."
    ),
    "cmu-phd-rhetoric": (
        "Scholars of rhetoric, writing, and communication who want a funded doctorate and a "
        "future in academic research and teaching."
    ),
    "cmu-phd-lcs": (
        "Researchers in literary and cultural studies who want a funded doctorate to pursue "
        "scholarship and a faculty career in the humanities."
    ),
    "cmu-history-phd": (
        "Future historians who want a funded doctorate to conduct original archival research and "
        "teach at the university level."
    ),
    "cmu-philosophy-phd": (
        "Aspiring philosophers who want a funded doctorate to do original work in areas such as "
        "logic, ethics, or philosophy of science, aiming at academic careers."
    ),
    "cmu-ms-lcm": (
        "Graduates drawn to formal methods in philosophy who want master's-level training in "
        "logic, computation, and methodology for research or doctoral study."
    ),
    "cmu-bdr-phd": (
        "Researchers who want a funded doctorate studying human judgment and decision-making, "
        "combining psychology and economics for academic or applied research."
    ),
    "cmu-ma-alsla": (
        "Language educators and graduates who want master's training in applied linguistics and "
        "second-language acquisition for teaching, assessment, or research."
    ),
    "cmu-mits": (
        "Professionals who want to align technology with organizational strategy, preparing for "
        "IT leadership, security strategy, and management roles."
    ),
    "cmu-msstair": (
        "Graduates focused on the security and policy dimensions of technology who want depth in "
        "international relations for government, defense, and analysis careers."
    ),
    "cmu-mint": (
        "Engineers and scientists who want to build technologies that interface with the nervous "
        "system, aiming at neurotechnology and neural-engineering roles."
    ),
    "cmu-pnc-phd": (
        "Researchers who want a funded doctorate modeling how neural circuits compute, bridging "
        "neuroscience, statistics, and machine learning."
    ),
    "cmu-psn-phd": (
        "Scientists who want a funded doctorate studying how brain systems produce perception and "
        "behavior, pointing toward systems-neuroscience research."
    ),
    "cmu-comp-cultural-phd": (
        "Humanities researchers who want to study culture and texts with computational methods, "
        "pursuing a funded doctorate in the digital humanities."
    ),
    "cmu-alsla-phd": (
        "Researchers in applied linguistics and second-language acquisition who want a funded "
        "doctorate and a future studying how people learn and use language."
    ),
    # ── College of Fine Arts ──
    "cmu-barch": (
        "Students who want a professional, studio-based path to becoming a licensed architect, "
        "combining design, history, and building technology."
    ),
    "cmu-art-bfa": (
        "Artists who want a conceptually rigorous studio education across media, preparing for "
        "professional art practice or graduate study."
    ),
    "cmu-design-bdes": (
        "Undergraduates who want to design for products, communication, and interactions, "
        "preparing for careers in UX, industrial, and service design."
    ),
    "cmu-drama-bfa": (
        "Performers and theatre-makers who want intensive conservatory training within a research "
        "university, preparing for professional careers in the dramatic arts."
    ),
    "cmu-music-bfa": (
        "Musicians who want conservatory-level performance and musicianship training alongside a "
        "broad university education."
    ),
    "cmu-music-technology-bs": (
        "Students at the meeting of music and engineering who want to build instruments, software, "
        "and audio systems for creative-technology careers."
    ),
    "cmu-march": (
        "Graduates pursuing licensure who want a professional architecture degree grounded in "
        "design research and emerging building technologies."
    ),
    "cmu-maad": (
        "Licensed or trained architects who want a post-professional year to develop an advanced, "
        "research-driven design practice."
    ),
    "cmu-ms-msrsd": (
        "Designers and architects who want to lead ecologically regenerative, sustainable design, "
        "aiming at green-building and environmental-design careers."
    ),
    "cmu-mud": (
        "Architects and planners who want to shape cities at the scale of districts and public "
        "space, preparing for urban-design practice."
    ),
    "cmu-arch-phd": (
        "Researchers in architectural history, theory, or building science who want a funded "
        "doctorate and an academic or research career."
    ),
    "cmu-art-mfa": (
        "Practicing artists who want a rigorous studio master's to develop a mature body of work "
        "and a professional or teaching career."
    ),
    "cmu-mdes": (
        "Designers who want to specialize in designing for interactions and complex systems, "
        "preparing for senior interaction- and service-design roles."
    ),
    "cmu-ma-design": (
        "Designers and researchers who want a focused master's to deepen design thinking and "
        "research methods for practice or doctoral study."
    ),
    "cmu-design-phd": (
        "Designers committed to systems-level, transition-oriented change who want a doctorate "
        "researching design for social and ecological transformation."
    ),
    "cmu-drama-mfa-directing": (
        "Theatre artists who want advanced conservatory training as directors, preparing for "
        "professional careers staging new and classic work."
    ),
    "cmu-drama-mfa-writing": (
        "Writers for the stage and screen who want intensive training in dramatic writing, aiming "
        "at professional playwriting and screenwriting careers."
    ),
    "cmu-drama-mfa-design": (
        "Theatre designers and technicians who want advanced training in scenic, lighting, sound, "
        "or costume design for professional production work."
    ),
    "cmu-mm": (
        "Musicians who want advanced performance training and artistic refinement on the way to "
        "professional careers as performers."
    ),
    "cmu-ms-music-tech": (
        "Graduates blending musicianship with engineering who want advanced study in audio, "
        "instruments, and music software for research or creative-technology roles."
    ),
    "cmu-mm-music-ed": (
        "Musicians who want to teach, combining performance with the pedagogy and practice of "
        "music education for school and studio careers."
    ),
    "cmu-mscd": (
        "Designers and architects who want to master computational design and digital fabrication "
        "for technology-driven design practice."
    ),
    "cmu-msbpd": (
        "Architects and engineers who want to analyze and improve how buildings perform, aiming "
        "at building-science, energy, and sustainability roles."
    ),
    "cmu-msaecm": (
        "Professionals who want to lead across architecture, engineering, and construction, "
        "combining technical and management skills for the built-environment industry."
    ),
    "cmu-ddes": (
        "Experienced designers and architects who want a practice-oriented doctorate to lead "
        "advanced design research in industry or academia."
    ),
    # ── Tepper School of Business ──
    "cmu-mba": (
        "Professionals who want an analytical, technology-forward MBA to step into leadership in "
        "management, consulting, finance, or product."
    ),
    "cmu-mba-online": (
        "Working professionals who want Tepper's data-driven MBA in a flexible hybrid-online "
        "format while continuing their careers."
    ),
    "cmu-msba": (
        "Early-career analysts who want to turn data into business decisions, preparing for "
        "analytics, consulting, and decision-support roles."
    ),
    "cmu-msba-online": (
        "Working professionals who want rigorous business-analytics training online to advance "
        "into data-driven decision roles."
    ),
    "cmu-msm": (
        "Recent graduates without a business background who want a focused master's to build "
        "management and analytical fundamentals for early-career business roles."
    ),
    "cmu-mspm": (
        "Technically minded graduates who want to lead the development of products, bridging "
        "engineering, design, and business for product-management careers."
    ),
    "cmu-mscf": (
        "Quantitatively elite graduates who want rigorous training in mathematical finance and "
        "computation for quantitative-finance and risk careers."
    ),
    "cmu-tepper-phd": (
        "Researchers in fields such as economics, finance, operations, or marketing who want a "
        "funded doctorate and a future as business-school faculty."
    ),
    # ── Heinz College of Information Systems and Public Policy ──
    "cmu-mism": (
        "Technically capable graduates who want to lead at the intersection of information "
        "systems and management, preparing for technology-management and consulting roles."
    ),
    "cmu-mism-bida": (
        "Graduates who want an information-systems master's concentrated in business intelligence "
        "and data analytics for data-leadership roles."
    ),
    "cmu-msit-online": (
        "Working professionals who want a flexible online master's in information technology to "
        "advance their technical and management careers."
    ),
    "cmu-msispm": (
        "Professionals who want to lead information security where technology meets policy and "
        "management, aiming at security-governance roles."
    ),
    "cmu-aim": (
        "Managers and technologists who want to lead the adoption of artificial intelligence in "
        "organizations, blending AI literacy with management."
    ),
    "cmu-heinz-ism-phd": (
        "Researchers studying information systems, technology, and organizations who want a funded "
        "doctorate and an academic or research career."
    ),
    "cmu-msppm": (
        "Aspiring policy analysts who want to combine public policy with strong data and "
        "management skills for government, nonprofit, and consulting careers."
    ),
    "cmu-msppm-da": (
        "Policy graduates who want a quantitative, data-analytics-focused master's to drive "
        "evidence-based decisions in the public sector."
    ),
    "cmu-msppm-dc": (
        "Policy professionals who want a Washington-based master's immersing them in federal "
        "policy and analytics, headed for government and advocacy roles."
    ),
    "cmu-mshca": (
        "Analysts focused on health and medicine who want to apply data science to care, costs, "
        "and outcomes, preparing for health-analytics careers."
    ),
    "cmu-mmm": (
        "Physicians and clinicians who want management and leadership skills to advance into "
        "executive roles in health-care organizations."
    ),
    "cmu-mpm": (
        "Public-service professionals who want a focused master's in public management to lead "
        "and improve government and nonprofit organizations."
    ),
    "cmu-heinz-ppm-phd": (
        "Researchers in public policy and management who want a funded doctorate to study policy "
        "questions empirically and pursue an academic career."
    ),
    "cmu-mam": (
        "Arts and culture professionals who want management and finance skills to lead museums, "
        "performing-arts organizations, and cultural institutions."
    ),
    "cmu-meim": (
        "Aspiring entertainment-industry leaders who want business and management training for "
        "careers in film, music, gaming, and media."
    ),
}
