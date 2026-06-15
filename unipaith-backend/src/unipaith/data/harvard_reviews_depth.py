"""Harvard University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``harvardprof6`` migration to merge
``DEPTH_REVIEWS`` into ``harvard_profile._REVIEWS_BY_SLUG`` for 49
remaining coverable programs (60/60 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "harvard-advanced-graduate-dentistry-and-oral-sciences-ms": {
        "summary": "Graduate students describe Harvard Dental Medicine's in Advanced/Graduate Dentistry and Oral Sciences as a research-oriented dental degree in the Longwood Medical Area; praise includes HMS collaboration and clinical training at Harvard Dental Center, with cautions about competitive specialty matching and Boston living costs.",
        "themes": [
            {
                "label": "Research dental school",
                "sentiment": "positive",
                "detail": "HSDM integrates dental education with HMS biomedical research.",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Students train at Harvard Dental Center and affiliated sites.",
            },
            {
                "label": "HMS ecosystem",
                "sentiment": "positive",
                "detail": "Proximity to HMS supports interdisciplinary biomedical study.",
            },
            {
                "label": "Specialty matching",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research.",
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": "Boston housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard School of Dental Medicine",
                "url": "https://hsdm.harvard.edu/education/dmd-program",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-advanced-graduate-dentistry-and-oral-sciences-phd": {
        "summary": "Graduate students describe Harvard Dental Medicine's Advanced/Graduate Dentistry and Oral Sciences as a research-oriented dental degree in the Longwood Medical Area; praise includes HMS collaboration and clinical training at Harvard Dental Center, with cautions about competitive specialty matching and Boston living costs.",
        "themes": [
            {
                "label": "Research dental school",
                "sentiment": "positive",
                "detail": "HSDM integrates dental education with HMS biomedical research.",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Students train at Harvard Dental Center and affiliated sites.",
            },
            {
                "label": "HMS ecosystem",
                "sentiment": "positive",
                "detail": "Proximity to HMS supports interdisciplinary biomedical study.",
            },
            {
                "label": "Specialty matching",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research.",
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": "Boston housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard School of Dental Medicine",
                "url": "https://hsdm.harvard.edu/education/dmd-program",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-architecture-ms": {
        "summary": "Graduate students describe Harvard GSD's in Architecture as a design-intensive degree in one of the nation's top-ranked design schools; praise includes studio culture, visiting critics, and Gund Hall community, with cautions about demanding studio workloads and variable job security in design fields.",
        "themes": [
            {
                "label": "Top design rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard GSD among leading graduate design programs.",
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the curriculum.",
            },
            {
                "label": "Visiting critics",
                "sentiment": "positive",
                "detail": "Leading architects and designers review student work.",
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
                "label": "Harvard \u2014 Harvard Graduate School of Design",
                "url": "https://www.gsd.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-art-history-ab": {
        "summary": "Students describe Harvard's History of Art & Architecture concentration as a rigorous humanities program with access to Harvard Art Museums and the Fogg, Busch-Reisinger, and Arthur M. Sackler collections; praise includes small seminars and faculty who are leading scholars, with cautions that the field feeds graduate school and museum careers more than direct industry placement and that course access can be competitive.",
        "themes": [
            {
                "label": "Museum collections",
                "sentiment": "positive",
                "detail": "Harvard Art Museums provide direct access to world-class collections.",
            },
            {
                "label": "Faculty scholars",
                "sentiment": "positive",
                "detail": "Professors are leading art historians across periods and regions.",
            },
            {
                "label": "Seminar culture",
                "sentiment": "positive",
                "detail": "Small seminars anchor close reading of visual and architectural history.",
            },
            {
                "label": "Graduate-school path",
                "sentiment": "mixed",
                "detail": "Many graduates pursue Ph.D. programs and museum careers.",
            },
            {
                "label": "Course access",
                "sentiment": "caution",
                "detail": "Popular seminars can be oversubscribed in a large college.",
            },
        ],
        "sources": [
            {
                "label": "Harvard History of Art & Architecture",
                "url": "https://haa.fas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-bioengineering-phd": {
        "summary": "Doctoral students describe Harvard SEAS's Ph.D. in Bioengineering as a research degree within an Ivy R1 university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for faculty mentorship and Allston research facilities, with cautions about funding competition and that SEAS is smaller than peer flagship engineering schools.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships in specialized labs.",
            },
            {
                "label": "Allston campus",
                "sentiment": "positive",
                "detail": "Science and Engineering Complex supports interdisciplinary research.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Cross-school collaboration with HMS, HBS, and FAS.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley engineering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Bioengineering",
                "url": "https://seas.harvard.edu/bioengineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-bioengineering-sb": {
        "summary": "Students describe Harvard's Bioengineering S.B. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that SEAS is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Harvard College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Bioengineering",
                "url": "https://seas.harvard.edu/bioengineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-biological-and-biomedical-sciences-other-ms": {
        "summary": "Students describe Harvard's in Biological and Biomedical Sciences, Other program within the Faculty of Arts & Sciences as a rigorous liberal-arts or graduate research degree; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that many majors feed graduate school more than direct industry hiring.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and tutorials anchor the Harvard College and GSAS experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Harvard sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many programs feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Biological and Biomedical Sciences, Other",
                "url": "https://gsas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-biomedical-medical-engineering-bs": {
        "summary": "Students describe Harvard's Biomedical/Medical Engineering S.B. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that SEAS is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Harvard College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Biomedical/Medical Engineering",
                "url": "https://seas.harvard.edu/bioengineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-biomedical-medical-engineering-ms": {
        "summary": "Graduate students describe Harvard SEAS's M.S. in in Biomedical/Medical Engineering as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Boston tech recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Boston recruiting",
                "sentiment": "positive",
                "detail": "Tech, biotech, and consulting firms recruit Harvard engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Biomedical/Medical Engineering",
                "url": "https://seas.harvard.edu/bioengineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-biomedical-phd": {
        "summary": "Doctoral students describe Harvard's Biomedical Sciences Ph.D. through the Division of Medical Sciences as a research degree with access to HMS labs and affiliated hospitals \u2014 U.S. News ranks Harvard Medical School #1 for research (2026); praise includes translational research infrastructure, with cautions about long dissertation timelines and competitive academic hiring.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks HMS #1 among medical schools for research.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Affiliated hospitals support clinical and translational studies.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Students join labs across HMS and affiliated institutions.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Biomedical Ph.D. programs commonly span five or more years.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Faculty positions in biomedical sciences are nationally competitive.",
            },
        ],
        "sources": [
            {
                "label": "Harvard Medical School \u2014 Ph.D. Programs",
                "url": "https://hms.harvard.edu/education/phd-programs",
            },
            {
                "label": "U.S. News \u2014 Harvard Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/harvard-university-04098",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-administration-management-and-operations-bs": {
        "summary": "Students and guides describe Harvard Business School's Business Administration, Management and Operations offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-administration-management-and-operations-ms": {
        "summary": "Students and guides describe Harvard Business School's in Business Administration, Management and Operations offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-administration-management-and-operations-phd": {
        "summary": "Students and guides describe Harvard Business School's Business Administration, Management and Operations offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-commerce-general-ms": {
        "summary": "Students and guides describe Harvard Business School's in Business/Commerce, General offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-corporate-communications-bs": {
        "summary": "Students and guides describe Harvard Business School's Business/Corporate Communications offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-corporate-communications-ms": {
        "summary": "Students and guides describe Harvard Business School's in Business/Corporate Communications offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-managerial-economics-ms": {
        "summary": "Students and guides describe Harvard Business School's in Business/Managerial Economics offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-business-phd": {
        "summary": "Doctoral students describe HBS's Business Administration Ph.D. as a small, highly selective research program producing faculty at leading business schools; praise includes case-method research culture and access to HBS archives and industry data, with cautions about extremely competitive academic hiring and a scholarly rather than practitioner orientation.",
        "themes": [
            {
                "label": "Faculty placement",
                "sentiment": "positive",
                "detail": "Graduates join tenure-track faculty at top business schools worldwide.",
            },
            {
                "label": "Case-method research",
                "sentiment": "positive",
                "detail": "Doctoral training integrates HBS's case-based research tradition.",
            },
            {
                "label": "Industry data access",
                "sentiment": "positive",
                "detail": "HBS archives and corporate partnerships support empirical work.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track business faculty positions are nationally competitive.",
            },
            {
                "label": "Small cohort",
                "sentiment": "mixed",
                "detail": "Tiny entering classes limit peer diversity compared to large public Ph.D. programs.",
            },
        ],
        "sources": [
            {
                "label": "HBS \u2014 Doctoral Programs",
                "url": "https://www.hbs.edu/doctoral/",
            },
            {
                "label": "Poets&Quants \u2014 Harvard Business School",
                "url": "https://poetsandquants.com/school-profile/harvard-business-school/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-computer-engineering-ms": {
        "summary": "Graduate students describe Harvard SEAS's M.S. in in Computer Engineering as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Boston tech recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Boston recruiting",
                "sentiment": "positive",
                "detail": "Tech, biotech, and consulting firms recruit Harvard engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Computer Engineering",
                "url": "https://seas.harvard.edu/electrical-engineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-computer-science-ms": {
        "summary": "Graduate students describe Harvard SEAS's M.S. in in Computer Science as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Boston tech recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Boston recruiting",
                "sentiment": "positive",
                "detail": "Tech, biotech, and consulting firms recruit Harvard engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Computer Science",
                "url": "https://seas.harvard.edu/computer-science",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-cs-phd": {
        "summary": "Doctoral students describe Harvard CS's Ph.D. as a research degree in a growing department with strengths in AI, systems, and theory; praise includes faculty mentorship and cross-school collaboration with SEAS and HMS, with cautions that Harvard CS ranks below MIT/Stanford/CMU, funding is competitive, and industry recruiting is less centralized than at larger CS-flagship departments.",
        "themes": [
            {
                "label": "Research areas",
                "sentiment": "positive",
                "detail": "Active groups in AI, systems, theory, and computational science.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships.",
            },
            {
                "label": "Interdisciplinary Harvard",
                "sentiment": "positive",
                "detail": "Collaboration with economics, medicine, and applied math.",
            },
            {
                "label": "Not a CS-flagship",
                "sentiment": "caution",
                "detail": "Harvard CS ranks below the very top CS-focused universities.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
        ],
        "sources": [
            {
                "label": "Harvard SEAS \u2014 Computer Science Graduate",
                "url": "https://seas.harvard.edu/computer-science/graduate-programs",
            },
            {
                "label": "U.S. News \u2014 Computer Science rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-dentistry-phd": {
        "summary": "Graduate students describe Harvard Medical School's Dentistry as a research-intensive degree \u2014 U.S. News ranks HMS #1 for research (2026) \u2014 with access to affiliated hospitals; praise includes translational research infrastructure, with cautions about competitive residency matching and Boston living costs.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks HMS #1 among medical schools for research.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Affiliated hospitals support clinical and translational studies.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Students join labs across HMS and affiliated institutions.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research portfolios.",
            },
            {
                "label": "Living costs",
                "sentiment": "caution",
                "detail": "Boston housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Medical School",
                "url": "https://hms.harvard.edu/education",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/harvard-university-04098",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-dmd": {
        "summary": "Dental students describe Harvard School of Dental Medicine's D.M.D. as a research-intensive dental program embedded in the Longwood Medical Area \u2014 U.S. News ranks HSDM among leading dental schools \u2014 with praise for early clinical exposure and HMS collaboration, with cautions about demanding coursework, Boston living costs, and competitive specialty residency matching.",
        "themes": [
            {
                "label": "Research dental school",
                "sentiment": "positive",
                "detail": "HSDM integrates dental education with HMS biomedical research.",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Students train at Harvard Dental Center and affiliated sites.",
            },
            {
                "label": "HMS ecosystem",
                "sentiment": "positive",
                "detail": "Proximity to HMS and Boston hospitals supports interdisciplinary study.",
            },
            {
                "label": "Specialty matching",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research.",
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": "Boston housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Harvard School of Dental Medicine \u2014 D.M.D.",
                "url": "https://hsdm.harvard.edu/education/dmd-program",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-economics-ms": {
        "summary": "Students describe Harvard's in Economics program within the Faculty of Arts & Sciences as a rigorous liberal-arts or graduate research degree; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that many majors feed graduate school more than direct industry hiring.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and tutorials anchor the Harvard College and GSAS experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Harvard sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many programs feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Economics",
                "url": "https://economics.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-economics-phd": {
        "summary": "Doctoral students describe Harvard Economics's Ph.D. as one of the world's top theory and applied programs \u2014 Niche ranks Harvard #6 for undergraduate economics and graduates join faculty at leading universities and policy institutions; praise includes the NBER ecosystem, faculty in macro, labor, and development, with cautions about extremely competitive admission, rigorous qualifying exams, and an academic job market that favors top-quartile candidates.",
        "themes": [
            {
                "label": "Top economics faculty",
                "sentiment": "positive",
                "detail": "Faculty span macro, labor, development, and industrial organization.",
            },
            {
                "label": "NBER & policy access",
                "sentiment": "positive",
                "detail": "Cambridge's NBER and Boston policy institutions support applied research.",
            },
            {
                "label": "Faculty placement",
                "sentiment": "positive",
                "detail": "Graduates join R1 faculty and central banks worldwide.",
            },
            {
                "label": "Qualifying exams",
                "sentiment": "caution",
                "detail": "Core micro, macro, and econometrics exams are demanding gatekeepers.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement concentrates at top research universities.",
            },
        ],
        "sources": [
            {
                "label": "Harvard Economics \u2014 Ph.D. Program",
                "url": "https://economics.harvard.edu/graduate/phd-program",
            },
            {
                "label": "Niche \u2014 Best Colleges for Economics",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-electrical-electronics-and-communications-engineering-bs": {
        "summary": "Students describe Harvard's Electrical, Electronics, and Communications Engineering S.B. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that SEAS is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Harvard College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://seas.harvard.edu/electrical-engineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-electrical-eng-sb": {
        "summary": "Students describe Harvard's Electrical Engineering S.B. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that SEAS is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Harvard College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Electrical Engineering",
                "url": "https://seas.harvard.edu/electrical-engineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-engineering-physics-ms": {
        "summary": "Graduate students describe Harvard SEAS's M.S. in in Engineering Physics as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Boston tech recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Boston recruiting",
                "sentiment": "positive",
                "detail": "Tech, biotech, and consulting firms recruit Harvard engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Engineering Physics",
                "url": "https://seas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-engineering-related-fields-ms": {
        "summary": "Graduate students describe Harvard SEAS's M.S. in in Engineering-Related Fields as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Boston tech recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Boston recruiting",
                "sentiment": "positive",
                "detail": "Tech, biotech, and consulting firms recruit Harvard engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Engineering-Related Fields",
                "url": "https://seas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-engineering-science-bs": {
        "summary": "Students describe Harvard's Engineering Science S.B. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that SEAS is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Harvard College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Engineering Science",
                "url": "https://seas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-engineering-science-ms": {
        "summary": "Graduate students describe Harvard SEAS's M.S. in in Engineering Science as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Boston tech recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Boston recruiting",
                "sentiment": "positive",
                "detail": "Tech, biotech, and consulting firms recruit Harvard engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Engineering Science",
                "url": "https://seas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-entrepreneurial-and-small-business-operations-ms": {
        "summary": "Students and guides describe Harvard Business School's in Entrepreneurial and Small Business Operations offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-environmental-eng-sb": {
        "summary": "Students describe Harvard's Environmental Science & Engineering S.B. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that SEAS is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Harvard College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Environmental Science & Engineering",
                "url": "https://seas.harvard.edu/environmental-science-and-engineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-film-video-and-photographic-arts-bs": {
        "summary": "Students describe Harvard's Film/Video and Photographic Arts program within the Faculty of Arts & Sciences as a rigorous liberal-arts or graduate research degree; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that many majors feed graduate school more than direct industry hiring.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and tutorials anchor the Harvard College and GSAS experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Harvard sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many programs feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Film/Video and Photographic Arts",
                "url": "https://afvs.fas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-film-video-and-photographic-arts-ms": {
        "summary": "Students describe Harvard's in Film/Video and Photographic Arts program within the Faculty of Arts & Sciences as a rigorous liberal-arts or graduate research degree; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that many majors feed graduate school more than direct industry hiring.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and tutorials anchor the Harvard College and GSAS experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Harvard sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many programs feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Film/Video and Photographic Arts",
                "url": "https://afvs.fas.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-finance-and-financial-management-services-ms": {
        "summary": "Students and guides describe Harvard Business School's in Finance and Financial Management Services offerings within the world's most recognized MBA brand \u2014 Poets&Quants and Fortune consistently rank HBS among top business schools; praise includes the case-method culture and alumni network, with cautions about extremely selective admission, high tuition, and that HBS is primarily a graduate professional school rather than an undergraduate program.",
        "themes": [
            {
                "label": "Case method & brand",
                "sentiment": "positive",
                "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands.",
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": "Rock Center for Entrepreneurship supports startup activity across programs.",
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs.",
            },
            {
                "label": "Graduate-only school",
                "sentiment": "mixed",
                "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Business School",
                "url": "https://www.hbs.edu/programs/doctoral/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-journalism-ms": {
        "summary": "Students describe Harvard's in Journalism program within the Faculty of Arts & Sciences as a rigorous liberal-arts or graduate research degree; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that many majors feed graduate school more than direct industry hiring.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and tutorials anchor the Harvard College and GSAS experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Harvard sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many programs feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Journalism",
                "url": "https://journalism.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-landscape-architecture-ms": {
        "summary": "Graduate students describe Harvard GSD's in Landscape Architecture as a design-intensive degree in one of the nation's top-ranked design schools; praise includes studio culture, visiting critics, and Gund Hall community, with cautions about demanding studio workloads and variable job security in design fields.",
        "themes": [
            {
                "label": "Top design rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard GSD among leading graduate design programs.",
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the curriculum.",
            },
            {
                "label": "Visiting critics",
                "sentiment": "positive",
                "detail": "Leading architects and designers review student work.",
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
                "label": "Harvard \u2014 Harvard Graduate School of Design",
                "url": "https://www.gsd.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-law-phd": {
        "summary": "Doctoral scholars describe Harvard Law's Law as a research degree within one of the nation's top-ranked law schools \u2014 U.S. News ranks Harvard Law No. 4 (2026); praise includes unmatched library resources and faculty mentorship, with cautions about competitive academic law-faculty hiring and a scholarly orientation.",
        "themes": [
            {
                "label": "Top law school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard Law among the nation's leading law schools.",
            },
            {
                "label": "Langdell library",
                "sentiment": "positive",
                "detail": "The world's largest academic law library supports dissertation research.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Tiny cohorts enable direct work with leading legal scholars.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Faculty hiring in law is highly competitive nationally.",
            },
            {
                "label": "Scholarly focus",
                "sentiment": "mixed",
                "detail": "The degree emphasizes legal scholarship over practitioner training.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Law School",
                "url": "https://hls.harvard.edu/academics/degrees/sjd/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/harvard-university-03009",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-law-sjd": {
        "summary": "Doctoral scholars describe Harvard Law's S.J.D. as the most advanced research law degree \u2014 U.S. News ranks Harvard Law No. 4 (2026) \u2014 attracting international legal scholars for dissertation work; praise includes unmatched library resources and faculty mentorship, with cautions about limited funding, a scholarly rather than practitioner orientation, and competitive academic law-faculty hiring.",
        "themes": [
            {
                "label": "Top law school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard Law among the nation's leading law schools.",
            },
            {
                "label": "Langdell library",
                "sentiment": "positive",
                "detail": "The world's largest academic law library supports dissertation research.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Tiny cohorts enable direct work with leading legal scholars.",
            },
            {
                "label": "Funding variability",
                "sentiment": "caution",
                "detail": "S.J.D. funding packages vary; many students rely on external fellowships.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Faculty hiring in law is highly competitive nationally.",
            },
        ],
        "sources": [
            {
                "label": "Harvard Law \u2014 S.J.D. Program",
                "url": "https://hls.harvard.edu/academics/degrees/sjd/",
            },
            {
                "label": "U.S. News \u2014 Harvard Law School",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/harvard-university-03009",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-mdes": {
        "summary": "Graduate students describe Harvard GSD's in Master in Design Studies (M.Des.) as a design-intensive degree in one of the nation's top-ranked design schools; praise includes studio culture, visiting critics, and Gund Hall community, with cautions about demanding studio workloads and variable job security in design fields.",
        "themes": [
            {
                "label": "Top design rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard GSD among leading graduate design programs.",
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the curriculum.",
            },
            {
                "label": "Visiting critics",
                "sentiment": "positive",
                "detail": "Leading architects and designers review student work.",
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
                "label": "Harvard \u2014 Harvard Graduate School of Design",
                "url": "https://www.gsd.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-mdiv": {
        "summary": "Students describe Harvard Divinity School's M.Div. as a theologically rigorous ordination-track degree in a nonsectarian divinity school embedded in a major research university; praise includes Andover Harvard Theological Library access and interdisciplinary Harvard coursework, with cautions about limited financial aid relative to tuition and a career path concentrated in ministry and nonprofit leadership.",
        "themes": [
            {
                "label": "Ecumenical formation",
                "sentiment": "positive",
                "detail": "M.Div. integrates worship, field education, and theological study.",
            },
            {
                "label": "Harvard ecosystem",
                "sentiment": "positive",
                "detail": "Students cross-register across Harvard's professional schools.",
            },
            {
                "label": "Theological library",
                "sentiment": "positive",
                "detail": "Andover Harvard Theological Library supports research across traditions.",
            },
            {
                "label": "Tuition & aid",
                "sentiment": "caution",
                "detail": "Seminary tuition is substantial; aid packages vary by need.",
            },
            {
                "label": "Ministry-focused careers",
                "sentiment": "mixed",
                "detail": "Graduates primarily enter ordained ministry, chaplaincy, and nonprofit roles.",
            },
        ],
        "sources": [
            {
                "label": "Harvard Divinity School \u2014 M.Div.",
                "url": "https://hds.harvard.edu/academics/mdiv",
            },
            {
                "label": "Niche \u2014 Harvard University reviews",
                "url": "https://www.niche.com/colleges/harvard-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-mechanical-eng-sb": {
        "summary": "Students describe Harvard's Mechanical Engineering S.B. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Harvard Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that SEAS is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Harvard College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Mechanical Engineering",
                "url": "https://seas.harvard.edu/mechanical-engineering",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-medicine-ms": {
        "summary": "Graduate students describe Harvard Medical School's in Medicine as a research-intensive degree \u2014 U.S. News ranks HMS #1 for research (2026) \u2014 with access to affiliated hospitals; praise includes translational research infrastructure, with cautions about competitive residency matching and Boston living costs.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks HMS #1 among medical schools for research.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Affiliated hospitals support clinical and translational studies.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Students join labs across HMS and affiliated institutions.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research portfolios.",
            },
            {
                "label": "Living costs",
                "sentiment": "caution",
                "detail": "Boston housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Medical School",
                "url": "https://hms.harvard.edu/education",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/harvard-university-04098",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-medicine-phd": {
        "summary": "Graduate students describe Harvard Medical School's Medicine as a research-intensive degree \u2014 U.S. News ranks HMS #1 for research (2026) \u2014 with access to affiliated hospitals; praise includes translational research infrastructure, with cautions about competitive residency matching and Boston living costs.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks HMS #1 among medical schools for research.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Affiliated hospitals support clinical and translational studies.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Students join labs across HMS and affiliated institutions.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research portfolios.",
            },
            {
                "label": "Living costs",
                "sentiment": "caution",
                "detail": "Boston housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard Medical School",
                "url": "https://hms.harvard.edu/education",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/harvard-university-04098",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-mla": {
        "summary": "Graduate students describe Harvard GSD's Master in Landscape Architecture (M.L.A.) as a design-intensive degree in one of the nation's top-ranked landscape programs \u2014 U.S. News ranks Harvard among leading graduate architecture and design schools; praise includes studio culture and visiting critics, with cautions about demanding studio workloads and a profession with variable job security.",
        "themes": [
            {
                "label": "Top design rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard GSD among leading graduate design programs.",
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the M.L.A. curriculum.",
            },
            {
                "label": "Visiting critics",
                "sentiment": "positive",
                "detail": "Leading landscape architects review student work.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Design studios require long hours and iterative critique.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Landscape architecture hiring cycles with the construction economy.",
            },
        ],
        "sources": [
            {
                "label": "Harvard GSD \u2014 Landscape Architecture",
                "url": "https://www.gsd.harvard.edu/landscape-architecture/",
            },
            {
                "label": "U.S. News \u2014 Architecture rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-public-health-bs": {
        "summary": "Graduate students describe Harvard Chan's undergraduate in Public Health as a research-oriented health degree \u2014 U.S. News ranks Harvard #1 among public-health schools (2026) \u2014 with praise for epidemiology and health-policy faculty; cautions include self-funded tuition for some master's tracks and a smaller cohort than large public-health schools.",
        "themes": [
            {
                "label": "Top public-health rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard #1 among schools of public health.",
            },
            {
                "label": "Epidemiology strength",
                "sentiment": "positive",
                "detail": "Faculty lead work in chronic disease, global health, and biostatistics.",
            },
            {
                "label": "Policy connections",
                "sentiment": "positive",
                "detail": "Proximity to HKS and HMS supports health-policy study.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students may self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public-health schools at Michigan or Johns Hopkins.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard T.H. Chan School of Public Health",
                "url": "https://www.hsph.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/harvard-university-04098",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-public-health-ms": {
        "summary": "Graduate students describe Harvard Chan's graduate in in Public Health as a research-oriented health degree \u2014 U.S. News ranks Harvard #1 among public-health schools (2026) \u2014 with praise for epidemiology and health-policy faculty; cautions include self-funded tuition for some master's tracks and a smaller cohort than large public-health schools.",
        "themes": [
            {
                "label": "Top public-health rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard #1 among schools of public health.",
            },
            {
                "label": "Epidemiology strength",
                "sentiment": "positive",
                "detail": "Faculty lead work in chronic disease, global health, and biostatistics.",
            },
            {
                "label": "Policy connections",
                "sentiment": "positive",
                "detail": "Proximity to HKS and HMS supports health-policy study.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students may self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public-health schools at Michigan or Johns Hopkins.",
            },
        ],
        "sources": [
            {
                "label": "Harvard \u2014 Harvard T.H. Chan School of Public Health",
                "url": "https://www.hsph.harvard.edu/",
            },
            {
                "label": "U.S. News \u2014 Harvard University",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/harvard-university-04098",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "harvard-sm-public-health": {
        "summary": "Graduate students describe Harvard Chan's Master of Science in Public Health as a research-oriented health degree \u2014 U.S. News ranks Harvard #1 among public-health schools (2026) \u2014 with praise for epidemiology and biostatistics faculty; cautions include self-funded tuition for some master's tracks and a fast-paced curriculum.",
        "themes": [
            {
                "label": "Top public-health rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Harvard #1 among schools of public health.",
            },
            {
                "label": "Epidemiology strength",
                "sentiment": "positive",
                "detail": "Faculty lead work in chronic disease, global health, and biostatistics.",
            },
            {
                "label": "Policy connections",
                "sentiment": "positive",
                "detail": "Proximity to HKS and HMS supports health-policy study.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students may self-fund without assistantships.",
            },
            {
                "label": "Intensive timeline",
                "sentiment": "caution",
                "detail": "Research master's programs require sustained coursework and thesis work.",
            },
        ],
        "sources": [
            {
                "label": "Harvard Chan \u2014 Degree Programs",
                "url": "https://www.hsph.harvard.edu/admissions/degree-programs/",
            },
            {
                "label": "U.S. News \u2014 Harvard T.H. Chan School of Public Health",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/harvard-university-04098",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
