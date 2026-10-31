# Review — feat/237-standings-tie-order-v2

diff_sha256: f1b9af0e4f3c02ada9b797309516562f0dc127ad97c1ac4f2f91de588b0f5022

rounds: 2

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- int_standings__official_rank joins the rebuilt table's latest kick-off 1:1 on (league_code, season_api_year, group_name, team_sk); a null key, played or points keeps the provider's rank.
- is_section_matched is constant across a section; within a matched section place_by_rules is never null, and row_number by (place_by_rules, standing_rank, team_sk) is deterministic and runs 1 to n.
- table_position is null exactly where place_by_rules is shared on the full key (assert_tiebreak_rules_end_undecidable), so the new test cannot false-fail on a shared place.
- Our goals equal the provider's in a reproduced season, so the goal-based criteria agree with the displayed row.
- Every fct_standings.standing_rank reader classified: mart_standings, mart_next_matchday and int_team_season__standings_primary switch; table_state (previous_position, no cycle), section_kinds and four tests stay.
- Round 1 found assert_one_match_that_matters_per_competition still ranking by the provider's place and a false standing_rank description; round 2 confirms both fixed.
- The vacuous-pass risk of the new test is answered by prod evidence: every section with a rule table is compared in all 15 leagues.
- Layer placement, competition-agnostic SQL, description lengths and the R7 approval checked.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every non-task path is in scope_paths, including layering.md, shared.yml and the next-matchday test added on a clean tree in round 2.
- The impact_map states the dbt ls result (14 models) and names the next-matchday test.
- decisions_taken names the plan, the mart_standings header sentence, the split R7 and metric_layer.md sentences and the cost, all approved in chat, 2026-10-31; decisions_reserved is none.
- layering.md is not on the core-document list of working_agreement.md section 10, so its two inventory rows need no pre-approved text; metric_layer.md is, and its sentence is approved.
- No credential, workflow or permission change; no site_v2/src or export change, so approved_design does not apply.
- Round 1 found layering.md stale and the impact map unevidenced; round 2 confirms both fixed.

## escalations
(none)
