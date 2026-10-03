# Review — docs/metric-descriptions — every catalogue description in plain words, held by a check; lower_is_better gone

diff_sha256: f212f9c1bd64f3970822556d40f5ef09142e3a6cb60e50d051b9602a01abe2fc

rounds: 2

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- All 89 descriptions against each row's formula: each is real on the pitch, one sentence under 200 characters, no listed word or snake_case name; twins read alike where their formulas match.
- Round 1 FAIL fixed: goals_against_player, saves_player_pct and shots_on_goal_against_player say "in goal", as the cleaned keeper figure is; passes_key_per_match and league_rank reworded.
- Shares hold on the pitch: every numerator is part of its denominator; finishing holds through the cleaning's shots-on-target rule.
- The dropped lower_is_better agreed with direction on all 89 rows (16 lower_better), so no information is lost; the 16 directions read football-correct.
- Notes on unchanged columns (#177 labels and interpretations, #184 own goals) are recorded in the contract; the goals_against_player interpretation is a note for #187.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every description against its numerator, denominator and base relation; no formula column changes.
- Readers of the dropped column: mart_team_leaderboards reads direction, the catalogue's tests read neither lower_is_better nor description, and the deleted lockstep test has no other reference; the seed drop reaches prod through the nightly seed run.
- The export maps direction to its legacy flag one to one; the three lower_better bound metrics are exactly the three true entries in the committed legacy file.
- The conversion is a serialisation of a warehouse value, inside the consumption-layer rule.
- Round 2 delta: five description texts and their regenerated blocks match the formulas and each other.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The description check raises Abort in _render, so both the write and --check fail closed, and CI runs --check in validate:governance.
- Round 1 FAIL fixed: one refused case per listed word, mixed-case and digit snake_case refused, "annulled" and "rapid" accepted, so removing a word or the word boundaries turns a test red; the 200/201 boundary is pinned.
- The case-insensitive snake_case pattern finds nothing in the real seed; metric_columns.md matches the generator's output, with no stale derived block.
- The export's removed helper has no remaining reference; no dependency, workflow, hook or build change.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The four document lines swap lower_is_better for direction and nothing else; no block gains or loses a field, row, tier or order.
- direction holds what the lines need (higher_better, lower_better, neutral), and the team-profile delta line is correct for goals against.
- site_v2 reads direction only, and no page reads catalogue descriptions, so nothing a fan sees changes.
- Given in round 1; the round-2 delta touches no wireframe, site_v2 or i18n file.

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed path is in scope_paths; the round-2 contract amendment records the football reviewer's notes with #190's authority, made on a clean tree.
- Reserved: labels, groups, tiers, order, format, direction and interpretation unchanged on every row; no metric added or removed; no formula column edited.
- The rewrite rests on the CPO's quoted instruction of 2026-10-02; the two readings are declared under the dated delegation.
- No new mechanism or recurring cost: the check sits inside the existing script beside the window check.
- No credential, workflow or permission change; doc-sync holds, the only remaining lower_is_better is the export's output key for the frozen legacy site.

## escalations
(none)
