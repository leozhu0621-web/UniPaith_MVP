"""University of California, Berkeley external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``berkeleyprof6`` migration to merge
``DEPTH_REVIEWS`` into ``berkeley_profile._REVIEWS_BY_SLUG`` for 59
remaining coverable programs.
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "berkeley-public-health-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate public-health major as an interdisciplinary L&S program drawing on epidemiology, biostatistics, and health policy through the School of Public Health; praise includes access to top-ranked faculty and California agency internships, with cautions that the major is newer than peer pre-med tracks, lower-division prerequisites span multiple departments, and upper-division public-health courses can fill quickly.",
        "themes": [
            {
                "label": "Interdisciplinary design",
                "sentiment": "positive",
                "detail": "Combines population health, statistics, and policy across L&S and Public Health."
            },
            {
                "label": "Faculty & research access",
                "sentiment": "positive",
                "detail": "Students connect to epidemiology and environmental-health labs on campus."
            },
            {
                "label": "California internships",
                "sentiment": "positive",
                "detail": "Bay Area county and state agencies recruit Berkeley public-health undergraduates."
            },
            {
                "label": "Prerequisite navigation",
                "sentiment": "caution",
                "detail": "Students coordinate biology, statistics, and public-health requirements across units."
            },
            {
                "label": "Course capacity",
                "sentiment": "caution",
                "detail": "Popular upper-division public-health electives can be competitive to access."
            }
        ],
        "sources": [
            {
                "label": "UC Berkeley Public Health \u2014 U.S. News No. 6 (2026)",
                "url": "https://publichealth.berkeley.edu/articles/news/ucbph-surges-to-6-in-us-news-rankings"
            },
            {
                "label": "Niche \u2014 UC Berkeley School of Public Health",
                "url": "https://www.niche.com/graduate-schools/uc-berkeley-school-of-public-health/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-architecture-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate architecture program within CED as a design-intensive path with sustainability and social-equity emphasis \u2014 QS ranks Berkeley among the top global architecture programs \u2014 praising studio culture and interdisciplinary CED community; common cautions are long studio hours, limited studio seats, and that the B.A. in Architecture is a pre-professional degree requiring further study for licensure.",
        "themes": [
            {
                "label": "Global architecture standing",
                "sentiment": "positive",
                "detail": "QS ranks Berkeley among the top public architecture programs worldwide."
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and crits anchor a hands-on, project-based curriculum."
            },
            {
                "label": "Sustainability focus",
                "sentiment": "positive",
                "detail": "CED emphasizes climate solutions and equitable design in studio work."
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Long studio hours and intensive crit schedules are recurring themes."
            },
            {
                "label": "Pre-professional path",
                "sentiment": "mixed",
                "detail": "The B.A. requires further professional study for architecture licensure."
            }
        ],
        "sources": [
            {
                "label": "CED at UC Berkeley \u2014 Architecture",
                "url": "https://ced.berkeley.edu/architecture"
            },
            {
                "label": "QS \u2014 Architecture & Built Environment",
                "url": "https://www.topuniversities.com/university-subject-rankings/architecture-built-environment"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-agricultural-business-and-management-ms": {
        "summary": "Graduate applicants describe Berkeley ARE's M.S. in Agricultural and Resource Economics as a quantitatively rigorous applied-economics degree in food, environmental, and development policy within Rausser College; students value faculty expertise in econometrics and California agribusiness, with cautions about self-funded tuition for terminal master's students and a niche hiring market outside food and environmental policy.",
        "themes": [
            {
                "label": "Applied economics depth",
                "sentiment": "positive",
                "detail": "Coursework spans econometrics, environmental economics, and development."
            },
            {
                "label": "Rausser faculty",
                "sentiment": "positive",
                "detail": "ARE faculty lead research in food systems and resource policy."
            },
            {
                "label": "Policy & industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter agribusiness, consulting, and government analytics."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Niche market",
                "sentiment": "mixed",
                "detail": "Roles concentrate in food, environment, and policy rather than general finance."
            }
        ],
        "sources": [
            {
                "label": "Rausser College \u2014 ARE graduate programs",
                "url": "https://are.berkeley.edu/graduate"
            },
            {
                "label": "U.S. News \u2014 UC Berkeley",
                "url": "https://www.usnews.com/best-colleges/university-of-california-berkeley-1312"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-agricultural-business-and-management-phd": {
        "summary": "Doctoral students describe Berkeley ARE's Ph.D. as a research degree producing economists in environmental, agricultural, and development economics; praise centers on faculty mentorship in econometrics and experimental methods, with cautions about competitive admission, five-plus-year dissertation timelines, and academic job markets favoring specialized applied-economics placements.",
        "themes": [
            {
                "label": "Econometrics & policy research",
                "sentiment": "positive",
                "detail": "Doctoral training emphasizes rigorous empirical methods."
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "ARE faculty mentor dissertations in food, environment, and trade."
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts and policy research institutes."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Rausser College \u2014 ARE graduate programs",
                "url": "https://are.berkeley.edu/graduate"
            },
            {
                "label": "U.S. News \u2014 UC Berkeley",
                "url": "https://www.usnews.com/best-colleges/university-of-california-berkeley-1312"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-architecture-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in Architecture as a research-oriented master's within CED spanning building science, history, and design research; students praise interdisciplinary faculty and sustainability labs, with cautions about self-funded tuition for terminal master's students and that the degree differs from the professional M.Arch path to licensure.",
        "themes": [
            {
                "label": "Research-oriented design",
                "sentiment": "positive",
                "detail": "Students pursue thesis research in building science and design history."
            },
            {
                "label": "CED interdisciplinary community",
                "sentiment": "positive",
                "detail": "Graduate students collaborate across architecture, planning, and landscape."
            },
            {
                "label": "Sustainability labs",
                "sentiment": "positive",
                "detail": "Research centers connect students to climate and equity-focused projects."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Not a licensure path",
                "sentiment": "mixed",
                "detail": "The M.S. differs from the professional M.Arch for architecture licensure."
            }
        ],
        "sources": [
            {
                "label": "CED at UC Berkeley \u2014 Architecture",
                "url": "https://ced.berkeley.edu/architecture"
            },
            {
                "label": "QS \u2014 Architecture & Built Environment",
                "url": "https://www.topuniversities.com/university-subject-rankings/architecture-built-environment"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-architecture-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in Architecture as a research doctorate in history, theory, and building science within CED; praise includes access to leading design-research faculty and the Environmental Design Archives, with cautions about competitive admission, long dissertation timelines, and academic placements concentrated in research universities.",
        "themes": [
            {
                "label": "Design research depth",
                "sentiment": "positive",
                "detail": "Doctoral work spans architectural history, theory, and building science."
            },
            {
                "label": "Faculty & archives",
                "sentiment": "positive",
                "detail": "CED faculty and the Environmental Design Archives support dissertation research."
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts in architecture and environmental design."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "CED at UC Berkeley \u2014 Architecture",
                "url": "https://ced.berkeley.edu/architecture"
            },
            {
                "label": "QS \u2014 Architecture & Built Environment",
                "url": "https://www.topuniversities.com/university-subject-rankings/architecture-built-environment"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-landscape-architecture-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate landscape architecture program within CED as a design-intensive path connecting ecology, planning, and the built environment; praise includes studio access and California climate-adaptation research, with cautions about long studio hours, limited enrollment, and that the degree requires further study for professional licensure.",
        "themes": [
            {
                "label": "Ecology & design",
                "sentiment": "positive",
                "detail": "Curriculum connects landscape ecology with design studios."
            },
            {
                "label": "CED studio culture",
                "sentiment": "positive",
                "detail": "Small cohorts work in interdisciplinary design studios."
            },
            {
                "label": "Climate adaptation",
                "sentiment": "positive",
                "detail": "Faculty research addresses drought, fire, and urban green infrastructure."
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Long studio hours and intensive project deadlines are common."
            },
            {
                "label": "Professional licensure",
                "sentiment": "mixed",
                "detail": "The undergraduate degree requires further study for licensure."
            }
        ],
        "sources": [
            {
                "label": "CED at UC Berkeley \u2014 Landscape Architecture",
                "url": "https://ced.berkeley.edu/landscape-architecture-environmental-planning"
            },
            {
                "label": "Niche \u2014 University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-landscape-architecture-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in Landscape Architecture as a research master's in environmental planning and landscape ecology within CED; students value faculty expertise in climate resilience and urban greening, with cautions about self-funded tuition for terminal master's students and a smaller cohort than the professional MLA program.",
        "themes": [
            {
                "label": "Environmental planning",
                "sentiment": "positive",
                "detail": "Research spans urban ecology, hydrology, and green infrastructure."
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "CED faculty lead climate-resilience and equity-focused research."
            },
            {
                "label": "Bay Area practice ties",
                "sentiment": "positive",
                "detail": "Graduates enter planning firms and public-agency roles."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Smaller cohort",
                "sentiment": "mixed",
                "detail": "The research M.S. enrolls fewer students than the professional MLA."
            }
        ],
        "sources": [
            {
                "label": "CED at UC Berkeley \u2014 Landscape Architecture",
                "url": "https://ced.berkeley.edu/landscape-architecture-environmental-planning"
            },
            {
                "label": "Niche \u2014 University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-landscape-architecture-prof": {
        "summary": "Students and third-party guides describe Berkeley's Master of Landscape Architecture as a top public professional program within CED emphasizing ecology, equity, and climate adaptation; praise includes design-build studios and Bay Area practice connections, with cautions about intense studio workloads, in-state vs. out-of-state tuition gaps, and competitive portfolio admission.",
        "themes": [
            {
                "label": "Professional design training",
                "sentiment": "positive",
                "detail": "Studio sequence prepares graduates for landscape architecture licensure."
            },
            {
                "label": "Climate & equity focus",
                "sentiment": "positive",
                "detail": "CED emphasizes drought adaptation and equitable public landscapes."
            },
            {
                "label": "Design-build studios",
                "sentiment": "positive",
                "detail": "Hands-on studios connect students to community design projects."
            },
            {
                "label": "Studio intensity",
                "sentiment": "caution",
                "detail": "Long studio hours and crit-heavy semesters are recurring themes."
            },
            {
                "label": "Tuition gap",
                "sentiment": "mixed",
                "detail": "Out-of-state tuition is substantially higher than in-state rates."
            }
        ],
        "sources": [
            {
                "label": "CED at UC Berkeley \u2014 Landscape Architecture",
                "url": "https://ced.berkeley.edu/landscape-architecture-environmental-planning"
            },
            {
                "label": "Niche \u2014 University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-journalism-ms": {
        "summary": "Students and third-party guides describe Berkeley's two-year M.J. as a rigorous investigative and multimedia journalism program \u2014 U.S. News historically ranks it among the top graduate journalism schools \u2014 praising faculty practitioners, the Investigative Reporting Program, and Bay Area media ties; common cautions are intense deadline pressure, limited class size, and a challenging journalism job market outside major metros.",
        "themes": [
            {
                "label": "Investigative depth",
                "sentiment": "positive",
                "detail": "The Investigative Reporting Program anchors long-form accountability journalism."
            },
            {
                "label": "Practitioner faculty",
                "sentiment": "positive",
                "detail": "Working journalists and editors teach skills-focused seminars."
            },
            {
                "label": "Bay Area media ties",
                "sentiment": "positive",
                "detail": "Internships connect students to regional and national newsrooms."
            },
            {
                "label": "Deadline intensity",
                "sentiment": "caution",
                "detail": "Daily reporting assignments and editing cycles are demanding."
            },
            {
                "label": "Job market",
                "sentiment": "mixed",
                "detail": "National newsroom hiring remains competitive beyond major metros."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Journalism \u2014 Graduate program",
                "url": "https://journalism.berkeley.edu/programs/masters/"
            },
            {
                "label": "Niche \u2014 University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-computer-science-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in Computer Science as a selective research-oriented degree within CDSS/EECS \u2014 U.S. News ranks Berkeley CS No. 2 nationally (2026) \u2014 praising faculty depth and Bay Area industry ties; common cautions are that most admitted students pursue the Ph.D. track, terminal M.S. seats are limited and often self-funded, and coursework is extremely demanding.",
        "themes": [
            {
                "label": "Elite CS standing",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley graduate CS No. 2 nationally (2026)."
            },
            {
                "label": "Faculty & research labs",
                "sentiment": "positive",
                "detail": "Students access leading AI, systems, and theory research groups."
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates place into Bay Area tech firms and startups."
            },
            {
                "label": "Limited terminal MS",
                "sentiment": "caution",
                "detail": "Most seats favor Ph.D.-bound students; terminal M.S. admission is selective."
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Terminal master's students often fund tuition without department support."
            }
        ],
        "sources": [
            {
                "label": "CDSS at UC Berkeley \u2014 U.S. News CS rankings (2026)",
                "url": "https://cdss.berkeley.edu/news/uc-berkeley-ranked-1-data-science-and-2-computer-science-2026"
            },
            {
                "label": "U.S. News \u2014 Best Computer Science Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-computer-science-phd": {
        "summary": "Doctoral students describe Berkeley CS as a top-tier research doctorate within CDSS/EECS \u2014 U.S. News ranks Berkeley CS No. 2 nationally (2026) \u2014 praising Turing Award-winning faculty and pioneering AI/systems labs; common cautions are extreme selectivity, long time-to-degree, and intense research expectations.",
        "themes": [
            {
                "label": "World-class CS research",
                "sentiment": "positive",
                "detail": "Doctoral students join leading labs in AI, systems, security, and theory."
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Faculty include Turing Award winners and National Academy members."
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts, industry R&D labs, and startups."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with a small incoming cohort."
            },
            {
                "label": "Research intensity",
                "sentiment": "caution",
                "detail": "The dissertation path demands sustained, publication-oriented work."
            }
        ],
        "sources": [
            {
                "label": "CDSS at UC Berkeley \u2014 U.S. News CS rankings (2026)",
                "url": "https://cdss.berkeley.edu/news/uc-berkeley-ranked-1-data-science-and-2-computer-science-2026"
            },
            {
                "label": "U.S. News \u2014 Best Computer Science Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-engineering-general-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in engineering as a research-oriented master's within the College of Engineering \u2014 Berkeley Engineering ranks among the top three nationally \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Elite engineering college",
                "sentiment": "positive",
                "detail": "Berkeley Engineering ranks among the top three nationally."
            },
            {
                "label": "Cross-department access",
                "sentiment": "positive",
                "detail": "Graduate students take courses across all engineering departments."
            },
            {
                "label": "Research & industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter academia, national labs, and Bay Area industry."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students often fund tuition without department support."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Engineering",
                "url": "https://engineering.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-engineering-general-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in engineering as a top-tier research doctorate within the College of Engineering \u2014 Berkeley Engineering ranks among the top three nationally \u2014 praising funded research training and faculty mentorship; cautions include competitive admission and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Elite engineering college",
                "sentiment": "positive",
                "detail": "Berkeley Engineering ranks among the top three nationally."
            },
            {
                "label": "Cross-department access",
                "sentiment": "positive",
                "detail": "Graduate students take courses across all engineering departments."
            },
            {
                "label": "Research & industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter academia, national labs, and Bay Area industry."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Engineering",
                "url": "https://engineering.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-engineering-general-prof": {
        "summary": "Students describe Berkeley's Master of Engineering in engineering as a one-year professional degree combining advanced coursework with a capstone design project \u2014 Berkeley Engineering ranks among the top three nationally \u2014 praising industry-relevant skills and Bay Area recruiting; common cautions are self-funded tuition, an intensive one-year schedule, and that the MEng differs from a research-focused M.S.",
        "themes": [
            {
                "label": "Elite engineering college",
                "sentiment": "positive",
                "detail": "Berkeley Engineering ranks among the top three nationally."
            },
            {
                "label": "Cross-department access",
                "sentiment": "positive",
                "detail": "Graduate students take courses across all engineering departments."
            },
            {
                "label": "Research & industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter academia, national labs, and Bay Area industry."
            },
            {
                "label": "Intensive schedule",
                "sentiment": "caution",
                "detail": "The one-year professional curriculum is fast-paced and project-heavy."
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "MEng students typically fund tuition without research assistantships."
            },
            {
                "label": "Distinct from M.S.",
                "sentiment": "mixed",
                "detail": "The professional MEng differs from the research-oriented M.S. path."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Engineering",
                "url": "https://engineering.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-agricultural-engineering-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate biological and agricultural engineering program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley biological systems engineering connects engineering and natural resources \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Bio-ag engineering",
                "sentiment": "positive",
                "detail": "Program connects mechanical design with agricultural and environmental systems."
            },
            {
                "label": "Rausser ties",
                "sentiment": "positive",
                "detail": "Students collaborate with natural-resources and ARE faculty."
            },
            {
                "label": "Sustainability focus",
                "sentiment": "positive",
                "detail": "Research addresses water, energy, and food-system engineering."
            },
            {
                "label": "Smaller program",
                "sentiment": "mixed",
                "detail": "Biological systems engineering enrolls a smaller cohort than core departments."
            },
            {
                "label": "Cross-college requirements",
                "sentiment": "caution",
                "detail": "Students coordinate engineering and natural-resources coursework."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Biological And Agricultural Engineering",
                "url": "https://engineering.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-biomedical-medical-engineering-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate bioengineering program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley-UCSF bioengineering ranks among top biomedical programs \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Berkeley-UCSF partnership",
                "sentiment": "positive",
                "detail": "Joint bioengineering program connects engineering and medical research."
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Students access labs in medical devices, imaging, and synthetic biology."
            },
            {
                "label": "Biotech placement",
                "sentiment": "positive",
                "detail": "Graduates enter medical-device and biotech firms in the Bay Area."
            },
            {
                "label": "Cross-campus coordination",
                "sentiment": "caution",
                "detail": "Some courses and labs require travel to UCSF."
            },
            {
                "label": "Selective admission",
                "sentiment": "mixed",
                "detail": "Bioengineering is among the most competitive engineering majors."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Bioengineering",
                "url": "https://bioeng.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-biomedical-medical-engineering-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in bioengineering as a research-oriented master's within the College of Engineering \u2014 Berkeley-UCSF bioengineering ranks among top biomedical programs \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Berkeley-UCSF partnership",
                "sentiment": "positive",
                "detail": "Joint bioengineering program connects engineering and medical research."
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Students access labs in medical devices, imaging, and synthetic biology."
            },
            {
                "label": "Biotech placement",
                "sentiment": "positive",
                "detail": "Graduates enter medical-device and biotech firms in the Bay Area."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Cross-campus coordination",
                "sentiment": "caution",
                "detail": "Some courses and labs require travel to UCSF."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Bioengineering",
                "url": "https://bioeng.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-biomedical-medical-engineering-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in bioengineering as a top-tier research doctorate within the College of Engineering \u2014 Berkeley-UCSF bioengineering ranks among top biomedical programs \u2014 praising funded research training and faculty mentorship; cautions include competitive admission and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Berkeley-UCSF partnership",
                "sentiment": "positive",
                "detail": "Joint bioengineering program connects engineering and medical research."
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Students access labs in medical devices, imaging, and synthetic biology."
            },
            {
                "label": "Biotech placement",
                "sentiment": "positive",
                "detail": "Graduates enter medical-device and biotech firms in the Bay Area."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Bioengineering",
                "url": "https://bioeng.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-biomedical-medical-engineering-prof": {
        "summary": "Students describe Berkeley's Master of Engineering in bioengineering as a one-year professional degree combining advanced coursework with a capstone design project \u2014 Berkeley-UCSF bioengineering ranks among top biomedical programs \u2014 praising industry-relevant skills and Bay Area recruiting; common cautions are self-funded tuition, an intensive one-year schedule, and that the MEng differs from a research-focused M.S.",
        "themes": [
            {
                "label": "Berkeley-UCSF partnership",
                "sentiment": "positive",
                "detail": "Joint bioengineering program connects engineering and medical research."
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Students access labs in medical devices, imaging, and synthetic biology."
            },
            {
                "label": "Biotech placement",
                "sentiment": "positive",
                "detail": "Graduates enter medical-device and biotech firms in the Bay Area."
            },
            {
                "label": "Intensive schedule",
                "sentiment": "caution",
                "detail": "The one-year professional curriculum is fast-paced and project-heavy."
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "MEng students typically fund tuition without research assistantships."
            },
            {
                "label": "Distinct from M.S.",
                "sentiment": "mixed",
                "detail": "The professional MEng differs from the research-oriented M.S. path."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Bioengineering",
                "url": "https://bioeng.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-chemical-engineering-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in chemical engineering as a research-oriented master's within the College of Engineering \u2014 U.S. News ranks Berkeley chemical engineering No. 3 nationally (2026) \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Top-three ChemE",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley chemical engineering No. 3 nationally (2026)."
            },
            {
                "label": "Biotech ties",
                "sentiment": "positive",
                "detail": "Strong connections to Bay Area biotech and energy research."
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Curriculum spans transport, thermodynamics, and reactor design."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Intense workload",
                "sentiment": "mixed",
                "detail": "Long problem sets and a fast semester system are common."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Chemical Engineering",
                "url": "https://chemistry.berkeley.edu/cbe"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-chemical-engineering-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in chemical engineering as a top-tier research doctorate within the College of Engineering \u2014 U.S. News ranks Berkeley chemical engineering No. 3 nationally (2026) \u2014 praising funded research training and faculty mentorship; cautions include competitive admission and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Top-three ChemE",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley chemical engineering No. 3 nationally (2026)."
            },
            {
                "label": "Biotech ties",
                "sentiment": "positive",
                "detail": "Strong connections to Bay Area biotech and energy research."
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Curriculum spans transport, thermodynamics, and reactor design."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Chemical Engineering",
                "url": "https://chemistry.berkeley.edu/cbe"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-civil-engineering-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate civil engineering program within the College of Engineering as rigorous and well-regarded \u2014 U.S. News ranks Berkeley civil engineering among the top three nationally \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Top civil program",
                "sentiment": "positive",
                "detail": "Berkeley CE ranks among the top three nationally in U.S. News surveys."
            },
            {
                "label": "Infrastructure & earthquake",
                "sentiment": "positive",
                "detail": "Faculty lead research in seismic design and sustainable infrastructure."
            },
            {
                "label": "Public-sector placement",
                "sentiment": "positive",
                "detail": "Graduates enter transportation, water, and structural engineering firms."
            },
            {
                "label": "Quantitative core",
                "sentiment": "caution",
                "detail": "Structural analysis and fluid mechanics requirements are mathematically demanding."
            },
            {
                "label": "Lab capacity",
                "sentiment": "caution",
                "detail": "Upper-division lab sections can be competitive to access."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Civil Engineering",
                "url": "https://ce.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-civil-engineering-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in civil engineering as a research-oriented master's within the College of Engineering \u2014 U.S. News ranks Berkeley civil engineering among the top three nationally \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Top civil program",
                "sentiment": "positive",
                "detail": "Berkeley CE ranks among the top three nationally in U.S. News surveys."
            },
            {
                "label": "Infrastructure & earthquake",
                "sentiment": "positive",
                "detail": "Faculty lead research in seismic design and sustainable infrastructure."
            },
            {
                "label": "Public-sector placement",
                "sentiment": "positive",
                "detail": "Graduates enter transportation, water, and structural engineering firms."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Quantitative core",
                "sentiment": "caution",
                "detail": "Structural analysis and fluid mechanics requirements are mathematically demanding."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Civil Engineering",
                "url": "https://ce.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-civil-engineering-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in civil engineering as a top-tier research doctorate within the College of Engineering \u2014 U.S. News ranks Berkeley civil engineering among the top three nationally \u2014 praising funded research training and faculty mentorship; cautions include competitive admission and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Top civil program",
                "sentiment": "positive",
                "detail": "Berkeley CE ranks among the top three nationally in U.S. News surveys."
            },
            {
                "label": "Infrastructure & earthquake",
                "sentiment": "positive",
                "detail": "Faculty lead research in seismic design and sustainable infrastructure."
            },
            {
                "label": "Public-sector placement",
                "sentiment": "positive",
                "detail": "Graduates enter transportation, water, and structural engineering firms."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Civil Engineering",
                "url": "https://ce.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-civil-engineering-prof": {
        "summary": "Students describe Berkeley's Master of Engineering in civil engineering as a one-year professional degree combining advanced coursework with a capstone design project \u2014 U.S. News ranks Berkeley civil engineering among the top three nationally \u2014 praising industry-relevant skills and Bay Area recruiting; common cautions are self-funded tuition, an intensive one-year schedule, and that the MEng differs from a research-focused M.S.",
        "themes": [
            {
                "label": "Top civil program",
                "sentiment": "positive",
                "detail": "Berkeley CE ranks among the top three nationally in U.S. News surveys."
            },
            {
                "label": "Infrastructure & earthquake",
                "sentiment": "positive",
                "detail": "Faculty lead research in seismic design and sustainable infrastructure."
            },
            {
                "label": "Public-sector placement",
                "sentiment": "positive",
                "detail": "Graduates enter transportation, water, and structural engineering firms."
            },
            {
                "label": "Intensive schedule",
                "sentiment": "caution",
                "detail": "The one-year professional curriculum is fast-paced and project-heavy."
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "MEng students typically fund tuition without research assistantships."
            },
            {
                "label": "Distinct from M.S.",
                "sentiment": "mixed",
                "detail": "The professional MEng differs from the research-oriented M.S. path."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Civil Engineering",
                "url": "https://ce.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in electrical engineering and computer sciences as a research-oriented master's within the College of Engineering \u2014 U.S. News ranks Berkeley EECS among the top three nationally \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Elite EECS standing",
                "sentiment": "positive",
                "detail": "Berkeley EECS ranks among the top three engineering programs nationally."
            },
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Students access leading labs in circuits, communications, and power systems."
            },
            {
                "label": "Bay Area placement",
                "sentiment": "positive",
                "detail": "Graduates place into semiconductor, energy, and tech firms."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Competitive environment",
                "sentiment": "caution",
                "detail": "EECS is among the most selective and demanding majors on campus."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Electrical Engineering And Computer Sciences",
                "url": "https://eecs.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-electrical-electronics-and-communications-engineering-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in electrical engineering and computer sciences as a top-tier research doctorate within the College of Engineering \u2014 U.S. News ranks Berkeley EECS among the top three nationally \u2014 praising funded research training and faculty mentorship; cautions include competitive admission and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Elite EECS standing",
                "sentiment": "positive",
                "detail": "Berkeley EECS ranks among the top three engineering programs nationally."
            },
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Students access leading labs in circuits, communications, and power systems."
            },
            {
                "label": "Bay Area placement",
                "sentiment": "positive",
                "detail": "Graduates place into semiconductor, energy, and tech firms."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Electrical Engineering And Computer Sciences",
                "url": "https://eecs.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-electrical-electronics-and-communications-engineering-prof": {
        "summary": "Students describe Berkeley's Master of Engineering in electrical engineering and computer sciences as a one-year professional degree combining advanced coursework with a capstone design project \u2014 U.S. News ranks Berkeley EECS among the top three nationally \u2014 praising industry-relevant skills and Bay Area recruiting; common cautions are self-funded tuition, an intensive one-year schedule, and that the MEng differs from a research-focused M.S.",
        "themes": [
            {
                "label": "Elite EECS standing",
                "sentiment": "positive",
                "detail": "Berkeley EECS ranks among the top three engineering programs nationally."
            },
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Students access leading labs in circuits, communications, and power systems."
            },
            {
                "label": "Bay Area placement",
                "sentiment": "positive",
                "detail": "Graduates place into semiconductor, energy, and tech firms."
            },
            {
                "label": "Intensive schedule",
                "sentiment": "caution",
                "detail": "The one-year professional curriculum is fast-paced and project-heavy."
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "MEng students typically fund tuition without research assistantships."
            },
            {
                "label": "Distinct from M.S.",
                "sentiment": "mixed",
                "detail": "The professional MEng differs from the research-oriented M.S. path."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Electrical Engineering And Computer Sciences",
                "url": "https://eecs.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-engineering-physics-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate engineering physics program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley engineering physics bridges physics and engineering within the top-three college \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Physics-engineering bridge",
                "sentiment": "positive",
                "detail": "Curriculum combines advanced physics with engineering applications."
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Students join labs in materials, plasma, and quantum systems."
            },
            {
                "label": "Graduate-school prep",
                "sentiment": "positive",
                "detail": "Many graduates continue to top Ph.D. programs in physics and engineering."
            },
            {
                "label": "Heavy math & physics",
                "sentiment": "caution",
                "detail": "Advanced physics and mathematics requirements are demanding."
            },
            {
                "label": "Smaller major",
                "sentiment": "mixed",
                "detail": "Engineering physics enrolls a smaller cohort than EECS or ME."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Engineering Physics",
                "url": "https://engineering.berkeley.edu/academics/undergraduate-programs/majors/engineering-physics/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-engineering-science-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate engineering science program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley engineering science offers a flexible interdisciplinary engineering path \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Interdisciplinary design",
                "sentiment": "positive",
                "detail": "Students tailor coursework across engineering and science departments."
            },
            {
                "label": "Research flexibility",
                "sentiment": "positive",
                "detail": "The major supports thesis work in emerging interdisciplinary fields."
            },
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "Housed within U.S. News' No. 3 undergraduate engineering college."
            },
            {
                "label": "Self-designed path",
                "sentiment": "caution",
                "detail": "Students must proactively plan course sequences across departments."
            },
            {
                "label": "Advising demands",
                "sentiment": "caution",
                "detail": "Navigating requirements across units requires careful planning."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Engineering Science",
                "url": "https://engineering.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-environmental-environmental-health-engineering-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate environmental engineering program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley environmental engineering ranks among the top programs nationally \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Environmental leadership",
                "sentiment": "positive",
                "detail": "Faculty lead research in water quality, air pollution, and climate adaptation."
            },
            {
                "label": "Interdisciplinary CEE",
                "sentiment": "positive",
                "detail": "Program connects civil, environmental, and public-health research."
            },
            {
                "label": "Policy & industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter consulting, utilities, and environmental agencies."
            },
            {
                "label": "Broad prerequisites",
                "sentiment": "mixed",
                "detail": "Students coordinate chemistry, biology, and engineering requirements."
            },
            {
                "label": "Project workload",
                "sentiment": "caution",
                "detail": "Design projects and field studies add scheduling demands."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Environmental Engineering",
                "url": "https://ce.berkeley.edu/environmental-engineering"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-mechanical-engineering-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in mechanical engineering as a research-oriented master's within the College of Engineering \u2014 U.S. News ranks Berkeley undergraduate ME No. 2 nationally (2026) \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Top-ranked ME",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley mechanical engineering among the top three nationally."
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "Students access robotics, energy, and manufacturing research labs."
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates enter aerospace, automotive, and Bay Area tech roles."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Heavy core load",
                "sentiment": "caution",
                "detail": "Shared engineering physics and math requirements create a demanding first two years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Mechanical Engineering",
                "url": "https://me.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-mechanical-engineering-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in mechanical engineering as a top-tier research doctorate within the College of Engineering \u2014 U.S. News ranks Berkeley undergraduate ME No. 2 nationally (2026) \u2014 praising funded research training and faculty mentorship; cautions include competitive admission and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Top-ranked ME",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley mechanical engineering among the top three nationally."
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "Students access robotics, energy, and manufacturing research labs."
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates enter aerospace, automotive, and Bay Area tech roles."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Mechanical Engineering",
                "url": "https://me.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-mechanical-engineering-prof": {
        "summary": "Students describe Berkeley's Master of Engineering in mechanical engineering as a one-year professional degree combining advanced coursework with a capstone design project \u2014 U.S. News ranks Berkeley undergraduate ME No. 2 nationally (2026) \u2014 praising industry-relevant skills and Bay Area recruiting; common cautions are self-funded tuition, an intensive one-year schedule, and that the MEng differs from a research-focused M.S.",
        "themes": [
            {
                "label": "Top-ranked ME",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley mechanical engineering among the top three nationally."
            },
            {
                "label": "Design & robotics",
                "sentiment": "positive",
                "detail": "Students access robotics, energy, and manufacturing research labs."
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates enter aerospace, automotive, and Bay Area tech roles."
            },
            {
                "label": "Intensive schedule",
                "sentiment": "caution",
                "detail": "The one-year professional curriculum is fast-paced and project-heavy."
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "MEng students typically fund tuition without research assistantships."
            },
            {
                "label": "Distinct from M.S.",
                "sentiment": "mixed",
                "detail": "The professional MEng differs from the research-oriented M.S. path."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Mechanical Engineering",
                "url": "https://me.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-nuclear-engineering-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate nuclear engineering program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley nuclear engineering is among the few U.S. programs with operating-reactor access \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Reactor access",
                "sentiment": "positive",
                "detail": "Berkeley operates a research reactor for hands-on neutron-science training."
            },
            {
                "label": "Energy & security research",
                "sentiment": "positive",
                "detail": "Faculty lead work in nuclear energy, nonproliferation, and radiation detection."
            },
            {
                "label": "National-lab ties",
                "sentiment": "positive",
                "detail": "Graduates enter national laboratories and energy agencies."
            },
            {
                "label": "Specialized field",
                "sentiment": "mixed",
                "detail": "Career paths concentrate in energy, defense, and national labs."
            },
            {
                "label": "Smaller cohort",
                "sentiment": "mixed",
                "detail": "Nuclear engineering enrolls a smaller cohort than larger departments."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Nuclear Engineering",
                "url": "https://nuc.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-nuclear-engineering-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in nuclear engineering as a research-oriented master's within the College of Engineering \u2014 Berkeley nuclear engineering is among the few U.S. programs with operating-reactor access \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Reactor access",
                "sentiment": "positive",
                "detail": "Berkeley operates a research reactor for hands-on neutron-science training."
            },
            {
                "label": "Energy & security research",
                "sentiment": "positive",
                "detail": "Faculty lead work in nuclear energy, nonproliferation, and radiation detection."
            },
            {
                "label": "National-lab ties",
                "sentiment": "positive",
                "detail": "Graduates enter national laboratories and energy agencies."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Specialized field",
                "sentiment": "mixed",
                "detail": "Career paths concentrate in energy, defense, and national labs."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Nuclear Engineering",
                "url": "https://nuc.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-nuclear-engineering-phd": {
        "summary": "Doctoral students describe Berkeley's Ph.D. in nuclear engineering as a top-tier research doctorate within the College of Engineering \u2014 Berkeley nuclear engineering is among the few U.S. programs with operating-reactor access \u2014 praising funded research training and faculty mentorship; cautions include competitive admission and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Reactor access",
                "sentiment": "positive",
                "detail": "Berkeley operates a research reactor for hands-on neutron-science training."
            },
            {
                "label": "Energy & security research",
                "sentiment": "positive",
                "detail": "Faculty lead work in nuclear energy, nonproliferation, and radiation detection."
            },
            {
                "label": "National-lab ties",
                "sentiment": "positive",
                "detail": "Graduates enter national laboratories and energy agencies."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Nuclear Engineering",
                "url": "https://nuc.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-nuclear-engineering-prof": {
        "summary": "Students describe Berkeley's Master of Engineering in nuclear engineering as a one-year professional degree combining advanced coursework with a capstone design project \u2014 Berkeley nuclear engineering is among the few U.S. programs with operating-reactor access \u2014 praising industry-relevant skills and Bay Area recruiting; common cautions are self-funded tuition, an intensive one-year schedule, and that the MEng differs from a research-focused M.S.",
        "themes": [
            {
                "label": "Reactor access",
                "sentiment": "positive",
                "detail": "Berkeley operates a research reactor for hands-on neutron-science training."
            },
            {
                "label": "Energy & security research",
                "sentiment": "positive",
                "detail": "Faculty lead work in nuclear energy, nonproliferation, and radiation detection."
            },
            {
                "label": "National-lab ties",
                "sentiment": "positive",
                "detail": "Graduates enter national laboratories and energy agencies."
            },
            {
                "label": "Intensive schedule",
                "sentiment": "caution",
                "detail": "The one-year professional curriculum is fast-paced and project-heavy."
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "MEng students typically fund tuition without research assistantships."
            },
            {
                "label": "Distinct from M.S.",
                "sentiment": "mixed",
                "detail": "The professional MEng differs from the research-oriented M.S. path."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Nuclear Engineering",
                "url": "https://nuc.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-manufacturing-engineering-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate mechanical engineering (manufacturing) program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley ME offers manufacturing and design within a top-three department \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Manufacturing & design",
                "sentiment": "positive",
                "detail": "Coursework spans CAD, automation, and production systems within ME."
            },
            {
                "label": "Top ME department",
                "sentiment": "positive",
                "detail": "Housed within U.S. News' No. 2 mechanical engineering program."
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates enter aerospace, automotive, and advanced-manufacturing roles."
            },
            {
                "label": "Shared ME core",
                "sentiment": "mixed",
                "detail": "Students complete the same demanding physics and math core as all ME majors."
            },
            {
                "label": "Specialized track",
                "sentiment": "mixed",
                "detail": "Manufacturing is a narrower focus than general mechanical engineering."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Mechanical Engineering (Manufacturing)",
                "url": "https://me.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-biochemical-engineering-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in chemical engineering as a research-oriented master's within the College of Engineering \u2014 U.S. News ranks Berkeley chemical engineering No. 3 nationally (2026) \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Top-three ChemE",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley chemical engineering No. 3 nationally (2026)."
            },
            {
                "label": "Biotech ties",
                "sentiment": "positive",
                "detail": "Strong connections to Bay Area biotech and energy research."
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Curriculum spans transport, thermodynamics, and reactor design."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Intense workload",
                "sentiment": "mixed",
                "detail": "Long problem sets and a fast semester system are common."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Chemical Engineering",
                "url": "https://chemistry.berkeley.edu/cbe"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-engineering-other-bs": {
        "summary": "Students and third-party guides describe Berkeley's undergraduate engineering program within the College of Engineering as rigorous and well-regarded \u2014 Berkeley Engineering ranks No. 3 nationally for undergraduates (2026) \u2014 praising research access and Bay Area industry ties; common cautions are a heavy shared engineering core, large lower-division classes, and a competitive pace.",
        "themes": [
            {
                "label": "Top-three college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley undergraduate engineering No. 3 nationally (2026)."
            },
            {
                "label": "Interdisciplinary options",
                "sentiment": "positive",
                "detail": "Students access courses across all engineering departments."
            },
            {
                "label": "Bay Area ecosystem",
                "sentiment": "positive",
                "detail": "Graduates place into tech, energy, and consulting roles."
            },
            {
                "label": "Shared core load",
                "sentiment": "mixed",
                "detail": "Engineering physics and math requirements are demanding."
            },
            {
                "label": "Large classes",
                "sentiment": "caution",
                "detail": "Lower-division courses can be very large."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Engineering",
                "url": "https://engineering.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-engineering-other-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in engineering as a research-oriented master's within the College of Engineering \u2014 Berkeley Engineering ranks No. 3 nationally for undergraduates (2026) \u2014 praising faculty labs and industry placement; common cautions are self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Top-three college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley undergraduate engineering No. 3 nationally (2026)."
            },
            {
                "label": "Interdisciplinary options",
                "sentiment": "positive",
                "detail": "Students access courses across all engineering departments."
            },
            {
                "label": "Bay Area ecosystem",
                "sentiment": "positive",
                "detail": "Graduates place into tech, energy, and consulting roles."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Shared core load",
                "sentiment": "mixed",
                "detail": "Engineering physics and math requirements are demanding."
            }
        ],
        "sources": [
            {
                "label": "Berkeley \u2014 Engineering",
                "url": "https://engineering.berkeley.edu/"
            },
            {
                "label": "Berkeley Engineering \u2014 U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-law-phd": {
        "summary": "Doctoral candidates describe Berkeley Law's J.S.D. as a selective research doctorate for scholars pursuing academic careers in comparative and international law; praise includes faculty mentorship from a top public law school and access to the Robbins Collection, with cautions about very limited enrollment, self-directed dissertation work, and academic job-market competition.",
        "themes": [
            {
                "label": "Academic law research",
                "sentiment": "positive",
                "detail": "The J.S.D. trains scholars for faculty careers in law."
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Berkeley Law faculty mentor dissertations in comparative and public law."
            },
            {
                "label": "Research resources",
                "sentiment": "positive",
                "detail": "The Robbins Collection and law library support dissertation research."
            },
            {
                "label": "Limited enrollment",
                "sentiment": "caution",
                "detail": "The program admits a very small cohort each cycle."
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Law faculty placements are highly competitive nationally."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Law \u2014 J.S.D. program",
                "url": "https://www.law.berkeley.edu/academics/areas-of-study/jsd/"
            },
            {
                "label": "Berkeley Law \u2014 2026 law school rankings",
                "url": "https://www.law.berkeley.edu/article/2026-law-school-rankings-faculty-excellence-impact/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-biological-and-biomedical-sciences-other-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in biological sciences as a research-oriented master's spanning molecular biology, neuroscience, and integrative biology departments; students value access to NIH-funded labs and the Bay Area biotech ecosystem, with cautions about self-funded tuition for terminal master's students and competitive lab placement.",
        "themes": [
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Students pursue thesis research across molecular and integrative biology."
            },
            {
                "label": "NIH-funded labs",
                "sentiment": "positive",
                "detail": "Campus labs receive major federal research funding."
            },
            {
                "label": "Biotech ecosystem",
                "sentiment": "positive",
                "detail": "Graduates enter Bay Area biotech and research institutes."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Lab placement",
                "sentiment": "caution",
                "detail": "Finding a thesis lab can be competitive in popular fields."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Biology \u2014 Graduate programs",
                "url": "https://biology.berkeley.edu/graduate"
            },
            {
                "label": "U.S. News \u2014 UC Berkeley Biological Sciences",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/biological-sciences-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-biological-and-biomedical-sciences-other-phd": {
        "summary": "Doctoral students describe Berkeley biological-sciences Ph.D. programs as top-tier research doctorates \u2014 U.S. News ranks Berkeley biological sciences among the top five nationally \u2014 praising funded trainee slots and pioneering faculty; cautions include competitive admission, qualifying-exam pressure, and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Top-ranked biological sciences",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley biological sciences among the top five."
            },
            {
                "label": "Funded research training",
                "sentiment": "positive",
                "detail": "Many doctoral students receive NIH and NSF funding."
            },
            {
                "label": "Pioneering faculty",
                "sentiment": "positive",
                "detail": "Faculty include Nobel laureates and National Academy members."
            },
            {
                "label": "Qualifying exams",
                "sentiment": "caution",
                "detail": "Core exams and candidacy requirements are demanding."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Biology \u2014 Graduate programs",
                "url": "https://biology.berkeley.edu/graduate"
            },
            {
                "label": "U.S. News \u2014 UC Berkeley Biological Sciences",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/biological-sciences-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-social-work-bs": {
        "summary": "Students describe Berkeley's social-welfare undergraduate pathway as an interdisciplinary social-justice-oriented program connected to the School of Social Welfare; praise includes community-practice field placements and faculty expertise in child welfare and poverty policy, with cautions that formal BSW licensure paths require the graduate MSW and that field-placement logistics can be demanding.",
        "themes": [
            {
                "label": "Social justice focus",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes equity, anti-racism, and community practice."
            },
            {
                "label": "Field placements",
                "sentiment": "positive",
                "detail": "Students gain practicum experience with Bay Area agencies."
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Social Welfare faculty research child welfare and poverty policy."
            },
            {
                "label": "Licensure path",
                "sentiment": "mixed",
                "detail": "Professional social-work licensure requires the graduate MSW."
            },
            {
                "label": "Placement logistics",
                "sentiment": "caution",
                "detail": "Field hours and supervision requirements add scheduling demands."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Social Welfare \u2014 Programs",
                "url": "https://socialwelfare.berkeley.edu/academics"
            },
            {
                "label": "U.S. News \u2014 Best Social Work Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-social-work-ms": {
        "summary": "Graduate applicants describe Berkeley's MSW as a top-ranked social-work program \u2014 U.S. News places Berkeley Social Welfare among the top ten nationally \u2014 praising clinical and macro concentrations, Bay Area agency partnerships, and faculty research; common cautions are competitive admission, limited funding for professional master's students, and high Bay Area living costs.",
        "themes": [
            {
                "label": "Top-ranked MSW",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley Social Welfare among the top ten nationally."
            },
            {
                "label": "Clinical & macro tracks",
                "sentiment": "positive",
                "detail": "Concentrations span direct practice and policy/administration."
            },
            {
                "label": "Agency partnerships",
                "sentiment": "positive",
                "detail": "Field placements connect students to Bay Area social-service agencies."
            },
            {
                "label": "Professional-student funding",
                "sentiment": "caution",
                "detail": "MSW students receive less funding than doctoral trainees."
            },
            {
                "label": "Bay Area costs",
                "sentiment": "caution",
                "detail": "High local living costs affect professional master's students."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Social Welfare \u2014 Programs",
                "url": "https://socialwelfare.berkeley.edu/academics"
            },
            {
                "label": "U.S. News \u2014 Best Social Work Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-social-work-phd": {
        "summary": "Doctoral students describe Berkeley Social Welfare's Ph.D. as a research doctorate in social policy, child welfare, and community interventions; praise includes funded research assistantships and faculty mentorship, with cautions about competitive admission, long dissertation timelines, and academic job markets concentrated in social-work research programs.",
        "themes": [
            {
                "label": "Policy research training",
                "sentiment": "positive",
                "detail": "Doctoral work spans intervention research and social policy."
            },
            {
                "label": "Funded assistantships",
                "sentiment": "positive",
                "detail": "Many doctoral students receive research and teaching support."
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Faculty mentor dissertations in child welfare and poverty."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Social-work faculty placements are competitive nationally."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Social Welfare \u2014 Programs",
                "url": "https://socialwelfare.berkeley.edu/academics"
            },
            {
                "label": "U.S. News \u2014 Best Social Work Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-social-work-prof": {
        "summary": "Students describe Berkeley's professional social-work programs as rigorous clinical and community-practice degrees \u2014 U.S. News ranks Berkeley Social Welfare among the top ten nationally \u2014 praising field-education quality and faculty expertise; common cautions are intensive field-hour requirements, limited professional-student funding, and high Bay Area living costs.",
        "themes": [
            {
                "label": "Top-ranked program",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley Social Welfare among the top ten nationally."
            },
            {
                "label": "Field education",
                "sentiment": "positive",
                "detail": "Supervised practicum hours anchor clinical and macro training."
            },
            {
                "label": "Faculty practitioners",
                "sentiment": "positive",
                "detail": "Faculty combine research with community practice expertise."
            },
            {
                "label": "Field-hour demands",
                "sentiment": "caution",
                "detail": "Practicum and supervision requirements are time-intensive."
            },
            {
                "label": "Living costs",
                "sentiment": "caution",
                "detail": "Bay Area housing costs affect professional students."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Social Welfare \u2014 Programs",
                "url": "https://socialwelfare.berkeley.edu/academics"
            },
            {
                "label": "U.S. News \u2014 Best Social Work Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-economics-ms": {
        "summary": "Graduate applicants describe Berkeley's M.A. in Economics as a quantitatively rigorous preparatory degree for doctoral study or policy analytics \u2014 the department ranks among the top five nationally \u2014 praising econometrics training and faculty mentorship; common cautions are that the M.A. is primarily a Ph.D. prep program, funding is limited for terminal master's students, and coursework is mathematically demanding.",
        "themes": [
            {
                "label": "Top-ranked department",
                "sentiment": "positive",
                "detail": "Berkeley economics ranks among the top five graduate programs nationally."
            },
            {
                "label": "Econometrics rigor",
                "sentiment": "positive",
                "detail": "Core sequences emphasize mathematical economics and empirical methods."
            },
            {
                "label": "Ph.D. preparation",
                "sentiment": "positive",
                "detail": "Many graduates continue to top economics doctoral programs."
            },
            {
                "label": "Limited terminal funding",
                "sentiment": "caution",
                "detail": "The M.A. is primarily a Ph.D. prep path with limited assistantships."
            },
            {
                "label": "Mathematical demands",
                "sentiment": "caution",
                "detail": "Real analysis and econometrics requirements are rigorous."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Economics \u2014 Graduate programs",
                "url": "https://www.econ.berkeley.edu/grad"
            },
            {
                "label": "Berkeley News \u2014 U.S. News 2026 rankings",
                "url": "https://news.berkeley.edu/2025/09/22/uc-berkeley-named-top-public-school-in-the-country-by-us-news/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-economics-phd": {
        "summary": "Doctoral students describe Berkeley economics as a top-tier research doctorate with Nobel-laureate faculty and strength in econometrics, labor, and development; praise includes faculty mentorship and placement into academia and policy, with cautions about competitive admission, qualifying-exam pressure, and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Nobel-caliber faculty",
                "sentiment": "positive",
                "detail": "Faculty include Nobel laureates and leaders in econometrics and policy."
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Doctoral fields span labor, development, macro, and industrial organization."
            },
            {
                "label": "Academic & policy placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty posts, the Fed, and international organizations."
            },
            {
                "label": "Qualifying exams",
                "sentiment": "caution",
                "detail": "Core exams in micro, macro, and econometrics are demanding."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation research typically spans five or more years."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Economics \u2014 Graduate programs",
                "url": "https://www.econ.berkeley.edu/grad"
            },
            {
                "label": "Berkeley News \u2014 U.S. News 2026 rankings",
                "url": "https://news.berkeley.edu/2025/09/22/uc-berkeley-named-top-public-school-in-the-country-by-us-news/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-film-video-and-photographic-arts-bs": {
        "summary": "Students describe Berkeley's film and media undergraduate program as an interdisciplinary arts degree combining production, history, and critical theory within the Department of Film & Media; praise includes access to production facilities and Bay Area film culture, with cautions about limited enrollment in production courses and that the program is more academic than a conservatory film school.",
        "themes": [
            {
                "label": "Critical & production blend",
                "sentiment": "positive",
                "detail": "Curriculum combines film history, theory, and production."
            },
            {
                "label": "Bay Area film culture",
                "sentiment": "positive",
                "detail": "Students access festivals, archives, and regional production."
            },
            {
                "label": "Faculty filmmakers",
                "sentiment": "positive",
                "detail": "Faculty include working filmmakers and media scholars."
            },
            {
                "label": "Production capacity",
                "sentiment": "caution",
                "detail": "Enrollment in production courses can be limited."
            },
            {
                "label": "Academic vs. conservatory",
                "sentiment": "mixed",
                "detail": "The program emphasizes scholarship alongside production skills."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Film & Media \u2014 Graduate programs",
                "url": "https://filmmedia.berkeley.edu/graduate-programs/"
            },
            {
                "label": "Niche \u2014 University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-film-video-and-photographic-arts-ms": {
        "summary": "Graduate applicants describe Berkeley Film & Media's M.A. as a research-oriented master's in media history, theory, and documentary practice; students value faculty scholarship and the Pacific Film Archive, with cautions about self-funded tuition for terminal master's students and a smaller cohort than professional film schools.",
        "themes": [
            {
                "label": "Media scholarship",
                "sentiment": "positive",
                "detail": "Graduate coursework spans film history, theory, and documentary."
            },
            {
                "label": "Pacific Film Archive",
                "sentiment": "positive",
                "detail": "PFA collections and screenings support graduate research."
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Faculty include internationally recognized media scholars."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically fund tuition without assistantships."
            },
            {
                "label": "Smaller cohort",
                "sentiment": "mixed",
                "detail": "Enrollment is smaller than at dedicated film conservatories."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Film & Media \u2014 Graduate programs",
                "url": "https://filmmedia.berkeley.edu/graduate-programs/"
            },
            {
                "label": "Niche \u2014 University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-film-video-and-photographic-arts-phd": {
        "summary": "Doctoral students describe Berkeley Film & Media's Ph.D. as a research doctorate in cinema and media studies; praise includes faculty mentorship and the Pacific Film Archive, with cautions about competitive admission, long dissertation timelines, and academic job markets concentrated in film-studies departments.",
        "themes": [
            {
                "label": "Cinema studies research",
                "sentiment": "positive",
                "detail": "Doctoral work spans media history, theory, and cultural studies."
            },
            {
                "label": "PFA resources",
                "sentiment": "positive",
                "detail": "The Pacific Film Archive supports archival dissertation research."
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Faculty mentor dissertations in global cinema and media."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive with limited funded slots."
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Film-studies faculty placements are competitive nationally."
            }
        ],
        "sources": [
            {
                "label": "Berkeley Film & Media \u2014 Graduate programs",
                "url": "https://filmmedia.berkeley.edu/graduate-programs/"
            },
            {
                "label": "Niche \u2014 University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-public-health-ms": {
        "summary": "Graduate applicants describe Berkeley's M.S. in Public Health as a research-oriented master's spanning epidemiology, biostatistics, and health policy \u2014 the school ranks No. 6 nationally (2026) \u2014 praising faculty depth and California agency ties; common cautions are self-funded tuition for terminal master's students and that research M.S. paths differ from the professional MPH.",
        "themes": [
            {
                "label": "Top-ten school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley Public Health No. 6 nationally (2026)."
            },
            {
                "label": "Research training",
                "sentiment": "positive",
                "detail": "Students pursue thesis research in epidemiology and biostatistics."
            },
            {
                "label": "California agency ties",
                "sentiment": "positive",
                "detail": "Connections to state and county public-health organizations."
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal research master's students typically self-fund tuition."
            },
            {
                "label": "Distinct from MPH",
                "sentiment": "mixed",
                "detail": "The research M.S. differs from the professional MPH curriculum."
            }
        ],
        "sources": [
            {
                "label": "UC Berkeley Public Health \u2014 U.S. News No. 6 (2026)",
                "url": "https://publichealth.berkeley.edu/articles/news/ucbph-surges-to-6-in-us-news-rankings"
            },
            {
                "label": "Niche \u2014 UC Berkeley School of Public Health",
                "url": "https://www.niche.com/graduate-schools/uc-berkeley-school-of-public-health/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-public-health-phd": {
        "summary": "Doctoral students describe Berkeley Public Health's Ph.D. as a research doctorate in epidemiology, environmental health, and health policy \u2014 the school ranks No. 6 nationally (2026) \u2014 praising funded trainee slots and California population-health research; cautions include competitive admission, long dissertation timelines, and placements concentrated in academia and government research.",
        "themes": [
            {
                "label": "Top-ten school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Berkeley Public Health No. 6 nationally (2026)."
            },
            {
                "label": "Funded research training",
                "sentiment": "positive",
                "detail": "Many doctoral students receive NIH and foundation funding."
            },
            {
                "label": "Population-health research",
                "sentiment": "positive",
                "detail": "Faculty lead studies in epidemiology, environmental health, and policy."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is competitive across concentrations."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation and fieldwork typically span five or more years."
            }
        ],
        "sources": [
            {
                "label": "UC Berkeley Public Health \u2014 U.S. News No. 6 (2026)",
                "url": "https://publichealth.berkeley.edu/articles/news/ucbph-surges-to-6-in-us-news-rankings"
            },
            {
                "label": "Niche \u2014 UC Berkeley School of Public Health",
                "url": "https://www.niche.com/graduate-schools/uc-berkeley-school-of-public-health/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-business-administration-management-and-operations-ms": {
        "summary": "Graduate applicants describe Berkeley Haas specialized master's programs in management and operations as analytically rigorous complements to the flagship MBA \u2014 Poets&Quants ranks Haas among the top U.S. business schools \u2014 praising Bay Area tech and consulting placement; common cautions are smaller cohorts than the MBA, self-funded tuition, and that specialized master's paths require proactive recruiting.",
        "themes": [
            {
                "label": "Haas analytical rigor",
                "sentiment": "positive",
                "detail": "Quantitative coursework respected in consulting and tech roles."
            },
            {
                "label": "Bay Area placement",
                "sentiment": "positive",
                "detail": "Graduates access Silicon Valley recruiting networks."
            },
            {
                "label": "Specialized focus",
                "sentiment": "positive",
                "detail": "Programs target management science and operations analytics."
            },
            {
                "label": "Smaller cohort",
                "sentiment": "caution",
                "detail": "Enrollment is smaller than the flagship MBA program."
            },
            {
                "label": "Self-directed recruiting",
                "sentiment": "mixed",
                "detail": "Students outside core tech/consulting paths run more self-directed searches."
            }
        ],
        "sources": [
            {
                "label": "Poets&Quants \u2014 Berkeley Haas school profile",
                "url": "https://poetsandquants.com/school-profile/university-of-california-berkeley-haas-school-of-business/"
            },
            {
                "label": "Haas School of Business \u2014 Ph.D. Program",
                "url": "https://haas.berkeley.edu/phd/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    },
    "berkeley-business-administration-management-and-operations-phd": {
        "summary": "Doctoral students describe Berkeley Haas Ph.D. programs in management and operations as research doctorates producing scholars in finance, marketing, and operations \u2014 Haas ranks among the top business Ph.D. programs \u2014 praising faculty mentorship and academic placement; cautions include competitive admission, rigorous qualifying exams, and five-plus-year dissertation timelines.",
        "themes": [
            {
                "label": "Research-focused Ph.D.",
                "sentiment": "positive",
                "detail": "Doctoral training emphasizes original research in business disciplines."
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Haas faculty mentor dissertations in finance, marketing, and operations."
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": "Graduates join business school faculty posts nationally."
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Doctoral admission is highly competitive with small cohorts."
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Coursework, exams, and dissertation typically span five or more years."
            }
        ],
        "sources": [
            {
                "label": "Poets&Quants \u2014 Berkeley Haas school profile",
                "url": "https://poetsandquants.com/school-profile/university-of-california-berkeley-haas-school-of-business/"
            },
            {
                "label": "Haas School of Business \u2014 Ph.D. Program",
                "url": "https://haas.berkeley.edu/phd/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources \u2014 not individual verbatim reviews."
    }
}
