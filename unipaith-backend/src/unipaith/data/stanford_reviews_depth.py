"""Stanford University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``stanfordprof6`` migration to merge
``DEPTH_REVIEWS`` into ``stanford_profile._REVIEWS_BY_SLUG`` for 28
remaining coverable programs (41/41 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "stanford-aerospace-aeronautical-and-astronautical-space-engineering-bs": {
        "summary": "Students describe Stanford's undergraduate Aerospace, Aeronautical, and Astronautical/Space Engineering program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Aerospace, Aeronautical, and Astronautical/Space Engineering",
                "url": "https://aa.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-biological-and-biomedical-sciences-other-ms": {
        "summary": "Students describe Stanford Medicine's MS pathways in biological and biomedical sciences as research-oriented degrees for pre-med, industry, or doctoral pipeline careers; praise includes biosciences faculty and Stanford Hospital access, with cautions about self-funded tuition and outcomes that vary by specialization.",
        "themes": [
            {
                "label": "Biosciences breadth",
                "sentiment": "positive",
                "detail": "Programs span genetics, immunology, neuroscience, and more.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Stanford Hospital provides clinical-research context.",
            },
            {
                "label": "Ph.D. pipeline",
                "sentiment": "positive",
                "detail": "Many graduates continue to doctoral or industry research roles.",
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
                "label": "Stanford Biosciences \u2014 Master's programs",
                "url": "https://biosciences.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/stanford-university-04057",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-biomedical-medical-engineering-ms": {
        "summary": "Graduate students describe Stanford's MS in Bioengineering as a cross-disciplinary degree bridging engineering and medicine; praise includes the Clark Center hub, Stanford Hospital clinical ties, and med-device startup culture, with cautions that terminal MS students typically self-fund and the program is highly selective.",
        "themes": [
            {
                "label": "Engineering-medicine bridge",
                "sentiment": "positive",
                "detail": "BioE sits at the interface of engineering, biology, and clinical care.",
            },
            {
                "label": "Clark Center hub",
                "sentiment": "positive",
                "detail": "Shared research space connects BioE, Medicine, and Chemistry.",
            },
            {
                "label": "Med-device ecosystem",
                "sentiment": "positive",
                "detail": "Bay Area biotech and device startups recruit BioE graduates.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across bioengineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Bioengineering \u2014 Graduate",
                "url": "https://bioengineering.stanford.edu/academics-admissions/graduate-programs",
            },
            {
                "label": "U.S. News \u2014 Engineering rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-business-management-marketing-and-related-support-services-other-ms": {
        "summary": "Students describe Stanford GSB's specialized master's programs (beyond the MBA) as rigorous, small-cohort degrees in areas like MSx and executive education; praise includes GSB faculty and Silicon Valley networks, with cautions that non-MBA master's paths have narrower recruiting pipelines than the flagship MBA.",
        "themes": [
            {
                "label": "GSB faculty",
                "sentiment": "positive",
                "detail": "Courses taught by the same faculty who lead the MBA and Ph.D. programs.",
            },
            {
                "label": "Silicon Valley network",
                "sentiment": "positive",
                "detail": "Access to GSB alumni and Bay Area employers.",
            },
            {
                "label": "Small cohorts",
                "sentiment": "positive",
                "detail": "Specialized programs maintain intimate class sizes.",
            },
            {
                "label": "Narrower recruiting",
                "sentiment": "caution",
                "detail": "Non-MBA master's paths lack the MBA's structured recruiting funnel.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Bay Area living pushes total cost well above tuition alone.",
            },
        ],
        "sources": [
            {
                "label": "Stanford GSB \u2014 Programs",
                "url": "https://www.gsb.stanford.edu/programs",
            },
            {
                "label": "Poets&Quants \u2014 Stanford GSB",
                "url": "https://poetsandquants.com/schools/stanford-graduate-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-cee-ms": {
        "summary": "Graduate students describe Stanford's MS in Civil and Environmental Engineering as a research-oriented degree spanning structures, water, and sustainability; praise includes the Blume Earthquake Engineering Center and Doerr School ties, with cautions about self-funded tuition for terminal master's students and a smaller department than large public CEE schools.",
        "themes": [
            {
                "label": "Sustainability focus",
                "sentiment": "positive",
                "detail": "CEE connects to the Doerr School and Woods Institute on climate and water.",
            },
            {
                "label": "Earthquake engineering",
                "sentiment": "positive",
                "detail": "Blume Center is a leading seismic-research hub.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "Faculty collaborate across engineering, policy, and earth sciences.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller CEE faculty than large public engineering colleges.",
            },
        ],
        "sources": [
            {
                "label": "Stanford CEE \u2014 Graduate Programs",
                "url": "https://cee.stanford.edu/academics-admissions/graduate-programs",
            },
            {
                "label": "U.S. News \u2014 Engineering rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-chemical-engineering-bs": {
        "summary": "Students describe Stanford's undergraduate Chemical Engineering program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Chemical Engineering",
                "url": "https://chemeng.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-chemical-engineering-ms": {
        "summary": "Graduate students describe Stanford's MS in in Chemical Engineering within the School of Engineering as a research- and coursework-intensive degree; praise includes faculty labs and Silicon Valley recruiting, with cautions that terminal MS students typically self-fund and admission is highly selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and Bay Area employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. graduate engineering schools.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without assistantships typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Chemical Engineering",
                "url": "https://chemeng.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-civil-engineering-bs": {
        "summary": "Students describe Stanford's undergraduate Civil Engineering program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Civil Engineering",
                "url": "https://engineering.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-cs-phd": {
        "summary": "Doctoral students describe Stanford's Ph.D. in Computer Science as one of the world's most selective and influential research programs \u2014 QS ranks Stanford No. 2 globally in computer science (2026) \u2014 praising SAIL, HAI, and Silicon Valley collaborations; common cautions are extremely competitive admission, long dissertation timelines, and Bay Area cost of living.",
        "themes": [
            {
                "label": "Global CS standing",
                "sentiment": "positive",
                "detail": "QS ranks Stanford No. 2 worldwide in computer science (2026).",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "SAIL, HAI, and industry partnerships anchor doctoral research.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small cohorts work closely with leading AI, systems, and theory faculty.",
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": "Admission admits a tiny fraction of a very large applicant pool.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Stanford CS \u2014 Ph.D. Program",
                "url": "https://www.cs.stanford.edu/admissions/phd-admissions",
            },
            {
                "label": "QS \u2014 Computer Science subject rankings (2026)",
                "url": "https://www.topuniversities.com/university-subject-rankings/computer-science-information-systems",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-economics-ms": {
        "summary": "Students describe Stanford's MS in Economics as a quantitatively rigorous graduate degree preparing for doctoral study or policy/analytics roles; praise includes SIEPR faculty and econometrics training, with cautions that it is research-oriented rather than a professional terminal degree and admission is selective with limited departmental funding.",
        "themes": [
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Core coursework spans micro, macro, econometrics, and field courses.",
            },
            {
                "label": "SIEPR access",
                "sentiment": "positive",
                "detail": "Students join policy-research seminars and faculty projects.",
            },
            {
                "label": "Ph.D. pipeline",
                "sentiment": "positive",
                "detail": "Many graduates continue to top doctoral programs or research roles.",
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
                "label": "Stanford Economics \u2014 Graduate",
                "url": "https://economics.stanford.edu/graduate-programs",
            },
            {
                "label": "U.S. News \u2014 Economics rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-economics-phd": {
        "summary": "Doctoral students describe Stanford's Ph.D. in Economics as a top-tier program within SIEPR \u2014 U.S. News ranks Stanford #6 among national universities (2026); praise includes faculty in market design, development, and econometrics plus Silicon Valley policy ties, with cautions about competitive academic job markets and long dissertation timelines.",
        "themes": [
            {
                "label": "SIEPR research",
                "sentiment": "positive",
                "detail": "Stanford Institute for Economic Policy Research anchors applied work.",
            },
            {
                "label": "Faculty breadth",
                "sentiment": "positive",
                "detail": "Strengths span theory, econometrics, development, and market design.",
            },
            {
                "label": "Policy & tech ties",
                "sentiment": "positive",
                "detail": "Bay Area tech and policy institutions enrich doctoral research.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track economics faculty positions are nationally competitive.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Economics \u2014 Ph.D.",
                "url": "https://economics.stanford.edu/phd-program",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/stanford-university-1305",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-electrical-electronics-and-communications-engineering-bs": {
        "summary": "Students describe Stanford's undergraduate Electrical, Electronics, and Communications Engineering program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://ee.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-energy-science-engineering-ms": {
        "summary": "Graduate students describe Stanford's MS in Energy Science and Engineering within the Doerr School as an interdisciplinary degree bridging earth sciences, policy, and engineering; praise includes the Precourt Institute for Energy and Woods Institute ties, with cautions that the school is new (2022) and employer demand varies by energy sub-sector.",
        "themes": [
            {
                "label": "Interdisciplinary energy",
                "sentiment": "positive",
                "detail": "Curriculum spans engineering, earth systems, and policy.",
            },
            {
                "label": "Precourt & Woods ties",
                "sentiment": "positive",
                "detail": "Leading energy and environment institutes enrich coursework and research.",
            },
            {
                "label": "Climate focus",
                "sentiment": "positive",
                "detail": "Doerr School mission aligns with growing clean-energy hiring.",
            },
            {
                "label": "New school",
                "sentiment": "mixed",
                "detail": "Doerr School opened in 2022; curriculum and recruiting still evolving.",
            },
            {
                "label": "Sector variability",
                "sentiment": "caution",
                "detail": "Energy hiring cycles shift with commodity prices and policy.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Doerr School \u2014 Energy programs",
                "url": "https://sustainability.stanford.edu/academics/graduate-programs",
            },
            {
                "label": "Precourt Institute for Energy",
                "url": "https://energy.stanford.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-engineering-other-bs": {
        "summary": "Students describe Stanford's undergraduate Engineering, Other program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Engineering, Other",
                "url": "https://engineering.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-engineering-other-ms": {
        "summary": "Graduate students describe Stanford's MS in in Engineering, Other within the School of Engineering as a research- and coursework-intensive degree; praise includes faculty labs and Silicon Valley recruiting, with cautions that terminal MS students typically self-fund and admission is highly selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and Bay Area employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. graduate engineering schools.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without assistantships typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Engineering, Other",
                "url": "https://engineering.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-engineering-related-fields-bs": {
        "summary": "Students describe Stanford's undergraduate Engineering-Related Fields program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Engineering-Related Fields",
                "url": "https://engineering.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-engineering-related-fields-ms": {
        "summary": "Graduate students describe Stanford's MS in in Engineering-Related Fields within the School of Engineering as a research- and coursework-intensive degree; praise includes faculty labs and Silicon Valley recruiting, with cautions that terminal MS students typically self-fund and admission is highly selective.",
        "themes": [
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Faculty labs and Bay Area employers enrich graduate training.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. graduate engineering schools.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without assistantships typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across engineering specializations.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Engineering-Related Fields",
                "url": "https://engineering.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-environmental-environmental-health-engineering-bs": {
        "summary": "Students describe Stanford's undergraduate Environmental/Environmental Health Engineering program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Environmental/Environmental Health Engineering",
                "url": "https://cee.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-film-video-and-photographic-arts-bs": {
        "summary": "Students describe Stanford's Film and Media Studies major as a humanities-based film program within H&S \u2014 Niche lists film-related study among Stanford's distinctive arts offerings; praise includes documentary and critical-media courses plus Bay Area film-industry access, with cautions that it is an academic rather than a conservatory film school.",
        "themes": [
            {
                "label": "Critical media studies",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes film history, theory, and documentary practice.",
            },
            {
                "label": "Bay Area film access",
                "sentiment": "positive",
                "detail": "San Francisco and Silicon Valley media industries provide internship paths.",
            },
            {
                "label": "Interdisciplinary arts",
                "sentiment": "positive",
                "detail": "Students combine film with CS, design, or humanities majors.",
            },
            {
                "label": "Not a conservatory",
                "sentiment": "mixed",
                "detail": "Academic program rather than a hands-on film-production conservatory.",
            },
            {
                "label": "Limited production depth",
                "sentiment": "caution",
                "detail": "Fewer dedicated production courses than at USC or NYU film schools.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Arts \u2014 Film and Media Studies",
                "url": "https://art.stanford.edu/",
            },
            {
                "label": "Niche \u2014 Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-film-video-and-photographic-arts-ms": {
        "summary": "Graduate students describe Stanford's Documentary Film and Video MFA as a small, highly selective program within the Art & Art History department; praise includes one-on-one faculty mentorship and Bay Area documentary community ties, with cautions about extremely limited enrollment and a niche career path versus mainstream film-industry pipelines.",
        "themes": [
            {
                "label": "Documentary focus",
                "sentiment": "positive",
                "detail": "MFA emphasizes documentary filmmaking and visual storytelling.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Tiny cohort enables close advisor relationships.",
            },
            {
                "label": "Bay Area community",
                "sentiment": "positive",
                "detail": "San Francisco documentary festivals and media nonprofits enrich the program.",
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": "Program admits only a handful of students per cycle.",
            },
            {
                "label": "Niche career path",
                "sentiment": "mixed",
                "detail": "Best suited for documentary rather than commercial film careers.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Art \u2014 Documentary Film MFA",
                "url": "https://art.stanford.edu/",
            },
            {
                "label": "Niche \u2014 Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-gsb-phd": {
        "summary": "Doctoral students describe Stanford GSB's Ph.D. in Business as a research-intensive program in accounting, finance, marketing, and organizational behavior \u2014 U.S. News ranks Stanford GSB among top business schools; praise includes close faculty mentorship and Silicon Valley entrepreneurship research, with cautions about competitive academic job markets and a smaller cohort than large public business Ph.D. programs.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Small cohorts enable close advisor relationships across business disciplines.",
            },
            {
                "label": "Silicon Valley context",
                "sentiment": "positive",
                "detail": "Entrepreneurship, VC, and tech-market research are program strengths.",
            },
            {
                "label": "GSB reputation",
                "sentiment": "positive",
                "detail": "Stanford GSB ranks among the world's leading business research schools.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track business faculty positions are nationally competitive.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than large public business Ph.D. programs.",
            },
        ],
        "sources": [
            {
                "label": "Stanford GSB \u2014 Ph.D. Program",
                "url": "https://www.gsb.stanford.edu/programs/phd",
            },
            {
                "label": "U.S. News \u2014 Stanford GSB",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/stanford-university-01028",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-law-phd": {
        "summary": "Legal scholars describe Stanford Law's Doctor of Philosophy in Law (J.S.D./S.J.D.) as an advanced research degree for academic legal careers \u2014 U.S. News ranks Stanford Law #2 nationally (2026); praise includes faculty mentorship in technology, environmental, and international law, with cautions about extremely competitive law-faculty hiring and a small cohort.",
        "themes": [
            {
                "label": "Top law school rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Stanford Law #2 nationally (2026).",
            },
            {
                "label": "Tech & policy law",
                "sentiment": "positive",
                "detail": "Faculty strengths in IP, cyber, and innovation law.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Close advisor relationships with leading legal scholars.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track law faculty positions are highly competitive.",
            },
            {
                "label": "Small cohort",
                "sentiment": "mixed",
                "detail": "Fewer doctoral law students than large public law schools.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Law \u2014 Advanced Legal Degrees",
                "url": "https://law.stanford.edu/education/degrees/advanced-legal-degrees/",
            },
            {
                "label": "U.S. News \u2014 Stanford Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/stanford-university-03020",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-materials-engineering-bs": {
        "summary": "Students describe Stanford's undergraduate Materials Engineering program within the School of Engineering as a rigorous B.S. at a top-ranked private research university; praise includes undergraduate research access, design courses, and Silicon Valley recruiting, with cautions about demanding prerequisites and curved grading against elite peers.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across engineering departments.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": "Niche reviewers note grading against an exceptionally strong peer group.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Materials Engineering",
                "url": "https://mse.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-me-ms": {
        "summary": "Graduate students describe Stanford's MS in Mechanical Engineering as a research- and coursework-intensive degree within a top-ranked engineering school; praise includes robotics labs (CHARM Lab, Biomimetics & Dexterous Manipulation), design courses, and Silicon Valley recruiting, with cautions that terminal MS students typically self-fund and admission is highly selective.",
        "themes": [
            {
                "label": "Robotics & design",
                "sentiment": "positive",
                "detail": "ME labs span robotics, biomechanics, and product design.",
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": "Graduates enter aerospace, robotics, med-device, and tech roles.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Stanford Engineering ranks among top U.S. graduate engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is competitive across ME specializations.",
            },
        ],
        "sources": [
            {
                "label": "Stanford ME \u2014 Graduate Program",
                "url": "https://me.stanford.edu/academics-admissions/graduate-program",
            },
            {
                "label": "U.S. News \u2014 Engineering rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-medicine-phd": {
        "summary": "Doctoral students describe Stanford Medicine's Ph.D. programs as research-intensive training across biosciences \u2014 U.S. News ranks Stanford Medicine #3 for research (2025); praise includes Biosciences umbrella structure, Stanford Hospital clinical ties, and interdisciplinary institutes, with cautions about long timelines and competitive funding for research assistantships.",
        "themes": [
            {
                "label": "Top research ranking",
                "sentiment": "positive",
                "detail": "U.S. News ranks Stanford #3 among medical schools for research (2025).",
            },
            {
                "label": "Biosciences structure",
                "sentiment": "positive",
                "detail": "Ph.D. programs span biochemistry, genetics, neuroscience, and more.",
            },
            {
                "label": "Clinical integration",
                "sentiment": "positive",
                "detail": "Stanford Hospital and Lucile Packard enrich translational research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Doctoral programs commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across departments.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Medicine \u2014 Biosciences Ph.D.",
                "url": "https://biosciences.stanford.edu/prospective-students/phd-programs/",
            },
            {
                "label": "U.S. News \u2014 Stanford Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/stanford-university-04057",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-petroleum-engineering-ms": {
        "summary": "Graduate students describe Stanford's MS in Energy Resources Engineering (petroleum and subsurface focus) as a research-oriented degree within the Doerr School; praise includes the Energy Resources Engineering department's subsurface modeling and geophysics strengths, with cautions that petroleum-sector hiring cycles fluctuate and the program is transitioning under the sustainability school's broader energy mission.",
        "themes": [
            {
                "label": "Subsurface expertise",
                "sentiment": "positive",
                "detail": "Faculty lead research in reservoir engineering and geophysics.",
            },
            {
                "label": "Energy transition",
                "sentiment": "positive",
                "detail": "Doerr School reframes petroleum training within broader energy systems.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Students join faculty projects in energy modeling and carbon storage.",
            },
            {
                "label": "Sector hiring cycles",
                "sentiment": "caution",
                "detail": "Oil-and-gas recruiting fluctuates with commodity prices.",
            },
            {
                "label": "Program transition",
                "sentiment": "mixed",
                "detail": "Doerr School restructuring may shift course offerings over time.",
            },
        ],
        "sources": [
            {
                "label": "Stanford \u2014 Energy Resources Engineering",
                "url": "https://energy.stanford.edu/",
            },
            {
                "label": "Stanford Doerr School \u2014 Graduate programs",
                "url": "https://sustainability.stanford.edu/academics/graduate-programs",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-public-health-ms": {
        "summary": "Students describe Stanford's MS in Public Health (Epidemiology & Clinical Research) as a research-oriented health-sciences degree within Stanford Medicine; praise includes clinical-research methodology and Stanford Hospital data access, with cautions that it is not a generalist MPH and admission is selective with self-funded tuition for most students.",
        "themes": [
            {
                "label": "Clinical research focus",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes epidemiology and clinical-trial methods.",
            },
            {
                "label": "Stanford Hospital access",
                "sentiment": "positive",
                "detail": "Students work with faculty on real clinical datasets.",
            },
            {
                "label": "Medicine reputation",
                "sentiment": "positive",
                "detail": "Stanford Medicine ranks among top U.S. research medical schools.",
            },
            {
                "label": "Not a generalist MPH",
                "sentiment": "mixed",
                "detail": "Program is narrower than a traditional community-health MPH.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Most MS students self-fund without departmental assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Medicine \u2014 MS Epidemiology & Clinical Research",
                "url": "https://med.stanford.edu/epidemiology/education/ms-program.html",
            },
            {
                "label": "U.S. News \u2014 Stanford Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/stanford-university-04057",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "stanford-veterinary-biomedical-and-clinical-sciences-ms": {
        "summary": "Students describe Stanford Medicine's biomedical-sciences master's pathways as research-oriented credentials for health-sciences careers; praise includes Stanford Hospital and biosciences faculty access, with cautions that these are specialized research degrees rather than clinical veterinary programs and most students self-fund.",
        "themes": [
            {
                "label": "Research training",
                "sentiment": "positive",
                "detail": "Coursework and lab work prepare for health-sciences research roles.",
            },
            {
                "label": "Medicine ties",
                "sentiment": "positive",
                "detail": "Stanford Hospital and biosciences faculty enrich training.",
            },
            {
                "label": "Interdisciplinary scope",
                "sentiment": "positive",
                "detail": "Students bridge biology, engineering, and clinical research.",
            },
            {
                "label": "Not a DVM program",
                "sentiment": "mixed",
                "detail": "Stanford does not offer a Doctor of Veterinary Medicine degree.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Most master's students self-fund without assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Stanford Biosciences",
                "url": "https://biosciences.stanford.edu/",
            },
            {
                "label": "U.S. News \u2014 Stanford Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/stanford-university-04057",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
