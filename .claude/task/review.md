# Review — fix/own-goal-shootout-goal-split — #179 own goals and shoot-out kicks in the goal split

diff_sha256: 4c9b766f5023339b64faf6fd193b2a0be1148df69eb33f50a0cde00684e484bd

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: all 7 non-artifact files (4 models, the new test, metric_catalogue.csv, metric_columns.md) are in scope_paths; no amendments; nothing out of scope touched.
- Decision classes: catalogue and description wording change with meaning unchanged; the contract cites the CPO's plan approval and his ruling "A. Error, 3 named"; the three excluded fixture ids match that ruling; no metric label, format or URL changed.
- Doc sync: seed and metric_columns.md consistent; no other contract document describes the changed filter.
- decisions_reserved: the provider-event correction for the three matches and a player-side shoot-out test are not done in the diff.
- Impact map: carries the actual dbt ls selection and its 42-model output, measured counts, the reader list and the deploy order (test merges with the model change); not a coverage cut.
- Thresholds: NEW MECHANISM none (singular test, store_failures an established pattern, the id list is the CPO's ruling); RECURRING COST declared at 38 MB per run.
- Secrets and permissions: nothing credential-shaped, no workflow or permission change.
- A1 to A5: no new metric, logic stays in the intermediate layer, no frontend logic, no escalations.log entry.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the four changes are in 4_intermediate models reading only fct_fixture_event; no stg or mart ref, no materialisation override, no partition_by or cluster_by; exactly four fct_fixture_event readers exist and all four are in the diff.
- Own-goal fix: the ev_own / ev_opp double join is one join on l.team_sk; events groups by (fixture_sk, team_sk) so the leg grain is unchanged; the rename own_goals_scored to own_goals_credited leaves no stale reference.
- Shoot-out filter: `event_comments is distinct from 'Penalty Shootout'` is NULL-safe; event_comments exists on fct_fixture_event; same wording in the four models and the test.
- Test: recounts open-play goals from 'Normal Goal' events, so it is not checked against the model's own difference and goes red if the own-goal join or the shoot-out filter regresses; coverage keeps only matches whose attributable goal events sum to the score; error severity per the ruling.
- Hardcoded fixture ids: fixture_sk equals fixture_api_id, so the ids are valid; fixture, not competition, identifiers; each named with its reason.
- Catalogue: description text only on the three rows; expression, source, grain, format, group and order untouched; metric_columns.md matches the seed.
- Consumption layer: no export script or frontend code in the diff.
- Impact map: writers, lineage, column readers, layer rules, deploy order and blast radius all present and specific.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Catalogue diff: three rows, description only; every other cell on those rows unchanged against main; no new metric or formula.
- Football validity: a shoot-out kick is not a goal in the scoreline, so leaving it out of penalty goals and the open-play split is right; an own goal counts for the side it benefits; the new goals_own wording is accurate and matches the corrected join.
- Model, test and description agree: own-goal event joined on the team's own team_sk; all four readers filter shoot-out kicks NULL-safely; the test checks events against the scoreline at error severity.
- Edge cases: the finishing rows stay untouched and nothing is capped; the three provider-mislabelled matches are named in the test with reasons and reserved to the CPO.
- Direction: goals_penalty and goals_own stay higher_better; no direction changed.
- Scope: every changed file inside scope_paths; the docs block regenerated from the seed.

## escalations
(none)
