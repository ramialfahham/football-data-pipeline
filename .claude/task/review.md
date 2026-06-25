# Review — refactor/500-metric-layer-naming — 2026-06-25 (PR-a, rebased on main)

> G3 review artifact. PR-a of the non-gated #500 metric-layer consolidation:
> catalogue restructure + metric-layer renames + v2 consumers + CSV-corruption repair.
> REBASED onto main after #569 (finishing_efficiency = open-play conversion) merged; the
> rebase had conflicts, resolved so the branch carries BOTH #567's renames/de-dup AND
> #569's open-play finishing. Re-reviewed cold on the rebased diff. scope-auditor +
> analytics-engineer re-run on the merged diff (both PASS). cto-reviewer PASS carried from
> the pre-rebase review — its surfaces (scripts/export_site_data.py + the no-drift guard
> test) are byte-identical to its reviewed versions (the rebase did not conflict on them
> and #569 did not touch them). football-analytics ESCALATEd one wording point; CPO ruled.

diff_sha256: addfa2af20740792c6c2f7002279bd2d1b1f559f7714ed7187162c52b0ed6839

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file is within PR-a's scope_paths; the merge introduces no new CPO-only
  decision beyond the two already-locked sets (#567's #500 renames + entity de-dup; #569's
  open-play finishing, already merged). The new component metrics stay as separate team+player
  rows (no unauthorised de-dup); the merged finishing row is a single "team and player" row
  carrying #569's goals_open_play numerator — both locked changes, no third decision.
- Drift / Appendix A: no metric invented without a catalogue row; no coverage-cut framed as a
  fix; PR-a itself remains rename-only (the finishing NUMBER change belongs to the already-merged
  #569). blast_radius honest.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Rename + finishing coexistence: both player models carry #567's renames (shots_on_goal, saves,
  goals_against, *_per90) AND #569's finishing (events join → goals_penalty, goals_open_play, the
  open-play CASE), and the CASE references the RENAMED denominator shots_on_goal — no dangling
  reference to a renamed-away column (shots_on_target / goals_saves / goals_conceded) anywhere.
  int_season_record__team's legs CTE projects tl.goals_penalty/tl.goals_own (the #569 build fix
  survived the rebase).
- No-drift guard vs catalogue: the guard's `c.entity = m.entity OR c.entity = 'team and player'`
  clause maps the team model (finishing_efficiency_season → finishing_efficiency; goals_*_season)
  and the player model (finishing_efficiency, saves, goals_against, shots_on_goal, goals_penalty,
  goals_open_play) each to a catalogue (entity, metric_id) row — incl. the merged "team and player"
  finishing row and the separate team/player component rows. Guard passes; uniqueness holds; renamed
  ids consistent across catalogue + models + macros + benchmark accepted_values.

## cto-reviewer
VERDICT: PASS
risks_checked:
- (Carried from the pre-rebase #567 review — these two surfaces are byte-identical to the reviewed
  versions; the rebase did not conflict on them and #569 did not touch them.)
- export_site_data.py is the gitignored v2 export, absent from the live pages workflow `paths:`, so
  its renamed literal refs (shots_on_target→shots_on_goal) cannot break the live MVP (D4 holds).
- The no-drift guard test change (drop the goals_saves→saves normalisation; keep the _season strip;
  add the `team and player` clause) is internally consistent with the player model now outputting
  `saves` and the de-duped catalogue rows.

## football-analytics-expert-reviewer
VERDICT: ESCALATE
risks_checked:
- Numerator/denominator penalty-consistency: shots_on_goal excludes penalty kicks (provider
  convention, confirmed by the diagnostic); the merged finishing numerator goals_open_play also
  excludes penalties (and own goals for teams) — both sides penalty-free, [0,1] guarded by the
  model CASE. Football-correct open-play conversion.
- goals_own team-only correctness: own goals credited to the benefiting team's scoreline; a
  player's goals_total already excludes own goals — so the player rows carry goals_penalty +
  goals_open_play but no goals_own. Descriptions accurate; "uncapped"/">100%" wording removed.
- ESCALATED: the merged "team and player" finishing row uses one description whose null clause is
  team-centric ("Null when the window is not fully shot-covered"); for players the current code
  nulls more simply (no shots on goal). Asked whether the merged description is accurate enough for
  both entities or needs a player-specific null clause.
  CPO ANSWER (this conversation, 2026-06-25): the rule is UNIVERSAL — every metric, team and
  player, is NULL when the data to calculate it is not 100% available. The description "Null when
  the window is not fully shot-covered …" therefore states the CORRECT intended rule for BOTH
  entities; no reword needed. What is wrong is the player IMPLEMENTATION (it coalesces missing shot
  data to 0 and computes anyway, instead of nulling on incomplete coverage). Bringing every metric
  — team and player — into compliance with the universal incomplete-data→NULL rule is a separate
  CPO-directed task, NOT part of this rename-only PR (which inherits #569's behaviour unchanged).

## escalations
- question: The merged "team and player" finishing_efficiency catalogue row carries one description
  whose null clause is team-centric ("Null when the window is not fully shot-covered"); the player
  finishing currently nulls only when there are no shots on goal. Is the merged description accurate
  enough for both entities, or must it carry a player-specific null clause?
  CPO ANSWER: The incomplete-data→NULL rule is universal across every metric, team and player, so
  the description states the correct intended rule for both — no reword. The player implementation's
  coalesce-missing-to-0 is the actual defect; fixing every metric to NULL on incomplete coverage is
  a separate CPO-directed task, tracked outside this rename-only PR.
