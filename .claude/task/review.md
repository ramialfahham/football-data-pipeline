# Review — feat/metric-rename-goals — 2026-08-26

diff_sha256: f16ef3354811f4f3976f171e0898577f89f4be8fedd8a19a9b094b1f188567de

rounds: 2

<!--
WHAT CHANGED BETWEEN ROUND 1 AND ROUND 2. The CODE is byte-identical: 11 dbt files, +52/-57 in both
rounds. The only substantive delta is that the round-1 scope-auditor FAIL is fixed at its root —
the naming programme's six rulings are now recorded in `.claude/task/escalations.log` in the CPO's
own words, and `contract.md`'s `refs` cites that entry instead of an uncommitted plan file outside
the repo. scope-auditor is re-spawned. The two PASSes stand: neither depended on the citation, and
analytics-engineer explicitly verified the ruling against `escalations.log` after it was written.
-->


<!--
Required reviewer set computed from .claude/review_routing.json against the staged paths:
  scope-auditor                       always
  analytics-engineer-reviewer         dbt_project/**
  football-analytics-expert-reviewer  dbt_project/seeds/metric_catalogue.csv
No guard path is staged, so no opus promotion; all three run on the pinned sonnet. Verdicts are
appended below as each blinded reviewer returns; none is written by the builder.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 metric-naming authority: verified `escalations.log` now contains a committed, timestamped
  entry "2026-08-26 THE METRIC CATALOGUE NAMING PROGRAMME" whose RULING 1 quotes the CPO verbatim,
  "goals_for becomes goals", and that `contract.md`'s `refs` cites exactly that entry. This is the
  defect round 1 FAILed on, an uncommitted unverifiable plan file substituted for the log; it is
  resolved with a real, quotable, committed ruling.
- Scope: every file in the diff falls inside `scope_paths`. No model SQL, no column rename, no
  frontend file touched.
- Reference-count arithmetic: counted the repoints directly in the patch. 12 team-grain, 6
  player-grain, matching the claimed 18, including the non-obvious `mart_player_match_log` case
  where the column is the team scoreline rather than a player stat.
- Catalogue row: only `metric_id` and `label_i18n_key` changed. Formula, direction and
  interpretation untouched, so a pure identifier rename rather than a redefinition.
- Columns unchanged: `goals_for` remains the column name everywhere it appears; only the
  description reference moves. `decisions_reserved` correctly leaves "whether the columns follow"
  open rather than deciding it silently.
- Credentials/secrets: swept the full diff; nothing credential-shaped.
- Threshold crossings: no new mechanism, no recurring cost, no schedule change; `decisions_taken`
  correctly declares none and nothing in the diff contradicts it.

## escalations
(none)

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Read the single changed catalogue row in full: confirmed only `metric_id` and `label_i18n_key`
  changed. Formula (`sum(goals_for)`), base_relation, direction, lower_is_better, group, tier and
  the description and interpretation text are byte-identical. No football definition changed; this
  is a pure identifier rename, not a redefinition.
- Direction sanity: `higher_better` for a team's scored-goals count is football-correct and
  unchanged.
- Edge-case honesty: the description still states the count is read from the authoritative match
  scoreline rather than summed from player or event records, which is the honest reason it does not
  undercount own goals.
- Traced the docs-block fan-out the rename forces: read both new blocks. The team block correctly
  describes the scoreline-sourced team count, the player block correctly stays "Goals scored." for
  `sum(goals_total)`. No conflation between the two entities' definitions.
- Dangling references: grepped for every derived block being removed
  (`goals_for_prev_season__team`, `goals_for_sum_season__team`, `goals_for_this_season__team`,
  `goals_for_delta_yoy__team`, `last_meeting_goals_for__team`) — none is referenced anywhere, and
  the corresponding columns carry no `description:` at all, confirming only the two bare blocks
  dangled and both are repointed.
- Frontend blast radius: grepped `site_v2/src` for `metrics.goals_for` and `metrics.goals.label` —
  zero hits in the locale dictionaries, the row contract or any page spec. The displayed team goals
  row is the separate `goals_per_match` metric, untouched. `metrics_display.md` confirms the raw
  team total is not itself a rendered row.
- Confirmed the team/player collision on `goals` is intentional and safe: the seed's uniqueness
  tests scope per entity, and the same shared-bare-name pattern already exists for `goals_against`.
- ⚠ On the contract's authority: noted that `refs` quotes a plan file rather than a verbatim
  `escalations.log` entry, and classed that as a provenance question for scope-auditor rather than
  a football-truth defect.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: zero model SQL files touched. Only the seed row, the generated docs blocks and
  `description:` lines in nine yml files. No logic moved between layers; the layering contract is
  not engaged.
- Catalogue governance: the rename's authority is confirmed present, verbatim, in
  `escalations.log` as RULING 1. A real quotable CPO decision backs the rename.
- Per-reference classification: read the actual model behind every one of the 18 repointed
  references rather than trusting the contract's prose. All 12 team repoints sit on team-grain
  models, all 6 player repoints on player-grain models. The one non-obvious case,
  `mart_player_match_log`, checked against `mart_player_match_log.sql:89-90`: its `goals_for` is
  `if(team_sk = home_team_sk, f.goals_home, f.goals_away)`, the fixture scoreline, distinct from the
  player's own `goals_total` which carries no doc reference. Classification correct.
- Dangling-reference sweep: grepped the whole `dbt_project/` tree for both retired block names after
  the patch. Zero hits.
- Seed-as-config impact: `ref('metric_catalogue')` appears only in five singular tests, never in a
  model, so the impact_map's "no lineage change" claim holds. The one test naming a `goals_for*`
  string addresses the column `goals_for_sum_season`, unrenamed and untouched, not the metric id.
- Orphaned derived blocks: verified the five deleted derived names correspond to columns that carry
  no `description:` at all in the current tree, and none of those files is part of this diff, so
  the loss is pre-existing rather than a regression introduced here.
- Seed structural integrity: 87 lines, 15-column header, the renamed row keeps
  `numerator_expr = sum(goals_for)` against the untouched column, and the pre-existing
  `goals,player` row remains a distinct pair.
- Consumption layer, competition-agnostic and same-window checks: no export script, no frontend
  file, no league-code logic and no new ratio in this diff, so none of those triggers apply.
