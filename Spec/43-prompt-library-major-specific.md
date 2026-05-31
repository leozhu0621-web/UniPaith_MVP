# 43 · Prompt Library — Major-Specific Field Catalog

> The full per-discipline readiness-signal catalog, split out of `42` §3.18 per its open-question note. Each track is a JSONB subdocument on `student_major_specific_signals.{track_key}`, populated only when the student's `target_major_field_primary` matches the track. Source: `Misc./Prompt Library.docx` (deepest enumeration) + Master Paper Appendix A (typed I/O).
>
> Status: **draft v1.0** · 2026-05-29 · Companion to `42-prompt-library-schema.md` (which holds the cross-cutting input/output catalog). This doc is the major-specific INPUT detail; major-specific OUTPUTS are in `42` §4.18.

---

## 1. How tracks work

- A track activates when `target_major_field_primary` maps to its `track_key`.
- Multiple tracks can be active (dual-target students); each is an independent JSONB subdoc.
- Every field carries the universal record metadata (`42` §5): value, normalized, source, confidence, version, provenance.
- Self-ratings use **1–5** (1 = none, 5 = expert) unless noted; proficiency entries follow the §3.23 skill-matrix shape from `42`.
- All tracks below feed the major-specific OUTPUTS in `42` §4.18 (`major_track_fit_score`, `coding_readiness_band`, `suggested_artifacts_to_add`, etc.).

### Track registry (15)
`cs_data_ai` · `engineering` · `business` · `health` · `arts_design` · `performing_arts` · `humanities_social_sciences` · `law_policy` · `education_counseling` · `journalism_communications` · `math_physics_chemistry_sciences` · `comp_engineering_robotics` · `environmental_sustainability` · `language_linguistics` · `entrepreneurship_product`

---

## 2. `cs_data_ai` — Computer Science / Data / AI

**Programming languages** (repeatable, skill-matrix shape): `language`, `proficiency` (1-5), `years_used`, `last_used`, `frequency`, `evidence_type`.

**CS fundamentals self-ratings** (1-5 each): data structures · algorithms · operating systems · networks · databases · discrete math · OOP · concurrency · security basics · computer architecture · compilers · software engineering.

**ML exposure** (tags + 1-5): supervised · unsupervised · deep learning · NLP/LLMs · recommenders · computer vision · time series · RL · evaluation-metrics literacy.

**Tool familiarity** (1-5): Docker · Kubernetes · Spark · dbt · Airflow · cloud (AWS/GCP/Azure) · data warehouse · BI tools · CI/CD · Git · Linux.

**Evidence/competitive:** `github_link`, `kaggle_link`, `open_source_contributions` (bool), `hackathon_list[]`, `competitive_programming_best_rank` (enum<n/a, regional, national, ICPC_finalist>), `leetcode_frequency`, `coding_assessment_score`.

**Track choice:** `track_choice` enum<data, AI, cyber, SWE, systems>.

---

## 3. `engineering` — Mechanical / Electrical / Civil / Aerospace / Chemical

**Core-topic readiness** (1-5): statics · dynamics · thermodynamics · fluid mechanics · circuits · controls · materials · heat transfer.

**EE-specific** (1-5): signals & systems · power systems · electromagnetics · embedded systems · VLSI.

**Civil-specific** (1-5): structural · geotechnical · transportation · environmental · construction mgmt.

**ChemE-specific** (1-5): reaction engineering · separations · process control · transport phenomena.

**Tools** (1-5): CAD (SolidWorks/AutoCAD) · FEA · CFD · MATLAB/Simulink · simulation.

**Hands-on:** manufacturing exposure (machining / 3D-printing / welding / metrology), lab-safety certifications, `pe_track_flag` (Professional Engineer path), capstone/project entries.

---

## 4. `business` — Finance / Marketing / Analytics / Operations

**Domain self-ratings** (1-5): finance · accounting · marketing · analytics · strategy · operations · quant methods.

**Tool depth** (1-5): Excel · SQL (+dialect) · Python (+libraries) · R · Tableau/Power BI · GA4 · CRM · Salesforce/HubSpot.

**Work-sample artifacts:** financial model, dashboard, campaign metrics (CTR/CVR/CAC/ROAS), case-competition placements, internship deal/project list.

**Credentials:** CFA/CPA progress, Bloomberg certification, etc.

---

