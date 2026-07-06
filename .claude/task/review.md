# Review — feat/484-player-tournament-window — 2026-07-06

> G3 Lock artifact. #484: re-point the player momentum builder (int_player_momentum__metrics) at the shared
> window model int_team_momentum_window, so the fixture-page top-players strip and the team form panel use ONE
> form window — cumulative (tournament_to_date / qualifiers) on tournament fixtures, last_5 elsewhere. Widens
> window_type accepted_values on the builder + mart, corrects the stale games_in_window "max 5" wording, adds the
> assert_player_momentum_window_matches_team parity test, and fixes the now-stale #484 doc-comment in the window
> model. No export change (window_type is already dropped from the strip payload); team path untouched.
> Required set (routing): scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**).

diff_sha256: 2b22c8a21adda902918157a9f995335868afd85451b95bd6550b6b1566f5d5fa

## scope-auditor
VERDICT: PASS
risks_checked:
- **Window-selection equivalence for zero-finished-match states.** The retired inline `ranked_team_legs` inner-
  joined upcoming sides to `int_legs__team_match`, returning no rows when a team has no finished matches before
  the fixture. The shared `int_team_momentum_window` returns no rows in the same state (documented, and its
  last5_legs CTE inner-joins the same source), so the contract's "non-tournament byte-identical" claim holds
  across this margin case — a missing player row is honest absence in both paths. Not a defect.
- **Tournament window_type cardinality per side.** The shared model guarantees exactly one window_type per
  (upcoming_fixture_sk, team_sk): `sides_with_tournament_legs` excludes qualifier_legs via NOT EXISTS
  (tournament_to_date OR qualifiers, never both), and last5 is the non-tournament branch. So carrying window_type
  through the player builder's GROUP BY cannot split a player's row; the (upcoming_fixture_sk, team_sk, player_sk)
  grain and its unique test still hold. Scope (7 files ⊆ scope_paths), §10 (no self-made decision — the "same
  window" ruling is the CPO's; display label reserved), and Appendix A all clean.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- **Join-key correctness after re-pointing.** `wl.leg_fixture_sk = p.fixture_sk AND wl.team_sk = p.team_sk` is
  structurally identical to the retired inline join; cross-checked int_legs__player_match (grain fixture_sk,
  player_sk; carries own team_sk) + int_legs__team_match (grain fixture_sk, team_sk) share the same finished-match
  filter — the leg set feeding player aggregation is exactly what int_team_momentum_window selected.
- **Non-tournament equivalence.** The retired inline last-5 predicate equals the shared model's last5_legs/
  last5_window (same team/entity/kickoff-before + club-vs-national season boundary + recency_rank<=5, plus a
  `not is_tournament` that is always false for non-tournament fixtures) — logically identical; byte-identical claim confirmed.
- **Grain preservation under widened GROUP BY.** int_team_momentum_window enforces unique (upcoming_fixture_sk,
  team_sk, leg_fixture_sk) and functionally determines one window_type/season_api_year/entity_type per side, so
  adding window_type to the group-by cannot split a player row; the player grain test still holds.
- **Layer contract.** intermediate→intermediate ref is legal (check_layer_contract only forbids intermediate→mart_*);
  no mart ref, no per-competition staging, no hardcoded league_code/competition literal in the rewritten builder.
- **Materialization / full-refresh trap.** Both models are materialized='table' full-rebuild (no incremental,
  no on_schema_change) — no column-rename NULL-out trap; the "no --full-refresh needed" claim holds.
- **Test coverage.** Widened accepted_values (last_5, tournament_to_date, qualifiers) present on both builder +
  mart; mart_team_momentum exposes window_type (line 37), so the new parity test is well-formed (proper FROM
  clauses, inner join on the side, inequality on window_type) and would catch a re-introduced inline last_5 drift.

## escalations
- None open. No ESCALATE verdict raised. The product decision ("player strip uses the same window as team form")
  is the CPO's explicit ruling this session; the approach, accepted_values widening, doc corrections, and parity
  test are mechanical / engineering-judgment consequences. Display-label + the §8.4 NT-context window are reserved
  (contract decisions_reserved), not touched here.
