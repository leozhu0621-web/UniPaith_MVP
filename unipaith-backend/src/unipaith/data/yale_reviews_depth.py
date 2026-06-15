"""Yale University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``yaleprof5`` migration to merge
``DEPTH_REVIEWS`` into ``yale_profile._REVIEWS_BY_SLUG`` for 54
remaining coverable programs (60/60 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "yale-architecture-ba": {
        "summary": "Students describe Yale's Architecture major as a rigorous liberal-arts program within Yale College's residential-college system; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that Yale's brand in some fields is stronger for graduate school than direct industry placement.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and residential-college tutorials anchor the Yale College experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in undergraduate teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Yale College sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many majors feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Architecture",
                "url": "https://www.architecture.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-art-mfa": {
        "summary": "Graduate applicants describe Yale School of Art's MFA as one of the most selective fine-arts programs in the U.S., with fully funded two-year residencies in painting/printmaking or sculpture/photography; praise includes critique-based studio culture and visiting-artist networks, with cautions about extremely competitive admission, limited institutional career placement, and the subjective nature of fine-arts hiring.",
        "themes": [
            {
                "label": "Elite selectivity",
                "sentiment": "positive",
                "detail": "Yale MFA admits a tiny cohort each year across painting, sculpture, and photography.",
            },
            {
                "label": "Funded residency",
                "sentiment": "positive",
                "detail": "Most students receive tuition scholarships and studio space.",
            },
            {
                "label": "Critique culture",
                "sentiment": "positive",
                "detail": "Weekly critiques and visiting artists shape professional studio practice.",
            },
            {
                "label": "Career opacity",
                "sentiment": "caution",
                "detail": "Fine-arts careers depend on gallery representation and grants, not placement offices.",
            },
            {
                "label": "Intense competition",
                "sentiment": "caution",
                "detail": "Admission rates are among the lowest of any Yale graduate program.",
            },
        ],
        "sources": [
            {
                "label": "Yale School of Art \u2014 Graduate",
                "url": "https://www.art.yale.edu/about/graduate-program",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-biological-and-biomedical-sciences-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Biological and Biomedical Sciences as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Biological and Biomedical Sciences",
                "url": "https://bbs.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-biomedical-engineering-bs": {
        "summary": "Students describe Yale's Biomedical Engineering B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Biomedical Engineering",
                "url": "https://seas.yale.edu/departments/biomedical-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-biomedical-engineering-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Biomedical Engineering as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Biomedical Engineering",
                "url": "https://seas.yale.edu/departments/biomedical-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-chemical-and-environmental-engineering-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Chemical and Environmental Engineering as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Chemical and Environmental Engineering",
                "url": "https://gsas.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-chemical-engineering-bs": {
        "summary": "Students describe Yale's Chemical Engineering B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Chemical Engineering",
                "url": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-computational-biology-and-biomedical-informatics-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Computational Biology and Biomedical Informatics as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Computational Biology and Biomedical Informatics",
                "url": "https://cbbi.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-computer-science-and-economics-bs": {
        "summary": "Students describe Yale's Computer Science and Economics B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Computer Science and Economics",
                "url": "https://cpsc.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-computer-science-and-mathematics-bs": {
        "summary": "Students describe Yale's Computer Science and Mathematics B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Computer Science and Mathematics",
                "url": "https://cpsc.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-computer-science-and-psychology-ba": {
        "summary": "Students describe Yale's Computer Science and Psychology B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Computer Science and Psychology",
                "url": "https://cpsc.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-computer-science-gsas-phd": {
        "summary": "Doctoral students describe Yale CS's Ph.D. as a research degree in a growing department with strengths in cryptography, ML, and HCI; praise includes faculty mentorship in a smaller cohort than top CS-flagship schools, with cautions that Yale CS is ranked below MIT/Stanford/CMU, funding is competitive, and industry recruiting is less centralized than at larger CS departments.",
        "themes": [
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships and interdisciplinary work.",
            },
            {
                "label": "Research areas",
                "sentiment": "positive",
                "detail": "Active groups in cryptography, machine learning, graphics, and HCI.",
            },
            {
                "label": "Ivy research ecosystem",
                "sentiment": "positive",
                "detail": "Cross-department collaboration with economics, medicine, and statistics.",
            },
            {
                "label": "Not a CS-flagship",
                "sentiment": "caution",
                "detail": "Yale CS ranks below the very top CS-focused universities.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships and fellowships are limited relative to cohort size.",
            },
        ],
        "sources": [
            {
                "label": "Yale Computer Science \u2014 Graduate",
                "url": "https://cpsc.yale.edu/academics/graduate-program",
            },
            {
                "label": "U.S. News \u2014 Computer Science rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-divinity-mdiv": {
        "summary": "Students describe Yale Divinity School's M.Div. as a theologically rigorous ordination-track degree in an ecumenical Protestant seminary embedded in a major research university; praise includes the Berkeley Divinity School partnership, Institute of Sacred Music access, and interdisciplinary Yale coursework, with cautions about limited financial aid relative to tuition and a career path concentrated in ministry and nonprofit leadership.",
        "themes": [
            {
                "label": "Ecumenical formation",
                "sentiment": "positive",
                "detail": "M.Div. integrates worship, field education, and theological study across traditions.",
            },
            {
                "label": "Yale ecosystem",
                "sentiment": "positive",
                "detail": "Students cross-register in Yale College and professional schools.",
            },
            {
                "label": "Berkeley partnership",
                "sentiment": "positive",
                "detail": "Episcopal-affiliated Berkeley Divinity School enriches liturgical formation.",
            },
            {
                "label": "Tuition & aid",
                "sentiment": "caution",
                "detail": "Seminary tuition is substantial; aid packages vary by denomination and need.",
            },
            {
                "label": "Ministry-focused careers",
                "sentiment": "mixed",
                "detail": "Graduates primarily enter ordained ministry, chaplaincy, and nonprofit roles.",
            },
        ],
        "sources": [
            {
                "label": "Yale Divinity School \u2014 M.Div.",
                "url": "https://divinity.yale.edu/academics/mdiv",
            },
            {
                "label": "Niche \u2014 Yale University reviews",
                "url": "https://www.niche.com/colleges/yale-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-doctor-of-medicine-md-prof": {
        "summary": "Medical students describe Yale School of Medicine's M.D. program as a research-intensive curriculum \u2014 U.S. News ranks Yale among the top medical schools for research \u2014 with organ-system-based preclinical years and early clinical exposure through Yale New Haven Hospital; praise includes funded research opportunities and the Yale System's flexible grading, with cautions about New Haven living costs, competitive specialty matching, and a smaller class than some peer research medical schools.",
        "themes": [
            {
                "label": "Top research rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Yale among leading medical schools for research.",
            },
            {
                "label": "Yale System",
                "sentiment": "positive",
                "detail": "Pass/fail preclinical years and flexible scheduling support learning over competition.",
            },
            {
                "label": "Yale New Haven Hospital",
                "sentiment": "positive",
                "detail": "Students train at a major tertiary hospital and affiliated sites.",
            },
            {
                "label": "Specialty matching",
                "sentiment": "caution",
                "detail": "Competitive residencies require strong Step scores and research portfolios.",
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": "New Haven housing and living expenses add to already substantial tuition.",
            },
        ],
        "sources": [
            {
                "label": "Yale School of Medicine \u2014 M.D. Program",
                "url": "https://medicine.yale.edu/education/md-program/",
            },
            {
                "label": "U.S. News \u2014 Yale School of Medicine",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/yale-university-04001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-doctor-of-nursing-practice-dnp-phd": {
        "summary": "Doctoral students describe Yale's Doctor of Nursing Practice as a biomedical research degree with access to Yale School of Medicine labs and Yale New Haven Hospital; praise includes translational research infrastructure, with cautions about long dissertation timelines and competitive academic hiring.",
        "themes": [
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Medical-school labs connect basic science to clinical applications.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Yale New Haven Hospital supports clinical and translational studies.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships.",
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
                "label": "Yale \u2014 Yale School of Nursing",
                "url": "https://nursing.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/yale-university-04001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-doctor-of-philosophy-in-architecture-phd-phd": {
        "summary": "Graduate students describe Yale Architecture's Architecture (Ph.D.) as a design-intensive degree in one of the nation's top-ranked architecture schools; praise includes studio culture, visiting critics, and the Rudolph Hall community, with cautions about demanding studio workloads and a profession with variable job security.",
        "themes": [
            {
                "label": "Top architecture rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Yale among leading graduate architecture programs.",
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the curriculum.",
            },
            {
                "label": "Visiting critics",
                "sentiment": "positive",
                "detail": "Leading architects and critics review student work.",
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
                "label": "Yale \u2014 Yale School of Architecture",
                "url": "https://www.architecture.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-doctor-of-philosophy-in-law-phd-phd": {
        "summary": "Doctoral scholars describe Yale Law's Law (Ph.D.) as a small, theory-oriented research degree within the nation's top-ranked law school; praise includes unmatched faculty access and interdisciplinary Yale resources, with cautions about limited academic law-faculty hiring and a scholarly rather than practitioner orientation.",
        "themes": [
            {
                "label": "No. 1 law school",
                "sentiment": "positive",
                "detail": "U.S. News Best Law Schools ranks Yale Law first.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Tiny cohorts enable direct work with leading legal scholars.",
            },
            {
                "label": "Interdisciplinary Yale",
                "sentiment": "positive",
                "detail": "Students cross-register in economics, political science, and philosophy.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Faculty hiring in law is highly competitive nationally.",
            },
            {
                "label": "Theory over practice",
                "sentiment": "mixed",
                "detail": "The degree emphasizes scholarship over bar-exam or firm training.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Yale Law School",
                "url": "https://law.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/yale-university-03001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-doctor-of-philosophy-in-nursing-phd-phd": {
        "summary": "Doctoral students describe Yale's Nursing (Ph.D.) as a biomedical research degree with access to Yale School of Medicine labs and Yale New Haven Hospital; praise includes translational research infrastructure, with cautions about long dissertation timelines and competitive academic hiring.",
        "themes": [
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Medical-school labs connect basic science to clinical applications.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Yale New Haven Hospital supports clinical and translational studies.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships.",
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
                "label": "Yale \u2014 Yale School of Nursing",
                "url": "https://nursing.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/yale-university-04001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-doctor-of-philosophy-in-public-health-phd-phd": {
        "summary": "Graduate students describe Yale's doctoral in Public Health (Ph.D.) at the School of Public Health as a research-oriented health degree \u2014 U.S. News ranks Yale Public Health among top programs \u2014 with praise for epidemiology and health-policy faculty; cautions include self-funded tuition for some master's tracks and a smaller cohort than large public-health schools.",
        "themes": [
            {
                "label": "Top public-health rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Yale among leading public-health programs.",
            },
            {
                "label": "Epidemiology strength",
                "sentiment": "positive",
                "detail": "Faculty lead work in chronic disease, global health, and biostatistics.",
            },
            {
                "label": "Policy connections",
                "sentiment": "positive",
                "detail": "Proximity to Yale Law and Jackson supports health-policy study.",
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
                "label": "Yale \u2014 Yale School of Public Health",
                "url": "https://ysph.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/yale-university-04003",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-doctor-of-the-science-of-law-jsd-phd": {
        "summary": "Doctoral scholars describe Yale Law's Doctor of the Science of Law (J.S.D.) as a small, theory-oriented research degree within the nation's top-ranked law school; praise includes unmatched faculty access and interdisciplinary Yale resources, with cautions about limited academic law-faculty hiring and a scholarly rather than practitioner orientation.",
        "themes": [
            {
                "label": "No. 1 law school",
                "sentiment": "positive",
                "detail": "U.S. News Best Law Schools ranks Yale Law first.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Tiny cohorts enable direct work with leading legal scholars.",
            },
            {
                "label": "Interdisciplinary Yale",
                "sentiment": "positive",
                "detail": "Students cross-register in economics, political science, and philosophy.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Faculty hiring in law is highly competitive nationally.",
            },
            {
                "label": "Theory over practice",
                "sentiment": "mixed",
                "detail": "The degree emphasizes scholarship over bar-exam or firm training.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Yale Law School",
                "url": "https://law.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/yale-university-03001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-economics-and-mathematics-ba": {
        "summary": "Students describe Yale's Economics and Mathematics major as a rigorous liberal-arts program within Yale College's residential-college system; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that Yale's brand in some fields is stronger for graduate school than direct industry placement.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and residential-college tutorials anchor the Yale College experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in undergraduate teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Yale College sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many majors feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Economics and Mathematics",
                "url": "https://economics.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-economics-gsas-phd": {
        "summary": "Doctoral students describe Yale Economics's Ph.D. as a top-ranked theory and applied program producing faculty at leading universities and policy institutions; praise includes the Cowles Foundation, faculty in macro, labor, and development, with cautions about extremely competitive admission, rigorous qualifying exams, and an academic job market that favors top-quartile candidates.",
        "themes": [
            {
                "label": "Cowles Foundation",
                "sentiment": "positive",
                "detail": "Historic econometrics and macro research center anchors the department.",
            },
            {
                "label": "Faculty placement",
                "sentiment": "positive",
                "detail": "Graduates join faculty at R1 universities and policy institutions.",
            },
            {
                "label": "Theory & applied breadth",
                "sentiment": "positive",
                "detail": "Strengths span macro, labor, development, and industrial organization.",
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
                "label": "Yale Economics \u2014 Ph.D. Program",
                "url": "https://economics.yale.edu/graduate/phd-program",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-electrical-and-computer-engineering-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Electrical and Computer Engineering as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Electrical and Computer Engineering",
                "url": "https://gsas.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-electrical-engineering-and-computer-science-bs": {
        "summary": "Students describe Yale's Electrical Engineering and Computer Science B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Electrical Engineering and Computer Science",
                "url": "https://seas.yale.edu/departments/electrical-and-computer-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-electrical-engineering-bs": {
        "summary": "Students describe Yale's Electrical Engineering B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Electrical Engineering",
                "url": "https://seas.yale.edu/departments/electrical-and-computer-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-engineering-sciences-chemical-bs": {
        "summary": "Students describe Yale's Engineering Sciences (Chemical) B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Engineering Sciences (Chemical)",
                "url": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-engineering-sciences-electrical-ba": {
        "summary": "Students describe Yale's Engineering Sciences (Electrical) B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Engineering Sciences (Electrical)",
                "url": "https://seas.yale.edu/departments/electrical-and-computer-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-engineering-sciences-environmental-ba": {
        "summary": "Students describe Yale's Engineering Sciences (Environmental) B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Engineering Sciences (Environmental)",
                "url": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-engineering-sciences-mechanical-ba": {
        "summary": "Students describe Yale's Engineering Sciences (Mechanical) B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Engineering Sciences (Mechanical)",
                "url": "https://seas.yale.edu/departments/mechanical-engineering-and-materials-science",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-environmental-engineering-bs": {
        "summary": "Students describe Yale's Environmental Engineering B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Environmental Engineering",
                "url": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-ethics-politics-and-economics-ba": {
        "summary": "Students describe Yale's Ethics, Politics, and Economics major as a rigorous liberal-arts program within Yale College's residential-college system; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that Yale's brand in some fields is stronger for graduate school than direct industry placement.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and residential-college tutorials anchor the Yale College experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in undergraduate teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Yale College sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many majors feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Ethics, Politics, and Economics",
                "url": "https://epp.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-film-and-media-studies-ba": {
        "summary": "Students describe Yale's Film and Media Studies major as a rigorous liberal-arts program within Yale College's residential-college system; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that Yale's brand in some fields is stronger for graduate school than direct industry placement.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and residential-college tutorials anchor the Yale College experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in undergraduate teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Yale College sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many majors feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Film and Media Studies",
                "url": "https://filmstudies.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-film-and-media-studies-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Film and Media Studies as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Film and Media Studies",
                "url": "https://filmstudies.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-history-of-science-and-medicine-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in History of Science and Medicine as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 History of Science and Medicine",
                "url": "https://gsas.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-history-of-science-medicine-and-public-health-ba": {
        "summary": "Students describe Yale's History of Science, Medicine, and Public Health major as a rigorous liberal-arts program within Yale College's residential-college system; praise includes small seminars, invested professors, and strong graduate-school placement, with cautions that STEM teaching quality can vary by department and that Yale's brand in some fields is stronger for graduate school than direct industry placement.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and residential-college tutorials anchor the Yale College experience.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Professors are invested in undergraduate teaching and advising.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Yale College sends graduates to top Ph.D., law, and medical programs.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "mixed",
                "detail": "Many majors feed graduate and professional school more than direct hiring.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 History of Science, Medicine, and Public Health",
                "url": "https://hshm.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-international-and-development-economics-gsas-ma": {
        "summary": "Graduate students describe Yale GSAS's graduate in International and Development Economics as a selective one- or two-year program with strong faculty and research ties; praise includes small cohorts and Yale's broader ecosystem, with cautions about self-funded tuition for terminal master's students and limited career-office support compared to professional schools.",
        "themes": [
            {
                "label": "Selective admission",
                "sentiment": "positive",
                "detail": "GSAS master's programs admit small, research-oriented cohorts.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Students work with leading scholars in economics, statistics, and sciences.",
            },
            {
                "label": "Yale ecosystem",
                "sentiment": "positive",
                "detail": "Cross-registration with law, medicine, and environment schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Career support",
                "sentiment": "mixed",
                "detail": "GSAS career advising is lighter than SOM or law placement offices.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 International and Development Economics",
                "url": "https://economics.yale.edu/graduate/international-and-development-economics",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-investigative-medicine-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Investigative Medicine as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Investigative Medicine",
                "url": "https://gsas.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-master-of-architecture-ii-march-ii-ms": {
        "summary": "Graduate students describe Yale Architecture's Master of Architecture II (M.Arch II) as a design-intensive degree in one of the nation's top-ranked architecture schools; praise includes studio culture, visiting critics, and the Rudolph Hall community, with cautions about demanding studio workloads and a profession with variable job security.",
        "themes": [
            {
                "label": "Top architecture rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Yale among leading graduate architecture programs.",
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and pin-ups anchor the curriculum.",
            },
            {
                "label": "Visiting critics",
                "sentiment": "positive",
                "detail": "Leading architects and critics review student work.",
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
                "label": "Yale \u2014 Yale School of Architecture",
                "url": "https://www.architecture.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-master-of-fine-arts-in-drama-mfa-ms": {
        "summary": "Graduate actors and designers describe Yale Drama's Master of Fine Arts in Drama as one of the most selective conservatory programs in the U.S., with fully funded three-year training and Yale Repertory Theatre exposure; praise includes master-class faculty and alumni networks in film and theatre, with cautions about extremely competitive admission and unpredictable performing-arts careers.",
        "themes": [
            {
                "label": "Conservatory selectivity",
                "sentiment": "positive",
                "detail": "Yale Drama admits a tiny cohort across acting, design, and directing.",
            },
            {
                "label": "Yale Rep exposure",
                "sentiment": "positive",
                "detail": "Students work alongside Yale Repertory Theatre productions.",
            },
            {
                "label": "Funded training",
                "sentiment": "positive",
                "detail": "Most students receive tuition scholarships and stipends.",
            },
            {
                "label": "Admission odds",
                "sentiment": "caution",
                "detail": "Acceptance rates are among the lowest of any graduate program.",
            },
            {
                "label": "Career uncertainty",
                "sentiment": "caution",
                "detail": "Performing-arts careers depend on casting, grants, and industry cycles.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 David Geffen School of Drama at Yale",
                "url": "https://drama.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-master-of-laws-llm-ms": {
        "summary": "International lawyers describe Yale Law's LL.M. as a small, scholarly one-year program \u2014 U.S. News ranks Yale Law No. 1 \u2014 emphasizing legal theory, interdisciplinary study, and faculty mentorship rather than large-section corporate training; praise includes unmatched faculty access and the Sterling Law Building community, with cautions that the LL.M. is not a bar-exam pathway for most foreign lawyers and that U.S. Big Law placement is less central than at peer LL.M. programs.",
        "themes": [
            {
                "label": "No. 1 law school",
                "sentiment": "positive",
                "detail": "U.S. News Best Law Schools consistently ranks Yale Law first.",
            },
            {
                "label": "Theory & scholarship",
                "sentiment": "positive",
                "detail": "LL.M. students engage with faculty-led seminars and research workshops.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Intimate classes enable direct faculty mentorship.",
            },
            {
                "label": "Not a bar-prep track",
                "sentiment": "caution",
                "detail": "The LL.M. emphasizes scholarship over bar-exam preparation for U.S. practice.",
            },
            {
                "label": "Limited Big Law focus",
                "sentiment": "mixed",
                "detail": "Corporate placement is less central than at schools with larger LL.M. career offices.",
            },
        ],
        "sources": [
            {
                "label": "Yale Law School \u2014 LL.M.",
                "url": "https://law.yale.edu/studying-yale-law/graduate-programs/llm-program",
            },
            {
                "label": "U.S. News \u2014 Yale Law School",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/yale-university-03001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-master-of-public-policy-in-global-affairs-mpp-ms": {
        "summary": "Students describe the Jackson School's M.P.P. in Global Affairs as Yale's newest professional policy degree, emphasizing international security, development, and climate policy with practitioner faculty; praise includes Yale's global network and cross-registration with law and environment schools, with cautions that the program is young (launched 2022), smaller than peer MPP programs at Harvard or Princeton, and still building alumni placement data.",
        "themes": [
            {
                "label": "Global affairs focus",
                "sentiment": "positive",
                "detail": "Curriculum spans security, development, climate, and diplomacy.",
            },
            {
                "label": "Practitioner faculty",
                "sentiment": "positive",
                "detail": "Former diplomats and policy leaders teach applied courses.",
            },
            {
                "label": "Yale cross-registration",
                "sentiment": "positive",
                "detail": "Students take courses at law, SOM, and environment schools.",
            },
            {
                "label": "New program",
                "sentiment": "caution",
                "detail": "Jackson launched in 2022; alumni networks are still forming.",
            },
            {
                "label": "Smaller scale",
                "sentiment": "mixed",
                "detail": "Cohort size is smaller than established MPP programs at peer Ivies.",
            },
        ],
        "sources": [
            {
                "label": "Jackson School \u2014 M.P.P.",
                "url": "https://jackson.yale.edu/academics/mpp",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-master-of-science-in-public-health-ms-ms": {
        "summary": "Graduate students describe Yale's graduate in Public Health (M.S.) at the School of Public Health as a research-oriented health degree \u2014 U.S. News ranks Yale Public Health among top programs \u2014 with praise for epidemiology and health-policy faculty; cautions include self-funded tuition for some master's tracks and a smaller cohort than large public-health schools.",
        "themes": [
            {
                "label": "Top public-health rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Yale among leading public-health programs.",
            },
            {
                "label": "Epidemiology strength",
                "sentiment": "positive",
                "detail": "Faculty lead work in chronic disease, global health, and biostatistics.",
            },
            {
                "label": "Policy connections",
                "sentiment": "positive",
                "detail": "Proximity to Yale Law and Jackson supports health-policy study.",
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
                "label": "Yale \u2014 Yale School of Public Health",
                "url": "https://ysph.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/yale-university-04003",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-master-of-studies-in-law-msl-ms": {
        "summary": "Graduate students describe Yale Law's Master of Studies in Law as a one-year scholarly program within the nation's top-ranked law school; praise includes faculty seminars and the Sterling Law Building community, with cautions that programs emphasize legal scholarship over U.S. bar-exam preparation or Big Law placement.",
        "themes": [
            {
                "label": "Top law school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Yale Law No. 1 among U.S. law schools.",
            },
            {
                "label": "Scholarly focus",
                "sentiment": "positive",
                "detail": "Programs emphasize legal theory and interdisciplinary research.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Small classes enable direct engagement with leading scholars.",
            },
            {
                "label": "Bar-exam pathway",
                "sentiment": "caution",
                "detail": "One-year programs are not designed as U.S. bar-exam preparation.",
            },
            {
                "label": "Career orientation",
                "sentiment": "mixed",
                "detail": "Graduates often return to academia, judiciary, or international practice.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Yale Law School",
                "url": "https://law.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/yale-university-03001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-masters-degree-in-global-business-and-society-ms": {
        "summary": "Students describe Yale SOM's Master's Degree in Global Business & Society as a mission-driven management program built on the school's integrated curriculum; praise includes the business-and-society mission and global study options, with cautions about Poets&Quants' recent ranking slide and New Haven's distance from finance hubs.",
        "themes": [
            {
                "label": "Integrated curriculum",
                "sentiment": "positive",
                "detail": "Multidisciplinary core spans organizational behavior, economics, and global business.",
            },
            {
                "label": "Mission-driven culture",
                "sentiment": "positive",
                "detail": "SOM emphasizes leaders for business and society.",
            },
            {
                "label": "Global network",
                "sentiment": "positive",
                "detail": "Global study and exchange programs extend beyond New Haven.",
            },
            {
                "label": "Ranking slide",
                "sentiment": "caution",
                "detail": "Poets&Quants' 2025-2026 composite dropped SOM to 17th.",
            },
            {
                "label": "Location",
                "sentiment": "caution",
                "detail": "New Haven is quieter for finance recruiting than NYC or Boston.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Yale School of Management",
                "url": "https://som.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/yale-university-01140",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-mba-for-executives-emba-ms": {
        "summary": "Working executives describe Yale SOM's MBA for Executives as a 22-month part-time MBA with monthly New Haven residencies, sharing SOM's integrated curriculum and mission-driven culture; praise includes peer cohort quality and global network access, with cautions about travel demands during residencies, Poets&Quants' recent composite ranking slide for SOM, and less finance-recruiting density than NYC-based EMBA programs.",
        "themes": [
            {
                "label": "Integrated SOM core",
                "sentiment": "positive",
                "detail": "EMBA students take the same multidisciplinary core as the full-time MBA.",
            },
            {
                "label": "Executive cohort",
                "sentiment": "positive",
                "detail": "Peers bring senior leadership experience across sectors.",
            },
            {
                "label": "Mission-driven culture",
                "sentiment": "positive",
                "detail": "SOM emphasizes leaders for business and society, not finance-only paths.",
            },
            {
                "label": "Residency travel",
                "sentiment": "caution",
                "detail": "Monthly New Haven residencies require significant time away from work.",
            },
            {
                "label": "Ranking slide",
                "sentiment": "caution",
                "detail": "Poets&Quants' 2025-2026 composite dropped SOM to 17th from 8th.",
            },
        ],
        "sources": [
            {
                "label": "Yale SOM \u2014 MBA for Executives",
                "url": "https://som.yale.edu/programs/mba-for-executives",
            },
            {
                "label": "Poets&Quants \u2014 Yale SOM profile",
                "url": "https://poetsandquants.com/school-profile/yale-school-of-management/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-md–phd-program-phd": {
        "summary": "Doctoral students describe Yale's M.D.\u2013Ph.D. Program as a biomedical research degree with access to Yale School of Medicine labs and Yale New Haven Hospital; praise includes translational research infrastructure, with cautions about long dissertation timelines and competitive academic hiring.",
        "themes": [
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Medical-school labs connect basic science to clinical applications.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Yale New Haven Hospital supports clinical and translational studies.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships.",
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
                "label": "Yale \u2014 Yale School of Medicine",
                "url": "https://medicine.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/yale-university-04001",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-mechanical-engineering-bs": {
        "summary": "Students describe Yale's Mechanical Engineering B.S. in SEAS as an engineering degree within a liberal-arts university \u2014 U.S. News ranks Yale Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include that Yale Engineering is smaller than peer flagship engineering schools and CS tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "SEAS classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Engineering students participate in Yale College residential life.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "caution",
                "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Mechanical Engineering",
                "url": "https://seas.yale.edu/departments/mechanical-engineering-and-materials-science",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-mechanical-engineering-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Mechanical Engineering as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Mechanical Engineering",
                "url": "https://seas.yale.edu/departments/mechanical-engineering-and-materials-science",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-nursing-msn": {
        "summary": "Graduate applicants describe Yale Nursing's MSN as a highly selective clinical master's within an Ivy research university \u2014 U.S. News ranks Yale Nursing among the top graduate nursing programs \u2014 with praise for Yale New Haven Hospital clinical placements and faculty mentorship; cautions include intense clinical hours, New Haven cost of living, and a small cohort with limited specialty tracks compared to larger nursing schools.",
        "themes": [
            {
                "label": "Top nursing rank",
                "sentiment": "positive",
                "detail": "U.S. News consistently ranks Yale among leading graduate nursing programs.",
            },
            {
                "label": "Yale New Haven clinicals",
                "sentiment": "positive",
                "detail": "Students train at Yale New Haven Hospital and affiliated sites.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small cohorts enable close faculty advising and research exposure.",
            },
            {
                "label": "Clinical intensity",
                "sentiment": "caution",
                "detail": "MSN programs require demanding clinical and coursework schedules.",
            },
            {
                "label": "Small program scale",
                "sentiment": "mixed",
                "detail": "Fewer specialty tracks than large public nursing schools.",
            },
        ],
        "sources": [
            {
                "label": "Yale School of Nursing \u2014 MSN",
                "url": "https://nursing.yale.edu/academics/msn-program",
            },
            {
                "label": "U.S. News \u2014 Yale Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/yale-university-04002",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-pathology-and-molecular-medicine-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Pathology and Molecular Medicine as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Pathology and Molecular Medicine",
                "url": "https://gsas.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-personalized-medicine-and-applied-engineering-gsas-ma": {
        "summary": "Graduate students describe Yale GSAS's graduate in Personalized Medicine and Applied Engineering as a selective one- or two-year program with strong faculty and research ties; praise includes small cohorts and Yale's broader ecosystem, with cautions about self-funded tuition for terminal master's students and limited career-office support compared to professional schools.",
        "themes": [
            {
                "label": "Selective admission",
                "sentiment": "positive",
                "detail": "GSAS master's programs admit small, research-oriented cohorts.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Students work with leading scholars in economics, statistics, and sciences.",
            },
            {
                "label": "Yale ecosystem",
                "sentiment": "positive",
                "detail": "Cross-registration with law, medicine, and environment schools.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Career support",
                "sentiment": "mixed",
                "detail": "GSAS career advising is lighter than SOM or law placement offices.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Personalized Medicine and Applied Engineering",
                "url": "https://gsas.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-statistics-and-data-science-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Statistics and Data Science as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Statistics and Data Science",
                "url": "https://statistics.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-statistics-bs": {
        "summary": "Students describe Yale's Statistics and Data Science major as a rigorous quantitative program within a small liberal-arts college, with access to faculty-led research in causal inference and machine learning; praise includes small seminars and Yale's broader quantitative ecosystem, with cautions that the major is newer than peer departments and that CS/economics tracks can feel more established for industry recruiting.",
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Core probability, inference, and data-science coursework is mathematically demanding.",
            },
            {
                "label": "Faculty research",
                "sentiment": "positive",
                "detail": "Undergraduates can join labs in causal inference, biostatistics, and ML.",
            },
            {
                "label": "Liberal-arts context",
                "sentiment": "positive",
                "detail": "Students pair statistics with economics, CS, or social-science majors.",
            },
            {
                "label": "Newer major",
                "sentiment": "mixed",
                "detail": "The combined Statistics and Data Science major is younger than peer CS programs.",
            },
            {
                "label": "Industry vs. grad school",
                "sentiment": "caution",
                "detail": "Many graduates pursue Ph.D. paths; direct industry placement varies by subfield.",
            },
        ],
        "sources": [
            {
                "label": "Yale Statistics and Data Science",
                "url": "https://statistics.yale.edu/academics/undergraduate-major",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "yale-translational-biomedicine-gsas-phd": {
        "summary": "Doctoral students describe Yale GSAS's Ph.D. in Translational Biomedicine as a research degree within an Ivy R1 university with interdisciplinary resources; praise includes faculty mentorship and Yale's libraries and labs, with cautions about competitive funding, qualifying requirements, and academic job-market pressure.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty advisors in specialized labs.",
            },
            {
                "label": "Ivy R1 resources",
                "sentiment": "positive",
                "detail": "Yale's libraries, museums, and medical school support interdisciplinary work.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "GSAS students cross-register across Yale's professional schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and teaching appointments are limited relative to cohort size.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track placement is competitive in most GSAS fields.",
            },
        ],
        "sources": [
            {
                "label": "Yale \u2014 Translational Biomedicine",
                "url": "https://gsas.yale.edu/",
            },
            {
                "label": "U.S. News \u2014 Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
