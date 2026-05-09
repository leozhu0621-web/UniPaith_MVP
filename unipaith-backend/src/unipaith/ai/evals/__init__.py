"""Eval harness for UniPaith AI agents.

The eval harness is a *first-class artifact* of this codebase — same review
discipline as application code. PRs that change prompts or agent code without
updating evals will be rejected.

See `runner.py` for the four suites:
  - framework_adherence      — golden conversations, validator-graded
  - extractor_accuracy       — F1 on labeled (turn, expected_extraction) pairs
  - bias_pairs               — paired-input vector-distance assertions
  - workshop_guardrails      — adversarial generation-attempts must all refuse

Run with: `make eval-ai`
"""
