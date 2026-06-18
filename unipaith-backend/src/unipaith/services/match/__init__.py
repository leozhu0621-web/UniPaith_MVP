"""CPEF match scoring helpers (Spec 3 — AI Structure).

Pure, deterministic, no LLM. `params` holds tunables + confidence→gain math;
`fits` holds the per-type fit functions. The top-level assembly lives in
`unipaith.services.matching` (which imports from here).
"""
