# Review — feat/deserved-vs-actual-in-points — 2026-07-22

> Required reviewers per `.claude/review_routing.json`: `scope-auditor` (always) +
> `analytics-engineer-reviewer` (`dbt_project/**`) + `football-analytics-expert-reviewer`
> (`dbt_project/seeds/metric_catalogue.csv`). No opus floor: no guard path is touched.
>
> **WHAT THIS CHANGES.** Two defects in one model, fixed together because they are the same block of
> SQL. (1) The read was WRONG for tournaments: `deserved_rank` ranked all teams 1..N while a
> group-stage standing is a position within a group, so 224 non-domestic rows carried mean absolute
> gaps of 8 to 21 places against 3.4 for real leagues. (2) Rank was the wrong space to communicate
> in: a fitted line there can predict positions that do not exist, which is why the approved mock's
> hero draws 0.4 and 21.3. Deserved-vs-actual now speaks in POINTS, and only where that sentence is
> true.
>
> **THE EVIDENCE, measured over 91 domestic league-seasons and 1,790 team-seasons.** SoT difference
> versus points is Pearson +0.84, stable across balanced (0.85) and unbalanced (0.83) seasons, and
> the slope gives the first fan-readable magnitude this metric has ever had: one extra shot on target
> of difference per match is worth about 9.8 points over a 38-game season. Stated up front because a
> reviewer will ask: goal difference correlates +0.96, far higher, but points are computed from those
> same goals, so it is near-tautological and cannot be a *deserved* signal.
>
> **SIX CPO RULINGS, all logged BEFORE any code** (`escalations.log`): deserved TOTAL points; keep
> `deserved_rank` but re-derive it from deserved points; gap signed actual minus deserved so NEGATIVE
> means under-performing; the names `deserved_points` and `sot_points_gap`; `sot_rank_gap` dropped so
> two gaps cannot carry contradictory signs; whole-points format.
>
> **FOUR ROUNDS, and every FAIL was correct.** The rounds are the substance of this review:
>
> 1. **Round 1** — scope PASS, analytics PASS, football FAIL. Restricting to domestic leagues is not
>    enough. MLS ranks within conferences and the Apertura/Clausura formats split a year, so
>    `actual_rank` restarts at 1 per section: the SAME defect that excluded the tournaments, surviving
>    inside the domestic set. I fixed the instance and missed the class, again. Its evidence was
>    partly wrong (it argued from `group_description`, which holds qualification annotations and is
>    multi-valued for the Premier League too); the conclusion was right, and I confirmed it by the
>    decisive property instead: 9 of 55 fittable league-seasons, 232 of 1,152 rows.
> 2. **Round 2** — analytics FAIL, and this one is mine twice over. My fix gated only the rank, which
>    made an existing test false for those 232 rows. I DELETED the failing direction instead of
>    narrowing it, leaving `deserved_rank` with no positive-existence guard at all: the column could
>    have gone silently empty across every normal league with the whole suite still green. **A test
>    may become NARROWER when a change makes it partly untrue. It must never become SHORTER.**
> 3. **Round 3** — football FAIL, on the deeper version of round 1. My claim that "points stay
>    comparable" is true for MLS and FALSE for Apertura/Clausura, where one season spans two separate
>    tournaments whose points reset. I VERIFIED this against the warehouse rather than taking it on
>    faith: Argentina 2025 carries 30 teams, a 15-position table, and 32 to 37 games per team. So the
>    gate moved into `league_season_fittable` and now withholds ALL THREE outputs, and the
>    biconditional test came back.
> 4. **Round 4** — scope FAIL, and it caught the worst one. I had recorded the withholding as an
>    application of the CPO's tournament reasoning. §10's meta-rule says that when a case does not
>    clearly match a written rule, the CLASSIFICATION is the CPO's, and "it is analogous to X" is not
>    a licence. **THIRD §10 misclassification of the identical shape in one day**, after the metric
>    rename and the review routing. Put discretely; **CPO: "Withhold all three, from all four"**.
>
> **THE PATTERN, stated because it is one pattern and not four bugs.** Every failure above is me
> treating a principle the CPO stated in one domain as permission to apply it in another, or trading
> away a guard to make my own change pass. The reviewers were not finding different defects.
>
> **WHAT THE DATA DOES, verified against the live warehouse and not asserted.** 920 rows over 46
> league-seasons. Zero violations on every data test. Zero non-domestic rows. Zero rank drift against
> the 864 balanced rows live in the mart today, so the flagship read did not move where it should not
> have. The gap sums to exactly 0 across a balanced season and approximately 0 mid-season, because
> each fitted rate is scaled by that team's own games played.
>
> **ACCEPTED COST, stated in the question the CPO answered:** MLS could probably support the points
> read and loses it, because separating a conference split from a two-tournament split needs a signal
> that does not exist. Recorded as owed; reversible.
>
> **NOT VERIFIED.** dbt and SQLFluff are broken locally and the dbt MCP is not connected, so nothing
> was compiled and no dbt test was executed. What ran: the layer contract, YAML parse on all three
> schema files, catalogue integrity, and the model's real SQL resolved against BigQuery with every
> data test re-expressed as an assertion. The dbt tests themselves are CI-gated.

