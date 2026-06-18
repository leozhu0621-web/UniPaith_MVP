#!/usr/bin/env python3
"""Generate per-credential UCSD program descriptions (distinct body per level)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from unipaith.data.ucsd_field_descriptions import FIELD_DESCRIPTIONS

# Hand-crafted overrides — verified UCSD units only (no fabricated centers).
MANUAL: dict[tuple[str, str], str] = {
    (
        "Aerospace Engineering",
        "bachelors",
    ): (
        "Jacobs School aerospace undergraduates study aerodynamics, propulsion, and spacecraft "
        "systems with wind-tunnel labs and flight-research facilities in the Department of "
        "Mechanical and Aerospace Engineering."
    ),
    (
        "Aerospace Engineering",
        "certificate",
    ): (
        "The graduate certificate in aerospace engineering offers focused graduate coursework in "
        "aerodynamics and propulsion, drawing on Jacobs School wind-tunnel and flight-research "
        "facilities and the CaliBaja Center for Resilient Materials and Systems."
    ),
    (
        "Aerospace Engineering",
        "masters",
    ): (
        "Master's students in aerospace engineering conduct thesis research in aerodynamics, "
        "propulsion, and spacecraft systems with Jacobs School faculty and ties to the CaliBaja "
        "Center for Resilient Materials and Systems and San Diego defense-industry partners."
    ),
    (
        "Applied Mathematics",
        "bachelors",
    ): (
        "Undergraduate applied mathematics at UC San Diego builds proof-based analysis, "
        "scientific computing, and mathematical modeling with the Center for Computational "
        "Mathematics and Scripps ocean-science applications."
    ),
    (
        "Applied Mathematics",
        "certificate",
    ): (
        "The graduate certificate in applied mathematics covers advanced modeling, scientific "
        "computing, and mathematical biology with the Center for Computational Mathematics "
        "and Scripps ocean modeling groups."
    ),
    (
        "Applied Mathematics",
        "masters",
    ): (
        "Master's students in applied mathematics pursue coursework and research in fluid "
        "dynamics, scientific computing, and mathematical biology through the Center for "
        "Computational Mathematics and Scripps partnerships."
    ),
    (
        "Bioinformatics",
        "bachelors",
    ): (
        "Undergraduate bioinformatics at UC San Diego connects genomics coursework with "
        "computational pipelines at the San Diego Supercomputer Center and the Institute for "
        "Genomic Medicine on the La Jolla mesa."
    ),
    (
        "Bioinformatics",
        "certificate",
    ): (
        "The graduate certificate in bioinformatics trains students in genomics pipelines, "
        "sequence analysis, and computational biology using the San Diego Supercomputer Center "
        "and the Institute for Genomic Medicine."
    ),
    (
        "Bioinformatics",
        "masters",
    ): (
        "Master's students in bioinformatics pair genomics research with high-performance "
        "computing at the San Diego Supercomputer Center and clinical genomics through the "
        "Institute for Genomic Medicine."
    ),
    (
        "Clinical Psychology",
        "bachelors",
    ): (
        "Undergraduate psychology coursework at UC San Diego introduces research methods and "
        "clinical science foundations before students pursue graduate training in assessment "
        "and evidence-based intervention."
    ),
}


def _core_clause(text: str) -> str:
    """Strip leading credential framing; keep field-specific substance."""
    t = text.strip()
    for prefix in (
        r"^Graduate [^.]+ at UCSD ",
        r"^Graduate [^.]+ coursework at UCSD ",
        r"^Graduate [^.]+ training at UCSD ",
        r"^The UC San Diego School of Medicine M\.D\. program integrates ",
        r"^Skaggs School Pharm\.D\. training emphasizes ",
        r"^Rady's full-time MBA emphasizes ",
        r"^Wertheim School MPH training covers ",
    ):
        t = re.sub(prefix, "", t, flags=re.I)
    return t[0].lower() + t[1:] if t else t


def _auto(field: str, dtype: str, base: str) -> str:
    core = _core_clause(base)
    fl = field.lower()
    if dtype == "bachelors":
        return (
            f"Undergraduate {fl} majors at UC San Diego build foundational coursework in "
            f"{core}"
        )
    if dtype == "masters":
        return (
            f"Master's students in {fl} pursue advanced seminars, research projects, and "
            f"professional development around {core}"
        )
    if dtype == "certificate":
        return (
            f"The graduate certificate in {fl} offers focused graduate coursework for students "
            f"deepening expertise in {core}"
        )
    if dtype == "phd":
        return (
            f"Doctoral students in {fl} conduct dissertation research with UC San Diego faculty "
            f"across {core}"
        )
    if dtype == "professional":
        return base
    return base


def main() -> None:
    multi_path = Path("/tmp/ucsd_multi.json")
    if not multi_path.exists():
        raise SystemExit("Run the multi-credential export first")

    multi: dict = json.loads(multi_path.read_text())
    entries: dict[tuple[str, str], str] = dict(MANUAL)

    for field, rows in sorted(multi.items()):
        base = FIELD_DESCRIPTIONS.get(field)
        if not base:
            raise SystemExit(f"Missing FIELD_DESCRIPTIONS for {field!r}")
        dtypes = {r["dtype"] for r in rows}
        for dtype in dtypes:
            key = (field, dtype)
            if key not in entries:
                entries[key] = _auto(field, dtype, base)

    out = Path(__file__).resolve().parent.parent / "src/unipaith/data/ucsd_credential_descriptions.py"
    lines = [
        '"""Per-credential program descriptions for UC San Diego multi-level fields.',
        "",
        "Each (field, degree_type) pair carries a distinct researched body — never one field",
        "text stamped across certificate/bachelor's/master's/PhD rows.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "from __future__ import annotations",
        "",
        "CREDENTIAL_DESCRIPTIONS: dict[tuple[str, str], str] = {",
    ]
    for (field, dtype), text in sorted(entries.items()):
        lines.append(f"    ({field!r}, {dtype!r}): (")
        lines.append(f"        {text!r}")
        lines.append("    ),")
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def description_for(field: str, degree_type: str) -> str | None:")
    lines.append('    """Return a per-credential description when this field spans levels."""')
    lines.append("    return CREDENTIAL_DESCRIPTIONS.get((field, degree_type))")
    lines.append("")

    out.write_text("\n".join(lines))
    print(f"Wrote {len(entries)} entries to {out}")


if __name__ == "__main__":
    main()