## 5. `health` — Pre-med / Nursing / Public Health

**Clinical exposure** (repeatable): setting (hospital/clinic/community), population, patient-contact level, hours.

**Certifications:** CNA · EMT · BLS · ACLS · phlebotomy.

**Prereq readiness** (1-5): bio · chem · orgo · physics · biochem · anatomy · physiology · stats.

**Licensure path + test flags:** `mcat_flag`, `nclex_flag`, `cna_flag`; intended licensure track.

**Public-health specific:** epidemiology exposure, biostatistics, community-health project hours.

---

## 6. `arts_design` — Art / Design / Architecture / Media

Portfolio depth (links to `42` §3.10 portfolio): discipline, medium/technique breadth, pieces count, software (Adobe CS, Figma, CAD, Rhino, etc. 1-5), exhibitions/publications, architecture-specific (studio hours, model-making, BIM), design-process artifacts.

---

## 7. `performing_arts` — Music / Theater / Dance

Audition readiness (links to `42` §3.10 performing-arts subset): instrument/voice type, repertoire list, years training, ensemble/company experience, competition placements, recording links, theory proficiency (1-5), dance styles/technique levels.

---

## 8. `humanities_social_sciences`

Writing-sample depth, research methods (qualitative/quantitative 1-5), language reading proficiency for sources, thesis/independent-study experience, relevant coursework rigor, publications/conference presentations.

---

## 9. `law_policy` — Law / Policy / International Relations

LSAT readiness/flag, writing-sample, debate/mock-trial/Model-UN, policy-research experience, internships (legislative/NGO/firm), languages, region/issue specialization.

---

## 10. `education_counseling` — Education / Teaching / Counseling / Social Work

Teaching/tutoring hours by setting + age group, certifications (teaching license progress), fieldwork/practicum hours, populations served, subject-area depth, counseling-theory exposure.

---

## 11. `journalism_communications`

Portfolio (clips/published work), beat/specialization, media tools (CMS, editing, multimedia 1-5), internships (newsroom/agency), social/audience metrics, ethics/law-of-press coursework.

---

## 12. `math_physics_chemistry_sciences` — Pure Sciences

Subject readiness (1-5): analysis · algebra · probability · classical/quantum mechanics · E&M · physical/organic chemistry · lab techniques. Research experience (lab, PI, outputs), competition placements (Putnam, olympiads), computational tools (1-5).

---

## 13. `comp_engineering_robotics` — Computer Engineering / Embedded / Robotics

Embedded (microcontrollers, RTOS, C/C++ 1-5), hardware (PCB design, FPGA, sensors), robotics (ROS, control, perception, SLAM 1-5), competition teams (FRC/VEX/RoboCup), project portfolio.

---

## 14. `environmental_sustainability` — Environmental / Sustainability / Energy

Field/lab methods, GIS proficiency (1-5), sustainability frameworks (LCA, ESG), policy exposure, fieldwork hours, energy-systems coursework, relevant certifications.

---

## 15. `language_linguistics` — Languages / Linguistics / Translation

Language proficiencies (CEFR/ACTFL per `42` §3.11), translation/interpretation experience, linguistics subfields (phonology/syntax/semantics/sociolinguistics 1-5), field-work, CAT tools, publications.

---

## 16. `entrepreneurship_product` — Entrepreneurship / Product / Innovation

Ventures founded (stage, role, traction metrics), product work (specs shipped, users, growth), fundraising experience, accelerator participation, technical+business hybrid skills, pitch/competition placements.

---

## 17. Storage + extensibility

- One JSONB column per active track on `student_major_specific_signals` (`42` §8).
- New tracks add a `track_key` + a field set here; no schema migration (JSONB).
- The exhaustive verbatim field list (every sub-field per track) lives in `Misc./Prompt Library.docx` + Master Paper Appendix A; this doc is the build-ready structured contract. Where a track needs the full enumeration, extract from those sources into the track's JSONB schema validator.

---

## 18. Open questions

- **CIP → track_key mapping.** Maintain the authoritative map from CIP major codes to `track_key` (some majors map to multiple tracks).
- **Cross-track fields.** Skill-matrix (`42` §3.23) overlaps per-track tools — store once in the skill matrix, reference from tracks, avoid duplication.
- **Per-track output depth.** `42` §4.18 samples CS outputs; each track needs its readiness bands + suggested-artifact logic defined as the matching ML matures.
