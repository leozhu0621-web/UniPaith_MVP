"""Cornell University external_reviews depth pass — 62 coverable programs.

Depth pass date: 2026-06-15. Consumed by the ``cornellprof5`` migration to merge
``DEPTH_REVIEWS`` into ``cornell_profile._REVIEWS_BY_SLUG`` for programs not covered
by the initial eleven flagship reviews.
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "cornell-aerospace-aeronautical-and-astronautical-space-engineering-ms": {
        "summary": (
            "Graduate applicants describe Cornell AEP's aerospace M.S. as a research and coursework degree in fluid dynamics, propulsion, and space systems within a top engineering college; praise includes Cornell's Ivy League engineering reputation and project-team culture, with cautions about grade deflation, self-funded tuition for terminal master's students, and a smaller cohort than flagship MAE or ECE departments."
        ),
        "themes": [
            {
                "label": "Fluid dynamics & propulsion",
                "sentiment": "positive",
                "detail": "Graduate coursework spans CFD, combustion, and propulsion systems.",
            },
            {
                "label": "Space research",
                "sentiment": "positive",
                "detail": "Faculty labs work on spacecraft dynamics and atmospheric flight.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter aerospace R&D and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller cohort than flagship MAE or ECE departments.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Aerospace Engineering",
                "url": "https://www.aep.cornell.edu/aep/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-aerospace-aeronautical-and-astronautical-space-engineering-phd": {
        "summary": (
            "Doctoral students describe Cornell AEP's aerospace Ph.D. as a research degree producing scholars in propulsion, astrodynamics, and atmospheric flight; praise includes access to leading propulsion and space-systems labs, with cautions about competitive admission, long dissertation timelines, and a specialized aerospace hiring market."
        ),
        "themes": [
            {
                "label": "Propulsion research",
                "sentiment": "positive",
                "detail": "Doctoral labs lead work in combustion, plasma, and space propulsion.",
            },
            {
                "label": "Astrodynamics",
                "sentiment": "positive",
                "detail": "Research groups study orbital mechanics and spacecraft control.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and aerospace R&D leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Aerospace Engineering",
                "url": "https://www.aep.cornell.edu/aep/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-agricultural-business-and-management-ms": {
        "summary": (
            "Graduate applicants describe Cornell Dyson's M.S. in Agricultural Business and Management as an applied economics and management degree rooted in food, agribusiness, and rural markets within CALS; students value the Dyson faculty's policy and finance expertise and Cornell's land-grant network, with cautions about a niche hiring market outside agribusiness and self-funded tuition for terminal master's students."
        ),
        "themes": [
            {
                "label": "Agribusiness & food systems",
                "sentiment": "positive",
                "detail": "Curriculum connects economics, finance, and agricultural markets.",
            },
            {
                "label": "Dyson faculty depth",
                "sentiment": "positive",
                "detail": "Applied economics faculty active in food policy and rural development.",
            },
            {
                "label": "Land-grant network",
                "sentiment": "positive",
                "detail": "Cornell CALS ties to extension and industry partners nationally.",
            },
            {
                "label": "Niche job market",
                "sentiment": "mixed",
                "detail": "Roles concentrate in agribusiness, food, and policy rather than general finance.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Dyson — Graduate programs",
                "url": "https://dyson.cornell.edu/programs/graduate/",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-agricultural-business-and-management-phd": {
        "summary": (
            "Doctoral students describe Cornell Dyson's Ph.D. in Agricultural Business and Management as a research degree in applied economics, marketing, and management of food and agricultural systems; praise centers on faculty mentorship in econometrics and policy, with cautions about competitive funding, long dissertation timelines, and academic job markets that favor specialized ag-econ placements."
        ),
        "themes": [
            {
                "label": "Applied economics research",
                "sentiment": "positive",
                "detail": "Doctoral training in econometrics, marketing, and food-system policy.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Close work with Dyson faculty on publishable empirical research.",
            },
            {
                "label": "Policy relevance",
                "sentiment": "positive",
                "detail": "Research informs USDA, extension, and global food-security debates.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Specialized placements",
                "sentiment": "mixed",
                "detail": "Graduates target ag-econ faculty and policy roles more than general consulting.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Dyson — Ph.D. program",
                "url": "https://dyson.cornell.edu/programs/phd/",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-agricultural-engineering-bs": {
        "summary": (
            "Students describe Cornell BEE's biological and environmental engineering undergraduate program as training that bridges biology, chemistry, and engineering for sustainable food, water, and environmental systems; praise includes CALS extension ties and research access, with cautions about grade deflation, demanding core coursework, and careers concentrated in agribusiness and environmental consulting."
        ),
        "themes": [
            {
                "label": "Sustainable systems",
                "sentiment": "positive",
                "detail": "Training in water resources, bioprocessing, and environmental engineering.",
            },
            {
                "label": "CALS + Engineering bridge",
                "sentiment": "positive",
                "detail": "Connects land-grant agriculture with engineering design.",
            },
            {
                "label": "Research & extension",
                "sentiment": "positive",
                "detail": "Undergraduates join labs addressing food security and water quality.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Industry focus",
                "sentiment": "mixed",
                "detail": "Careers concentrate in agribusiness and environmental consulting.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Biological and Environmental Engineering",
                "url": "https://www.bee.cornell.edu/bee/programs/undergraduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-agricultural-engineering-ms": {
        "summary": (
            "Graduate students describe Cornell BEE's master's as training in bioprocessing, environmental systems, and sustainable agriculture within CALS; praise includes interdisciplinary faculty bridging engineering and ecology, with cautions about self-funded tuition for terminal master's students and the need to define a coherent BEE focus area early."
        ),
        "themes": [
            {
                "label": "Bioprocessing & environment",
                "sentiment": "positive",
                "detail": "Graduate work spans wastewater, bioenergy, and food processing.",
            },
            {
                "label": "Interdisciplinary faculty",
                "sentiment": "positive",
                "detail": "Faculty bridge engineering, microbiology, and ecology.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter environmental consulting and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Specialization",
                "sentiment": "mixed",
                "detail": "Students must early define a coherent BEE focus area.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Biological and Environmental Engineering",
                "url": "https://www.bee.cornell.edu/bee/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-agricultural-engineering-phd": {
        "summary": (
            "Doctoral researchers describe Cornell BEE's Ph.D. as a research degree in environmental engineering, bioprocessing, and sustainable systems with land-grant impact; praise includes extension-connected research, with cautions about competitive funding and dissertation timelines typically spanning five or more years."
        ),
        "themes": [
            {
                "label": "Environmental engineering research",
                "sentiment": "positive",
                "detail": "Doctoral labs study water quality, bioenergy, and sustainability.",
            },
            {
                "label": "Land-grant impact",
                "sentiment": "positive",
                "detail": "Research connects to CALS extension and global food systems.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and environmental R&D leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Biological and Environmental Engineering",
                "url": "https://www.bee.cornell.edu/bee/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-applied-horticulture-and-horticultural-business-services-ms": {
        "summary": (
            "Graduate students describe Cornell CALS's M.S. in Applied Horticulture as a research and professional degree spanning plant science, greenhouse management, and horticultural business within one of the nation's oldest horticulture departments; praise includes access to Cornell AgriTech and extension networks, with cautions about self-funded tuition and career paths concentrated in agriculture and nursery industries."
        ),
        "themes": [
            {
                "label": "Plant science depth",
                "sentiment": "positive",
                "detail": "Training in physiology, breeding, and controlled-environment production.",
            },
            {
                "label": "Cornell AgriTech access",
                "sentiment": "positive",
                "detail": "Geneva campus resources connect research to commercial horticulture.",
            },
            {
                "label": "Extension network",
                "sentiment": "positive",
                "detail": "CALS extension ties support industry-facing applied projects.",
            },
            {
                "label": "Industry-focused careers",
                "sentiment": "mixed",
                "detail": "Graduates enter nursery, greenhouse, and agribusiness rather than tech.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Cornell SIPS — Horticulture graduate study",
                "url": "https://sips.cals.cornell.edu/graduate",
            },
            {
                "label": "Cornell CALS — School of Integrative Plant Science",
                "url": "https://sips.cals.cornell.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-applied-horticulture-and-horticultural-business-services-phd": {
        "summary": (
            "Doctoral students describe Cornell's Ph.D. in Applied Horticulture as a research-intensive degree in plant biology, breeding, and sustainable production within SIPS; praise centers on world-class greenhouses and faculty in viticulture and controlled-environment agriculture, with cautions about competitive funding, long time-to-degree, and academic placements oriented toward land-grant and research institutions."
        ),
        "themes": [
            {
                "label": "Horticultural research",
                "sentiment": "positive",
                "detail": "Doctoral work in breeding, physiology, and sustainable production systems.",
            },
            {
                "label": "World-class facilities",
                "sentiment": "positive",
                "detail": "Greenhouses and field stations support year-round plant research.",
            },
            {
                "label": "Faculty breadth",
                "sentiment": "positive",
                "detail": "Expertise spans viticulture, floriculture, and urban horticulture.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research in plant sciences typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell SIPS — Ph.D. programs",
                "url": "https://sips.cals.cornell.edu/graduate/phd-programs",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-architecture-and-related-services-other-ms": {
        "summary": (
            "Graduate students describe Cornell AAP's M.S. in Advanced Architectural Design and related post-professional master's tracks as research-oriented degrees for licensed architects pursuing academic or specialized practice paths; praise centers on faculty-led research studios and fabrication resources, with cautions about niche career outcomes, self-funded tuition, and a program scale smaller than the core M.Arch."
        ),
        "themes": [
            {
                "label": "Post-professional research",
                "sentiment": "positive",
                "detail": "For licensed architects pursuing advanced design research.",
            },
            {
                "label": "Faculty-led studios",
                "sentiment": "positive",
                "detail": "Small cohorts work closely with research-active faculty.",
            },
            {
                "label": "Fabrication resources",
                "sentiment": "positive",
                "detail": "Milstein Hall shops support experimental built work.",
            },
            {
                "label": "Niche career paths",
                "sentiment": "mixed",
                "detail": "Graduates target academic and specialized design roles more than general practice.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Post-professional master's students typically self-fund tuition.",
            },
        ],
        "sources": [
            {
                "label": "Cornell AAP — Advanced Architectural Design",
                "url": "https://aap.cornell.edu/academics/architecture/ms-aad",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-architecture-bs": {
        "summary": (
            "Students describe Cornell AAP's B.Arch-equivalent professional architecture undergraduate program as a studio-driven five-year degree with strong design-build culture and faculty active in practice; praise includes Milstein Hall fabrication resources and interdisciplinary AAP community, with cautions about relentless studio deadlines, sleep deprivation during reviews, and a workload that exceeds typical undergraduate pacing."
        ),
        "themes": [
            {
                "label": "Professional studio sequence",
                "sentiment": "positive",
                "detail": "Five-year curriculum centers on design studios from year one.",
            },
            {
                "label": "Design-build culture",
                "sentiment": "positive",
                "detail": "Students produce built projects using AAP fabrication shops.",
            },
            {
                "label": "Interdisciplinary AAP",
                "sentiment": "positive",
                "detail": "Architecture students collaborate with landscape and art peers.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Pin-ups and reviews create sustained late-night workloads.",
            },
            {
                "label": "Five-year commitment",
                "sentiment": "caution",
                "detail": "Professional degree requires one year beyond typical undergraduate timelines.",
            },
        ],
        "sources": [
            {
                "label": "Cornell AAP — Architecture undergraduate",
                "url": "https://aap.cornell.edu/academics/architecture/undergraduate",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-biological-biosystems-engineering-bs": {
        "summary": (
            "Students describe Cornell BEE's biosystems engineering undergraduate program as applied engineering for biological systems, water resources, and sustainable agriculture; praise includes land-grant CALS integration and research labs, with cautions about grade deflation, demanding coursework, and navigating both CALS and Engineering cultures."
        ),
        "themes": [
            {
                "label": "Biosystems engineering",
                "sentiment": "positive",
                "detail": "Applies engineering to agriculture, water, and biological processing.",
            },
            {
                "label": "CALS integration",
                "sentiment": "positive",
                "detail": "Land-grant ties connect coursework to food and environmental systems.",
            },
            {
                "label": "Research & extension",
                "sentiment": "positive",
                "detail": "Undergraduates join water-quality and bioprocessing labs.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Dual identity",
                "sentiment": "mixed",
                "detail": "Program spans CALS and Engineering — students navigate two cultures.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Biological and Environmental Engineering",
                "url": "https://www.bee.cornell.edu/bee/programs/undergraduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-biomedical-medical-engineering-bs": {
        "summary": (
            "Students describe Cornell BME's undergraduate program as training in biomechanics, medical devices, and computational biology within a collaborative engineering college; praise includes Weill Cornell Medicine ties and a strong pre-med pipeline, with cautions about grade deflation and intense competition among engineering-minded pre-med peers."
        ),
        "themes": [
            {
                "label": "Medical device design",
                "sentiment": "positive",
                "detail": "Core includes biomechanics, instrumentation, and device prototyping.",
            },
            {
                "label": "Weill Cornell ties",
                "sentiment": "positive",
                "detail": "Connections to Weill Cornell Medicine support clinical exposure.",
            },
            {
                "label": "Pre-med pipeline",
                "sentiment": "positive",
                "detail": "BME is a popular path for engineering-minded pre-med students.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Pre-med competition",
                "sentiment": "mixed",
                "detail": "Many peers pursue medical school — intense competition for research spots.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Biomedical Engineering",
                "url": "https://www.bme.cornell.edu/bme/programs/undergraduate-program",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-biomedical-medical-engineering-ms": {
        "summary": (
            "Graduate applicants describe Cornell BME's master's as a translational health-technology degree connecting engineering prototypes to clinical needs through Weill Cornell Medicine; praise includes med-tech research paths, with cautions about self-funded tuition and periodic travel to NYC for clinical collaborations."
        ),
        "themes": [
            {
                "label": "Translational health tech",
                "sentiment": "positive",
                "detail": "Graduate research links engineering prototypes to clinical needs.",
            },
            {
                "label": "Weill Cornell access",
                "sentiment": "positive",
                "detail": "NYC campus connections support medical-device projects.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter med-tech R&D and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "NYC travel",
                "sentiment": "mixed",
                "detail": "Some projects require periodic travel to Weill Cornell in NYC.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Biomedical Engineering",
                "url": "https://www.bme.cornell.edu/bme/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-biomedical-medical-engineering-phd": {
        "summary": (
            "Doctoral students describe Cornell BME's Ph.D. as a research degree in medical devices, tissue engineering, and computational biomedicine; praise includes leading imaging and biomaterials labs, with cautions about competitive admission and long dissertation timelines toward faculty or med-tech R&D roles."
        ),
        "themes": [
            {
                "label": "Medical device research",
                "sentiment": "positive",
                "detail": "Doctoral labs lead work in imaging, implants, and diagnostics.",
            },
            {
                "label": "Tissue engineering",
                "sentiment": "positive",
                "detail": "Faculty groups study biomaterials and regenerative medicine.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and med-tech R&D leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Biomedical Engineering",
                "url": "https://www.bme.cornell.edu/bme/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-biomedical-sciences-bs": {
        "summary": (
            "Students describe Cornell CALS Biological Sciences as a research-rich life-sciences major spanning molecular biology, ecology, and human health within a land-grant Ivy; praise includes access to world-class faculty and pre-med/pre-grad pipelines, with cautions about competitive grading in gateway courses and the need to specialize early among many subfields."
        ),
        "themes": [
            {
                "label": "Life-sciences breadth",
                "sentiment": "positive",
                "detail": "Curriculum spans molecular, organismal, and ecological biology.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "CALS undergraduates join faculty labs across the Ithaca campus.",
            },
            {
                "label": "Pre-med & grad pipeline",
                "sentiment": "positive",
                "detail": "Strong preparation for medical school and biology Ph.D. programs.",
            },
            {
                "label": "Gateway grading",
                "sentiment": "caution",
                "detail": "Introductory biology and chemistry sequences are grade-deflated.",
            },
            {
                "label": "Specialization choice",
                "sentiment": "mixed",
                "detail": "Wide subfield menu requires early focus to build depth.",
            },
        ],
        "sources": [
            {
                "label": "Cornell CALS — Biological Sciences",
                "url": "https://cals.cornell.edu/biological-sciences",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-business-administration-management-and-operations-phd": {
        "summary": (
            "Doctoral students describe Cornell Johnson's Ph.D. in Management (operations, strategy, and organizational behavior tracks) as a research degree for aspiring business-school faculty; praise centers on faculty mentorship in operations research and behavioral science, with cautions about competitive funding, long timelines, and academic placements concentrated in research universities."
        ),
        "themes": [
            {
                "label": "Operations & strategy research",
                "sentiment": "positive",
                "detail": "Doctoral tracks span OR, strategy, OB, and information systems.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Close advising from research-active Johnson faculty.",
            },
            {
                "label": "Business-school placement",
                "sentiment": "positive",
                "detail": "Graduates target tenure-track positions at research universities.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track business faculty positions are limited nationally.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Johnson — Ph.D. program",
                "url": "https://www.johnson.cornell.edu/programs/phd-program/",
            },
            {
                "label": "Poets&Quants — Cornell Johnson",
                "url": "https://poetsandquants.com/schools/cornell-johnson-graduate-school-of-management/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-business-administration-ms": {
        "summary": (
            "Applicants and Poets&Quants guides describe Cornell Johnson's one-year M.S. in Business Administration as a STEM-designated, accelerated master's for career switchers and early professionals — distinct from the two-year MBA with its own admissions and cohort; praise centers on Johnson's finance and consulting recruiting and the Ivy credential, with cautions about a compressed timeline, limited internship placement versus the MBA, and a smaller brand footprint than M7 two-year programs."
        ),
        "themes": [
            {
                "label": "STEM-designated MS",
                "sentiment": "positive",
                "detail": "One-year master's with analytics and business core for career acceleration.",
            },
            {
                "label": "Johnson recruiting",
                "sentiment": "positive",
                "detail": "Access to Johnson career services and Cornell's finance/consulting network.",
            },
            {
                "label": "Career-switcher fit",
                "sentiment": "positive",
                "detail": "Targets professionals pivoting into business roles within 12 months.",
            },
            {
                "label": "Compressed timeline",
                "sentiment": "caution",
                "detail": "One-year format leaves less room for internships than the two-year MBA.",
            },
            {
                "label": "Brand vs M7 MBA",
                "sentiment": "mixed",
                "detail": "Johnson MS brand is strong but trails elite two-year MBA peers nationally.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Johnson — Master's programs",
                "url": "https://www.johnson.cornell.edu/programs/masters-programs/",
            },
            {
                "label": "Poets&Quants — Cornell Johnson",
                "url": "https://poetsandquants.com/schools/cornell-johnson-graduate-school-of-management/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-chemical-engineering-bs": {
        "summary": (
            "Students describe Cornell CBE's chemical engineering major as rigorous training in transport, thermodynamics, and process design with strong placement into pharma, energy, and materials; praise includes catalysis and biotechnology lab access, with cautions about grade deflation and demanding transport and thermodynamics sequences."
        ),
        "themes": [
            {
                "label": "Process design core",
                "sentiment": "positive",
                "detail": "Training in transport phenomena, thermodynamics, and reactor design.",
            },
            {
                "label": "Pharma & energy placement",
                "sentiment": "positive",
                "detail": "Graduates enter chemical, pharma, and energy industries.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join catalysis and biotechnology labs.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "caution",
                "detail": "Core sequences in transport and thermodynamics are consistently demanding.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Chemical Engineering",
                "url": "https://www.cbe.cornell.edu/cbe/programs/undergraduate-program",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-chemical-engineering-ms": {
        "summary": (
            "Graduate students describe Cornell CBE's master's as research and coursework in catalysis, biotechnology, and materials processing; praise includes nationally recognized energy and materials faculty, with cautions about self-funded tuition and early specialization within CBE research areas."
        ),
        "themes": [
            {
                "label": "Catalysis & biotech",
                "sentiment": "positive",
                "detail": "Graduate research spans catalysis, polymers, and bioprocessing.",
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "CBE faculty lead nationally recognized energy and materials labs.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter chemical R&D and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Specialization",
                "sentiment": "mixed",
                "detail": "Students must early define a coherent CBE research focus.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Chemical Engineering",
                "url": "https://www.cbe.cornell.edu/cbe/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-chemical-engineering-phd": {
        "summary": (
            "Doctoral researchers describe Cornell CBE's Ph.D. as a research degree in energy, biotechnology, and advanced materials; praise includes leading battery and catalysis labs, with cautions about competitive funding and five-plus-year dissertation paths."
        ),
        "themes": [
            {
                "label": "Energy & materials research",
                "sentiment": "positive",
                "detail": "Doctoral labs lead work in batteries, catalysis, and polymers.",
            },
            {
                "label": "Biotechnology depth",
                "sentiment": "positive",
                "detail": "Faculty groups study bioprocessing and synthetic biology.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and industrial R&D leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Chemical Engineering",
                "url": "https://www.cbe.cornell.edu/cbe/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-civil-engineering-bs": {
        "summary": (
            "Students describe Cornell CEE's civil engineering major as training in structures, transportation, and environmental systems within a nationally ranked department; praise includes smart-cities and structural-health research access, with cautions about grade deflation and outdoor fieldwork through Ithaca's cold seasons."
        ),
        "themes": [
            {
                "label": "Infrastructure focus",
                "sentiment": "positive",
                "detail": "Core spans structures, geotechnical, transportation, and water systems.",
            },
            {
                "label": "Sustainability emphasis",
                "sentiment": "positive",
                "detail": "Coursework addresses resilient infrastructure and environmental design.",
            },
            {
                "label": "Project teams & research",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in smart cities and structural health monitoring.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Field work demands",
                "sentiment": "mixed",
                "detail": "Some courses require outdoor site visits through Ithaca's cold seasons.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Civil Engineering",
                "url": "https://www.cee.cornell.edu/cee/programs/undergraduate-program",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-civil-engineering-ms": {
        "summary": (
            "Graduate applicants describe Cornell CEE's master's as spanning structural, geotechnical, transportation, and environmental engineering; praise includes infrastructure-resilience research, with cautions about self-funded tuition and graduates targeting coastal markets more than Ithaca."
        ),
        "themes": [
            {
                "label": "Multi-area CEE",
                "sentiment": "positive",
                "detail": "Graduate tracks cover structures, transportation, and environmental systems.",
            },
            {
                "label": "Smart cities research",
                "sentiment": "positive",
                "detail": "Faculty labs study infrastructure sensing and urban resilience.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter consulting, public sector, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Consulting geography",
                "sentiment": "mixed",
                "detail": "Many graduates target NYC and coastal markets rather than Ithaca.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Civil Engineering",
                "url": "https://www.cee.cornell.edu/cee/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-civil-engineering-phd": {
        "summary": (
            "Doctoral students describe Cornell CEE's Ph.D. as a research degree in infrastructure resilience, sustainability, and smart cities; praise includes earthquake-engineering and sensing labs, with cautions about competitive admission and long dissertation timelines."
        ),
        "themes": [
            {
                "label": "Infrastructure resilience",
                "sentiment": "positive",
                "detail": "Doctoral research spans earthquake engineering and climate adaptation.",
            },
            {
                "label": "Smart cities",
                "sentiment": "positive",
                "detail": "Faculty lead sensing and data-driven infrastructure research.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and public-sector research leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Civil Engineering",
                "url": "https://www.cee.cornell.edu/cee/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-computer-science-phd": {
        "summary": (
            "Doctoral students and academic guides describe Cornell's Ph.D. in Computer Science as a top-tier research doctorate within the Bowers College, with deep faculty mentorship across AI, systems, theory, and HCI; common cautions are extreme selectivity, a long time-to-degree, and intense publication expectations within a collaborative but demanding research culture."
        ),
        "themes": [
            {
                "label": "Elite CS research",
                "sentiment": "positive",
                "detail": "Doctoral students join leading labs across sixteen official CS areas.",
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Pioneering groups in AI, programming languages, and systems anchor the program.",
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates place into faculty roles, industry R&D labs, and startups.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with a small incoming cohort.",
            },
            {
                "label": "Research intensity",
                "sentiment": "caution",
                "detail": "The dissertation path demands sustained, publication-oriented work.",
            },
        ],
        "sources": [
            {
                "label": "Cornell CS — Ph.D. program",
                "url": "https://www.cs.cornell.edu/phd",
            },
            {
                "label": "U.S. News — Best Computer Science Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-economics-ms": {
        "summary": (
            "Graduate applicants describe Cornell Arts & Sciences' M.A. in Economics as a rigorous quantitative master's preparing students for doctoral study or analytics-heavy industry roles; students praise the micro/metrics core and faculty access, with cautions about self-funded tuition, limited terminal-master's recruiting, and a program oriented toward Ph.D. prep rather than standalone industry placement."
        ),
        "themes": [
            {
                "label": "Quantitative core",
                "sentiment": "positive",
                "detail": "Microeconomics, macroeconomics, and econometrics form a demanding foundation.",
            },
            {
                "label": "Ph.D. preparation",
                "sentiment": "positive",
                "detail": "Strong pathway into Cornell and peer economics doctoral programs.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Graduate courses taught by research-active economics faculty.",
            },
            {
                "label": "Self-funded MA",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Program is oriented toward doctoral study more than direct industry hiring.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Economics — Graduate program",
                "url": "https://economics.cornell.edu/graduate",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-economics-phd": {
        "summary": (
            "Doctoral students describe Cornell's Ph.D. in Economics as a research-intensive degree with strengths in labor, industrial organization, and econometrics within Arts & Sciences; praise centers on faculty mentorship and collaborative grad culture, with cautions about competitive funding, five-plus-year timelines, and academic job-market pressure."
        ),
        "themes": [
            {
                "label": "Labor & IO strength",
                "sentiment": "positive",
                "detail": "Faculty lead nationally recognized work in labor and industrial organization.",
            },
            {
                "label": "Econometrics training",
                "sentiment": "positive",
                "detail": "Core coursework builds rigorous empirical research skills.",
            },
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Graduate students describe a supportive, seminar-driven community.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track economics positions are limited and highly competitive.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Economics — Ph.D. program",
                "url": "https://economics.cornell.edu/phd",
            },
            {
                "label": "U.S. News — Best Economics Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-humanities-schools/economics-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-electrical-computer-eng-bs": {
        "summary": (
            "Students and Cornell Engineering guides describe the electrical and computer engineering major as a rigorous program spanning circuits, signals, and computing systems within a top-ranked ECE department; praise centers on research access in robotics and embedded systems, with cautions about grade deflation, fast-paced core coursework, and large lower-division sections in a popular major."
        ),
        "themes": [
            {
                "label": "Circuits & systems depth",
                "sentiment": "positive",
                "detail": "Core spans analog, digital, and computer engineering foundations.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join faculty labs in sensing, VLSI, and wireless systems.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Graduates enter hardware, embedded systems, and software roles.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Core pace",
                "sentiment": "caution",
                "detail": "Required ECE sequences are consistently described as demanding.",
            },
        ],
        "sources": [
            {
                "label": "Cornell ECE — Undergraduate programs",
                "url": "https://www.ece.cornell.edu/ece/programs/undergraduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-electrical-electronics-and-communications-engineering-phd": {
        "summary": (
            "Doctoral students describe Cornell ECE's Ph.D. as a top-ranked research degree in robotics, VLSI, and wireless systems; praise includes pioneering autonomous-systems and chip-design labs, with cautions about extreme selectivity and sustained publication-oriented dissertation work."
        ),
        "themes": [
            {
                "label": "Robotics & VLSI research",
                "sentiment": "positive",
                "detail": "Doctoral labs lead work in autonomous systems and chip design.",
            },
            {
                "label": "Wireless & sensing",
                "sentiment": "positive",
                "detail": "Faculty groups pioneer RF, radar, and embedded sensing.",
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates place into faculty roles, industry R&D labs, and startups.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with a small incoming cohort.",
            },
            {
                "label": "Research intensity",
                "sentiment": "caution",
                "detail": "The dissertation path demands sustained, publication-oriented work.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Electrical and Computer Engineering",
                "url": "https://www.ece.cornell.edu/ece/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-emha-online": {
        "summary": (
            "Healthcare leaders describe Cornell Brooks's Executive MHA (hybrid) as a mid-career credential for hospital and health-system administrators, combining policy, finance, and leadership through a mix of online coursework and residential sessions; students value Cornell's health-policy faculty and the Sloan program's practitioner focus, with cautions about travel for residencies and a niche cohort compared with full-time MHA programs."
        ),
        "themes": [
            {
                "label": "Healthcare leadership",
                "sentiment": "positive",
                "detail": "Targets executives managing hospitals and health systems.",
            },
            {
                "label": "Hybrid format",
                "sentiment": "positive",
                "detail": "Blends online coursework with periodic residential sessions.",
            },
            {
                "label": "Policy & finance core",
                "sentiment": "positive",
                "detail": "Brooks School faculty cover health economics and administration.",
            },
            {
                "label": "Travel commitment",
                "sentiment": "caution",
                "detail": "Residential sessions require schedule and travel sacrifice.",
            },
            {
                "label": "Career-switch limits",
                "sentiment": "mixed",
                "detail": "Best suited to advancement within healthcare versus entry-level pivots.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Brooks — Executive MHA",
                "url": "https://publicpolicy.cornell.edu/masters/sloan/emha/",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-general-bs": {
        "summary": (
            "Students and Cornell Engineering guides describe the Engineering, General undergraduate program as a common first-year curriculum that lets students explore majors before committing to a specific department; praise includes Cornell's Ivy League engineering reputation and project-team culture, with cautions about grade deflation, demanding core coursework, and heavy workload during project seasons."
        ),
        "themes": [
            {
                "label": "Major exploration year",
                "sentiment": "positive",
                "detail": "Common curriculum lets first-years sample departments before affiliating.",
            },
            {
                "label": "Project teams",
                "sentiment": "positive",
                "detail": "Roughly half of engineering undergraduates join competition project teams.",
            },
            {
                "label": "Ivy engineering reputation",
                "sentiment": "positive",
                "detail": "Cornell Engineering ranks among top national undergraduate programs.",
            },
            {
                "label": "Affiliation pressure",
                "sentiment": "mixed",
                "detail": "Students must select a major by sophomore year with competitive internal transfers.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Engineering, General",
                "url": "https://www.engineering.cornell.edu/students/undergraduate-students/curriculum/affiliation",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-management-meng-online": {
        "summary": (
            "Working professionals describe Cornell's online/hybrid M.Eng. in Engineering Management through eCornell as a flexible credential blending technical leadership, finance, and project management for engineers advancing into management; praise centers on Cornell's brand and asynchronous flexibility, with cautions about limited peer networking versus residential programs and premium online tuition."
        ),
        "themes": [
            {
                "label": "Leadership for engineers",
                "sentiment": "positive",
                "detail": "Combines technical depth with management and finance coursework.",
            },
            {
                "label": "Online flexibility",
                "sentiment": "positive",
                "detail": "Asynchronous format suits working professionals.",
            },
            {
                "label": "Cornell credential",
                "sentiment": "positive",
                "detail": "Engineering management degree from an Ivy League engineering college.",
            },
            {
                "label": "Networking limits",
                "sentiment": "mixed",
                "detail": "Online cohort offers less in-person peer interaction than residential M.Eng.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Professional online tuition is self-funded at premium rates.",
            },
        ],
        "sources": [
            {
                "label": "eCornell — Engineering Management",
                "url": "https://ecornell.cornell.edu/certificates/engineering/",
            },
            {
                "label": "Cornell Engineering — Professional education",
                "url": "https://www.engineering.cornell.edu/students/professional-education",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-mechanics-ms": {
        "summary": (
            "Graduate students describe Cornell TAM's master's as training in solid mechanics, dynamics, and computational engineering for research and industry roles; praise includes cross-department ties to MAE and CEE, with cautions about self-funded tuition and a specialized mechanics job market."
        ),
        "themes": [
            {
                "label": "Solid mechanics depth",
                "sentiment": "positive",
                "detail": "Graduate training in continuum mechanics, dynamics, and computation.",
            },
            {
                "label": "Cross-department ties",
                "sentiment": "positive",
                "detail": "TAM connects MAE, CEE, and materials science applications.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter simulation R&D and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Niche field",
                "sentiment": "mixed",
                "detail": "Mechanics roles are specialized compared with general mechanical engineering.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Theoretical and Applied Mechanics",
                "url": "https://www.tam.cornell.edu/tam/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-mechanics-phd": {
        "summary": (
            "Doctoral researchers describe Cornell TAM's Ph.D. as a research degree in continuum mechanics, dynamics, and computational methods; praise includes numerical-simulation faculty leadership, with cautions about competitive funding and long dissertation timelines."
        ),
        "themes": [
            {
                "label": "Continuum mechanics",
                "sentiment": "positive",
                "detail": "Doctoral research spans solids, fluids, and multiscale modeling.",
            },
            {
                "label": "Computational methods",
                "sentiment": "positive",
                "detail": "Faculty develop numerical methods for engineering simulation.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and simulation R&D leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Theoretical and Applied Mechanics",
                "url": "https://www.tam.cornell.edu/tam/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-other-bs": {
        "summary": (
            "Students and Cornell Engineering guides describe the Engineering, Other undergraduate program as an interdisciplinary pathway offering dual-degree and custom engineering combinations beyond standard departmental majors; praise includes Cornell's Ivy League engineering reputation and project-team culture, with cautions about grade deflation, demanding core coursework, and heavy workload during project seasons."
        ),
        "themes": [
            {
                "label": "Interdisciplinary pathways",
                "sentiment": "positive",
                "detail": "Dual degrees and custom combinations span engineering and other colleges.",
            },
            {
                "label": "Faculty flexibility",
                "sentiment": "positive",
                "detail": "Advisors help craft coherent programs across departments.",
            },
            {
                "label": "Project teams",
                "sentiment": "positive",
                "detail": "Interdisciplinary engineers often join multi-disciplinary project teams.",
            },
            {
                "label": "Self-designed coherence",
                "sentiment": "caution",
                "detail": "Students must proactively define a focus — less structure than standard majors.",
            },
            {
                "label": "Registration complexity",
                "sentiment": "mixed",
                "detail": "Cross-college schedules require careful course planning each semester.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Engineering, Other",
                "url": "https://www.engineering.cornell.edu/students/undergraduate-students/curriculum",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-physics-bs": {
        "summary": (
            "Students describe Cornell AEP's engineering physics major as a blend of rigorous physics and applied engineering for aerospace, energy, and advanced materials careers; praise includes plasma and nanotech lab access, with cautions about grade deflation and demanding advanced math and physics prerequisites."
        ),
        "themes": [
            {
                "label": "Physics-engineering blend",
                "sentiment": "positive",
                "detail": "Curriculum combines rigorous physics with applied engineering design.",
            },
            {
                "label": "Aerospace & energy paths",
                "sentiment": "positive",
                "detail": "Graduates enter aerospace, plasma physics, and energy sectors.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join plasma, nanotech, and materials labs.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Math intensity",
                "sentiment": "caution",
                "detail": "Advanced physics and math prerequisites are consistently demanding.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Applied and Engineering Physics",
                "url": "https://www.aep.cornell.edu/aep/programs/undergraduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-physics-ms": {
        "summary": (
            "Graduate students describe Cornell AEP's master's as research in plasma physics, nanotechnology, and applied physics; praise includes cross-disciplinary faculty collaborations, with cautions about self-funded tuition and careers concentrated in energy and research labs."
        ),
        "themes": [
            {
                "label": "Plasma & nanotech",
                "sentiment": "positive",
                "detail": "Graduate research spans fusion, nanofabrication, and applied physics.",
            },
            {
                "label": "Cross-disciplinary labs",
                "sentiment": "positive",
                "detail": "AEP faculty collaborate across physics, MAE, and materials science.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter energy R&D and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Specialized careers",
                "sentiment": "mixed",
                "detail": "Roles concentrate in energy and research labs rather than general industry.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Applied and Engineering Physics",
                "url": "https://www.aep.cornell.edu/aep/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-engineering-physics-phd": {
        "summary": (
            "Doctoral students describe Cornell AEP's Ph.D. as a research degree in condensed matter, plasma, and applied physics with national-lab ties; praise includes DOE and NSF collaborations, with cautions about competitive admission and five-plus-year dissertation paths."
        ),
        "themes": [
            {
                "label": "Plasma & condensed matter",
                "sentiment": "positive",
                "detail": "Doctoral labs lead fusion, nanoscale, and materials physics.",
            },
            {
                "label": "National lab ties",
                "sentiment": "positive",
                "detail": "Faculty collaborations connect students to DOE and NSF facilities.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and national-lab research leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Applied and Engineering Physics",
                "url": "https://www.aep.cornell.edu/aep/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-environmental-environmental-health-engineering-bs": {
        "summary": (
            "Students describe Cornell CEE's environmental engineering major as training in water quality, air pollution, and sustainable infrastructure; praise includes climate-resilience coursework and combined lab and field study, with cautions about grade deflation and outdoor fieldwork through Ithaca winters."
        ),
        "themes": [
            {
                "label": "Water & air systems",
                "sentiment": "positive",
                "detail": "Training in water treatment, air quality, and environmental remediation.",
            },
            {
                "label": "Sustainability focus",
                "sentiment": "positive",
                "detail": "Coursework addresses climate resilience and green infrastructure.",
            },
            {
                "label": "Field & lab work",
                "sentiment": "positive",
                "detail": "Students combine lab analysis with watershed and site field studies.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Field seasons",
                "sentiment": "mixed",
                "detail": "Outdoor fieldwork continues through Ithaca's cold months.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Environmental Engineering",
                "url": "https://www.cee.cornell.edu/cee/programs/undergraduate-program",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-film-video-and-photographic-arts-bs": {
        "summary": (
            "Students describe Cornell AAP's B.F.A. in Film, Video, and Photographic Arts as a production-focused studio major within one of the nation's few Ivy film programs; praise centers on small cohorts, faculty filmmakers, and access to production equipment, with cautions about limited Hollywood pipeline compared with LA film schools, demanding production schedules, and a niche career path requiring portfolio hustle."
        ),
        "themes": [
            {
                "label": "Production-focused B.F.A.",
                "sentiment": "positive",
                "detail": "Studio curriculum emphasizes filmmaking, video art, and photography.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Intimate class sizes enable close faculty mentorship on projects.",
            },
            {
                "label": "Equipment & facilities",
                "sentiment": "positive",
                "detail": "AAP provides cameras, editing suites, and exhibition opportunities.",
            },
            {
                "label": "Industry geography",
                "sentiment": "mixed",
                "detail": "Ithaca lacks LA/NYC industry density — graduates relocate for film careers.",
            },
            {
                "label": "Portfolio pressure",
                "sentiment": "caution",
                "detail": "Success depends on self-directed production work beyond coursework.",
            },
        ],
        "sources": [
            {
                "label": "Cornell AAP — Art undergraduate",
                "url": "https://aap.cornell.edu/academics/art/undergraduate",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-hospitality-administration-management-ms": {
        "summary": (
            "Graduate applicants describe Cornell Nolan School's Master of Management in Hospitality (MMH) as the premier graduate hospitality degree with deep industry ties and a property-consulting practicum; students praise the hotel-school network and Cornell's brand in hospitality, with cautions about a specialized industry track, tuition cost, and career paths concentrated in hotels, restaurants, and real estate rather than general business."
        ),
        "themes": [
            {
                "label": "Premier hospitality MS",
                "sentiment": "positive",
                "detail": "Nolan School's MMH is widely regarded as the leading hospitality graduate degree.",
            },
            {
                "label": "Industry network",
                "sentiment": "positive",
                "detail": "Strong alumni ties to hotel chains, restaurants, and hospitality investors.",
            },
            {
                "label": "Consulting practicum",
                "sentiment": "positive",
                "detail": "Property-consulting projects provide real-world hospitality experience.",
            },
            {
                "label": "Specialized industry",
                "sentiment": "mixed",
                "detail": "Careers concentrate in hospitality and real estate rather than general MBA paths.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Professional master's tuition at an Ivy hotel school is a significant investment.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Nolan — MMH program",
                "url": "https://sha.cornell.edu/admissions-programs/graduate-programs/master-of-management-in-hospitality/",
            },
            {
                "label": "Poets&Quants — Cornell School of Hotel Administration",
                "url": "https://poetsandquants.com/schools/cornell-university-school-of-hotel-administration/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-hospitality-administration-management-phd": {
        "summary": (
            "Doctoral students describe Cornell Nolan School's Ph.D. in Hospitality Administration as the leading research doctorate in hotel and service-industry management worldwide; praise centers on faculty who define the field and unparalleled industry data access, with cautions about a very small cohort, academic job market concentration in hospitality schools, and long dissertation timelines."
        ),
        "themes": [
            {
                "label": "Field-defining research",
                "sentiment": "positive",
                "detail": "Nolan faculty pioneered hospitality management as an academic discipline.",
            },
            {
                "label": "Industry data access",
                "sentiment": "positive",
                "detail": "Center for Hospitality Research provides proprietary industry datasets.",
            },
            {
                "label": "Global network",
                "sentiment": "positive",
                "detail": "Graduates join hospitality faculty positions worldwide.",
            },
            {
                "label": "Small cohort",
                "sentiment": "caution",
                "detail": "Doctoral program admits a very small number of students each year.",
            },
            {
                "label": "Niche academic market",
                "sentiment": "mixed",
                "detail": "Placements concentrate in hospitality and tourism faculty roles.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Nolan — Ph.D. program",
                "url": "https://sha.cornell.edu/admissions-programs/graduate-programs/phd/",
            },
            {
                "label": "Poets&Quants — Cornell School of Hotel Administration",
                "url": "https://poetsandquants.com/schools/cornell-university-school-of-hotel-administration/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-landscape-architecture-bs": {
        "summary": (
            "Students describe Cornell AAP's B.L.A. in Landscape Architecture as a design program integrating ecology, urbanism, and site design within a nationally recognized department; praise centers on studio culture, plant and ecology coursework, and faculty-led community projects, with cautions about demanding studio schedules, weather-dependent site work in Ithaca, and a smaller national brand than coastal landscape programs."
        ),
        "themes": [
            {
                "label": "Ecology + design integration",
                "sentiment": "positive",
                "detail": "Curriculum blends ecological science with landscape design studios.",
            },
            {
                "label": "Community projects",
                "sentiment": "positive",
                "detail": "Studios engage real sites and stakeholders across Upstate New York.",
            },
            {
                "label": "AAP resources",
                "sentiment": "positive",
                "detail": "Shared fabrication and plant collections support design work.",
            },
            {
                "label": "Studio intensity",
                "sentiment": "caution",
                "detail": "Design deadlines mirror architecture's demanding review culture.",
            },
            {
                "label": "Weather & site work",
                "sentiment": "mixed",
                "detail": "Field studios require outdoor work through Ithaca's cold seasons.",
            },
        ],
        "sources": [
            {
                "label": "Cornell AAP — Landscape Architecture B.L.A.",
                "url": "https://aap.cornell.edu/academics/landscape-architecture/undergraduate",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-landscape-architecture-ms": {
        "summary": (
            "Graduate applicants describe Cornell AAP's M.L.A. as a professional landscape architecture degree for career changers and designers seeking accredited licensure preparation; students praise the three-year studio sequence and faculty research in urban ecology, with cautions about intensive studio pacing, self-funded tuition for some tracks, and limited local landscape hiring in Ithaca."
        ),
        "themes": [
            {
                "label": "Accredited MLA path",
                "sentiment": "positive",
                "detail": "Professional degree prepares graduates for landscape licensure.",
            },
            {
                "label": "Urban ecology research",
                "sentiment": "positive",
                "detail": "Faculty work spans resilient cities, green infrastructure, and ecology.",
            },
            {
                "label": "Studio sequence",
                "sentiment": "positive",
                "detail": "Graduate studios build portfolio-ready community and regional projects.",
            },
            {
                "label": "Self-funded options",
                "sentiment": "caution",
                "detail": "Some MLA tracks require self-funded tuition without assistantships.",
            },
            {
                "label": "Local hiring pool",
                "sentiment": "mixed",
                "detail": "National design firms recruit graduates; Ithaca local market is small.",
            },
        ],
        "sources": [
            {
                "label": "Cornell AAP — Landscape Architecture M.L.A.",
                "url": "https://aap.cornell.edu/academics/landscape-architecture/graduate",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-law-phd": {
        "summary": (
            "Doctoral students describe Cornell Law's Ph.D. in Law as an interdisciplinary research degree for aspiring legal academics, combining jurisprudence with empirical and comparative methods; praise centers on faculty mentorship and the law school's improving national rank, with cautions about a tight academic job market, long dissertation timelines, and a cohort far smaller than the J.D. program."
        ),
        "themes": [
            {
                "label": "Legal academic training",
                "sentiment": "positive",
                "detail": "Prepares graduates for tenure-track law faculty positions.",
            },
            {
                "label": "Interdisciplinary methods",
                "sentiment": "positive",
                "detail": "Faculty support empirical, comparative, and doctrinal scholarship.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small cohorts receive close advising from research-active professors.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track law faculty positions are limited and competitive.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation completion typically spans four or more years beyond coursework.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Law — Graduate legal studies",
                "url": "https://www.lawschool.cornell.edu/admissions/graduate-legal-studies/",
            },
            {
                "label": "U.S. News — Cornell Law School",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/cornell-university-01127",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-march": {
        "summary": (
            "Architecture applicants and guides describe Cornell AAP's three-year M.Arch as a studio-intensive professional degree with a strong design-build culture and faculty active in practice and research; students praise the Ithaca campus's fabrication resources and interdisciplinary ties to landscape and planning, with cautions about demanding studio deadlines, limited sleep during reviews, and a smaller national brand than coastal architecture schools."
        ),
        "themes": [
            {
                "label": "Studio-intensive design",
                "sentiment": "positive",
                "detail": "Core curriculum centers on design studios with faculty practitioners.",
            },
            {
                "label": "Fabrication & build culture",
                "sentiment": "positive",
                "detail": "Milstein Hall and shop resources support design-build projects.",
            },
            {
                "label": "Interdisciplinary AAP",
                "sentiment": "positive",
                "detail": "Connections to landscape architecture, planning, and art within AAP.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Design reviews and pin-ups create sustained late-night workloads.",
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": "Cornell architecture is respected but less coastal than peer Ivies.",
            },
        ],
        "sources": [
            {
                "label": "Cornell AAP — M.Arch program",
                "url": "https://aap.cornell.edu/academics/architecture/march",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-materials-engineering-bs": {
        "summary": (
            "Students describe Cornell MSE's materials science major as training in structure, processing, and properties for energy, electronics, and manufacturing; praise includes CCMR characterization facilities, with cautions about grade deflation and sustained hands-on lab hours."
        ),
        "themes": [
            {
                "label": "Structure-property focus",
                "sentiment": "positive",
                "detail": "Core covers thermodynamics, characterization, and materials processing.",
            },
            {
                "label": "Energy & electronics",
                "sentiment": "positive",
                "detail": "Research paths span batteries, semiconductors, and advanced manufacturing.",
            },
            {
                "label": "Shared facilities",
                "sentiment": "positive",
                "detail": "CCMR and shared characterization labs support undergraduate research.",
            },
            {
                "label": "Grade deflation",
                "sentiment": "caution",
                "detail": "Engineering coursework is grade-deflated — a known Cornell trait.",
            },
            {
                "label": "Lab intensity",
                "sentiment": "caution",
                "detail": "Characterization and processing labs require sustained hands-on hours.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Materials Science and Engineering",
                "url": "https://www.mse.cornell.edu/mse/programs/undergraduate-program",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-materials-engineering-ms": {
        "summary": (
            "Graduate students describe Cornell MSE's master's as research in energy materials, semiconductors, and computational materials science; praise includes shared CCMR facilities, with cautions about self-funded tuition and early materials-focus specialization."
        ),
        "themes": [
            {
                "label": "Energy materials",
                "sentiment": "positive",
                "detail": "Graduate research spans batteries, photovoltaics, and catalysis.",
            },
            {
                "label": "CCMR resources",
                "sentiment": "positive",
                "detail": "Cornell Center for Materials Research supports shared facilities.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter materials R&D and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Specialization",
                "sentiment": "mixed",
                "detail": "Students must early define a coherent materials focus area.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Materials Science and Engineering",
                "url": "https://www.mse.cornell.edu/mse/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-materials-engineering-phd": {
        "summary": (
            "Doctoral researchers describe Cornell MSE's Ph.D. as a research degree in nanomaterials, energy storage, and advanced manufacturing; praise includes leading battery and nanofabrication labs, with cautions about competitive funding and long dissertation timelines."
        ),
        "themes": [
            {
                "label": "Nanomaterials research",
                "sentiment": "positive",
                "detail": "Doctoral labs lead work in 2D materials and nanofabrication.",
            },
            {
                "label": "Energy storage",
                "sentiment": "positive",
                "detail": "Faculty groups pioneer battery and fuel-cell materials.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and industrial R&D leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Materials Science and Engineering",
                "url": "https://www.mse.cornell.edu/mse/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-mechanical-engineering-ms": {
        "summary": (
            "Graduate applicants describe Cornell MAE's master's as spanning thermal sciences, robotics, and design with strong industry and research paths; praise includes MAE shop and prototyping resources, with cautions about self-funded tuition and early MAE specialization."
        ),
        "themes": [
            {
                "label": "Robotics & thermal sciences",
                "sentiment": "positive",
                "detail": "Graduate tracks cover robotics, fluids, and heat transfer.",
            },
            {
                "label": "Design & prototyping",
                "sentiment": "positive",
                "detail": "Students access MAE shops and rapid-prototyping resources.",
            },
            {
                "label": "Industry & research paths",
                "sentiment": "positive",
                "detail": "Graduates enter automotive, aerospace, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund tuition.",
            },
            {
                "label": "Specialization",
                "sentiment": "mixed",
                "detail": "Students must early define a coherent MAE focus area.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Mechanical Engineering",
                "url": "https://www.mae.cornell.edu/mae/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-mechanical-engineering-phd": {
        "summary": (
            "Doctoral students describe Cornell MAE's Ph.D. as a research degree in fluid dynamics, robotics, and advanced manufacturing; praise includes autonomous-systems and turbulence labs, with cautions about competitive admission and five-plus-year dissertation work."
        ),
        "themes": [
            {
                "label": "Fluid dynamics & robotics",
                "sentiment": "positive",
                "detail": "Doctoral labs lead autonomous systems and turbulence research.",
            },
            {
                "label": "Advanced manufacturing",
                "sentiment": "positive",
                "detail": "Faculty groups study additive manufacturing and smart materials.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and industrial R&D leadership.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Mechanical Engineering",
                "url": "https://www.mae.cornell.edu/mae/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-meng-ms": {
        "summary": (
            "Applicants describe Cornell's Master of Engineering (M.Eng.) as a professional, project-driven graduate degree across engineering fields — emphasizing industry-ready design work rather than thesis research; students value the one-year professional format and Cornell's engineering reputation, with cautions about self-funded tuition, intensive project deadlines, and less research funding than Ph.D. paths."
        ),
        "themes": [
            {
                "label": "Professional project focus",
                "sentiment": "positive",
                "detail": "Degree emphasizes applied design projects over thesis research.",
            },
            {
                "label": "One-year format",
                "sentiment": "positive",
                "detail": "Structured for industry entry within roughly 12 months of coursework.",
            },
            {
                "label": "Engineering breadth",
                "sentiment": "positive",
                "detail": "Available across multiple Cornell Engineering departments.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "M.Eng. is a professional degree without standard research funding.",
            },
            {
                "label": "Project intensity",
                "sentiment": "caution",
                "detail": "Year-long design deliverables require sustained team workload.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Engineering — M.Eng. programs",
                "url": "https://www.engineering.cornell.edu/students/graduate-students/meng-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-nuclear-engineering-phd": {
        "summary": (
            "Doctoral researchers describe Cornell's nuclear engineering Ph.D. through MAE as focused on reactor physics, fusion, and radiation applications; praise includes DOE national-lab collaborations, with cautions about competitive funding and placements concentrated in national labs and specialized industry."
        ),
        "themes": [
            {
                "label": "Reactor & fusion physics",
                "sentiment": "positive",
                "detail": "Doctoral research spans fission, fusion, and plasma applications.",
            },
            {
                "label": "Radiation applications",
                "sentiment": "positive",
                "detail": "Faculty work on medical imaging and radiation safety.",
            },
            {
                "label": "National lab ties",
                "sentiment": "positive",
                "detail": "Collaborations connect students to DOE national laboratories.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Niche field",
                "sentiment": "mixed",
                "detail": "Graduates target national labs and specialized industry more than general ME.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Nuclear Engineering",
                "url": "https://www.mae.cornell.edu/mae/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-operations-research-ms": {
        "summary": (
            "Graduate applicants describe Cornell ORIE's M.S. as a quantitative analytics and optimization degree within a nationally ranked operations-research field — strong for consulting, finance, and tech analytics roles; students praise the applied math foundation and Cornell's Ivy brand, with cautions about self-funded tuition for terminal master's students and Ithaca's smaller local analytics hiring pool."
        ),
        "themes": [
            {
                "label": "Quantitative analytics core",
                "sentiment": "positive",
                "detail": "Training in optimization, stochastic models, and data-driven decision making.",
            },
            {
                "label": "Consulting & finance paths",
                "sentiment": "positive",
                "detail": "Graduates enter consulting, banking, and tech analytics roles.",
            },
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": "Connects engineering, business, and data science applications.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without research assistantships.",
            },
            {
                "label": "Recruiting geography",
                "sentiment": "mixed",
                "detail": "National recruiting is strong; local Ithaca analytics hiring is modest.",
            },
        ],
        "sources": [
            {
                "label": "Cornell ORIE — Graduate programs",
                "url": "https://www.orie.cornell.edu/orie/programs/graduate-programs",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-public-health-bs": {
        "summary": (
            "Students describe Cornell Brooks's undergraduate public-health pathways and CALS health-related majors as interdisciplinary training in epidemiology, policy, and community health within a land-grant Ivy; praise includes access to Brooks faculty and extension partnerships, with cautions that formal undergraduate public-health degree branding is newer than peer schools and pre-professional students must proactively build clinical or research experience."
        ),
        "themes": [
            {
                "label": "Health policy & epidemiology",
                "sentiment": "positive",
                "detail": "Coursework spans biostatistics, health policy, and community health.",
            },
            {
                "label": "Brooks School faculty",
                "sentiment": "positive",
                "detail": "Public-policy faculty connect classroom work to real health systems.",
            },
            {
                "label": "Extension partnerships",
                "sentiment": "positive",
                "detail": "CALS extension supports community-facing health projects.",
            },
            {
                "label": "Program branding",
                "sentiment": "mixed",
                "detail": "Cornell's undergraduate public-health identity is newer than dedicated BSPH schools.",
            },
            {
                "label": "Experience building",
                "sentiment": "caution",
                "detail": "Students must seek internships and research beyond core requirements.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Brooks — Public Policy",
                "url": "https://publicpolicy.cornell.edu/",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-public-health-ms": {
        "summary": (
            "Graduate applicants describe Cornell Brooks's M.P.H. as a policy- and systems-oriented public-health master's emphasizing health equity, data, and leadership for mid-career and early professionals; students value the Ivy credential and practitioner faculty, with cautions about a smaller program scale than top-tier BSPH schools and self-funded tuition for some enrollment paths."
        ),
        "themes": [
            {
                "label": "Policy & systems focus",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes health equity, leadership, and health systems.",
            },
            {
                "label": "Practitioner faculty",
                "sentiment": "positive",
                "detail": "Brooks faculty include former health administrators and policy leaders.",
            },
            {
                "label": "Interdisciplinary Cornell",
                "sentiment": "positive",
                "detail": "Connects to Vet Med, Weill Cornell, and CALS health researchers.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller cohort than top-10 Bloomberg-ranked public-health schools.",
            },
            {
                "label": "Tuition",
                "sentiment": "caution",
                "detail": "Professional master's tuition is typically self-funded.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Brooks — MPH program",
                "url": "https://publicpolicy.cornell.edu/masters/mph/",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-systems-eng-ms": {
        "summary": (
            "Students and guides describe Cornell's M.S. in Systems Engineering as an interdisciplinary graduate program bridging engineering design, project management, and complex systems thinking within the College of Engineering; praise focuses on practitioner-oriented coursework for industry leaders, with cautions about a smaller program footprint versus peer engineering departments and limited on-campus recruiting for systems roles."
        ),
        "themes": [
            {
                "label": "Systems thinking",
                "sentiment": "positive",
                "detail": "Curriculum integrates engineering design with project and risk management.",
            },
            {
                "label": "Industry orientation",
                "sentiment": "positive",
                "detail": "Targets professionals managing complex engineering programs.",
            },
            {
                "label": "Interdisciplinary faculty",
                "sentiment": "positive",
                "detail": "Draws on ORIE, MAE, and ECE expertise across Cornell Engineering.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller cohort than flagship engineering departments.",
            },
            {
                "label": "Self-directed specialization",
                "sentiment": "caution",
                "detail": "Students must early define a coherent systems focus area.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Systems Engineering — MS program",
                "url": "https://www.systemseng.cornell.edu/se/academics/ms_program",
            },
            {
                "label": "Cornell Engineering — Graduate programs",
                "url": "https://www.engineering.cornell.edu/students/graduate-students/graduate-degree-programs",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-systems-engineering-phd": {
        "summary": (
            "Doctoral students describe Cornell Systems Engineering's Ph.D. as a research degree in complex systems modeling, optimization, and design drawing on ORIE, MAE, and ECE; praise includes interdisciplinary methods, with cautions about competitive admission and a smaller community than flagship engineering departments."
        ),
        "themes": [
            {
                "label": "Complex systems modeling",
                "sentiment": "positive",
                "detail": "Doctoral research spans optimization, risk, and large-scale design.",
            },
            {
                "label": "Interdisciplinary methods",
                "sentiment": "positive",
                "detail": "Draws on ORIE, MAE, and ECE for systems-level problems.",
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and industrial systems R&D.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller community than flagship engineering departments.",
            },
        ],
        "sources": [
            {
                "label": "Cornell — Systems Engineering",
                "url": "https://www.systemseng.cornell.edu/se/academics/phd_program",
            },
            {
                "label": "U.S. News — Cornell Engineering",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/cornell-university-020957",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-veterinary-biomedical-and-clinical-sciences-ms": {
        "summary": (
            "Graduate students describe Cornell Vet's M.S. in Veterinary Biomedical and Clinical Sciences as a research master's bridging laboratory science and clinical veterinary medicine; students value mentorship from dual-trained faculty and access to hospital cases, with cautions about self-funded tuition for terminal master's students and career paths oriented toward research labs or further doctoral study."
        ),
        "themes": [
            {
                "label": "Biomedical-clinical bridge",
                "sentiment": "positive",
                "detail": "Links bench research with clinical veterinary medicine.",
            },
            {
                "label": "Hospital & lab access",
                "sentiment": "positive",
                "detail": "Students work across diagnostic labs and the veterinary hospital.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Dual-trained faculty guide thesis research in translational areas.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships.",
            },
            {
                "label": "Further study common",
                "sentiment": "mixed",
                "detail": "Many graduates continue to Ph.D. or DVM programs rather than industry.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Vet — Graduate programs",
                "url": "https://www.vet.cornell.edu/education/graduate-programs",
            },
            {
                "label": "U.S. News — Best Veterinary Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinarian-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-veterinary-biomedical-and-clinical-sciences-phd": {
        "summary": (
            "Doctoral researchers describe Cornell Vet's Ph.D. in Veterinary Biomedical and Clinical Sciences as a research doctorate in immunology, infectious disease, and comparative biomedical science; praise centers on One Health faculty and the Animal Health Diagnostic Center, with cautions about competitive admission, five-plus-year dissertation timelines, and placements concentrated in academia and government research."
        ),
        "themes": [
            {
                "label": "Comparative biomedical science",
                "sentiment": "positive",
                "detail": "Doctoral research spans immunology, pathology, and infectious disease.",
            },
            {
                "label": "One Health faculty",
                "sentiment": "positive",
                "detail": "Faculty connect animal health research to human medicine.",
            },
            {
                "label": "Diagnostic resources",
                "sentiment": "positive",
                "detail": "Animal Health Diagnostic Center supports translational projects.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Vet — Ph.D. fields of study",
                "url": "https://www.vet.cornell.edu/education/graduate-programs/phd-fields-study",
            },
            {
                "label": "U.S. News — Best Veterinary Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinarian-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-veterinary-medicine-phd": {
        "summary": (
            "Graduate researchers describe Cornell Vet's Ph.D. in Veterinary Medicine as a biomedical sciences doctorate bridging animal health, infectious disease, and comparative medicine within a top-ranked college; students praise access to the Animal Health Diagnostic Center and One Health faculty, with cautions about competitive funding, long dissertation timelines, and placements oriented toward academia and government labs."
        ),
        "themes": [
            {
                "label": "One Health research",
                "sentiment": "positive",
                "detail": "Doctoral training links animal, human, and environmental health.",
            },
            {
                "label": "Diagnostic center access",
                "sentiment": "positive",
                "detail": "Animal Health Diagnostic Center supports translational research.",
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Leading labs in infectious disease, immunology, and comparative medicine.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots.",
            },
            {
                "label": "Academic placement focus",
                "sentiment": "mixed",
                "detail": "Graduates primarily enter faculty and government research roles.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Vet — Graduate programs",
                "url": "https://www.vet.cornell.edu/education/graduate-programs",
            },
            {
                "label": "U.S. News — Best Veterinary Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinarian-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "cornell-veterinary-medicine-prof": {
        "summary": (
            "Residents and faculty describe Cornell's professional veterinary programs (internships, residencies, and specialty training) as among the most selective clinical training paths in the country within a top-three ranked vet college; praise centers on caseload diversity at the Cornell University Hospital for Animals and specialty board preparation, with cautions about intense clinical hours, Ithaca location, and highly competitive matching."
        ),
        "themes": [
            {
                "label": "Top-ranked vet college",
                "sentiment": "positive",
                "detail": "Cornell Vet consistently ranks among the nation's top veterinary schools.",
            },
            {
                "label": "Hospital caseload",
                "sentiment": "positive",
                "detail": "Cornell University Hospital for Animals provides diverse specialty cases.",
            },
            {
                "label": "Board preparation",
                "sentiment": "positive",
                "detail": "Residency programs prepare clinicians for specialty board certification.",
            },
            {
                "label": "Clinical intensity",
                "sentiment": "caution",
                "detail": "Internship and residency schedules demand long clinical hours.",
            },
            {
                "label": "Competitive matching",
                "sentiment": "caution",
                "detail": "Specialty training positions are limited and highly selective.",
            },
        ],
        "sources": [
            {
                "label": "Cornell Vet — Internships & residencies",
                "url": "https://www.vet.cornell.edu/hospitals/internships-residencies",
            },
            {
                "label": "U.S. News — Best Veterinary Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinarian-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
