# Review — docs/109-testing-rules — 2026-09-18

diff_sha256: bcbd38c4ee7daf6b8540afb02785d4b3804fd8f01cd44e48ba5fc98ebabd7a84

rounds: 2

Text only: §3.1–§3.5 into `engineering_standards.md` §3, the severity rows kept as worked
examples under the question. Round 1: scope-auditor's verdict was a fail (resolved at round 2):
§3.2 restated `metric_layer.md`'s rule verbatim instead of deferring to it, and §3.5 named the
hygiene script as already enforcing a per-column rule it does not check; analytics-engineer-
reviewer's verdict was a fail (resolved at round 2): the catalogue carries no per-input column
mapping, so the "generated from the catalogue" guard cannot be built from the seed as written.
Round 2: §3.2 defers to `metric_layer.md` in one sentence; §3.5 says none of the four mechanisms
exists yet and describes what the hygiene script checks today; the catalogue-guard bullet names the
missing mapping as #111's first step and calls itself a rule in progress. Both PASS. The contract
is byte-identical across the rounds.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: §3.2's opening names `metric_layer.md` as the one home and repeats nothing of its rule — the contract's "builds on, not restates" is now true of the text; §3.5's four mechanisms stated as not yet built, the first bullet's account of `check_description_hygiene.py` checked against `_object_coverage()` (models, seeds, sources; the content of descriptions, not a column's presence) and found accurate; the catalogue-guard bullet discloses the missing mapping and names #111; the contract byte-identical to round 1 — scope, decisions, reservations unchanged; §3.1, §3.3, §3.4 unchanged and free of dates, round numbers, MR numbers, reviewer names.
- Round 1 (a fail, resolved at round 2): §3.2 quoted `metric_layer.md` line 23 verbatim — two homes for one rule; §3.5's first bullet claimed the hygiene script enforces per-column descriptions, which its code does not do — a mechanism stated as built against the contract's "work to come".
- Authority: a rule extension is the CPO's class; the contract rests on what he did (filed #109, read the draft, said "open the MR") and says the merge is the approval, claiming no approval of the text.
- The two `decisions_reserved` items are left open by the text: no sentence in §3.2 or §3.3 decides the player-derived rates or re-grades an existing test.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the catalogue-guard bullet now states what the seed lacks (no per-game column per expression token; the coverage counts live in the consuming models) and anchors the mapping to #111 — matching what `metric_catalogue.csv`'s header and `assert_metric_catalogue_expr_resolvable.sql` (tokens resolved against `base_relation` only) show; §3.2's opening no longer paraphrases `metric_layer.md` line 23; §3.5's first bullet matches the hygiene script's actual behaviour; §3.5's opening and the rate-guard bullet consistent with §3.2's disclosure.
- Round 1 (a fail, resolved at round 2): "written once, from `metric_catalogue.csv`" could not be built from the seed as it stands — the finding the round-2 text now carries.
- The instance §3.2 names is accurate: `mart_team_momentum.sql` 61-64 gates `shots_on_goal_pct` on `games_with_sot_stats` alone while dividing by `shots_total`; `int_team_season__metrics_cumulative.sql` 101-105 gates it on both counts.
- `dbt_utils.expression_is_true` is the repo's range-test form (`shared.yml` 107-114, `domestic_league.yml`), so the "range test" wording fits; `store_failures=true` beside the existing per-file `config(severity=…)` is valid dbt 1.7, and no test sets it today.
- The severity question re-grades real tests both ways (`status_short` `accepted_values` at `warn`; `deserved_points_cap_did_not_bind` at `warn` matches the "cap that did not bind" row) — deferred to step 2 by `decisions_reserved`, as the contract says.
- The column-class table is an overlay on the per-layer minimums, not a conflict with staging's `not_null` on keys.

## escalations
(none)
