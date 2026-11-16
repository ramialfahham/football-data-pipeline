# Review — claude/184-save-pct-own-goals-65edb0 — 2026-11-16

diff_sha256: afed4c5b6edcd8c55119b62ce147f7f3534ff824826a9dde10f07d1ef2b86ef7

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file in the diff sits in scope_paths; the two catalogue descriptions match the text decisions_taken records as approved in chat, 16 Nov 2026; labels and ids unchanged; no new mechanism, cost or page output.
- Round 2: the corrected decisions_taken sentence (a whole-match keeper's own goals counted from the events where the conceded goal events add up) matches the guards in both base models.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Spell guards, the NULL rule, goals_own_against never above goals_against, the positional union order in fct_fixture_player_stats, same-window gating on the six generated surfaces, the benchmark macro reading shots_on_goal_against_player on every caller, and the value test on fixtures 868079, 1575150 and 1575216 all hold.
- Round 2: the contract's whole-match sentence now states what the code does; the round 1 mismatch is closed.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- An own goal is not a shot on target the keeper faced, so it leaves both the save percentage's denominator and the shots-faced count; the share cannot pass 100%; the descriptions match the formulas and the team twin saves_pct; goals_against_player still counts own goals, correctly.

## platform-reviewer
VERDICT: PASS
risks_checked:
- shots_on_goal_against_player joining POSITION_COUNTS regenerates exactly the position, window and squad-window surfaces; tests/test_generate_metric_sql.py would catch drift; the generator stays deterministic and the extra columns cost nothing measurable.

## escalations
(none)
