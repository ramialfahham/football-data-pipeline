# Review — claude/328-declare-staging-columns-6ccddd

diff_sha256: 72f56338dad8a52d8555cafb67d3f955990733e711a3dc0f88675742c8877351

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Changed files against scope_paths: only stg_apif__generic.yml and the task folder; no SQL, no test added.
- Both descriptions reuse existing text (core.yml group_name, doc season_api_year); no new mechanism, cost or decision-class item; decisions_taken names the approval.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- group_name exists at stg_apif__standings.sql:43 and season at stg_apif__teams.sql:25; both are named by the grain tests, so the declarations close the gap.
- group_name text is identical to core.yml and accurate for the raw $.group field; season doc resolves to the provider season year; rendered lengths are within the 1,024-character limit.
- Documentation only: no layer-contract exposure, no catalogue or metric effect.

## escalations
(none)
