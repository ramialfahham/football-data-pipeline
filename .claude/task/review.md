# Review — fix/player-cleaning-and-generated-metrics — player stats cleaned once in base, player metrics generated from the catalogue

diff_sha256: a21ecce08220439690c015f0fa5de83a589153e6cc9c6d940d5ef35a9fc47118

rounds: 4

rounds_cap_override: the CPO approved a fourth round in chat after the MR build failed player_contribution_player_pct_within_unit on a player credited with a goal and its assist; the fix is one cleaning check under the approved contradiction rule, with its test and answer-key case.

Round 4 went to scope-auditor, analytics-engineer-reviewer and football-analytics-expert-reviewer. Its delta (the assists check in base_apif__fixture_players, the cleaning test, the answer key, base.yml, the contract) touches no path routed to platform-reviewer or cto-reviewer; their round-3 verdicts below stand.

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every file in the cumulative diff is in scope_paths; the .sqlfluff, sync_metric_docs_blocks.py and its test, and the new history test carry amendments naming their authority. No secret-shaped string in the patch; escalations.log untouched.
- Threshold crossings: the generator script with its pytest and the one-time re-merge in fct_fixture_player_stats are declared as NEW MECHANISM with their authority; the recurring read (base reading events, statistics and fixtures; the season and position models reading the legs; the cleaning test reading staging; the re-merge check; the history test) is declared under RECURRING COST with a measure-before-merge commitment.
- §10 and Appendix A: every catalogue edit is a rename or one of the recorded rulings (pass accuracy as a count, the goal and penalty source rules, raised_to_part, the 8% limit, the finishing-efficiency guard replaced); no invented metric, nothing in the frontend. The builder readings are declared as readings, not as CPO rulings, and surface in the MR head.
- Rounds 2 and 3 (deltas): the re-merge check is a recovery path of the same ruled re-merge, not a new mechanism class; the renamed history test and its contract entries agree on the file name; its half-of-base line is a test-internal tripwire explained in its header and the amendment.
- Round 4 (delta): limited_to_team_goals is recorded among the CPO-approved names and in an amendments entry, with its counts; the check applies the issue's contradiction rule and its gap of 2 to assists, a match stat, so no result is altered; the name agrees across base.yml, the model's correction entry, the test's rule list and the answer key; no new model, file, source read or recurring query.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layers: base reads only stg_* and base_* models and sets no materialisation; core refs only base; windows and eligibility are hand-written in int and mart models, formulas generated. No layer breach.
- Tests with the change: the grain test stays; the four new tests are severity error with store_failures; the formula recompute has a floor against a vacuous pass and re-derives each window independently; not_null tests removed only where the descriptions now say NULL is legal.
- Same-window rule: every generated ratio gates numerator and denominator on the same window_is_complete and per-row input; no mismatched-coverage ratio. Marts keep every export key; no competition identifier in the added lines; the impact map's 38-model lineage recounted.
- Round 2: the re-merge check covers column absent, column present on no row, and populated; no path makes every build a full re-merge. Round 3: the table-wide history test catches a history never merged and no longer fails on a row whose base value moved after its merge; that limit is stated in deploy_order.
- Round 4 (delta): assists_checked caps a player's assists at the team's goals minus his cleaned goals after the goals are resolved, gap of 2 corrected, larger blank, NULLs passed through; assists_checked_by_team blanks only positive assists, so a team's remaining sum is at most its goals; the output and the stat_corrections entry follow; the two new test checks read the cleaned output and the score, not the model's CTEs; no new ref, no league identifier, no metric SQL changed.
- Residual, for the team-side step, not this diff: int_legs__team_from_players sums around a player value the cleaning blanked, a blanked assist included.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanisms: scripts/generate_metric_sql.py (stdlib only, plain SQL between markers, pytest drift check) matches the issue's decided mechanism; the one-time re-merge is declared with the CPO's answer. No guard path, dependency or credential in the diff; the new tests fail closed.
- Round 2: the re-merge check is a second condition on the ruled re-merge; countif returns 0 on an empty table, so no NULL trap; its query is under BigQuery's 10 MB minimum and declared.
- Round 3: the history test is one countif per table, no join; coarser than a per-row comparison, which is acceptable because the failure it guards is all-or-nothing (one merge statement); its nightly read falls from about 0.2 GB to about 30 MB and the change is declared in scope_paths, deploy_order, RECURRING COST and the amendment.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL, two findings: the re-merge trigger keyed on the column's existence, so a build failing between the schema change and the merge would leave the history empty for good (verified against dbt-bigquery's incremental macro: the schema change and the merge are separate statements); and no test pinned the re-merge branch. Round 2: finding 1 closed by the check for goals_penalty on no row; finding 2 open, because the per-row fact-versus-base test could fail on a base value that moved after its merge. Round 3: both closed by the table-wide history test, which fails when the fact carries goals_penalty on fewer than half as many rows as base and pins the trigger.
- Generator: idempotent re-run, --check and the pytest fail closed on drift; its aggregate regex meets no nested parentheses in the current catalogue rows.
- CI lint: `sqlfluff lint models` from dbt_project/ with the dbt templater passes on every model, the files newly inside the raised size limit included.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Catalogue scope: in-place edits only, no row added, removed or re-keyed; the player formulas move to the new input names; the two accurate-passes rows lose the conversion and now read "passes that found a team-mate".
- Football validity: pass accuracy, per-90, open-play goals and minutes per appearance are formulas a fan accepts; finishing efficiency stays within 0 to 1 without the window guard, because base raises shots on target to open-play goals and limits penalty goals to goals, and the cleaning test names both contradictions.
- Direction flags unchanged and correct; every rewritten ratio states its zero-denominator NULL; the contribution description matches the model's strict window.
- Unchanged by this branch and outside this review: player save percentage counts own goals conceded, already filed as its own issue.
- Its territory (metric_catalogue.csv) is unchanged by the round-2, round-3 and round-4 deltas.
- Round 4 (the football reading of the assists check): every assist belongs to a team goal and a player cannot assist his own, so a genuine assist cannot exceed the team's goals minus his own and cannot trip the player bound; the bound treats unknown goals as 0 and uses the full score, so it only loosens; the team-level blank keeps zeros, which cannot be part of an excess, and matches the keepers' pattern; the Lens case (goals 1 from the events, assists 1, team goals 1) becomes 100% instead of 200%, worked out correctly by hand.

## escalations
(none)
