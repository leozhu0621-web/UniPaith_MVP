"""Programmatic anti-stub gate for university program catalogs (enrich-profile §8.5).

``check_conformance`` is PRESENCE-only: a catalog whose every required field is
non-empty is "conformant" even when every ``description_text`` is a school-blurb /
classification / per-field stub. That hole let eight consecutive stub-swap "repair"
PRs sail through conformance + green CI and auto-merge (REPAIR_BACKLOG run 55).

This module closes the hole. It measures the description-quality tells the gold MIT
reference scores **zero** on, so a stub-swap catalog FAILS the gate instead of
passing as a "repair". Every metric below is a count of rows/fields exhibiting a
fabrication tell; a clean (gold-equal) catalog returns ``0`` for all of them.

The gate is enforced by ``tests/test_anti_stub_gate.py`` over a registry of catalogs
certified clean (``CERTIFIED_CLEAN``). A catalog ships as "repaired"/gold only by
joining that registry, at which point CI re-computes these metrics and blocks the
merge if any is non-zero. The thresholds are NOT tunable — a non-zero means the rows
are un-researched (the no-fabrication / structure-before-depth invariant), not a knob.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

# Credential designations stripped to recover the field-of-study part of a name.
# Ordered longest-first so "Master of Science in" wins over "Master of ".
_CRED_PREFIXES: tuple[str, ...] = (
    "Bachelor of Arts in ",
    "Bachelor of Science in ",
    "Bachelor of Fine Arts in ",
    "Bachelor of ",
    "Master of Science in ",
    "Master of Arts in ",
    "Master of Fine Arts in ",
    "Master of Engineering in ",
    "Master of Public Health",
    "Master of Public Policy",
    "Master of Business Administration",
    "Master of ",
    "Doctor of Philosophy in ",
    "Doctor of Medicine",
    "Doctor of Pharmacy",
    "Doctor of ",
    "PhD in ",
    "Graduate Certificate in ",
    "Certificate in ",
    "Bachelor's in ",
    "Master's in ",
    "Doctorate in ",
)

# Pure-classification descriptions: text that only states the credential level and/or
# owning unit and swaps in the field — carrying no field-specific fact (the gold
# contrast). The wording is a moving target, so this matches the durable *forms*, not
# one fixed string (REPAIR_BACKLOG miss #8). Gold MIT matches none of these.
_CLASSIFICATION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\boffered through the [A-Z]"),  # "...offered through the Anthropology"
    re.compile(
        r"\bis (a|an) (under)?graduate (degree |major |program )?"
        r"(program |major |degree )?(offered |at |in |through )",
        re.I,
    ),
    re.compile(r"\bis a (doctoral|master's|professional|certificate) (program|degree)\b", re.I),
    re.compile(
        r" — a .+ (bachelors|masters|doctoral|professional|certificate) program offered through "
    ),
)

# Minimum shared leading body that counts as per-field stamping (miss #8 suffix-diversifier).
_SHARED_BODY_MIN_CHARS = 120
_SHARED_BODY_MIN_FRACTION = 0.5

# Machine-build artifacts that a description-generation script left in the prose. These
# pass every metric above (no "..", no shared body, no classification phrase) yet render
# raw junk to students — observed live on three "certified-clean" catalogs (UW/Michigan/
# UCLA shipped 350-374 rows each opening "Catalog entry <hex>: Catalog entry <hex>: …",
# UW additionally said "Westwood campus" — UCLA's neighborhood — on a Seattle university).
# No real catalog prints an internal entry id, a commit/UUID-style hex token, or the same
# clause twice in a row, so any of these is an automatic FAIL (gold MIT scores 0).
_ARTIFACT_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bCatalog entry\b", re.I),  # "Catalog entry 5686776b4e64: …"
    # raw hex id (UUID/commit fragment) — requires both a digit and an a-f letter so plain
    # numbers (years) and ordinary words never match
    re.compile(r"\b(?=[0-9a-f]*[0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{8,}\b"),
)


def field_of(program_name: str) -> str:
    """The field-of-study part of a program name (credential designation stripped)."""
    for pre in _CRED_PREFIXES:
        if program_name.startswith(pre):
            rest = program_name[len(pre) :].strip()
            return rest or program_name
    return program_name


def _common_prefix(a: str, b: str) -> str:
    i = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        i += 1
    return a[:i]


# A leading per-credential FRAME / degree-classification / field-definition sentence. When
# a still-shared field body is prepended with such a frame ("Rice offers the undergraduate
# major in {field}.", "Doctoral study in {field} … centers on dissertation research in",
# "Master's students in {field} complete …", "{Field} is the study of …"), the frame
# differs by credential while the body stays identical across a field's BA / MS / PhD rows —
# so the leading-PREFIX shared-body count in :func:`analyze` reads a false 0 (REPAIR_BACKLOG
# miss #8 credential-frame sub-bullet). Strip the frame, then measure the shared body
# ANYWHERE in the siblings (longest common substring), not only as a leading prefix.
_FRAME_LEAD_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^Doctoral study in .{0,140}?dissertation research in\s+", re.I),
    re.compile(r"^Doctoral study\b.{0,200}?(?:—|\.)\s+", re.I),
    re.compile(r"^Master'?s students\b.{0,200}?(?:—|\.)\s+", re.I),
    re.compile(r"^.{0,160}?\boffers?\b.{0,160}?\.\s+", re.I),
    re.compile(r"^Graduate (?:study|certificate)\.\s+", re.I),
    re.compile(r"^[A-Z][a-z]+(?: [a-z]+){0,3} is the (?:study|science) of .{0,160}?\.\s+"),
)


def _strip_frame(description: str) -> str:
    """Remove a leading credential-frame / classification / field-definition sentence."""
    for rx in _FRAME_LEAD_RES:
        m = rx.match(description)
        if m and m.end() < len(description):
            return description[m.end() :]
    return description


def _longest_common_substring(a: str, b: str) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def frame_stripped_shared_body(
    programs: list[dict],
    min_chars: int = 80,
    min_fraction: float = 0.5,
    abs_chars: int | None = None,
) -> list[str]:
    """Fields whose credential siblings share a body once a leading frame is stripped.

    For each field (program name minus its credential designation) with >= 2 rows, strip a
    leading credential-frame sentence from every sibling description and compute the longest
    common substring of each pair. A field is flagged when any sibling pair shares a run of
    >= ``min_chars`` characters that is also >= ``min_fraction`` of the shorter stripped
    body — the run-65 credential-frame + tail-shared field body (miss #8). Gold MIT scores
    0 (every credential level has its own researched body); a non-zero is the
    no-fabrication / per-program-research invariant, not a tunable knob.

    ``abs_chars`` adds the run-67 absolute floor (miss #8 fraction-floor sub-bullet): the
    ``min_fraction`` guard is itself a loophole — PADDING the per-credential tail dilutes a
    still-identical 150+-char leading SENTENCE below ``min_fraction`` of the now-long body,
    so the fraction-only count reads a false 0. When ``abs_chars`` is set, a shared run of
    >= ``abs_chars`` characters flags the field REGARDLESS of fraction (a full stamped
    sentence is never a coincidence). Default ``None`` preserves the prior fraction-only
    behavior so the fleet-wide default gate is unchanged until each catalog is repaired.
    """
    by_field: dict[str, list[str]] = defaultdict(list)
    for p in programs:
        by_field[field_of(p.get("program_name") or "")].append(_strip_frame(_desc(p)))
    flagged: list[str] = []
    for field, bodies in by_field.items():
        if len(bodies) < 2:
            continue
        hit = False
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                shortest = min(len(bodies[i]), len(bodies[j]))
                if not shortest:
                    continue
                lcs = _longest_common_substring(bodies[i], bodies[j])
                if lcs >= min_chars and (
                    lcs >= min_fraction * shortest or (abs_chars is not None and lcs >= abs_chars)
                ):
                    hit = True
        if hit:
            flagged.append(field)
    return flagged


@dataclass(frozen=True)
class AntiStubReport:
    """Per-metric violation lists. A gold-equal catalog has every list empty."""

    n: int
    name_prefixed: list[str]  # description restates the program_name (heading doubled)
    classification: list[str]  # pure-classification / template stub descriptions
    double_period: list[str]  # ".." splice (school-blurb-into-frame breakage)
    verbatim_shared: list[str]  # description_text identical across >= 2 programs
    shared_leading_body: list[str]  # field's credential siblings share a >=120ch leading body
    cross_field_clause: list[str]  # one body stamped across rows of >= 2 DIFFERENT fields

    @property
    def violations(self) -> dict[str, list[str]]:
        return {
            "name_prefixed": self.name_prefixed,
            "classification": self.classification,
            "double_period": self.double_period,
            "verbatim_shared": self.verbatim_shared,
            "shared_leading_body": self.shared_leading_body,
            "cross_field_clause": self.cross_field_clause,
        }

    @property
    def is_clean(self) -> bool:
        return not any(self.violations.values())

    def summary(self) -> str:
        parts = [f"{k}={len(v)}" for k, v in self.violations.items() if v]
        return ", ".join(parts) if parts else "clean"


def _desc(program: dict) -> str:
    return (program.get("description") or program.get("description_text") or "").strip()


def analyze(programs: list[dict]) -> AntiStubReport:
    """Compute the gold-MIT-0% anti-stub metrics over a program catalog.

    Each program is a dict with at least ``program_name`` and ``description`` (or
    ``description_text``). Returns an :class:`AntiStubReport` whose lists are all empty
    for a clean catalog.
    """
    descs = [_desc(p) for p in programs]
    names = [p.get("program_name") or "" for p in programs]

    name_prefixed = [names[i] for i, d in enumerate(descs) if names[i] and d.startswith(names[i])]
    classification = [
        names[i]
        for i, d in enumerate(descs)
        if d and any(rx.search(d) for rx in _CLASSIFICATION_RES)
    ]
    double_period = [names[i] for i, d in enumerate(descs) if ".." in d]

    counts: dict[str, int] = defaultdict(int)
    for d in descs:
        if d:
            counts[d] += 1
    verbatim_shared = [names[i] for i, d in enumerate(descs) if d and counts[d] > 1]

    # Per-field shared leading body across a field's credential siblings.
    by_field: dict[str, list[str]] = defaultdict(list)
    for d, n in zip(descs, names):
        by_field[field_of(n)].append(d)
    shared_leading_body: list[str] = []
    for field, ds in by_field.items():
        if len(ds) < 2:
            continue
        prefix = ds[0]
        for other in ds[1:]:
            prefix = _common_prefix(prefix, other)
        shortest = min(len(x) for x in ds)
        if (
            len(prefix) >= _SHARED_BODY_MIN_CHARS
            and shortest
            and len(prefix) >= _SHARED_BODY_MIN_FRACTION * shortest
        ):
            shared_leading_body.append(field)

    # Catalog-wide: one leading body stamped across rows of >= 2 DIFFERENT fields
    # (the school-blurb stamp the field-keyed count above never compares). The field name
    # is interpolated into the blurb ("{Univ}'s {field} program connects to {SCHOOL
    # blurb}…"), so neutralize the field token before comparing — otherwise the leading
    # text differs per row only by the swapped-in field and the stamp hides. The blurb may
    # lowercase the field token ("anthropology program connects…") while program_name is
    # title-cased ("… in Anthropology"), so the neutralization is CASE-INSENSITIVE — a
    # case-sensitive replace would miss the lowercase occurrence and let the stamp hide.
    head_to_fields: dict[str, set[str]] = defaultdict(set)
    for d, n in zip(descs, names):
        if len(d) < _SHARED_BODY_MIN_CHARS:
            continue
        field = field_of(n)
        normalized = re.sub(re.escape(field), "{FIELD}", d, flags=re.IGNORECASE) if field else d
        head_to_fields[normalized[: _SHARED_BODY_MIN_CHARS * 2]].add(field)
    cross_field_clause = [head for head, fields in head_to_fields.items() if len(fields) >= 2]

    return AntiStubReport(
        n=len(programs),
        name_prefixed=name_prefixed,
        classification=classification,
        double_period=double_period,
        verbatim_shared=verbatim_shared,
        shared_leading_body=shared_leading_body,
        cross_field_clause=cross_field_clause,
    )


def machine_artifacts(programs: list[dict]) -> list[str]:
    """Program names whose description carries a description-generation build artifact.

    Separate from :func:`analyze` (and ``AntiStubReport.is_clean``) so that adding it
    cannot crash an already-broken catalog's import-time self-check — it is enforced by
    ``tests/test_anti_stub_gate.py`` over the certified-clean registry instead. Catches
    the live "Catalog entry <hex>:" / raw-hex-id junk that three certified catalogs
    shipped while scoring 0 on every description-quality metric above.
    """
    return [
        (p.get("program_name") or "")
        for p in programs
        if any(rx.search(_desc(p)) for rx in _ARTIFACT_RES)
    ]


# Raw scraped CATALOGUE DEBRIS left in ``description_text`` instead of researched prose: a
# degree-requirements / course-list fragment, a unit-count opening, a department contact /
# address block, or a fragment truncated mid-sentence / on a trailing colon (REPAIR_BACKLOG
# miss #8 scrape-debris sub-bullet, run 66 — USC shipped ~80 such rows). Each is unique per
# row, so it scores 0 on every share/form metric in :func:`analyze` yet renders raw catalogue
# text — a course requirement list, a phone number, a mailing address — to a student. Gold MIT
# scores 0. Kept separate from ``analyze``/``is_clean`` (like :func:`machine_artifacts`) so it
# cannot crash an already-broken catalog's import self-check; enforced by
# ``tests/test_anti_stub_gate.py`` over a debris-clean registry.
_DEBRIS_COURSE_CODE = re.compile(r"\b[A-Z]{2,4}\s?\d{3}[A-Za-z]?\b")
_DEBRIS_UNIT_COUNT = re.compile(r"\b\d+\s+(additional\s+)?(units|credits|semester hours)\b", re.I)
_DEBRIS_CONTACT = re.compile(r"\(\d{3}\)\s?\d{3}-\d{4}|[\w.]+@[\w.]+\.edu")
_DEBRIS_ADDRESS = re.compile(
    r"\b(Suite|Room)\s+\d+|"
    r"\b[A-Z][A-Za-z0-9&' -]{2,}\s+Hall\s+\d+\b|"
    r"\b[A-Z][A-Za-z0-9&' -]{2,}\s+Hall,\s+\(\d{3}\)"
)


# Template-SLOT machine grammar (REPAIR_BACKLOG run 71, FLAG #1c). The successor evasion
# to the credential-frame + shared-body gates: a per-credential "repair" that gives each
# credential its OWN frame but SLOTS a field phrase into a fixed grammatical template,
# producing prose that DIFFERS per row (so :func:`analyze` and
# :func:`frame_stripped_shared_body` read 0) yet renders machine junk a student reads —
# Berkeley auto-merged 107 such rows + UCLA 6, all green and in ``CERTIFIED_CLEAN``. The
# two unambiguous, zero-false-positive tells (gold MIT and the clean fleet score 0):
#   (i)  the CREDENTIAL DOUBLED inside the body — the degree designation is already the
#        program_name heading, so re-stating it ("...coursework in the Master of Science
#        in …", "Doctoral training in the Doctor of Philosophy in …") is a template
#        artifact the :func:`analyze` ``startswith(program_name)`` check MISSES (the body
#        opens on a level-word, not the verbatim name).
#   (ii) a DOUBLE / DANGLING preposition from an empty or mis-typed slot — a template verb
#        ("research/study/coursework/training in", "builds on", "advances", "emphasizes")
#        followed immediately by a redundant preposition ("research in of farm…",
#        "research in for students…") or by a comma / period (the slot came back empty).
# Anchored to the template verbs so natural prose ("research in international relations")
# never matches.
_TEMPLATE_SLOT_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:training|study|coursework|research|seminars?|expertise|specialization)\s+in\s+"
        r"(?:the\s+)?(?:Doctor of Philosophy|Doctor of|Master of|Master'?s|Bachelor of|"
        r"Bachelor'?s|Doctorate|Graduate Certificate|Certificate)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:research|study|coursework|training|builds on|advances|emphasizes|"
        r"centers? on|focused on)\s+in\s+(?:of|for|on|in)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:research|study|coursework|training)\s+in\s*[.,;:]",
        re.I,
    ),
)


def template_slot_artifacts(programs: list[dict]) -> list[str]:
    """Program names whose ``description`` is a field phrase slotted into a fixed template.

    Catches the run-71 template-slot evasion (see ``_TEMPLATE_SLOT_RES``): a per-credential
    body that DIFFERS per row — so every share/form metric reads 0 — yet carries a doubled
    credential or a double/dangling preposition that proves it was machine-assembled, not
    researched. Kept separate from :func:`analyze` / ``is_clean`` (like
    :func:`machine_artifacts`) so it cannot crash an already-broken catalog's import
    self-check; enforced by ``tests/test_anti_stub_gate.py`` over ``CERTIFIED_CLEAN``. Gold
    MIT returns ``[]``.
    """
    return [
        (p.get("program_name") or "")
        for p in programs
        if any(rx.search(_desc(p)) for rx in _TEMPLATE_SLOT_RES)
    ]


def scrape_debris(programs: list[dict]) -> list[str]:
    """Program names whose ``description`` is raw scraped catalogue debris, not researched prose.

    A description FAILS when it carries any of: a course-code token ("MATH 225"), a unit/credit
    count in its opening clause, a phone number / ``@…edu`` email / department mailing address,
    or a fragment that ends mid-sentence (no terminal ``.``/``!``/``?``) or on a trailing colon.
    None of these appear in researched prose about what a program studies; all appeared live on
    USC's scrape-built catalog (REPAIR_BACKLOG CRITICAL #1, run 66). Gold MIT returns ``[]``.
    """
    hits: list[str] = []
    for p in programs:
        d = _desc(p)
        if not d:
            continue
        # A well-sourced description often ENDS in a parenthetical citation —
        # "...prepares graduates for government. (Source: ace.illinois.edu)" — so the
        # terminal-punctuation / trailing-colon tells must run on the text with a trailing
        # "(...)" stripped, or every cited row false-flags as truncated debris (REPAIR_BACKLOG
        # human-flag #2: the un-stripped tell flagged ~144 well-sourced UT-Austin rows). The
        # course-code / unit-count / contact / address tells still run on the FULL text.
        d_term = re.sub(r"\s*\([^()]*\)\s*$", "", d).rstrip()
        bad = (
            _DEBRIS_COURSE_CODE.search(d)
            or _DEBRIS_UNIT_COUNT.search(d[:160])
            or _DEBRIS_CONTACT.search(d)
            or _DEBRIS_ADDRESS.search(d)
            or not re.search(r"[.!?][\"')]?$", d_term)
            or d_term.endswith(":")
        )
        if bad:
            hits.append(p.get("program_name") or "")
    return hits
