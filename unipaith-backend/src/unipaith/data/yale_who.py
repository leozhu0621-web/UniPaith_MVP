"""Yale University — universal ``who_its_for`` depth field per program.

REPAIR_BACKLOG #4 (SKILL miss #8): a UNIVERSAL depth field that must be filled on EVERY
program AND be PROGRAM-DISTINCT (distinct strings / programs approximately 1.0), never a
degree-type template keyed on credential alone. Each statement names the applicant the
program fits — the field's substance, who is drawn to it, and the typical next step —
derived strictly from that program's own field and degree level. No fabricated facts (no
rankings, numbers, or named centers), matching the field-specific gold bar (Duke/Emory/
Brown/Purdue). All strings are distinct (distinct/total = 1.0): the bachelor's, master's,
and doctoral rows of one field read differently because a survey major, a specialized
master's, and a funded dissertation study the field at different depths.
"""

from __future__ import annotations

WHO_BY_SLUG: dict[str, str] = {
    'yale-economics-bs': (
        'Undergraduates drawn to the analysis of markets, incentives, and policy through '
        'micro, macro, and econometric reasoning. Suited to graduate study or careers in '
        'policy, research, law, and the professions.'
    ),
    'yale-computer-science-bs': (
        'Undergraduates drawn to computing — algorithms, systems, theory, and artificial '
        'intelligence. Suited to graduate study, research, or quantitative and technical '
        'careers.'
    ),
    'yale-political-science-bs': (
        'Undergraduates drawn to political institutions, behavior, and theory across '
        'American, comparative, and international politics. Suited to graduate study or '
        'careers in policy, research, law, and the professions.'
    ),
    'yale-history-bs': (
        'Undergraduates drawn to the human past across periods and regions, read through '
        'primary sources and argument. Suited to graduate study or careers in writing, '
        'education, culture, law, and public life.'
    ),
    'yale-mcdb-bs': (
        'Undergraduates drawn to the molecular basis of life — genetics, cell biology, and '
        'how organisms develop. Suited to graduate study, research, or quantitative and '
        'technical careers.'
    ),
    'yale-psychology-bs': (
        'Undergraduates drawn to the science of mind and behavior, from cognition and '
        'development to social and clinical questions. Suited to graduate study or careers in '
        'policy, research, law, and the professions.'
    ),
    'yale-global-affairs-bs': (
        'Undergraduates drawn to international policy, security, and development across '
        'disciplines. Suited to graduate study or careers in policy, research, law, and the '
        'professions.'
    ),
    'yale-english-bs': (
        'Undergraduates drawn to literature in English, criticism, and creative writing. '
        'Suited to graduate study or careers in writing, education, culture, law, and public '
        'life.'
    ),
    'yale-statistics-bs': (
        'Undergraduates drawn to probability, statistical inference, and data-driven '
        'computation. Suited to graduate study, research, or quantitative and technical '
        'careers.'
    ),
    'yale-mathematics-bs': (
        'Undergraduates drawn to rigorous mathematics — analysis, algebra, geometry, and '
        'number theory. Suited to graduate study, research, or quantitative and technical '
        'careers.'
    ),
    'yale-mba': (
        'Graduate students seeking advanced, specialized study of leadership and management '
        'across business and society, taught through an integrated core. Best for those '
        'advancing into senior professional practice.'
    ),
    'yale-environmental-management-mem': (
        'Graduate students seeking advanced, specialized study of environmental policy, '
        'management, and science for environmental leadership. Best for those advancing into '
        'senior professional practice.'
    ),
    'yale-environmental-science-mesc': (
        'Graduate students seeking advanced, specialized study of research-grade '
        'environmental science — ecology, ecosystems, and global change. Best for those '
        'advancing into senior professional practice.'
    ),
    'yale-public-health-mph': (
        'Graduate students seeking advanced, specialized study of population health through '
        'epidemiology, biostatistics, environmental health, and health policy. Best for those '
        'advancing into senior professional practice.'
    ),
    'yale-physician-associate-mmsc': (
        'Graduate students seeking advanced, specialized study of clinical training to '
        'practice medicine as a physician associate. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-nursing-msn': (
        'Graduate students seeking advanced, specialized study of advanced-practice nursing '
        'across clinical specialties. Best for those advancing into senior professional '
        'practice.'
    ),
    'yale-divinity-mdiv': (
        'Graduate students seeking advanced, specialized study of theological and ministerial '
        'study for religious leadership and scholarship. Best for those targeting advanced '
        'scholarship, teaching, or expert practice.'
    ),
    'yale-architecture-march': (
        'Graduate students seeking advanced, specialized study of the history, theory, and '
        'design of the built environment. Best for those advancing into senior professional '
        'practice.'
    ),
    'yale-art-mfa': (
        'Graduate students seeking advanced, specialized study of studio art at the highest '
        'level — graphic design, painting, photography, or sculpture. Best for those '
        'targeting advanced scholarship, teaching, or expert practice.'
    ),
    'yale-music-mm': (
        'Graduate students seeking advanced, specialized study of conservatory-level '
        'performance and composition within a research university. Best for those targeting '
        'advanced scholarship, teaching, or expert practice.'
    ),
    'yale-african-studies-ba': (
        'Undergraduates drawn to the histories, languages, politics, and cultures of Africa. '
        'Suited to graduate study or careers in writing, education, culture, law, and public '
        'life.'
    ),
    'yale-american-studies-ba': (
        'Undergraduates drawn to the culture, politics, and history of the United States read '
        'across disciplines. Suited to graduate study or careers in writing, education, '
        'culture, law, and public life.'
    ),
    'yale-anthropology-ba': (
        'Undergraduates drawn to human societies and cultures across time, from ethnography '
        'to material evidence. Suited to graduate study or careers in policy, research, law, '
        'and the professions.'
    ),
    'yale-applied-mathematics-ba': (
        'Undergraduates drawn to mathematics applied to problems in science, engineering, and '
        'computation. Suited to graduate study, research, or quantitative and technical '
        'careers.'
    ),
    'yale-applied-physics-bs': (
        'Undergraduates drawn to the physics of materials, devices, and quantum and optical '
        'systems. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-archaeological-studies-ba': (
        'Undergraduates drawn to the material record of past societies, from excavation to '
        'analysis. Suited to graduate study or careers in policy, research, law, and the '
        'professions.'
    ),
    'yale-architecture-ba': (
        'Undergraduates drawn to the history, theory, and design of the built environment. '
        'Suited to graduate or professional study and to careers in the field.'
    ),
    'yale-art-ba': (
        'Undergraduates drawn to studio practice across drawing, painting, sculpture, and new '
        'media. Suited to graduate study or careers in writing, education, culture, law, and '
        'public life.'
    ),
    'yale-astronomy-ba': (
        'Undergraduates drawn to the physics of stars, galaxies, and the universe. Suited to '
        'graduate study, research, or quantitative and technical careers.'
    ),
    'yale-astrophysics-bs': (
        'Undergraduates drawn to the physical processes governing stars, galaxies, and '
        'cosmology. Suited to graduate study, research, or quantitative and technical '
        'careers.'
    ),
    'yale-biomedical-engineering-bs': (
        'Undergraduates drawn to engineering applied to medicine and human biology. Suited to '
        'graduate study, research, or quantitative and technical careers.'
    ),
    'yale-black-studies-ba': (
        'Undergraduates drawn to the histories, politics, and cultural production of Black '
        'people and the African diaspora. Suited to graduate study or careers in writing, '
        'education, culture, law, and public life.'
    ),
    'yale-chemical-engineering-bs': (
        'Undergraduates drawn to the design of processes that transform matter and energy at '
        'scale. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-chemistry-ba': (
        'Undergraduates drawn to the structure, reactivity, and synthesis of matter across '
        'organic, inorganic, and physical chemistry. Suited to graduate study, research, or '
        'quantitative and technical careers.'
    ),
    'yale-classical-civilization-ba': (
        'Undergraduates drawn to the literature, history, and material culture of ancient '
        'Greece and Rome. Suited to graduate study or careers in writing, education, culture, '
        'law, and public life.'
    ),
    'yale-classics-ba': (
        'Undergraduates drawn to the languages, literatures, and thought of ancient Greece '
        'and Rome. Suited to graduate study or careers in writing, education, culture, law, '
        'and public life.'
    ),
    'yale-cognitive-science-ba': (
        'Undergraduates drawn to the mind as an information-processing system, across '
        'psychology, philosophy, linguistics, and computation. Suited to graduate study or '
        'careers in writing, education, culture, law, and public life.'
    ),
    'yale-comparative-literature-ba': (
        'Undergraduates drawn to literature read across languages, national traditions, and '
        'media. Suited to graduate study or careers in writing, education, culture, law, and '
        'public life.'
    ),
    'yale-computer-science-and-economics-bs': (
        'Undergraduates drawn to the intersection of computation and markets — algorithms, '
        'incentives, and data. Suited to graduate study, research, or quantitative and '
        'technical careers.'
    ),
    'yale-computer-science-and-mathematics-bs': (
        'Undergraduates drawn to the theoretical core shared by computing and mathematics. '
        'Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-computer-science-and-psychology-ba': (
        'Undergraduates drawn to computation and the human mind, from cognition to '
        'human-computer interaction. Suited to graduate study, research, or quantitative and '
        'technical careers.'
    ),
    'yale-computing-and-linguistics-ba': (
        'Undergraduates drawn to language as a computational system, from formal grammar to '
        'language technology. Suited to graduate study, research, or quantitative and '
        'technical careers.'
    ),
    'yale-computing-and-the-arts-ba': (
        'Undergraduates drawn to creative practice made with code, across visual art, music, '
        'and design. Suited to graduate study or careers in writing, education, culture, law, '
        'and public life.'
    ),
    'yale-earth-and-planetary-sciences-ba': (
        'Undergraduates drawn to the physical Earth and planets — geology, climate, and '
        'planetary processes. Suited to graduate study, research, or quantitative and '
        'technical careers.'
    ),
    'yale-east-asian-languages-and-literatures-ba': (
        'Undergraduates drawn to the languages and literary traditions of East Asia. Suited '
        'to graduate study or careers in writing, education, culture, law, and public life.'
    ),
    'yale-east-asian-studies-ba': (
        'Undergraduates drawn to the societies, histories, and cultures of East Asia. Suited '
        'to graduate study or careers in writing, education, culture, law, and public life.'
    ),
    'yale-ecology-and-evolutionary-biology-ba': (
        'Undergraduates drawn to the diversity of life, ecological systems, and evolution. '
        'Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-economics-and-mathematics-ba': (
        'Undergraduates drawn to economic theory expressed and analyzed with rigorous '
        'mathematics. Suited to graduate study or careers in policy, research, law, and the '
        'professions.'
    ),
    'yale-electrical-engineering-bs': (
        'Undergraduates drawn to the engineering of circuits, signals, and electronic and '
        'photonic systems. Suited to graduate study, research, or quantitative and technical '
        'careers.'
    ),
    'yale-electrical-engineering-and-computer-science-bs': (
        'Undergraduates drawn to the joint engineering of computing hardware and software '
        'systems. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-engineering-sciences-chemical-bs': (
        'Undergraduates drawn to chemical engineering grounded in the broad engineering '
        'sciences. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-engineering-sciences-electrical-ba': (
        'Undergraduates drawn to electrical engineering grounded in the broad engineering '
        'sciences. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-engineering-sciences-environmental-ba': (
        'Undergraduates drawn to environmental engineering grounded in the broad engineering '
        'sciences. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-engineering-sciences-mechanical-ba': (
        'Undergraduates drawn to mechanical engineering grounded in the broad engineering '
        'sciences. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-environmental-engineering-bs': (
        'Undergraduates drawn to engineering for clean water, air, and a sustainable '
        'environment. Suited to graduate study, research, or quantitative and technical '
        'careers.'
    ),
    'yale-environmental-studies-ba': (
        'Undergraduates drawn to the environment studied across natural science, policy, and '
        'the humanities. Suited to graduate or professional study and to careers in the '
        'field.'
    ),
    'yale-ethics-politics-and-economics-ba': (
        'Undergraduates drawn to moral, political, and economic reasoning about public '
        'questions. Suited to graduate study or careers in writing, education, culture, law, '
        'and public life.'
    ),
    'yale-ethnicity-race-and-migration-ba': (
        'Undergraduates drawn to race, ethnicity, and migration as forces shaping societies. '
        'Suited to graduate study or careers in writing, education, culture, law, and public '
        'life.'
    ),
    'yale-film-and-media-studies-ba': (
        'Undergraduates drawn to the history, theory, and analysis of film and media. Suited '
        'to graduate study or careers in writing, education, culture, law, and public life.'
    ),
    'yale-french-ba': (
        'Undergraduates drawn to the language, literature, and culture of the French-speaking '
        'world. Suited to graduate study or careers in writing, education, culture, law, and '
        'public life.'
    ),
    'yale-german-studies-ba': (
        'Undergraduates drawn to the language, literature, and intellectual history of the '
        'German-speaking world. Suited to graduate study or careers in writing, education, '
        'culture, law, and public life.'
    ),
    'yale-greek-ancient-and-modern-ba': (
        'Undergraduates drawn to the Greek language and literature from antiquity to the '
        'present. Suited to graduate study or careers in writing, education, culture, law, '
        'and public life.'
    ),
    'yale-history-of-art-ba': (
        'Undergraduates drawn to the visual record of human culture — objects, images, and '
        'buildings across periods. Suited to graduate study or careers in writing, education, '
        'culture, law, and public life.'
    ),
    'yale-history-of-science-medicine-and-public-health-ba': (
        'Undergraduates drawn to how science, medicine, and public health have developed and '
        'shaped society. Suited to graduate study or careers in writing, education, culture, '
        'law, and public life.'
    ),
    'yale-humanities-ba': (
        'Undergraduates drawn to great works and ideas read across literature, philosophy, '
        'and history. Suited to graduate study or careers in writing, education, culture, '
        'law, and public life.'
    ),
    'yale-italian-studies-ba': (
        'Undergraduates drawn to the language, literature, and culture of Italy. Suited to '
        'graduate study or careers in writing, education, culture, law, and public life.'
    ),
    'yale-jewish-studies-ba': (
        'Undergraduates drawn to Jewish history, texts, languages, and thought across eras. '
        'Suited to graduate study or careers in writing, education, culture, law, and public '
        'life.'
    ),
    'yale-latin-american-studies-ba': (
        'Undergraduates drawn to the histories, politics, and cultures of Latin America. '
        'Suited to graduate study or careers in writing, education, culture, law, and public '
        'life.'
    ),
    'yale-linguistics-ba': (
        'Undergraduates drawn to the structure of human language — sound, form, meaning, and '
        'grammar. Suited to graduate study or careers in writing, education, culture, law, '
        'and public life.'
    ),
    'yale-mathematics-and-philosophy-ba': (
        'Undergraduates drawn to the shared foundations of mathematics and philosophy, from '
        'logic to the philosophy of math. Suited to graduate study, research, or quantitative '
        'and technical careers.'
    ),
    'yale-mathematics-and-physics-bs': (
        'Undergraduates drawn to the deep connections between mathematics and the physical '
        'sciences. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-mechanical-engineering-bs': (
        'Undergraduates drawn to the design and analysis of mechanical and thermal systems. '
        'Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-modern-middle-east-studies-ba': (
        'Undergraduates drawn to the modern history, politics, and cultures of the Middle '
        'East. Suited to graduate study or careers in writing, education, culture, law, and '
        'public life.'
    ),
    'yale-molecular-biophysics-and-biochemistry-ba': (
        'Undergraduates drawn to the molecular machinery of life — biochemistry, biophysics, '
        'and molecular biology. Suited to graduate study, research, or quantitative and '
        'technical careers.'
    ),
    'yale-music-ba': (
        'Undergraduates drawn to music as an academic discipline — theory, history, and '
        'practice. Suited to graduate study or careers in writing, education, culture, law, '
        'and public life.'
    ),
    'yale-near-eastern-languages-and-civilizations-ba': (
        'Undergraduates drawn to the languages and civilizations of the ancient and modern '
        'Near East. Suited to graduate study or careers in writing, education, culture, law, '
        'and public life.'
    ),
    'yale-neuroscience-ba': (
        'Undergraduates drawn to the biology of the nervous system, from molecules to '
        'behavior. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-philosophy-ba': (
        'Undergraduates drawn to fundamental questions of knowledge, reality, ethics, and '
        'logic. Suited to graduate study or careers in writing, education, culture, law, and '
        'public life.'
    ),
    'yale-physics-bs': (
        'Undergraduates drawn to the fundamental laws governing matter, energy, space, and '
        'time. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-physics-and-geosciences-bs': (
        'Undergraduates drawn to physics applied to the Earth and planetary systems. Suited '
        'to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-physics-and-philosophy-ba': (
        'Undergraduates drawn to physics together with the philosophical foundations of '
        'science. Suited to graduate study, research, or quantitative and technical careers.'
    ),
    'yale-portuguese-ba': (
        'Undergraduates drawn to the language, literature, and culture of the '
        'Portuguese-speaking world. Suited to graduate study or careers in writing, '
        'education, culture, law, and public life.'
    ),
    'yale-religious-studies-ba': (
        'Undergraduates drawn to religious traditions, texts, and practices studied '
        'analytically. Suited to graduate study or careers in writing, education, culture, '
        'law, and public life.'
    ),
    'yale-russian-ba': (
        'Undergraduates drawn to the Russian language, literature, and culture. Suited to '
        'graduate study or careers in writing, education, culture, law, and public life.'
    ),
    'yale-russian-east-european-and-eurasian-studies-ba': (
        'Undergraduates drawn to the histories, politics, and cultures of Russia, Eastern '
        'Europe, and Eurasia. Suited to graduate study or careers in writing, education, '
        'culture, law, and public life.'
    ),
    'yale-sociology-ba': (
        'Undergraduates drawn to the structure of social life — institutions, inequality, and '
        'social change. Suited to graduate study or careers in policy, research, law, and the '
        'professions.'
    ),
    'yale-spanish-ba': (
        'Undergraduates drawn to the language, literature, and culture of the '
        'Spanish-speaking world. Suited to graduate study or careers in writing, education, '
        'culture, law, and public life.'
    ),
    'yale-theater-dance-and-performance-studies-ba': (
        'Undergraduates drawn to theater, dance, and performance as art forms and objects of '
        'study. Suited to graduate study or careers in writing, education, culture, law, and '
        'public life.'
    ),
    'yale-urban-studies-ba': (
        'Undergraduates drawn to cities — their design, politics, economies, and social life. '
        'Suited to graduate study or careers in policy, research, law, and the professions.'
    ),
    'yale-womens-gender-and-sexuality-studies-ba': (
        'Undergraduates drawn to gender and sexuality as categories shaping culture, '
        'politics, and knowledge. Suited to graduate study or careers in writing, education, '
        'culture, law, and public life.'
    ),
    'yale-juris-doctor-jd-prof': (
        'Students preparing for a professional career grounded in the law through small '
        'classes and a scholarly, public-interest tradition. Best for those advancing into '
        'senior professional practice.'
    ),
    'yale-master-of-laws-llm-ms': (
        'Graduate students seeking advanced, specialized study of advanced legal study for '
        'those who already hold a first degree in law. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-master-of-studies-in-law-msl-ms': (
        'Graduate students seeking advanced, specialized study of legal reasoning for '
        'accomplished professionals in other fields. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-doctor-of-the-science-of-law-jsd-phd': (
        'Prospective scholars who want to make original contributions to doctoral legal '
        'research for future legal scholars, ready for funded doctoral study and a '
        'dissertation. Best for those advancing into senior professional practice.'
    ),
    'yale-doctor-of-philosophy-in-law-phd-phd': (
        'Prospective scholars who want to make original contributions to legal scholarship at '
        'the doctoral level for J.D. holders, ready for funded doctoral study and a '
        'dissertation. Best for those advancing into senior professional practice.'
    ),
    'yale-mba-for-executives-emba-ms': (
        'Graduate students seeking advanced, specialized study of management for working '
        'professionals, with a focus in asset management, healthcare, or sustainability. Best '
        'for those advancing into senior professional practice.'
    ),
    'yale-master-of-advanced-management-mam-ms': (
        'Graduate students seeking advanced, specialized study of global management for '
        'graduates of leading business schools. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-masters-degree-in-asset-management-ms': (
        'Graduate students seeking advanced, specialized study of the theory and practice of '
        'managing investment portfolios. Best for those advancing into senior professional '
        'practice.'
    ),
    'yale-masters-degree-in-global-business-and-society-ms': (
        'Graduate students seeking advanced, specialized study of leadership at the '
        'intersection of business and society. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-masters-degree-in-systemic-risk-ms': (
        'Graduate students seeking advanced, specialized study of the sources and management '
        'of risk across the financial system. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-masters-degree-in-technology-management-ms': (
        'Graduate students seeking advanced, specialized study of the management of '
        'technology for engineers and computer scientists. Best for those advancing into '
        'senior professional practice.'
    ),
    'yale-masters-degree-in-public-education-management-ms': (
        'Graduate students seeking advanced, specialized study of the leadership and '
        'management of large public-school systems. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-doctor-of-philosophy-in-management-phd-phd': (
        'Prospective scholars who want to make original contributions to rigorous research in '
        'accounting, finance, marketing, operations, and organizations, ready for funded '
        'doctoral study and a dissertation. Best for those advancing into senior professional '
        'practice.'
    ),
    'yale-doctor-of-medicine-md-prof': (
        'Students preparing for a professional career grounded in the practice of medicine '
        'through self-directed study and a required research thesis. Best for those advancing '
        'into senior professional practice.'
    ),
    'yale-md–phd-program-phd': (
        'Prospective scholars who want to make original contributions to the integration of '
        'medicine and biomedical research for physician-scientists, ready for funded doctoral '
        'study and a dissertation. Best for those advancing into senior professional '
        'practice.'
    ),
    'yale-master-of-health-science-mhs-ms': (
        'Graduate students seeking advanced, specialized study of clinical and translational '
        'research methods for clinicians and scientists. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-doctor-of-nursing-practice-dnp-phd': (
        'Prospective scholars who want to make original contributions to the highest level of '
        'advanced nursing practice and clinical leadership, ready for funded doctoral study '
        'and a dissertation. Best for those advancing into senior professional practice.'
    ),
    'yale-doctor-of-philosophy-in-nursing-phd-phd': (
        'Prospective scholars who want to make original contributions to research that builds '
        'the science base of nursing, ready for funded doctoral study and a dissertation. '
        'Best for those advancing into senior professional practice.'
    ),
    'yale-master-of-science-in-public-health-ms-ms': (
        'Graduate students seeking advanced, specialized study of research-oriented public '
        'health across biostatistics, epidemiology, and health informatics. Best for those '
        'advancing into senior professional practice.'
    ),
    'yale-doctor-of-philosophy-in-public-health-phd-phd': (
        'Prospective scholars who want to make original contributions to doctoral research '
        'across the public-health sciences, ready for funded doctoral study and a '
        'dissertation. Best for those advancing into senior professional practice.'
    ),
    'yale-master-of-forestry-mf-ms': (
        'Graduate students seeking advanced, specialized study of the science and practice of '
        'managing forests and natural resources. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-master-of-forest-science-mfs-ms': (
        'Graduate students seeking advanced, specialized study of research-grade forest and '
        'ecosystem science. Best for those advancing into senior professional practice.'
    ),
    'yale-doctor-of-philosophy-in-environment-phd-phd': (
        'Prospective scholars who want to make original contributions to doctoral research in '
        'environmental science, management, and policy, ready for funded doctoral study and a '
        'dissertation. Best for those advancing into senior professional practice.'
    ),
    'yale-master-of-arts-in-religion-mar-ms': (
        'Graduate students seeking advanced, specialized study of the academic study of '
        'religion across traditions. Best for those targeting advanced scholarship, teaching, '
        'or expert practice.'
    ),
    'yale-master-of-sacred-theology-stm-ms': (
        'Graduate students seeking advanced, specialized study of advanced theological study '
        'for those with a first theological degree. Best for those targeting advanced '
        'scholarship, teaching, or expert practice.'
    ),
    'yale-master-of-architecture-ii-march-ii-ms': (
        'Graduate students seeking advanced, specialized study of advanced architectural '
        'design beyond the professional degree. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-master-of-environmental-design-med-ms': (
        'Graduate students seeking advanced, specialized study of the history, theory, and '
        'criticism of the built and natural environment. Best for those advancing into senior '
        'professional practice.'
    ),
    'yale-doctor-of-philosophy-in-architecture-phd-phd': (
        'Prospective scholars who want to make original contributions to doctoral research in '
        'the history and theory of architecture, ready for funded doctoral study and a '
        'dissertation. Best for those advancing into senior professional practice.'
    ),
    'yale-master-of-musical-arts-mma-ms': (
        'Graduate students seeking advanced, specialized study of advanced conservatory '
        "performance beyond the master's. Best for those targeting advanced scholarship, "
        'teaching, or expert practice.'
    ),
    'yale-doctor-of-musical-arts-dma-phd': (
        'Prospective scholars who want to make original contributions to the terminal '
        'performance doctorate, completed with a dissertation, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced scholarship, teaching, '
        'or expert practice.'
    ),
    'yale-artist-diploma-ad-cert': (
        'Exceptional candidates seeking focused, credit-bearing training in elite '
        'instrumental performance at the conservatory level outside a standard degree track. '
        'Best for those targeting advanced scholarship, teaching, or expert practice.'
    ),
    'yale-certificate-in-performance-cert': (
        'Exceptional candidates seeking focused, credit-bearing training in conservatory '
        'performance training for exceptional musicians outside a standard degree track. Best '
        'for those targeting advanced scholarship, teaching, or expert practice.'
    ),
    'yale-master-of-fine-arts-in-drama-mfa-ms': (
        'Graduate students seeking advanced, specialized study of professional conservatory '
        'theater across acting, directing, design, and stagecraft. Best for those targeting '
        'advanced scholarship, teaching, or expert practice.'
    ),
    'yale-doctor-of-fine-arts-dfa-phd': (
        'Prospective scholars who want to make original contributions to doctoral research in '
        'dramaturgy and dramatic criticism, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-certificate-in-drama-cert': (
        'Exceptional candidates seeking focused, credit-bearing training in the conservatory '
        'theater curriculum at the professional level outside a standard degree track. Best '
        'for those targeting advanced scholarship, teaching, or expert practice.'
    ),
    'yale-master-of-public-policy-in-global-affairs-mpp-ms': (
        'Graduate students seeking advanced, specialized study of professional policy '
        'practice in global affairs for the public, private, and nonprofit sectors. Best for '
        'those targeting advanced research, policy, or leadership roles.'
    ),
    'yale-master-of-advanced-study-in-global-affairs-mas-ms': (
        'Graduate students seeking advanced, specialized study of global affairs for '
        'accomplished mid-career professionals. Best for those targeting advanced research, '
        'policy, or leadership roles.'
    ),
    'yale-african-studies-gsas-ma': (
        'Graduate students seeking advanced, specialized study of the histories, languages, '
        'politics, and cultures of Africa. Best for those targeting advanced scholarship, '
        'teaching, or expert practice.'
    ),
    'yale-american-studies-gsas-phd': (
        'Prospective scholars who want to make original contributions to the culture, '
        'politics, and history of the United States read across disciplines, ready for funded '
        'doctoral study and a dissertation. Best for those targeting advanced scholarship, '
        'teaching, or expert practice.'
    ),
    'yale-anthropology-gsas-phd': (
        'Prospective scholars who want to make original contributions to human societies and '
        'cultures across time, from ethnography to material evidence, ready for funded '
        'doctoral study and a dissertation. Best for those targeting advanced research, '
        'policy, or leadership roles.'
    ),
    'yale-applied-and-computational-mathematics-gsas-phd': (
        'Prospective scholars who want to make original contributions to mathematics and '
        'computation applied to problems across science and engineering, ready for funded '
        'doctoral study and a dissertation. Best for those targeting advanced technical, '
        'research, or industry roles.'
    ),
    'yale-applied-physics-gsas-phd': (
        'Prospective scholars who want to make original contributions to the physics of '
        'materials, devices, and quantum and optical systems, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-archaeological-studies-gsas-ma': (
        'Graduate students seeking advanced, specialized study of the material record of past '
        'societies, from excavation to analysis. Best for those targeting advanced research, '
        'policy, or leadership roles.'
    ),
    'yale-astronomy-gsas-phd': (
        'Prospective scholars who want to make original contributions to the physics of '
        'stars, galaxies, and the universe, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-biological-and-biomedical-sciences-gsas-phd': (
        'Prospective scholars who want to make original contributions to the broad biological '
        'and biomedical sciences underlying health and disease, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-biomedical-engineering-gsas-phd': (
        'Prospective scholars who want to make original contributions to engineering applied '
        'to medicine and human biology, ready for funded doctoral study and a dissertation. '
        'Best for those targeting advanced technical, research, or industry roles.'
    ),
    'yale-cell-biology-gsas-phd': (
        'Prospective scholars who want to make original contributions to the structure and '
        'function of cells and their molecular machinery, ready for funded doctoral study and '
        'a dissertation. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-cellular-and-molecular-physiology-gsas-phd': (
        'Prospective scholars who want to make original contributions to how cells and '
        'systems function, from molecules to organ physiology, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-chemical-and-environmental-engineering-gsas-phd': (
        'Prospective scholars who want to make original contributions to chemical and '
        'environmental engineering for energy, materials, and sustainability, ready for '
        'funded doctoral study and a dissertation. Best for those targeting advanced '
        'technical, research, or industry roles.'
    ),
    'yale-chemistry-gsas-phd': (
        'Prospective scholars who want to make original contributions to the structure, '
        'reactivity, and synthesis of matter across organic, inorganic, and physical '
        'chemistry, ready for funded doctoral study and a dissertation. Best for those '
        'targeting advanced technical, research, or industry roles.'
    ),
    'yale-classics-gsas-phd': (
        'Prospective scholars who want to make original contributions to the languages, '
        'literatures, and thought of ancient Greece and Rome, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced scholarship, teaching, or '
        'expert practice.'
    ),
    'yale-comparative-literature-gsas-phd': (
        'Prospective scholars who want to make original contributions to literature read '
        'across languages, national traditions, and media, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced scholarship, teaching, or '
        'expert practice.'
    ),
    'yale-computational-biology-and-biomedical-informatics-gsas-phd': (
        'Prospective scholars who want to make original contributions to computation applied '
        'to biology and biomedical data, ready for funded doctoral study and a dissertation. '
        'Best for those targeting advanced technical, research, or industry roles.'
    ),
    'yale-computer-science-gsas-phd': (
        'Prospective scholars who want to make original contributions to computing — '
        'algorithms, systems, theory, and artificial intelligence, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-earth-and-planetary-sciences-gsas-phd': (
        'Prospective scholars who want to make original contributions to the physical Earth '
        'and planets — geology, climate, and planetary processes, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-east-asian-languages-and-literatures-gsas-phd': (
        'Prospective scholars who want to make original contributions to the languages and '
        'literary traditions of East Asia, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-east-asian-studies-gsas-ma': (
        'Graduate students seeking advanced, specialized study of the societies, histories, '
        'and cultures of East Asia. Best for those targeting advanced scholarship, teaching, '
        'or expert practice.'
    ),
    'yale-ecology-and-evolutionary-biology-gsas-phd': (
        'Prospective scholars who want to make original contributions to the diversity of '
        'life, ecological systems, and evolution, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-economics-gsas-phd': (
        'Prospective scholars who want to make original contributions to the analysis of '
        'markets, incentives, and policy through micro, macro, and econometric reasoning, '
        'ready for funded doctoral study and a dissertation. Best for those targeting '
        'advanced research, policy, or leadership roles.'
    ),
    'yale-electrical-and-computer-engineering-gsas-phd': (
        'Prospective scholars who want to make original contributions to the engineering of '
        'electronic, computing, and communication systems, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-english-language-and-literature-gsas-phd': (
        'Prospective scholars who want to make original contributions to literature in '
        'English, criticism, and literary history, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-european-and-russian-studies-gsas-ma': (
        'Graduate students seeking advanced, specialized study of the histories, politics, '
        'and cultures of Europe and Russia. Best for those targeting advanced scholarship, '
        'teaching, or expert practice.'
    ),
    'yale-film-and-media-studies-gsas-phd': (
        'Prospective scholars who want to make original contributions to the history, theory, '
        'and analysis of film and media, ready for funded doctoral study and a dissertation. '
        'Best for those targeting advanced scholarship, teaching, or expert practice.'
    ),
    'yale-french-gsas-phd': (
        'Prospective scholars who want to make original contributions to the language, '
        'literature, and culture of the French-speaking world, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced scholarship, teaching, '
        'or expert practice.'
    ),
    'yale-genetics-gsas-phd': (
        'Prospective scholars who want to make original contributions to heredity and the '
        'molecular basis of genetic function and disease, ready for funded doctoral study and '
        'a dissertation. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-germanic-languages-and-literatures-gsas-phd': (
        'Prospective scholars who want to make original contributions to the languages, '
        'literatures, and thought of the Germanic world, ready for funded doctoral study and '
        'a dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-history-gsas-phd': (
        'Prospective scholars who want to make original contributions to the human past '
        'across periods and regions, read through primary sources and argument, ready for '
        'funded doctoral study and a dissertation. Best for those targeting advanced '
        'scholarship, teaching, or expert practice.'
    ),
    'yale-history-of-art-gsas-phd': (
        'Prospective scholars who want to make original contributions to the visual record of '
        'human culture — objects, images, and buildings across periods, ready for funded '
        'doctoral study and a dissertation. Best for those targeting advanced scholarship, '
        'teaching, or expert practice.'
    ),
    'yale-history-of-science-and-medicine-gsas-phd': (
        'Prospective scholars who want to make original contributions to how science and '
        'medicine developed and shaped society, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-immunobiology-gsas-phd': (
        'Prospective scholars who want to make original contributions to the immune system in '
        'health and disease, ready for funded doctoral study and a dissertation. Best for '
        'those targeting advanced technical, research, or industry roles.'
    ),
    'yale-interdepartmental-neuroscience-program-gsas-phd': (
        'Prospective scholars who want to make original contributions to the nervous system '
        'across molecular, cellular, systems, and cognitive scales, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-international-and-development-economics-gsas-ma': (
        'Graduate students seeking advanced, specialized study of economic analysis of '
        'development and the international economy. Best for those targeting advanced '
        'research, policy, or leadership roles.'
    ),
    'yale-investigative-medicine-gsas-phd': (
        'Prospective scholars who want to make original contributions to patient-oriented and '
        'translational biomedical research, ready for funded doctoral study and a '
        'dissertation. Best for those advancing into senior professional practice.'
    ),
    'yale-italian-studies-gsas-phd': (
        'Prospective scholars who want to make original contributions to the language, '
        'literature, and culture of Italy, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-linguistics-gsas-phd': (
        'Prospective scholars who want to make original contributions to the structure of '
        'human language — sound, form, meaning, and grammar, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced scholarship, teaching, or '
        'expert practice.'
    ),
    'yale-materials-science-gsas-phd': (
        'Prospective scholars who want to make original contributions to the structure, '
        'properties, and design of advanced materials, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-mathematics-gsas-phd': (
        'Prospective scholars who want to make original contributions to rigorous mathematics '
        '— analysis, algebra, geometry, and number theory, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-mechanical-engineering-gsas-phd': (
        'Prospective scholars who want to make original contributions to the design and '
        'analysis of mechanical and thermal systems, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-medieval-studies-gsas-phd': (
        'Prospective scholars who want to make original contributions to the history, '
        'literature, and culture of the medieval world, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-microbiology-gsas-phd': (
        'Prospective scholars who want to make original contributions to microorganisms and '
        'their roles in life, disease, and the environment, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-molecular-biophysics-and-biochemistry-gsas-phd': (
        'Prospective scholars who want to make original contributions to the molecular '
        'machinery of life — biochemistry, biophysics, and molecular biology, ready for '
        'funded doctoral study and a dissertation. Best for those targeting advanced '
        'technical, research, or industry roles.'
    ),
    'yale-molecular-cellular-and-developmental-biology-gsas-phd': (
        'Prospective scholars who want to make original contributions to the molecular basis '
        'of life — genetics, cell biology, and how organisms develop, ready for funded '
        'doctoral study and a dissertation. Best for those targeting advanced technical, '
        'research, or industry roles.'
    ),
    'yale-music-gsas-phd': (
        'Prospective scholars who want to make original contributions to music as an academic '
        'discipline — theory, history, and practice, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced scholarship, teaching, or expert '
        'practice.'
    ),
    'yale-near-eastern-languages-and-civilizations-gsas-phd': (
        'Prospective scholars who want to make original contributions to the languages and '
        'civilizations of the ancient and modern Near East, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced scholarship, teaching, or '
        'expert practice.'
    ),
    'yale-pathology-and-molecular-medicine-gsas-phd': (
        'Prospective scholars who want to make original contributions to the molecular '
        'mechanisms of human disease, ready for funded doctoral study and a dissertation. '
        'Best for those targeting advanced technical, research, or industry roles.'
    ),
    'yale-personalized-medicine-and-applied-engineering-gsas-ma': (
        'Graduate students seeking advanced, specialized study of biomedical engineering for '
        'personalized medicine. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-pharmacology-gsas-phd': (
        'Prospective scholars who want to make original contributions to how drugs act on '
        'biological systems, ready for funded doctoral study and a dissertation. Best for '
        'those targeting advanced technical, research, or industry roles.'
    ),
    'yale-philosophy-gsas-phd': (
        'Prospective scholars who want to make original contributions to fundamental '
        'questions of knowledge, reality, ethics, and logic, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced scholarship, teaching, or '
        'expert practice.'
    ),
    'yale-physics-gsas-phd': (
        'Prospective scholars who want to make original contributions to the fundamental laws '
        'governing matter, energy, space, and time, ready for funded doctoral study and a '
        'dissertation. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-political-science-gsas-phd': (
        'Prospective scholars who want to make original contributions to political '
        'institutions, behavior, and theory across American, comparative, and international '
        'politics, ready for funded doctoral study and a dissertation. Best for those '
        'targeting advanced research, policy, or leadership roles.'
    ),
    'yale-psychology-gsas-phd': (
        'Prospective scholars who want to make original contributions to the science of mind '
        'and behavior, from cognition and development to social and clinical questions, ready '
        'for funded doctoral study and a dissertation. Best for those targeting advanced '
        'research, policy, or leadership roles.'
    ),
    'yale-religious-studies-gsas-phd': (
        'Prospective scholars who want to make original contributions to religious '
        'traditions, texts, and practices studied analytically, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced scholarship, teaching, '
        'or expert practice.'
    ),
    'yale-slavic-languages-and-literatures-gsas-phd': (
        'Prospective scholars who want to make original contributions to the languages and '
        'literatures of the Slavic world, ready for funded doctoral study and a dissertation. '
        'Best for those targeting advanced scholarship, teaching, or expert practice.'
    ),
    'yale-sociology-gsas-phd': (
        'Prospective scholars who want to make original contributions to the structure of '
        'social life — institutions, inequality, and social change, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced research, policy, or '
        'leadership roles.'
    ),
    'yale-spanish-and-portuguese-gsas-phd': (
        'Prospective scholars who want to make original contributions to the languages, '
        'literatures, and cultures of the Spanish- and Portuguese-speaking worlds, ready for '
        'funded doctoral study and a dissertation. Best for those targeting advanced '
        'scholarship, teaching, or expert practice.'
    ),
    'yale-statistics-gsas-ma': (
        'Graduate students seeking advanced, specialized study of statistical theory and '
        'methodology. Best for those targeting advanced technical, research, or industry '
        'roles.'
    ),
    'yale-statistics-and-data-science-gsas-phd': (
        'Prospective scholars who want to make original contributions to probability, '
        'statistical inference, and data-driven computation, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-translational-biomedicine-gsas-phd': (
        'Prospective scholars who want to make original contributions to research that '
        'translates biomedical discovery toward the clinic, ready for funded doctoral study '
        'and a dissertation. Best for those targeting advanced technical, research, or '
        'industry roles.'
    ),
    'yale-womens-gender-and-sexuality-studies-gsas-phd': (
        'Prospective scholars who want to make original contributions to gender and sexuality '
        'as categories shaping culture, politics, and knowledge, ready for funded doctoral '
        'study and a dissertation. Best for those targeting advanced scholarship, teaching, '
        'or expert practice.'
    ),
}
