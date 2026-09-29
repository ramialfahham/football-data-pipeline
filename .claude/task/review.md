# Review — fix/save-pct-own-goals — #180 team save percentage leaves out own goals conceded

diff_sha256: 5988187ad111a3d1a5360073f8a7b66d791e59abf959cba879eec9c91e1171e7

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: all 12 non-artifact files (6 SQL, 4 yml, metric_catalogue.csv, metric_columns.md) are in scope_paths; no amendments needed.
- decisions_reserved: no player save percentage code touched (#184); the saves_pct id and the label "% Shots saved" unchanged.
- Decision classes: the definition change rests on the CPO's scope ruling "B. Team now, player issue" and the plan approval, both in decisions_taken; goals_own_against follows the id pattern recorded on #94; no unapproved wording, URL or format change.
- Thresholds: NEW MECHANISM and RECURRING COST declared none; one self-join on the existing events CTE, one integer column, two sums in models the nightly already builds.
- Impact map: dbt ls lineage (29 models), reader list, layer rules, deploy order and measured blast radius (4,371 of 119,674 legs); no coverage cut.
- Undeclared reach: every downstream reader of saves_pct named; new columns stay in intermediate models, no mart schema gains a column.
- Doc sync: metric_columns.md and the catalogue formula and description updated together; only a historical audit note and the tracker snapshot mention the old formula outside the models.
- A1, A4, A5: logic in intermediate and mart SQL; the new window sums use the same goalkeeper_saves-not-null filter as goals_against_in_save_games; frontend untouched.
- Secrets: nothing credential-shaped, no workflow change, no escalations.log entry, no host address.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: own-goal count read from fct_fixture_event in int_legs__team_match's existing events CTE; coverage-restricted sums in the two same-window intermediates; the subtraction at the two existing division sites; no inversion, no new ref.
- Fan-out: the new ev_opp join reads events grouped by (fixture_sk, team_sk), at most one row per leg; grain holds; missing event row coalesces to 0 like goals_own.
- Dividing sites: only mart_team_momentum and int_team_season__metrics_cumulative divide; every other reader carries saves_pct unchanged; no consumption-layer computation.
- Same-window rule: goals_own_against_in_save_games uses the goalkeeper_saves-is-not-null predicate of goals_against_in_save_games in both the sum and the window variants.
- Column propagation: new columns reach no mart; mart_team_momentum_window, mart_team_momentum and int_team_season__metrics_cumulative select explicitly.
- Tests: no new test by the recorded ruling; the saves_pct 0-1 range tests remain on the marts and int_team_season; none deleted or weakened.
- Catalogue: a redefinition, not a new metric; formula and description change, label, id and format unchanged; the seed row keeps its column count; metric_columns.md in step.
- Competition-agnostic: no league identifier added.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Football validity: saves / (saves + goals_against - goals_own_against); an own goal is conceded but no opposing shot on target reached the keeper; penalties stay in the denominator as shots on target.
- Own-goal side: goals_own_against reads the events credited to the opponent, the mirror of goals_own; shoot-out events already excluded in the same CTE.
- Zero denominators: safe_divide gives NULL when saves plus non-own goals conceded is 0; the coverage guard is untouched.
- Same-window consistency: the new sum uses the same save-covered filter as goals_against_in_save_games and is divided at both sites.
- Direction higher_better unchanged and correct; label unchanged; one transparent ratio of counts.
- Deferred: the player rows still count own goals, reserved as #184; team and player "% Shots saved" can differ for a keeper until then.

## escalations
(none)
