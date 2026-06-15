"""Johns Hopkins University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``jhuprof3`` migration to merge
``DEPTH_REVIEWS`` into ``jhu_profile._REVIEWS_BY_SLUG`` for 34
remaining coverable programs (44/44 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "jhu-aerospace-aeronautical-and-astronautical-space-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Aerospace, Aeronautical, and Astronautical/Space Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Aerospace, Aeronautical, and Astronautical/Space Engineering",
                "url": "https://engineering.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-biomedical-medical-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Biomedical/Medical Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Biomedical/Medical Engineering",
                "url": "https://www.bme.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-business-administration-management-and-operations-bs": {
        "summary": "Students in Carey's undergraduate business major describe a liberal-arts-plus-business curriculum on Homewood with quantitative requirements; praise includes flexibility to combine with sciences or IR, with cautions that Carey is newer than peer undergraduate business programs and lacks a standalone B-school campus.",
        "themes": [
            {
                "label": "Interdisciplinary flexibility",
                "sentiment": "positive",
                "detail": "Business major pairs with engineering, public health, or IR on Homewood.",
            },
            {
                "label": "Quantitative core",
                "sentiment": "positive",
                "detail": "Calculus and statistics requirements suit analytics-minded students.",
            },
            {
                "label": "Young program",
                "sentiment": "mixed",
                "detail": "Carey undergraduate business is newer than long-established peer majors.",
            },
            {
                "label": "Recruiting breadth",
                "sentiment": "caution",
                "detail": "Consulting/finance placement is strong but smaller than dedicated B-school undergrad paths.",
            },
        ],
        "sources": [
            {
                "label": "Carey \u2014 Undergraduate Business",
                "url": "https://carey.jhu.edu/programs/undergraduate/business",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/johns-hopkins-university-2071",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-business-commerce-general-bs": {
        "summary": "Students describe Carey's undergraduate business pathway in Business/Commerce, General on Homewood as a flexible, quant-oriented major within a top-10 research university; praise includes interdisciplinary pairing with engineering or public health, with cautions about recruiting breadth versus dedicated undergraduate business schools.",
        "themes": [
            {
                "label": "Interdisciplinary pairing",
                "sentiment": "positive",
                "detail": "Business coursework combines with sciences, engineering, or IR.",
            },
            {
                "label": "Quantitative core",
                "sentiment": "positive",
                "detail": "Statistics and calculus requirements suit analytics careers.",
            },
            {
                "label": "Homewood community",
                "sentiment": "positive",
                "detail": "Undergraduates benefit from JHU's residential campus culture.",
            },
            {
                "label": "Recruiting breadth",
                "sentiment": "caution",
                "detail": "Consulting/finance pipelines are smaller than at dedicated B-school undergrad programs.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Business/Commerce, General",
                "url": "https://carey.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/johns-hopkins-university-01026",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-business-commerce-general-ms": {
        "summary": "Students describe Carey's graduate program in in Business/Commerce, General as a professionally focused business degree at a top-10 national university \u2014 U.S. News ranks JHU #7 (2026); praise includes health-sector and analytics threads unique to Carey, with cautions that the business school's national brand is still building compared with M7 peers.",
        "themes": [
            {
                "label": "Health-sector focus",
                "sentiment": "positive",
                "detail": "Carey leverages Hopkins Medicine and public-health proximity.",
            },
            {
                "label": "Analytics curriculum",
                "sentiment": "positive",
                "detail": "Quantitative methods and design-thinking run through Carey programs.",
            },
            {
                "label": "Collaborative cohort",
                "sentiment": "positive",
                "detail": "Smaller class sizes foster close faculty relationships.",
            },
            {
                "label": "Brand recognition",
                "sentiment": "mixed",
                "detail": "Carey is newer than long-established top MBA brands.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private graduate business tuition exceeds most public programs.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Business/Commerce, General",
                "url": "https://carey.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/johns-hopkins-university-01026",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-chemical-engineering-bs": {
        "summary": "Students describe JHU's undergraduate program in Chemical Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Chemical Engineering",
                "url": "https://chbe.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-chemical-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Chemical Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Chemical Engineering",
                "url": "https://chbe.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-civil-engineering-bs": {
        "summary": "Students describe JHU's undergraduate program in Civil Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Civil Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-civil-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Civil Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Civil Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-computer-engineering-bs": {
        "summary": "Students describe JHU's undergraduate Computer Engineering as rigorous and research-oriented within the Whiting School; praise includes faculty access and ties to AI/robotics institutes, with cautions that the curriculum is theory-heavy and some want more industry-facing project courses.",
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in AI, robotics, and systems.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong foundations but fewer applied-software courses than some peers.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Small upper-level classes on Homewood campus.",
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates enter top tech firms, research labs, and graduate programs.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Computer Engineering",
                "url": "https://engineering.jhu.edu/ece/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-economics-ms": {
        "summary": "Graduate students describe JHU's master's in in Economics within the Krieger School as quantitatively rigorous training for consulting, policy, and PhD paths; praise includes faculty research access and Baltimore/Washington proximity, with cautions about limited formal master's funding compared with PhD programs.",
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Math-intensive coursework prepares students for analytics and PhD work.",
            },
            {
                "label": "Faculty research",
                "sentiment": "positive",
                "detail": "Graduate students join applied micro, macro, and econometrics labs.",
            },
            {
                "label": "DC policy access",
                "sentiment": "positive",
                "detail": "Baltimore\u2013Washington corridor offers internship opportunities.",
            },
            {
                "label": "Funding limits",
                "sentiment": "caution",
                "detail": "Terminal master's students receive less funding than PhD admits.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Economics",
                "url": "https://econ.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/johns-hopkins-university-2071",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-electrical-electronics-and-communications-engineering-bs": {
        "summary": "Students describe JHU's undergraduate Electrical, Electronics, and Communications Engineering as rigorous and research-oriented within the Whiting School; praise includes faculty access and ties to AI/robotics institutes, with cautions that the curriculum is theory-heavy and some want more industry-facing project courses.",
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in AI, robotics, and systems.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong foundations but fewer applied-software courses than some peers.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Small upper-level classes on Homewood campus.",
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates enter top tech firms, research labs, and graduate programs.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://engineering.jhu.edu/ece/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Electrical, Electronics, and Communications Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://engineering.jhu.edu/ece/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-engineering-general-bs": {
        "summary": "Students describe JHU's undergraduate program in Engineering, General within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Engineering, General",
                "url": "https://engineering.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-engineering-general-ms": {
        "summary": "Students describe JHU's graduate program in in Engineering, General within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Engineering, General",
                "url": "https://engineering.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-engineering-general-phd": {
        "summary": "Doctoral students describe JHU's PhD in Engineering, General within the Whiting School as intensely research-focused with strong NIH and industry partnerships; praise includes faculty mentorship and APL collaboration, with cautions about competitive funding and the demanding Baltimore research environment.",
        "themes": [
            {
                "label": "Research intensity",
                "sentiment": "positive",
                "detail": "Whiting PhD students lead projects in top-ranked engineering labs.",
            },
            {
                "label": "APL collaboration",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory offers distinctive research opportunities.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small departments foster close advisor relationships.",
            },
            {
                "label": "Funding variability",
                "sentiment": "caution",
                "detail": "RA/TA packages depend on advisor grants and department.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Engineering, General",
                "url": "https://engineering.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-engineering-mechanics-bs": {
        "summary": "Students describe JHU's undergraduate program in Engineering Mechanics within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Engineering Mechanics",
                "url": "https://me.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-engineering-related-fields-ms": {
        "summary": "Students describe JHU's graduate program in in Engineering-Related Fields within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Engineering-Related Fields",
                "url": "https://engineering.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-environmental-environmental-health-engineering-bs": {
        "summary": "Students describe JHU's undergraduate program in Environmental/Environmental Health Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Environmental/Environmental Health Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-environmental-environmental-health-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Environmental/Environmental Health Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Environmental/Environmental Health Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-film-video-and-photographic-arts-ms": {
        "summary": "Graduate students describe Peabody's film and media programs as conservatory-style training within a major research university; praise includes faculty practitioners and Baltimore/D.C. production access, with cautions that the program is small and industry placement varies by concentration.",
        "themes": [
            {
                "label": "Conservatory training",
                "sentiment": "positive",
                "detail": "Peabody combines arts-school rigor with Hopkins resources.",
            },
            {
                "label": "Faculty practitioners",
                "sentiment": "positive",
                "detail": "Working filmmakers and media artists lead studio instruction.",
            },
            {
                "label": "Regional production access",
                "sentiment": "positive",
                "detail": "Baltimore and D.C. media markets provide internship opportunities.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Small cohort means fewer peer specializations than large film schools.",
            },
            {
                "label": "Industry placement",
                "sentiment": "caution",
                "detail": "Outcomes vary by portfolio strength and networking effort.",
            },
        ],
        "sources": [
            {
                "label": "Peabody Institute \u2014 Film & Media",
                "url": "https://peabody.jhu.edu/",
            },
            {
                "label": "Niche \u2014 Johns Hopkins University",
                "url": "https://www.niche.com/colleges/johns-hopkins-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-finance-and-financial-management-services-ms": {
        "summary": "Students describe Carey's MS in Finance as a STEM-designated, quant-heavy finance degree in Baltimore with access to Hopkins health-sector and DC-adjacent recruiting; praise includes small cohorts and applied analytics, with cautions that the Carey MBA/finance brand trails M7 peers outside health care and finance.",
        "themes": [
            {
                "label": "Quantitative finance",
                "sentiment": "positive",
                "detail": "STEM-designated curriculum emphasizes modeling, analytics, and valuation.",
            },
            {
                "label": "Health-sector ties",
                "sentiment": "positive",
                "detail": "Proximity to Hopkins Medicine creates distinctive health-finance recruiting.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Carey's smaller class sizes foster faculty access.",
            },
            {
                "label": "Brand vs. M7 peers",
                "sentiment": "mixed",
                "detail": "Less national finance brand cachet than top-10 MBA programs in NYC/Chicago.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private graduate tuition is steep relative to public finance programs.",
            },
        ],
        "sources": [
            {
                "label": "Carey \u2014 MS in Finance",
                "url": "https://carey.jhu.edu/programs/master-of-science/ms-finance",
            },
            {
                "label": "Poets&Quants \u2014 Carey Business School",
                "url": "https://poetsandquants.com/schools/carey-business-school-johns-hopkins-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-industrial-engineering-bs": {
        "summary": "Students describe JHU's undergraduate program in Industrial Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Industrial Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-industrial-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Industrial Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Industrial Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-materials-engineering-bs": {
        "summary": "Students describe JHU's undergraduate program in Materials Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Materials Engineering",
                "url": "https://engineering.jhu.edu/mse/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-materials-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Materials Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Materials Engineering",
                "url": "https://engineering.jhu.edu/mse/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-mechanical-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Mechanical Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Mechanical Engineering",
                "url": "https://me.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-mechatronics-robotics-and-automation-engineering-ms": {
        "summary": "Students describe JHU's robotics-focused engineering master's as leveraging the Laboratory for Computational Sensing and Robotics (LCSR) and Malone Center; praise includes cutting-edge autonomy research and APL partnerships, with cautions that the program is selective and research-oriented rather than coursework-only.",
        "themes": [
            {
                "label": "LCSR robotics",
                "sentiment": "positive",
                "detail": "World-renowned robotics lab anchors research and thesis work.",
            },
            {
                "label": "APL partnerships",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory connects students to defense and space robotics.",
            },
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Faculty-led projects in medical robotics and autonomous systems.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong quantitative and robotics background expected.",
            },
        ],
        "sources": [
            {
                "label": "LCSR \u2014 Johns Hopkins Robotics",
                "url": "https://lcsr.jhu.edu/",
            },
            {
                "label": "U.S. News \u2014 Best Engineering Schools",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-medicine-phd": {
        "summary": "Doctoral trainees describe Hopkins Medicine's biomedical PhD programs as intensely research-focused within the nation's top-ranked medical school; praise includes NIH funding depth and clinical collaboration, with cautions about competitive lab placement and the demanding Baltimore research culture.",
        "themes": [
            {
                "label": "Research intensity",
                "sentiment": "positive",
                "detail": "Hopkins Medicine leads NIH funding among U.S. medical schools.",
            },
            {
                "label": "Clinical collaboration",
                "sentiment": "positive",
                "detail": "Bench-to-bedside research with Johns Hopkins Hospital.",
            },
            {
                "label": "Lab placement",
                "sentiment": "caution",
                "detail": "Competitive admission to top labs requires strong prior research.",
            },
            {
                "label": "Demanding culture",
                "sentiment": "mixed",
                "detail": "High expectations and long hours are common in biomedical PhD training.",
            },
        ],
        "sources": [
            {
                "label": "Hopkins Medicine \u2014 Graduate Programs",
                "url": "https://www.hopkinsmedicine.org/som/education/graduate/",
            },
            {
                "label": "U.S. News \u2014 Best Medical Schools: Research",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/johns-hopkins-university-040101",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-public-health-bs": {
        "summary": "Undergraduates describe JHU's public health major \u2014 one of few BA/BS public-health paths at a top research university \u2014 as rigorous and pre-professional, with praise for Bloomberg School faculty access and Baltimore field sites, and cautions that intro courses can feel large and graduate-school planning is expected.",
        "themes": [
            {
                "label": "Rare undergrad major",
                "sentiment": "positive",
                "detail": "Few national universities offer a dedicated undergraduate public-health major.",
            },
            {
                "label": "Bloomberg School access",
                "sentiment": "positive",
                "detail": "Students take courses alongside the #1-ranked school of public health.",
            },
            {
                "label": "Field experience",
                "sentiment": "positive",
                "detail": "Baltimore health agencies and community sites provide applied learning.",
            },
            {
                "label": "Grad-school orientation",
                "sentiment": "mixed",
                "detail": "Many students pursue MPH/MD paths after graduation.",
            },
            {
                "label": "Course scale",
                "sentiment": "caution",
                "detail": "Popular gateway courses can feel large before students reach seminars.",
            },
        ],
        "sources": [
            {
                "label": "Bloomberg School \u2014 Public Health Studies",
                "url": "https://publichealth.jhu.edu/academics/public-health-studies",
            },
            {
                "label": "U.S. News \u2014 Best Public Health Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-bs": {
        "summary": "Students in JHU's direct-entry BSN describe a top-ranked nursing school with intensive clinical rotations at Johns Hopkins Hospital; praise includes faculty mentorship and research exposure, with cautions about demanding clinical schedules and East Baltimore housing logistics.",
        "themes": [
            {
                "label": "Top-ranked school",
                "sentiment": "positive",
                "detail": "U.S. News ranks JHU Nursing among the top 3 nationally.",
            },
            {
                "label": "Clinical rotations",
                "sentiment": "positive",
                "detail": "Johns Hopkins Hospital provides world-class patient-care training.",
            },
            {
                "label": "Research exposure",
                "sentiment": "positive",
                "detail": "Undergraduates engage with NIH-funded nursing research.",
            },
            {
                "label": "Clinical workload",
                "sentiment": "caution",
                "detail": "BSN clinical hours and coursework demand strong time management.",
            },
            {
                "label": "Urban setting",
                "sentiment": "mixed",
                "detail": "East Baltimore offers clinical richness but requires planning for housing.",
            },
        ],
        "sources": [
            {
                "label": "School of Nursing \u2014 BSN",
                "url": "https://nursing.jhu.edu/academics/bsn/",
            },
            {
                "label": "U.S. News \u2014 Best Nursing Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/johns-hopkins-university-040101",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-phd": {
        "summary": "Doctoral nursing students describe JHU's PhD in nursing as a research-intensive path for future faculty and health-policy scholars; praise includes mentorship from leading nurse scientists, with cautions about limited funding compared to STEM PhDs and the niche academic job market.",
        "themes": [
            {
                "label": "Nurse-scientist training",
                "sentiment": "positive",
                "detail": "Program prepares graduates for faculty and health-services research careers.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Top-ranked faculty in aging, community health, and health equity.",
            },
            {
                "label": "Research funding",
                "sentiment": "mixed",
                "detail": "Funding packages vary by mentor and grant portfolio.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track nursing faculty roles are competitive nationally.",
            },
        ],
        "sources": [
            {
                "label": "School of Nursing \u2014 PhD Program",
                "url": "https://nursing.jhu.edu/academics/phd/",
            },
            {
                "label": "U.S. News \u2014 Best Nursing Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/johns-hopkins-university-040101",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-systems-engineering-bs": {
        "summary": "Students describe JHU's undergraduate program in Systems Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Systems Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "jhu-systems-engineering-ms": {
        "summary": "Students describe JHU's graduate program in in Systems Engineering within the Whiting School as research-oriented engineering at a top-10 national university; praise includes APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions about demanding coursework and a smaller department than large state engineering schools.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Whiting emphasizes faculty-led research from undergrad through master's.",
            },
            {
                "label": "APL & medicine ties",
                "sentiment": "positive",
                "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects.",
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "LCSR and design courses provide hands-on engineering experience.",
            },
            {
                "label": "Program size",
                "sentiment": "mixed",
                "detail": "Smaller departments than large public engineering colleges.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "JHU engineering coursework is consistently described as rigorous.",
            },
        ],
        "sources": [
            {
                "label": "Johns Hopkins \u2014 Systems Engineering",
                "url": "https://engineering.jhu.edu/case/",
            },
            {
                "label": "U.S. News \u2014 Johns Hopkins University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
