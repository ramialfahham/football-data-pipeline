# Review — chore/261-comments-scripts — 2026-11-10

diff_sha256: 998f04967e244e7e9f7a7cc297ef2b9d345957f9e1f4b32caed462e577d39f2e

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every touched file is in scope_paths; the protected, held and excluded scripts are untouched.
- The only non-comment change is the two pins; trailing comments removed from code lines leave the code identical.
- No module docstring a script reads through __doc__ is in any hunk.
- Rewritten comments are true of the code, including the drop scripts' --dry-run default and the wait_for_nightly polling rules.
- The impact_map names the export scripts' readers; no new mechanism, rule or cost.

## platform-reviewer
VERDICT: PASS
risks_checked:
- No code line, SQL, regex, help text or printed string changes in the 35 scripts, the six CI gate scripts included.
- wait_for_nightly.py keeps why an in-progress run is one without completionTime, why five executions suffice, and why an API error must raise.
- The two drop scripts say they drop unless --dry-run, and the injuries one keeps its run-after-ingest-removal precondition.
- Blank lines before defs are intact; no changed script is cited by line number anywhere.
- The pin drop of 37 lines matches the marker lines the patch removes.
- check_layer_contract.py quotes both layer materialisation lines that tests/test_materialisation_policy.py pins, and no other test pins comment text of a changed script.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The four export scripts change only docstrings; queries, tables, parameters and output paths are untouched.
- No data rule a reader needs was lost; the metric grain and the longest-stem rule stay stated where the code uses them.
- No kept comment in the dbt-reasoning scripts is false about today's code.
- The impact_map lists every reader of the export scripts, and none reads a comment.

## escalations
- none
