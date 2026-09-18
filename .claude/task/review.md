# Review — feat/111-rate-guard — 2026-09-18

diff_sha256: cb01c3ec496622feac591901ed950d5d0ca705f244776d54ef472a8dee787160

rounds: 2

Round 1: scope-auditor and platform-reviewer PASS; analytics-engineer-reviewer's verdict was a
fail (resolved at round 2): the passes coverage count paired passes_total and passes_accurate
and gated `passes_per_match` on it, though that rate reads only passes_total — a proxy in the
safe direction, invisible to the guard, the class the rule forbids. Round 2: one count per input
on both builders; `passes_per_match` on the passes_total count, `passes_accuracy_pct` on both;
the contract's `impact_map` count corrected and the round recorded. analytics-engineer-reviewer
and scope-auditor PASS; platform-reviewer's round-1 PASS stands, no script or test changed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 2: both builders carry `games_with_passes_total_stats` and `games_with_passes_accurate_stats`; `passes_per_match` gated on and divided by the first alone on both surfaces, matching its one catalogue input; `passes_accuracy_pct` gated on both, matching its two; the `_sum_season` columns each on their own count; no reference to the old name remains; the ymls describe both counts with `not_null`.
- Round 1 (a fail, resolved at round 2): the paired count over-gated `passes_per_match` on an input its formula does not read.
- The two tests follow `assert_metric_catalogue_expr_resolvable`'s pattern (`run_query` under execute, `depends_on`, identical tokenizer); the seed filter against the real catalogue excludes exactly the no-denominator team rows; `finishing_efficiency_pct` and `saves_pct` traced — `goals_penalty`/`goals_own` coalesced, `goals_for`/`goals_against` from the scoreline, so their predicates reduce to the SoT and saves inputs and cannot misfire.
- The player-feed predicate (`p.fixture_sk is null`) matches the entity rule and each rate's model gate; the awarded exclusion matches both builders' carve-out.
- The season monotonicity argument holds for every rate, including `goals_open_play_in_sot_games` (it diverges from a full sum only where the SoT gate already blanks the value); cumulative counts increase by at most one per game, so "first uncovered onward" is valid.
- The `{% else %}` branches match the execute branch's eight columns; the member floors sit well under the live counts.
- The cumulative model reads the new counts only inside `case when`, so `int_team_season__metrics`' shape and `assert_no_uncatalogued_season_metric` are untouched; `not_null` on every new count; the longest composed doc block (~800 chars) under the 1,024 limit; every reference to a team rate block is a pass-through of the once-computed column, so the NULL sentence is true at each; layering respected.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `_definition()`: the `entity == "team"` and denominator conditions AND'd; `_read_rows` validates the required fields before it runs; `denominator_expr` correctly optional; one function feeds `_blocks` and `_derived_blocks`, so the sentence has one home; `RATE_NULL_SENTENCE` carries no "window".
- The two pytests pin both halves of the condition with three rows and read the written file through `main()` (whitespace-collapsed), so the derived path is exercised; the claimed mutation is what the assertions catch.
- `validate:governance` runs `--check` unconditionally; the CRLF-tolerant compare is untouched.
- `data:build:mr` runs the full singular suite with `--defer` regardless of the build's slimming, so both guards run on every MR; `.data_paths_mr` covers `dbt_project/tests/**` and `models/**`; `sqlfluff lint models` is CI's only sqlfluff call, so the tests' jinja lint noise is outside CI as before.
- The member floor's `raise_compiler_error` sits under `{% if execute %}`, so parse is unaffected; `generate_schema_name` gives the audit dataset the target's prefix and the SA already creates per-MR datasets; the nightly's unselected `dbt build --target prod` runs the guards.
- All four models stay tables; no CI, hook, workflow or dependency file touched; no credential-shaped content.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: the delta is exactly the passes split across the two builders, the two consumers and the two ymls; the amendment names the defect and the fix and attributes the finding to the reviewer, not the CPO; `impact_map`'s corrected count matches the five new columns; nothing else moved.
- Every changed path in `scope_paths` (`int_team_season.yml` listed and untouched); `decisions_taken` presents the player-derived gate as the unobjected reservation of !201, not as a ruling; the two tests follow an existing pattern and `store_failures` implements §3.4; the member floor disclosed.
- `impact_map` evidenced: measured prod counts, lineage by grep, the leaderboard and benchmark consequences named; a coverage-tightening fix, not a cut.
- `decisions_reserved` untouched by the diff (no severity or `store_failures` change beyond the two tests); the docs replace the two wrong sentences and add nothing new.
- No dates, MR numbers, reviewer names or round numbers in the SQL, tests or generator; no credential-shaped content in the patch.

## escalations
(none)
