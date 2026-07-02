# Review — feat/391-gap21-benchmarks-export — 2026-07-02

> G3 Lock artifact. #391 GAP-21: wire mart_player_competition_benchmarks into the v2 player export so the
> Stats-percentile screen (12, spec'd #625) has a payload. Mart + intermediate + export: the mart gains
> metric_numerator/metric_denominator (the volume behind each ratio %, for the {num} of {den} · {pct}% triple),
> populated via the shared player_benchmark_metrics() macro; int_player_season_position__metrics exposes the
> goals_penalty atom (for the finishing numerator); shape_player_payload attaches a per-season benchmarks[]
> block (position_group → metrics[]); fetch_player_payloads queries the mart (scoped on sample runs). Plan +
> 3 build choices CPO-approved via ExitPlanMode; one CI-driven scope amendment (see amendments in contract.md).
> Required set (routing): scope-auditor + analytics-engineer (dbt_project/** + export) + cto (export + tests).
>
> History (ONE commit; collapsed):
> - R1 (28ac234d) all 3 PASS → ci-data-build FAILED SQLFluff LT02 on the mart num/den {% if %} block.
> - R2 (79956960, ebbcfd4 base) LT02 FIXED (uniform CASEs matching metric_value, inline then); all 3 PASS.
> - R3 (2a8c84da, #626 base) REBASED after sibling #626 merged first (only .claude/task/* diverged; code
>   byte-identical) → ci-data-build FAILED to BUILD the mart: "Unrecognized name: goals_penalty" (the finishing
>   numerator goals - goals_penalty referenced an atom int_player_season_position__metrics summed internally
>   but never output).
> - R4 (5b12c48f, THIS lock) exposed goals_penalty on int_player_season_position__metrics (one line; already
>   summed) + a CI-driven contract scope amendment; all 3 PASS. Offline: layer-check green; 25 pytest pass.

diff_sha256: 5b12c48f45c187d83ca683e7d6d6b43f1333d96a82f8483cda573a35e2da21de

## scope-auditor
VERDICT: PASS
risks_checked:
- Amendment legitimacy + §10: the scope extension (adding int_player_season_position__metrics.sql) is a
  discrete, documented, CI-driven data-availability fix (gate-enforced on a clean tree), NOT scope creep;
  exposing goals_penalty is not a metric redefinition (the num expr goals - goals_penalty is unchanged and
  matches the merged wireframe §5; the atom was already summed) and metric_catalogue.csv is not in the diff.
  All staged changes inside the amended scope_paths; no PROTECTED path. Held.
- Table rebuild + null-gate: int_player_season_position__metrics is a non-incremental table → full rebuild,
  no historical NULL-out; the DQ test binds num/den non-null iff a ratio metric; the mart/macro/export are
  unchanged from the prior PASS. Held.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Root-cause correctness + range safety: goals_penalty is already summed in the aggregated CTE (line 98) —
  the diff only adds it to the output SELECT (line 130), so the mart's finishing num (goals - goals_penalty)
  now resolves against the season CTE. The exposed numerator is structurally in [0, shots_on_goal] on every
  surviving row: metric_value for finishing is the identically null-guarded expr (lines 156-160) and the mart
  keeps only metric_value-not-null rows (line 104). Held.
- Engine isolation + drift-guard scope: int_player_competition_benchmarks does select * then unpivots m.col
  only (never m.num/m.den) → the extra column is inert; grain (unique-combo) untouched (SELECT-list-only).
  Read assert_metric_catalogue_expr_resolvable.sql — its base_relations (int_legs__team_match/…team_from_players
  /…player_match) EXCLUDE this model; no test enumerates its column set → goals_penalty is a raw atom addition
  (like duels_total/saves already output), not a catalogue-governed metric. Held.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Fix minimality + no second latent bug: int_player_season_position__metrics.sql:130 now outputs
  goals_penalty (the exact identifier the macro/mart require); verified the OTHER 4 ratios' num/den atoms
  (saves, goals_against, passes_accurate, passes_total, duels_won, duels_total, dribbles_success,
  dribbles_attempts) were ALREADY in the output SELECT — no second "unrecognized name" of the same class. Held.
- Cross-domain isolation + no regression: the export + test hunks are byte-identical to the prior PASS with
  zero goals_penalty/dbt references; SQLFluff/dbt (.sql/.yml) and pytest (.py) are independent CI domains, so
  the dbt-only fix cannot regress python-ci; model is a non-incremental table (no NULL-out); no cost/frequency
  change; no PROTECTED path in the diff; file set matches scope_paths. Held.

## escalations
(none) — implements the CPO-approved plan for the merged GAP-21 spec; num/den are display atoms on the
benchmark mart (no catalogue change), goals_penalty is a raw-atom exposure (data-availability, amendment
documented), the export select/reshapes only. No frontend (Phase E); Career / Phase C (#480) / Phase D
remain reserved backlog.
