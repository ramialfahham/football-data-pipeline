# Review — feat/last-matchday-flag — #159

diff_sha256: 8b042d31c4bde1d3a120877b095d5d537e4896f882f412ba2e7e1adb69b749fa

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the definition rests on the CPO's Option-1 answer quoted in decisions_taken; the impact_map names the dbt ls command and its test list with a measured blast radius matching the evidence; THRESHOLD DECLARATIONS state no new mechanism and no recurring cost, and the diff is an additive column on the is_next_round pattern; no site, export or ingestion file touched; no credential-shaped string.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- is_last_round sits in the mart beside is_next_round, built from fct_fixture, int_legs__team_match and mart_next_matchday; traced by hand: last_round is season-scoped through next_round, takes the max round_sequence among rounds with a played fixture, and the column also requires the row to be played, so a round in progress carries both flags and a finished tournament none.
- The new column has not_null and accepted_values; the singular test recomputes from fct_fixture and int_legs__team_match, not the model's CTEs; no metric catalogue entry needed (a boolean flag, as its siblings); no hardcoded league; the export's explicit column list excludes the column; the mart is a leaf (only its own tests reference it); grain unchanged.

## escalations
- question: When a competition's latest round is only partly played (a round in progress, or a postponed match inside it), which matches are its 'last matchday'?
  CPO ANSWER: Option 1: the played part of the newest round; only played matches are ever flagged (answered in plan mode; issue #159's first line reworded to match).
