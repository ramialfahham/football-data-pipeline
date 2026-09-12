# Review — chore/115-step8-sweep-tests — 2026-09-11

diff_sha256: 7f65a2f383f8865c581d70929387b1aed804728d29d6e1404ae4a70365f34d09

rounds: 2

platform-reviewer: PASS at round 1 (`8d083659…`), PASS at round 2 (delta: the one line read from
  disk; the patch body byte-identical elsewhere, same 30 headers, same end line)
scope-auditor: PASS at round 1 (`8d083659…`), PASS at round 2 (delta: the one index line
  changed, `test_refetch_cadence.py` only; the contract's index unchanged)

Round 1 → 2. One docstring line, `test_refetch_cadence.py:105`: the platform-reviewer noted the
rewrite "shipped instead" implied a production defect where the bug was in fact found in review;
now "was found in review instead". Comment-only; count unchanged (250, 56).

## platform-reviewer
VERDICT: PASS (round 1)
risks_checked:
- All 2,598 patch lines read, every hunk in the 28 test files: `#` lines, docstring lines and
  module docstrings only; code lines sharing a hunk are context (the dict literal in
  `test_completeness_outcome_and_summary.py:180-188`, `PINNED_CASES` at
  `test_governance_hooks.py:663-680`, the `ROUTING` dict at `:1084-1096`, the parametrize list in
  `test_sync_metric_docs_blocks.py:154-165`, `_MINUTE_LIMIT` in `test_dropped_call_visibility.py`,
  `shared_guard_paths()` still reading the literal `"platform-reviewer"` key).
- `GOOD_BODY`: HEAD's literal and the new concatenation evaluate to the identical string (the
  `\n\n` between sections, the trailing `\n`); all 44 uses in the file consume the value, and every
  `.replace` substring still occurs in it.
- Meaning drift, 20+ rewrites sampled: `test_refetch_cadence.py:301-308` names
  `scripts/check_raw_freshness.py` — verified to exist, read `sources.yml` and parse
  `freshness.error_after`/`warn_after`; `deploy/nightly/README.md:133,202` confirms it is
  `fdp-freshness`. `test_no_dead_issue_refs.py` keeps #115/#151/35 with the date dropped and
  `min(DEAD_GITHUB_ISSUES) == 151` unchanged. `test_raw_merge_on_write.py` keeps the reversal
  reasoning, the mechanism, the damage figures and the compaction rule. Routing keys reworded to
  roles in prose only; every code-level key untouched. One wording drift noted (the
  `test_refetch_cadence.py:105` "shipped instead") — fixed at round 2.
- The pin: 495 − 245 = 250, 84 − 28 = 56; the only hunk in the pin file is the two constants;
  not independently re-measured (no shell).
- False-clean grep over `tests/*.py` for every marker shape: every date hit is fixture data,
  every `-reviewer` hit a routing key in code or a regex in `test_governance_doc_parity.py`,
  every `CPO`/`!27`/date-in-prose hit a string literal (gate samples, fixture bodies, assertion
  messages — outside the comment/docstring definition and criterion 2 forbids touching them).
  GitHub-era "MR2/MR3/MR4b/MR6" labels in six files are neither `!N` nor a credit; pattern
  widening is reserved — recorded, not failed.
- Docstring readers: `__doc__` once (presence only, a script function); `inspect.getsource` once
  for real, feeding `ast.parse` (comments invisible). Nothing asserts on a swept docstring's text.
findings:
- none

## scope-auditor
VERDICT: PASS (round 1)
risks_checked:
- Every hunk read (2,599 lines): only `tests/**` and the contract; no hook, script or dbt file, so
  `protected_override: none` is accurate; nothing crosses §10.
- Authority: the dated "do it" to the four-sweep plan, consistent with sweeps 1–2.
- Non-comment changes: the pin (495−245 = 250, 84−28 = 56) and the `GOOD_BODY` re-join — the
  three segments concatenated by hand equal the original triple-quoted value; a form choice.
- Attribution: every `+` hit is an issue pointer kept by rule or a credit correctly dropped; the
  two "product owner" substitutions describe a class of decision, not a past finding.
- Stale-fact corrections verified: `scripts/check_raw_freshness.py` exists and reads
  `sources.yml`; the #115/#151 facts kept.
- The single amendment accounts for the only non-comment change; `decisions_reserved` intact;
  no credential or permission change.
findings:
- none
