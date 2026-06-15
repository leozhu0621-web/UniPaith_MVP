"""University of California-San Diego external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``ucsdprof3`` migration to merge
``DEPTH_REVIEWS`` into ``ucsd_profile._REVIEWS_BY_SLUG`` for 28
remaining coverable programs (64/64 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "ucsd-aerospace-aeronautical-and-astronautical-space-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Aerospace, Aeronautical, and Astronautical/Space Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Aerospace, Aeronautical, and Astronautical/Space Engineering",
                "url": "https://mae.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-biological-and-biomedical-sciences-other-ms": {
        "summary": "Students describe UCSD's MS pathways in biological and biomedical sciences as research-oriented degrees for pre-med, industry, or doctoral pipeline careers; praise includes School of Biological Sciences faculty and UC San Diego Health access, with cautions about self-funded tuition and outcomes that vary by specialization.",
        "themes": [
            {
                "label": "Biosciences breadth",
                "sentiment": "positive",
                "detail": "Programs span molecular biology, neuroscience, and ecology divisions.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates and graduate students join faculty labs across seven biology divisions.",
            },
            {
                "label": "Health system ties",
                "sentiment": "positive",
                "detail": "UC San Diego Health provides clinical-research context.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Most MS students self-fund without departmental assistantships.",
            },
            {
                "label": "Outcome variability",
                "sentiment": "mixed",
                "detail": "Placement depends heavily on specialization and prior research experience.",
            },
        ],
        "sources": [
            {
                "label": "UCSD Biological Sciences \u2014 Graduate",
                "url": "https://biology.ucsd.edu/education/graduate/index.html",
            },
            {
                "label": "U.S. News \u2014 Biological Sciences",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/biological-sciences-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-biological-biosystems-engineering-bs": {
        "summary": "Students describe UCSD's undergraduate Biological/Biosystems Engineering program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Biological/Biosystems Engineering",
                "url": "https://be.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-biomedical-medical-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in Bioengineering as a cross-disciplinary degree bridging engineering and medicine at a top-5 bioengineering program; praise includes the Institute of Engineering in Medicine and UC San Diego Health clinical ties, with cautions that terminal MS students typically self-fund and the program is highly selective.",
        "themes": [
            {
                "label": "Top bioengineering rank",
                "sentiment": "positive",
                "detail": "U.S. News regularly ranks UCSD bioengineering among the top five nationally.",
            },
            {
                "label": "Med-engineering bridge",
                "sentiment": "positive",
                "detail": "BioE sits at the interface of engineering, biology, and clinical care.",
            },
            {
                "label": "Biotech pipeline",
                "sentiment": "positive",
                "detail": "San Diego biotech and med-device firms recruit BioE graduates.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without assistantships typically self-fund.",
            },
            {
                "label": "Workload intensity",
                "sentiment": "caution",
                "detail": "Demanding coursework combining engineering rigor with biology depth.",
            },
        ],
        "sources": [
            {
                "label": "UCSD Bioengineering \u2014 Graduate",
                "url": "https://be.ucsd.edu/grad/index.html",
            },
            {
                "label": "U.S. News \u2014 Bioengineering rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/bioengineering-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-chemical-engineering-bs": {
        "summary": "Students describe UCSD's undergraduate Chemical Engineering program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Chemical Engineering",
                "url": "https://nanoengineering.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-chemical-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Chemical Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Chemical Engineering",
                "url": "https://nanoengineering.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-civil-engineering-bs": {
        "summary": "Students describe UCSD's undergraduate Civil Engineering program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Civil Engineering",
                "url": "https://structuralengineering.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-civil-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Civil Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Civil Engineering",
                "url": "https://structuralengineering.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-computer-engineering-bs": {
        "summary": "Students describe UCSD's undergraduate Computer Engineering program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Computer Engineering",
                "url": "https://cse.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-computer-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Computer Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Computer Engineering",
                "url": "https://cse.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-computer-science-ms": {
        "summary": "Graduate students describe UCSD's MS in Computer Science through CSE as a selective, research-oriented degree at a top-20 public engineering school; praise includes systems, AI/ML, and HCI faculty plus San Diego biotech and defense-tech recruiting, with cautions that terminal MS students often self-fund and core sequences are demanding.",
        "themes": [
            {
                "label": "CSE research depth",
                "sentiment": "positive",
                "detail": "Faculty span systems, AI, theory, and HCI with ties to SDSC and Qualcomm Institute.",
            },
            {
                "label": "Industry pipeline",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit from Jacobs CSE.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public engineering schools nationally.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund tuition.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive with strong quantitative prerequisites.",
            },
        ],
        "sources": [
            {
                "label": "UCSD CSE \u2014 Graduate Programs",
                "url": "https://cse.ucsd.edu/graduate/graduate-programs",
            },
            {
                "label": "U.S. News \u2014 Computer Science rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-economics-ms": {
        "summary": "Students describe UCSD's MS in Economics as a quantitatively rigorous graduate degree preparing for doctoral study or policy/analytics roles; praise includes micro/metrics training and faculty research in international trade and experimental economics, with cautions that it is research-oriented rather than a professional terminal degree and funding is limited.",
        "themes": [
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Core coursework spans micro, macro, econometrics, and field courses.",
            },
            {
                "label": "Faculty research",
                "sentiment": "positive",
                "detail": "Strengths in international economics, development, and econometrics.",
            },
            {
                "label": "Ph.D. pipeline",
                "sentiment": "positive",
                "detail": "Many graduates continue to doctoral programs or research roles.",
            },
            {
                "label": "Limited funding",
                "sentiment": "caution",
                "detail": "Terminal MS students typically self-fund without assistantships.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Small cohort relative to applicant volume.",
            },
        ],
        "sources": [
            {
                "label": "UCSD Economics \u2014 Graduate Programs",
                "url": "https://economics.ucsd.edu/graduate-programs/index.html",
            },
            {
                "label": "U.S. News \u2014 Economics rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-electrical-electronics-and-communications-engineering-bs": {
        "summary": "Students describe UCSD's undergraduate Electrical, Electronics, and Communications Engineering program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://ece.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Electrical, Electronics, and Communications Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://ece.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-engineering-other-bs": {
        "summary": "Students describe UCSD's undergraduate Engineering, Other program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Engineering, Other",
                "url": "https://jacobsschool.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-engineering-other-ms": {
        "summary": "Graduate students describe UCSD's MS in in Engineering, Other within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Engineering, Other",
                "url": "https://jacobsschool.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-engineering-physics-bs": {
        "summary": "Students describe UCSD's undergraduate Engineering Physics program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Engineering Physics",
                "url": "https://physics.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-engineering-physics-ms": {
        "summary": "Graduate students describe UCSD's MS in in Engineering Physics within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Engineering Physics",
                "url": "https://physics.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-engineering-science-bs": {
        "summary": "Students describe UCSD's undergraduate Engineering Science program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Engineering Science",
                "url": "https://jacobsschool.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-environmental-environmental-health-engineering-bs": {
        "summary": "Students describe UCSD's undergraduate Environmental/Environmental Health Engineering program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Environmental/Environmental Health Engineering",
                "url": "https://structuralengineering.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-finance-and-financial-management-services-ms": {
        "summary": "Students describe Rady's Master of Finance as a quantitatively rigorous one-year program emphasizing analytics and risk management; Poets&Quants highlights Rady's entrepreneurship rankings and small cohort culture, with cautions that the MFin brand is regional compared to top-10 national finance programs and San Diego finance hiring is narrower than NYC.",
        "themes": [
            {
                "label": "Quantitative curriculum",
                "sentiment": "positive",
                "detail": "Analytics-heavy coursework in risk, investments, and financial modeling.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Intimate class sizes enable close faculty and career-services access.",
            },
            {
                "label": "Entrepreneurship context",
                "sentiment": "positive",
                "detail": "Rady's innovation focus suits biotech and venture-finance paths.",
            },
            {
                "label": "Regional finance market",
                "sentiment": "mixed",
                "detail": "San Diego finance hiring is smaller than NYC or SF banking hubs.",
            },
            {
                "label": "Program selectivity",
                "sentiment": "caution",
                "detail": "Admission expects strong quantitative and programming backgrounds.",
            },
        ],
        "sources": [
            {
                "label": "Rady School \u2014 Master of Finance",
                "url": "https://rady.ucsd.edu/programs/master-of-finance/",
            },
            {
                "label": "Poets&Quants \u2014 Rady School",
                "url": "https://poetsandquants.com/schools/rady-school-of-management-university-of-california-san-diego/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-materials-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Materials Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Materials Engineering",
                "url": "https://mseg.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-mathematics-and-computer-science-bs": {
        "summary": "Students and third-party guides describe UCSD's undergraduate program in Mathematics and Computer Science within School of Physical Sciences as a professionally focused degree at a top-30 public research university; praise includes UCSD faculty and San Diego's biotech and defense ecosystem, with cautions about competitive admission, cost of living, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top public research",
                "sentiment": "positive",
                "detail": "U.S. News ranks UC San Diego #29 among national universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Mathematics and Computer Science lead research and professional training.",
            },
            {
                "label": "San Diego ecosystem",
                "sentiment": "positive",
                "detail": "Biotech, defense, and health employers enrich study and internships.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "UCSD graduate and professional programs have selective admission pools.",
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": "San Diego housing pushes total cost well above tuition alone.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Mathematics and Computer Science",
                "url": "https://cse.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/university-of-california-san-diego-1317",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-mechanical-engineering-bs": {
        "summary": "Students describe UCSD's undergraduate Mechanical Engineering program within the Jacobs School as a rigorous B.S. at a top public research university; praise includes undergraduate research access, design courses, and San Diego biotech and defense-tech recruiting, with cautions about large lower-division classes and the quarter system's fast pace.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Jacobs School departments.",
            },
            {
                "label": "San Diego industry",
                "sentiment": "positive",
                "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public undergraduate engineering schools.",
            },
            {
                "label": "Large core classes",
                "sentiment": "mixed",
                "detail": "High demand means crowded lower-division engineering sequences.",
            },
            {
                "label": "Quarter pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters move quickly; course planning is essential.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Mechanical Engineering",
                "url": "https://mae.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-mechanical-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Mechanical Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Mechanical Engineering",
                "url": "https://mae.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-medicine-phd": {
        "summary": "Doctoral students describe UCSD's Ph.D. pathways in medicine and biomedical sciences as research-intensive training at a top-20 medical school \u2014 U.S. News ranks UC San Diego School of Medicine among leading research medical schools; praise includes UC San Diego Health clinical access and NIH-funded labs, with cautions about competitive academic job markets and San Diego cost of living.",
        "themes": [
            {
                "label": "Research medical school",
                "sentiment": "positive",
                "detail": "Top-20 medical school with $1B+ research enterprise through UC San Diego Health.",
            },
            {
                "label": "Clinical & translational access",
                "sentiment": "positive",
                "detail": "Altman CTSA and Moores Cancer Center anchor doctoral research.",
            },
            {
                "label": "NIH funding",
                "sentiment": "positive",
                "detail": "Strong federal research support across biomedical sciences.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track biomedical faculty positions are nationally competitive.",
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": "San Diego housing costs are among the highest in the UC system.",
            },
        ],
        "sources": [
            {
                "label": "UCSD School of Medicine \u2014 Graduate Programs",
                "url": "https://medschool.ucsd.edu/education/graduate-programs/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-california-san-diego-04038",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-public-health-ms": {
        "summary": "Students describe UCSD's MPH through the Herbert Wertheim School as a research-oriented public health degree leveraging UC San Diego Health and the campus's biostatistics ecosystem; praise includes epidemiology faculty and community-health fieldwork, with cautions that the school is young (founded 2019) and employer networks are still maturing.",
        "themes": [
            {
                "label": "Health-sciences ecosystem",
                "sentiment": "positive",
                "detail": "Access to School of Medicine, pharmacy, and UC San Diego Health.",
            },
            {
                "label": "Epidemiology & biostats",
                "sentiment": "positive",
                "detail": "Faculty strengths in chronic disease, aging, and quantitative methods.",
            },
            {
                "label": "Fieldwork access",
                "sentiment": "positive",
                "detail": "San Diego County and border-region health partnerships enrich practicum.",
            },
            {
                "label": "Young school",
                "sentiment": "mixed",
                "detail": "Wertheim School founded 2019 \u2014 alumni network still developing.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "MPH cohorts are small relative to applicant interest.",
            },
        ],
        "sources": [
            {
                "label": "Wertheim School \u2014 MPH Program",
                "url": "https://publichealth.ucsd.edu/masters-programs/mph/index.html",
            },
            {
                "label": "U.S. News \u2014 Public Health rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "ucsd-systems-engineering-ms": {
        "summary": "Graduate students describe UCSD's MS in in Systems Engineering within the Jacobs School as a research- and coursework-intensive degree; praise includes faculty labs and San Diego biotech and defense recruiting, with cautions that terminal MS students typically self-fund and admission is selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and San Diego employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Jacobs School ranks among top public graduate engineering schools.",
            },
            {
                "label": "Biotech & defense pipeline",
                "sentiment": "positive",
                "detail": "Regional employers hire across engineering specializations.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "UC San Diego \u2014 Systems Engineering",
                "url": "https://jacobsschool.ucsd.edu/",
            },
            {
                "label": "U.S. News \u2014 UC San Diego",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