diff_sha256: cd32009bfae417dbd6d7bf4b7e9b850b3dbafe8eef2422a4e8a87bff9d5452a1

## scope-auditor
VERDICT: PASS
risks_checked:
- The §10 authority for withholding the deserved read from four live competitions. Confirmed the `escalations.log` entry records a discrete, locatable CPO ruling covering exactly what the code does (all three outputs, all four leagues), that the contract amendment now cites that ruling rather than an analogy, and that its admission of the earlier weaker claim is explicit rather than a silent overwrite.
- Sign-convention safety across the retired and replacement gap. Verified `sot_rank_gap` is deleted from the model, the mart, both schemas and the catalogue, and that the arithmetic contract test pins the inverted convention, so the two cannot coexist and contradict each other.
- Gate decomposition and the boundary case. Verified all three outputs gate together on the single-ladder property rather than a league list, that the biconditional and single-ladder tests assert the condition held, and that the property form catches a future split-format league with no file edit, preserving the zero-file rule.
- Scope and smuggling across four rounds: every touched file inside `scope_paths`, every amendment written on a clean tree, no path added.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The positive-existence guard I had deleted. Confirmed `ranked` is back to a single condition and that `league_season_fittable` is group-constant, so `deserved_points` and `deserved_rank` cannot diverge on any code path: the defect is now closed structurally, not merely by a paired test.
- Vacuity versus redundancy in the four tests. Traced which are provably implied by the gate and reported them as redundant-but-not-coverage-losing, noting the retained uniqueness test checks by an independent execution path over materialised output rather than re-reading the same in-CTE boolean. Confirmed no test that could previously catch a real defect was weakened.
- The computational effect of folding a fourth condition into the gate. Verified `stats` and `fitted` compute window aggregates over the whole partition regardless of the flag, that no BigQuery aggregate throws on a degenerate window, and that the newly excluded groups flow through with clean NULLs.
- Earlier rounds, still standing: the OLS identity is genuine and invariant to the sample-versus-population stddev choice because the divisor cancels; the only two divisions are `safe_divide`; the balanced-season rank invariance is structural rather than coincidental; and no dangling `sot_rank_gap` reference remains anywhere.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Whether any surviving published row still rests on a season that is not one continuous competition. Traced the mechanism through all four CTEs and confirmed all three outputs are structurally tied to one condition, then cross-checked the exclusion set against the competition registry, whose own note independently confirms Liga MX runs Apertura plus Clausura in one API season. The remaining leagues carry no documented split-table format.
- Whether the descriptions still claim points survive in those leagues, which was the substance of its FAIL. Read all three catalogue rows, the model header and the CTE comments, and confirmed the false claim is gone from every file and replaced by an accurate statement of why the rows are null.
- The MLS decision against football reality rather than internal logic: its points genuinely are cross-conference comparable, since the Supporters' Shield is awarded on combined points, so blanket withholding is stricter than the football fact requires. Judged acceptable because it is disclosed rather than hidden, the model comment says so outright, and the alternative is correctly deferred as a design decision.
- The `safe_divide` no-spread null path it raised earlier: confirmed present verbatim in two catalogue rows and inherited without carve-out by the third, and stated twice in the model comment.

## escalations
- question: Deserved vs actual cannot be computed honestly for MLS, Liga MX, Argentina and J-League, because their tables are not a single 1..N ladder. What should happen to them? Three paths offered: withhold all three metrics from all four; withhold only where points genuinely reset, keeping the points read for MLS; or park the change until a continuity signal is designed. Recommended withholding from all four, because for Argentina and Liga MX even the points total sums two separate competitions, while separating the two cases needs a signal that does not exist and the alternative is a hardcoded league list that breaks the zero-file rule.
  CPO ANSWER: "Withhold all three, from all four" (AskUserQuestion, 2026-07-22). Accepted cost, stated in the question: MLS loses a points read it could probably support. Full record is the last entry in `.claude/task/escalations.log`.
- question: The six metric-definition decisions this change rests on (points as the unit, keeping a rank derived from it, the gap sign, the two names, dropping the rank gap, the display format).
  CPO ANSWER: all six answered discretely via AskUserQuestion on 2026-07-22 and recorded in `.claude/task/escalations.log` before any model file was touched.
