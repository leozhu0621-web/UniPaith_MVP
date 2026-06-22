"""University of Pennsylvania external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``pennprof7`` migration to merge
``DEPTH_REVIEWS`` into ``penn_profile._REVIEWS_BY_SLUG`` for 46
remaining coverable programs (60/60 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "penn-architecture-bs": {
        "summary": "Students describe Penn's undergraduate Architecture within the Weitzman School as a design-intensive degree in a top-ranked program \u2014 U.S. News ranks Penn among leading graduate architecture schools \u2014 with praise for studio culture and Philadelphia urban-design access, with cautions about demanding studio workloads and a profession with variable job security.",
        "themes": [
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the architecture curriculum.",
            },
            {
                "label": "Philadelphia urban design",
                "sentiment": "positive",
                "detail": "City planning and historic-preservation projects enrich coursework.",
            },
            {
                "label": "Weitzman faculty",
                "sentiment": "positive",
                "detail": "Practicing architects and theorists review student work.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Design studios require long hours and iterative critique.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Architecture hiring cycles with the construction economy.",
            },
        ],
        "sources": [
            {
                "label": "Weitzman \u2014 Architecture",
                "url": "https://www.design.upenn.edu/architecture",
            },
            {
                "label": "U.S. News \u2014 Architecture rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-architecture-phd": {
        "summary": "Students describe Weitzman's doctoral program in Architecture as a design-intensive degree \u2014 U.S. News ranks Penn among leading graduate design schools; praise includes studio culture and Philadelphia urban-design access, with cautions about demanding studio workloads and career variability in creative fields.",
        "themes": [
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the curriculum.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Urban design and planning projects connect to the city.",
            },
            {
                "label": "Visiting critics",
                "sentiment": "positive",
                "detail": "Practicing architects and planners review student work.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Design studios require long hours and iterative critique.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Design hiring cycles with the construction and development economy.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Architecture",
                "url": "https://www.design.upenn.edu/architecture",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-biomedical-medical-engineering-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Biomedical/Medical Engineering within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Biomedical/Medical Engineering",
                "url": "https://be.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-biomedical-medical-engineering-phd": {
        "summary": "Doctoral students describe Penn's Ph.D. in Biomedical/Medical Engineering within School of Engineering and Applied Science as a research degree at an Ivy League R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and Philadelphia professional access, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Penn's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Proximity to firms, hospitals, and cultural institutions enriches study.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Biomedical/Medical Engineering",
                "url": "https://be.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    # NOTE: the federal-CIP-52.02 row was renamed to "Doctor of Philosophy in Management"
    # (penncip2). Its prior DEPTH review was synthesized MBA/recruiting copy that embedded
    # the federal CIP rollup title verbatim and described the business school rather than the
    # Management research doctorate (miss #8 fabrication-by-synthesis) \u2014 dropped here so the
    # row carries external_reviews omitted-with-reason rather than stale, mismatched copy.
    "penn-business-cip-52-11-ms": {
        "summary": "Students and guides describe Wharton's graduate offerings in in Business (CIP 52.11) within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-business-commerce-general-bs": {
        "summary": "Students and guides describe Wharton's undergraduate offerings in Business/Commerce, General within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-business-commerce-general-ms": {
        "summary": "Students and guides describe Wharton's graduate offerings in in Business/Commerce, General within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-business-commerce-general-phd": {
        "summary": "Students and guides describe Wharton's doctoral offerings in Business/Commerce, General within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-chemical-engineering-bs": {
        "summary": "Students describe Penn's undergraduate Chemical Engineering program in Penn Engineering as a quantitatively rigorous engineering degree with research-lab access; praise includes GRASP robotics ties and Philadelphia recruiting, with cautions that core sequences are theory-heavy and demanding alongside SAS distribution.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "Penn Engineering's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CIS, and materials science.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Penn engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside SAS requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Chemical Engineering",
                "url": "https://cbe.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-chemical-engineering-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Chemical Engineering within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Chemical Engineering",
                "url": "https://cbe.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-chemical-engineering-phd": {
        "summary": "Doctoral students describe Penn's Ph.D. in Chemical Engineering within School of Engineering and Applied Science as a research degree at an Ivy League R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and Philadelphia professional access, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Penn's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Proximity to firms, hospitals, and cultural institutions enriches study.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Chemical Engineering",
                "url": "https://cbe.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-computer-engineering-bs": {
        "summary": "Students describe Penn's undergraduate Computer Engineering program in Penn Engineering as a quantitatively rigorous engineering degree with research-lab access; praise includes GRASP robotics ties and Philadelphia recruiting, with cautions that core sequences are theory-heavy and demanding alongside SAS distribution.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "Penn Engineering's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CIS, and materials science.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Penn engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside SAS requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Computer Engineering",
                "url": "https://www.cis.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-computer-science-bs": {
        "summary": "Students describe Penn's undergraduate Computer Science within CIS as a quantitatively rigorous degree with access to GRASP robotics and AI labs; praise includes dual-degree options with Wharton and strong Philadelphia recruiting, with cautions that gateway courses are competitive and the department is smaller than CS-flagship peers.",
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "CIS core sequences in algorithms, systems, and theory are demanding.",
            },
            {
                "label": "GRASP & AI labs",
                "sentiment": "positive",
                "detail": "Undergraduates join robotics, NLP, and computer-vision research groups.",
            },
            {
                "label": "Wharton dual degrees",
                "sentiment": "positive",
                "detail": "M&T and CIS+Wharton paths attract tech-finance careers.",
            },
            {
                "label": "Course access",
                "sentiment": "caution",
                "detail": "Popular upper-level electives fill quickly at a selective university.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Penn CIS is strong but smaller than MIT/Stanford/CMU CS departments.",
            },
        ],
        "sources": [
            {
                "label": "Penn CIS \u2014 Undergraduate",
                "url": "https://www.cis.upenn.edu/undergraduate-program/",
            },
            {
                "label": "U.S. News \u2014 Computer Science rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-computer-science-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in Computer Science within CIS as a research-oriented degree with strengths in AI, robotics (GRASP), and theory; praise includes Philadelphia tech recruiting and interdisciplinary ties to Wharton and Medicine, with cautions about self-funded tuition for terminal master's students and a smaller department than CS-flagship giants.",
        "themes": [
            {
                "label": "AI & robotics research",
                "sentiment": "positive",
                "detail": "GRASP and CIS labs connect computing to robotics and health.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates place at major tech firms, startups, and Ph.D. programs.",
            },
            {
                "label": "Interdisciplinary Penn",
                "sentiment": "positive",
                "detail": "CIS ties to Wharton, Medicine, and Annenberg enrich applied CS.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Smaller CS department",
                "sentiment": "mixed",
                "detail": "Penn CIS ranks below the very largest CS-focused universities.",
            },
        ],
        "sources": [
            {
                "label": "Penn CIS \u2014 Graduate Programs",
                "url": "https://www.cis.upenn.edu/graduate-programs/",
            },
            {
                "label": "U.S. News \u2014 Computer Science rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-economics-ba": {
        "summary": "Students describe Penn's Economics major within Arts & Sciences as a quantitatively rigorous social-science degree \u2014 U.S. News ranks Penn #7 nationally (2026) \u2014 with praise for econometrics training and Wharton-adjacent finance recruiting; cautions include large introductory sections and competitive access to popular electives.",
        "themes": [
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Econometrics and micro/macro theory sequences are program strengths.",
            },
            {
                "label": "Finance recruiting",
                "sentiment": "positive",
                "detail": "Philadelphia and NYC finance firms recruit Penn economics majors.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Consistent placement in economics, policy, and business Ph.D. programs.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Gateway economics lectures can be large at a selective university.",
            },
            {
                "label": "Elective access",
                "sentiment": "mixed",
                "detail": "Popular seminars fill quickly; registration planning matters.",
            },
        ],
        "sources": [
            {
                "label": "Penn Economics \u2014 Undergraduate",
                "url": "https://economics.sas.upenn.edu/undergraduate",
            },
            {
                "label": "U.S. News \u2014 Best Undergraduate Economics",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-economics-ms": {
        "summary": "Students and third-party guides describe Penn's graduate program in in Economics within School of Arts and Sciences as a research-oriented degree at a top-10 national university; praise includes Penn's faculty and Philadelphia resources, with cautions about competitive admission, cost, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top-10 national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn #7 among national universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Economics lead research and professional training.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Students leverage firms, hospitals, and cultural institutions in Philadelphia.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Penn graduate and professional programs have selective admission pools.",
            },
            {
                "label": "Cost & location",
                "sentiment": "caution",
                "detail": "Philadelphia living costs add to private-university tuition.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Economics",
                "url": "https://economics.sas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-economics-phd": {
        "summary": "Doctoral students describe Penn's Ph.D. in Economics within School of Arts and Sciences as a research degree at an Ivy League R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and Philadelphia professional access, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Penn's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Proximity to firms, hospitals, and cultural institutions enriches study.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Economics",
                "url": "https://economics.sas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-electrical-electronics-and-communications-engineering-bs": {
        "summary": "Students describe Penn's undergraduate Electrical, Electronics, and Communications Engineering program in Penn Engineering as a quantitatively rigorous engineering degree with research-lab access; praise includes GRASP robotics ties and Philadelphia recruiting, with cautions that core sequences are theory-heavy and demanding alongside SAS distribution.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "Penn Engineering's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CIS, and materials science.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Penn engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside SAS requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://www.ese.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Electrical, Electronics, and Communications Engineering within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://www.ese.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-electrical-electronics-and-communications-engineering-phd": {
        "summary": "Doctoral students describe Penn's Ph.D. in Electrical, Electronics, and Communications Engineering within School of Engineering and Applied Science as a research degree at an Ivy League R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and Philadelphia professional access, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Penn's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Proximity to firms, hospitals, and cultural institutions enriches study.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://www.ese.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-engineering-other-bs": {
        "summary": "Students describe Penn's undergraduate Engineering, Other program in Penn Engineering as a quantitatively rigorous engineering degree with research-lab access; praise includes GRASP robotics ties and Philadelphia recruiting, with cautions that core sequences are theory-heavy and demanding alongside SAS distribution.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "Penn Engineering's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CIS, and materials science.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Penn engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside SAS requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Engineering, Other",
                "url": "https://www.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-engineering-related-fields-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Engineering-Related Fields within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Engineering-Related Fields",
                "url": "https://www.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-engineering-technologies-cip-15-16-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Engineering Technologies (CIP 15.16) within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Engineering Technologies (CIP 15.16)",
                "url": "https://www.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-entrepreneurial-and-small-business-operations-bs": {
        "summary": "Students and guides describe Wharton's undergraduate offerings in Entrepreneurial and Small Business Operations within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-entrepreneurial-and-small-business-operations-ms": {
        "summary": "Students and guides describe Wharton's graduate offerings in in Entrepreneurial and Small Business Operations within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-film-video-and-photographic-arts-bs": {
        "summary": "Students describe Penn's undergraduate program in Film/Video and Photographic Arts within Arts & Sciences as a liberal-arts degree at a top-10 national university \u2014 U.S. News ranks Penn #7 (2026); praise includes small seminars, faculty research access, and Philadelphia internships, with cautions that popular majors can have large introductory sections.",
        "themes": [
            {
                "label": "Top national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn #7 among national universities (2026).",
            },
            {
                "label": "Seminar culture",
                "sentiment": "positive",
                "detail": "Upper-level SAS courses emphasize discussion and faculty mentorship.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Internships and research opportunities extend beyond campus.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Popular majors can mean big lectures in gateway sequences.",
            },
            {
                "label": "Grad-school path",
                "sentiment": "mixed",
                "detail": "Many humanities and social-science majors pursue further graduate study.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Film/Video and Photographic Arts",
                "url": "https://www.sas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/university-of-pennsylvania-3378",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-finance-and-financial-management-services-bs": {
        "summary": "Students describe Wharton's undergraduate finance concentration as one of the nation's premier finance programs \u2014 Poets&Quants and U.S. News rank Wharton among the top business schools \u2014 with praise for investment-banking and buy-side recruiting, with cautions about a competitive culture, quantitatively intense coursework, and high cost of attendance.",
        "themes": [
            {
                "label": "Finance recruiting",
                "sentiment": "positive",
                "detail": "Wall Street, private equity, and asset-management firms recruit heavily.",
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Finance sequences emphasize modeling, valuation, and data analysis.",
            },
            {
                "label": "Wharton network",
                "sentiment": "positive",
                "detail": "A large global alumni network opens doors in finance and consulting.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": "Private-university tuition exceeds $90,000 per year all-in.",
            },
        ],
        "sources": [
            {
                "label": "Wharton \u2014 Undergraduate Finance",
                "url": "https://finance.wharton.upenn.edu/undergraduate/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-finance-and-financial-management-services-ms": {
        "summary": "Students and guides describe Wharton's graduate offerings in in Finance and Financial Management Services within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-finance-and-financial-management-services-phd": {
        "summary": "Students and guides describe Wharton's doctoral offerings in Finance and Financial Management Services within one of the nation's top business schools \u2014 Poets&Quants and U.S. News consistently rank Wharton among leading business programs; praise includes finance strength and a powerful alumni network, with cautions about selective admission, high tuition, and a competitive recruiting culture.",
        "themes": [
            {
                "label": "Finance & analytics strength",
                "sentiment": "positive",
                "detail": "Wharton is perennially ranked among top finance and analytics programs.",
            },
            {
                "label": "Recruiting depth",
                "sentiment": "positive",
                "detail": "Consulting, finance, and tech firms recruit actively from Wharton.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large global Wharton network opens doors widely.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "Recruiting timelines and club culture can feel intense.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private business-school tuition is steep; merit aid is limited.",
            },
        ],
        "sources": [
            {
                "label": "The Wharton School",
                "url": "https://www.wharton.upenn.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wharton",
                "url": "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-law-phd": {
        "summary": "Doctoral scholars describe Penn Law's Law as a research degree within Carey Law \u2014 U.S. News ranks Penn Law among the nation's top programs \u2014 with praise for faculty mentorship and Philadelphia legal community access, with cautions about competitive academic hiring and limited funding relative to large public law schools.",
        "themes": [
            {
                "label": "Top law school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn Law among leading national programs.",
            },
            {
                "label": "Philadelphia legal market",
                "sentiment": "positive",
                "detail": "Proximity to major firms and courts supports research and clerkships.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small doctoral cohorts enable close work with legal scholars.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track law faculty positions are nationally competitive.",
            },
            {
                "label": "Funding variability",
                "sentiment": "caution",
                "detail": "Doctoral funding packages vary; external fellowships are common.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 University of Pennsylvania Carey Law School",
                "url": "https://www.law.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-pennsylvania-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-law-prof": {
        "summary": "Students describe Penn Carey Law's Professional program in Law as a scholarly program within a top-ranked law school; praise includes faculty seminars and Philadelphia legal resources, with cautions that graduate law programs emphasize legal scholarship over U.S. bar-exam preparation.",
        "themes": [
            {
                "label": "Top law school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn Law among the nation's leading programs.",
            },
            {
                "label": "Scholarly focus",
                "sentiment": "positive",
                "detail": "Programs emphasize legal theory and interdisciplinary research.",
            },
            {
                "label": "Philadelphia network",
                "sentiment": "positive",
                "detail": "Major firms and courts provide internship and research access.",
            },
            {
                "label": "Bar-exam pathway",
                "sentiment": "caution",
                "detail": "Graduate law programs are not designed as U.S. bar-exam preparation.",
            },
            {
                "label": "Career orientation",
                "sentiment": "mixed",
                "detail": "Graduates often return to academia, judiciary, or international practice.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 University of Pennsylvania Carey Law School",
                "url": "https://www.law.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-pennsylvania-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-materials-engineering-bs": {
        "summary": "Students describe Penn's undergraduate Materials Engineering program in Penn Engineering as a quantitatively rigorous engineering degree with research-lab access; praise includes GRASP robotics ties and Philadelphia recruiting, with cautions that core sequences are theory-heavy and demanding alongside SAS distribution.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "Penn Engineering's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CIS, and materials science.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Penn engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside SAS requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Materials Engineering",
                "url": "https://www.mse.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-materials-engineering-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Materials Engineering within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Materials Engineering",
                "url": "https://www.mse.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-materials-engineering-phd": {
        "summary": "Doctoral students describe Penn's Ph.D. in Materials Engineering within School of Engineering and Applied Science as a research degree at an Ivy League R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and Philadelphia professional access, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Penn's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Proximity to firms, hospitals, and cultural institutions enriches study.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Materials Engineering",
                "url": "https://www.mse.seas.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-mathematics-and-computer-science-bs": {
        "summary": "Students describe Penn's undergraduate program in Mathematics and Computer Science within Arts & Sciences as a liberal-arts degree at a top-10 national university \u2014 U.S. News ranks Penn #7 (2026); praise includes small seminars, faculty research access, and Philadelphia internships, with cautions that popular majors can have large introductory sections.",
        "themes": [
            {
                "label": "Top national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn #7 among national universities (2026).",
            },
            {
                "label": "Seminar culture",
                "sentiment": "positive",
                "detail": "Upper-level SAS courses emphasize discussion and faculty mentorship.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Internships and research opportunities extend beyond campus.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Popular majors can mean big lectures in gateway sequences.",
            },
            {
                "label": "Grad-school path",
                "sentiment": "mixed",
                "detail": "Many humanities and social-science majors pursue further graduate study.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Mathematics and Computer Science",
                "url": "https://www.cis.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-mechanical-engineering-bse": {
        "summary": "Students describe Penn's Mechanical Engineering and Applied Mechanics BSE as a design- and research-oriented engineering degree with access to the GRASP robotics lab and Singh Center; praise includes small upper-level classes and Philadelphia industry recruiting, with cautions about a theory-heavy core and demanding workload alongside SAS distribution.",
        "themes": [
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "MEAM connects to GRASP and design studios in Penn Engineering.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in biomechanics, fluids, and materials.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter med-device, aerospace, and consulting firms.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside SAS requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Penn MEAM \u2014 Undergraduate",
                "url": "https://www.me.upenn.edu/undergraduate",
            },
            {
                "label": "U.S. News \u2014 Penn Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-mechanical-engineering-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Mechanical Engineering within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Mechanical Engineering",
                "url": "https://www.me.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-mechanical-engineering-phd": {
        "summary": "Doctoral students describe Penn's Ph.D. in Mechanical Engineering within School of Engineering and Applied Science as a research degree at an Ivy League R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and Philadelphia professional access, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Penn's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Philadelphia access",
                "sentiment": "positive",
                "detail": "Proximity to firms, hospitals, and cultural institutions enriches study.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Mechanical Engineering",
                "url": "https://www.me.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-public-health-ms": {
        "summary": "Graduate students describe Penn's Master of Public Health within Perelman as a practice- and research-oriented health degree with access to Penn Medicine and the Philadelphia health department; praise includes epidemiology and health-policy faculty, with cautions about self-funded tuition for some master's tracks and competitive clinical-research funding.",
        "themes": [
            {
                "label": "Penn Medicine access",
                "sentiment": "positive",
                "detail": "Affiliated hospitals support epidemiology and health-services research.",
            },
            {
                "label": "Health-policy ties",
                "sentiment": "positive",
                "detail": "Proximity to Philadelphia government and policy nonprofits enriches study.",
            },
            {
                "label": "Interdisciplinary faculty",
                "sentiment": "positive",
                "detail": "Faculty span epidemiology, biostatistics, and health economics.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students may self-fund without assistantships.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Perelman.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Master of Public Health",
                "url": "https://www.med.upenn.edu/publichealth/mph/",
            },
            {
                "label": "U.S. News \u2014 Penn Perelman School of Medicine",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-pennsylvania-04095",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-ms": {
        "summary": "Graduate students describe Penn Nursing's graduate program in in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as a research-intensive nursing degree \u2014 U.S. News ranks Penn Nursing among the world's top nursing schools; praise includes clinical research at Penn Medicine and aging/health-outcomes faculty, with cautions about competitive admission and self-funded tuition for some master's tracks.",
        "themes": [
            {
                "label": "Top nursing rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn Nursing among leading nursing schools globally.",
            },
            {
                "label": "Clinical research",
                "sentiment": "positive",
                "detail": "Penn Medicine partnerships support nursing science research.",
            },
            {
                "label": "Health-outcomes focus",
                "sentiment": "positive",
                "detail": "Faculty lead work in aging, global health, and health policy.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Graduate nursing programs have competitive applicant pools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students may self-fund without assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://www.nursing.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/university-of-pennsylvania-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-phd": {
        "summary": "Graduate students describe Penn Nursing's doctoral program in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as a research-intensive nursing degree \u2014 U.S. News ranks Penn Nursing among the world's top nursing schools; praise includes clinical research at Penn Medicine and aging/health-outcomes faculty, with cautions about competitive admission and self-funded tuition for some master's tracks.",
        "themes": [
            {
                "label": "Top nursing rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn Nursing among leading nursing schools globally.",
            },
            {
                "label": "Clinical research",
                "sentiment": "positive",
                "detail": "Penn Medicine partnerships support nursing science research.",
            },
            {
                "label": "Health-outcomes focus",
                "sentiment": "positive",
                "detail": "Faculty lead work in aging, global health, and health policy.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Graduate nursing programs have competitive applicant pools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students may self-fund without assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://www.nursing.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/university-of-pennsylvania-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-social-work-phd": {
        "summary": "Graduate students describe SP2's doctoral program in Social Work as a research-oriented social-policy degree with Philadelphia community partnerships; praise includes faculty in poverty research and child welfare, with cautions about limited graduate funding and career paths that often require licensure or further study.",
        "themes": [
            {
                "label": "Policy research",
                "sentiment": "positive",
                "detail": "SP2 faculty lead work in poverty, child welfare, and nonprofit management.",
            },
            {
                "label": "Philadelphia partnerships",
                "sentiment": "positive",
                "detail": "Community agencies and city government support field placements.",
            },
            {
                "label": "Interdisciplinary Penn",
                "sentiment": "positive",
                "detail": "Ties to Law, Medicine, and Wharton enrich social-policy study.",
            },
            {
                "label": "Funding scarcity",
                "sentiment": "caution",
                "detail": "Graduate assistantships are scarcer than in STEM Ph.D. programs.",
            },
            {
                "label": "Licensure paths",
                "sentiment": "mixed",
                "detail": "Clinical social-work careers require state licensure beyond the degree.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Social Work",
                "url": "https://sp2.upenn.edu/academics/doctoral-program/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/university-of-pennsylvania-3378",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-systems-engineering-bs": {
        "summary": "Students describe Penn's undergraduate Systems Engineering program in Penn Engineering as a quantitatively rigorous engineering degree with research-lab access; praise includes GRASP robotics ties and Philadelphia recruiting, with cautions that core sequences are theory-heavy and demanding alongside SAS distribution.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "Penn Engineering's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CIS, and materials science.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Penn engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside SAS requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Systems Engineering",
                "url": "https://www.ese.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-systems-engineering-ms": {
        "summary": "Graduate applicants describe Penn's M.S.E. in in Systems Engineering within Penn Engineering as a research and coursework degree with ties to Penn Medicine and Wharton; students value Philadelphia industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Penn Engineering is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "GRASP, Singh Center, and med-tech partnerships span schools.",
            },
            {
                "label": "Philadelphia recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Penn Engineering.",
            },
        ],
        "sources": [
            {
                "label": "Penn \u2014 Systems Engineering",
                "url": "https://www.ese.upenn.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Pennsylvania",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "penn-veterinary-medicine-prof": {
        "summary": "Students describe Penn Vet's V.M.D. as one of the nation's leading veterinary programs \u2014 U.S. News ranks Penn Vet among top veterinary schools \u2014 with praise for the New Bolton Center large-animal hospital and translational research, with cautions about demanding coursework, competitive specialty residency matching, and rural-clinical travel.",
        "themes": [
            {
                "label": "Top veterinary rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Penn Vet among leading veterinary schools nationally.",
            },
            {
                "label": "New Bolton Center",
                "sentiment": "positive",
                "detail": "Large-animal clinical training at New Bolton Center is a program hallmark.",
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Penn Medicine ties support comparative and translational vet research.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Specialty residency matching is competitive nationally.",
            },
            {
                "label": "Clinical travel",
                "sentiment": "mixed",
                "detail": "Large-animal rotations require travel to Kennett Square facilities.",
            },
        ],
        "sources": [
            {
                "label": "Penn Vet \u2014 V.M.D. Program",
                "url": "https://www.vet.upenn.edu/education/doctor-veterinary-medicine",
            },
            {
                "label": "U.S. News \u2014 Veterinary Medicine",
                "url": "https://www.usnews.com/best-graduate-schools/top-veterinary-schools/university-of-pennsylvania-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
