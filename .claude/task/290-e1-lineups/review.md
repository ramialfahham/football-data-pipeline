# Review — claude/290-e1-lineups — 2026-11-13

diff_sha256: 33f74215b57c405f0568d1e79d51ad0f8a0963b9d06fc096bc4e4d6d0f073bbc

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file in the patch is in scope_paths; the contract carries no amendment and needs none.
- decisions_reserved is none: the position mapping, the winger grid-row rule, the two-names definition and the researched-team rule are in decisions_taken with the approval named and dated; the code matches each ruling.
- No new mechanism or recurring cost: one more failed_checks value, existing seeds, a singular test of the existing kind.
- Impact map evidenced: writers, the dbt ls result, layer rules, deploy order and a measured blast radius; the researched-team join reads a seed, so no cycle.
- No site_v2 or export file: approved_design "none: no page output changes" holds.
- Round 2: the three LAFC position letters follow the league's 4-3-3 line-up order; blast_radius names Sánchez's two events and a measured 0 events of other researched players.
- Round 3 (merge of main, 0ad252f1): the patch holds only this branch's 11 files; the base_apif__lineups conflict keeps main's sheet_ids and fixture_player_id with the branch's provider_position; nothing of main's dropped.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- All three changes sit in base; core.yml gains accepted_values only; no stg ref in core, no mart ref upstream.
- No ref cycle: base_apif__fixture_events reads seeds and staging; fixture_players reads events and the seed; lineups reads both.
- The 40 Austin–LAFC rows: 11 starters and 5 substitutions a side, every replaced player a starter whose minute off equals the substitute's minute on.
- Position CASE: name mapping, winger grid row, null for a null grid and for every other code; the pick is total (is_starter desc, sheet_index asc); the shared-id check counts distinct names and leaves researched matches out.
- Downstream position readers already filter to G/D/M/F; mart_player_fixture_stats now falls back to the line-up's code where a stat line had SUB or '-'.
- Round 2: LAFC's sheet reads 4 D, 3 M, 3 F under 4-3-3; only fixture 1482409 rows changed; the formation test still holds.
- Round 3 (merge of main, 0ad252f1): parsed builds player_id through fixture_player_id and carries provider_position to positioned; the shared-id check and the dedup key on the final id, and an own id belongs to one shirt, so no two people merge under it; the test's raw-id read matches the model for every non-placeholder id; the researched-team join keys on the final id; the position expression moved to the end of src unchanged.

## escalations
(none)
