# Task contract — #484: player momentum uses the same form window as team

> Written on a CLEAN tree (branch feat/484-player-tournament-window off main @ 28d751f).
> Plan approved via ExitPlanMode this session. See docs/working_agreement.md §2/§10/§11, Appendix A.

objective: >
  Fix the #484 parity gap: on a tournament fixture (world_championship / continental_championship) the
  fixture-page top-players strip still uses a last-5 window while the team form panel uses the GAP-18
  cumulative tournament window. Re-point the player momentum builder at the shared window model
  `int_team_momentum_window` (the same de-dup #323 did for the team aggregate) so both surfaces consume
  ONE window selection. CPO decision this session: the player strip must use the SAME window as team form.
refs: #484 (deferred from GAP-18); #323 (window extraction); docs/wireframes/01_fixture_page.md §5; docs/metrics_context_model.md §4.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/tests/assert_player_momentum_window_matches_team.sql
  - .claude/task/**

impact_map: >
  writers: `int_player_momentum__metrics` (materialized='table', full rebuild each run) — the only model
    whose logic changes. `int_team_momentum_window` gains ONE new consumer (the player builder now ref()s it);
    its own SQL is unchanged except a stale doc-comment.
  downstream (traced by grep — dbt CLI is broken locally, so lineage is from ref() inspection, not `dbt ls`):
    `int_player_momentum__metrics` → `mart_player_momentum` (sole model consumer) → `scripts/export_site_data.py`
    (reads `mart_player_momentum`, shape_top_players → the top-players strip). No other model ref()s either.
    `int_team_momentum_window` existing consumers (`int_team_momentum__metrics`, `mart_team_momentum_window`)
    are UNTOUCHED — team path unchanged.
  layer_rules: intermediate→intermediate ref (int_player_momentum__metrics → int_team_momentum_window, both
    4_intermediate/shared) is allowed; no per-competition staging; check_layer_contract stays green. league_code
    still flows via the leg rows (not hardcoded).
  deploy_order: NON-breaking. The player builder is a full-rebuild table (no incremental column-rename trap —
    columns are unchanged; only row VALUES shift on tournament sides + window_type gains 2 possible values).
    Rebuilds cleanly on the next `dbt build`; no --full-refresh needed. Picked up by ci-data-build and the 04:00
    nightly with no manual step.
  blast_radius: `mart_player_momentum` VALUES change ONLY for tournament-fixture sides (window last_5 → cumulative
    tournament_to_date/qualifiers). Non-tournament sides are byte-identical (the shared model's last_5 branch is
    the same join + season boundary + recency_rank<=5 as the retired inline CTEs). No number moves on any team
    mart, no export shape change (window_type is already in _TOPPLAYER_DROP so the payload shape is unchanged).

decisions_taken: >
  Rests on the CPO's explicit ruling this session ("team form and the player strip use different windows ->
  should be the same window"). Approach (consume the shared model vs mirror the branch) is engineering judgment —
  the shared window model already exists and is guarded; consuming it is the DRY, single-source choice #323
  established. The new parity test (assert_player_momentum_window_matches_team) is my quality tool per the issue's
  "add tests". Widening window_type accepted_values + correcting the stale games_in_window description are
  mechanical consequences of the change.

decisions_reserved:
  - A display LABEL for the player strip window ("in this tournament" vs "last 5") — §10 display/wireframe; NOT
    in scope (export drops window_type from the strip payload today). Separate follow-up only if the CPO wants it.
  - The broader national-team-as-context window (metrics_context_model.md §8.4) that the docs also hang on #484 —
    a different, design-heavy surface; explicitly NOT this parity fix.

done_when:
  - int_player_momentum__metrics reads int_team_momentum_window; the inline window CTEs are gone; window_type is
    carried through (no more hardcoded 'last_5').
  - window_type accepted_values widened to [last_5, tournament_to_date, qualifiers] in both int_momentum.yml
    (builder) and shared.yml (mart); games_in_window "max 5" wording corrected.
  - assert_player_momentum_window_matches_team.sql added (player vs team window_type must agree per shared side).
  - `python scripts/check_layer_contract.py` passes.
  - ci-data-build green: model builds, widened accepted_values pass, the new parity test passes, existing
    assert_tournament_form_window + assert_momentum_window_matches_momentum still green.
  - scope-auditor + analytics-engineer-reviewer PASS (>=2 named risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
