# Review — feat/175-played-match-data

diff_sha256: 69ca89357d2814c3d0a0e405dc75f6a508e7e6c7cafbdc96c8bbda39762aab3b

rounds: 2

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the shoot-out extraction sits in staging, the winner rule and lineup_order in base, core only casts, the marts serve; no league identifier in the new logic.
- The winner rule, provider status AWD included, follows decisions_taken on every branch; fct_fixture_winner_follows_the_result recomputes it independently, so a swapped comparison, a dropped status or a draw with a winner fails.
- The shoot-out columns are both or neither and never tied on PEN; a PEN without them fails the PEN-scoped not_null tests.
- lineup_order runs 1 to n per team sheet with every starter first, pinned by assert_fixture_lineup_order_starters_first; researched sheets fall to pitch position, then shirt number, with player_id as the last tiebreak.
- The score after each goal uses the same order in the window as in the array; score_after_wrong checks it steps one goal at a time to the served totals.
- Star selects of the changed models feed named-column outputs; the export names its columns, so no payload gains a key.
- Not tested, accepted: the provider order of a provider sheet (sheet_index is not an output column), and the mart's nullable pass-through of lineup_order.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; the one added test file is recorded in amendments with its standing-rule authority (engineering_standards.md §3.1).
- The column names, the winner rule and the order rule match decisions_taken; the AWD status applies the approved "otherwise the side with more goals".
- decisions_reserved stay untouched: a penalties match still counts as a draw in int_legs__team_match; AWD matches stay out of the player mart; no site or export change.
- Thresholds: no new mechanism; the declared recurring cost is the staging read, measured unchanged.
- The fct_fixture description and the new doc blocks state the current state only, with no history.

## escalations
(none)
