# Review — feat/480-per-club-player-season-foundation — 2026-07-02

> G3 Lock artifact. #480 §8.3 (Phase C, brick 1): introduce the canonical per-club player-season atoms base
> `int_player_club_season__metrics` (grain player×club×competition-season); re-express `int_player_season__metrics`
> as a byte-identical composition of it (mart_player_profile + mart_leaderboards unchanged); rebuild
> `mart_player_career` to the per-club × competition-season career log; retire the redundant
> `int_player_career__metrics`. Model/data change — went through plan mode, CPO-approved.
> Required set (routing `.claude/review_routing.json`): scope-auditor (always) + analytics-engineer
> (`dbt_project/**`). No metric_catalogue.csv change → football-analytics not required. No export/hooks/CI →
> cto not required. No wireframe/i18n → bi-analyst not required.
>
> Cycle history (re-run fresh on every hash change):
> - Round 1 (hash 47e5ffb3): scope-auditor FAIL + analytics-engineer FAIL — team_sk tie non-determinism +
>   the byte-stability claim wanted independent evidence; the impact_map was prose not the TEMPLATE labeled
>   form; review_input.patch was stale (prior #627 diff). Fixes: deterministic team_sk secondary sort +
>   team_sk not_null/relationships test; impact_map rewritten to the labeled format with grep lineage;
>   review_input.patch regenerated.
> - Round 2 (hash be04b16e): scope-auditor PASS + analytics-engineer PASS (AE independently reconstructed the
>   OLD compiled model and confirmed byte-stability atom-by-atom). AE raised two non-blocking quality nits: a
>   tautological mart test + a dropped dim_player_team_season_mapping-distinction doc.
> - Round 3 (hash 78e22435): analytics-engineer PASS; scope-auditor FAIL — the contract's supporting_edits
>   still described the old (tautological) test after it was replaced. Fix: synced the contract line + added
>   amendment #3. (Quality nits fixed: tautology → `appearances >= 1`; doc distinction restored.)
> - Round 4 (hash 0a165aff, THIS lock): scope-auditor PASS + analytics-engineer PASS. Only contract text
>   changed since round 3; AE re-confirmed the code is byte-identical to its round-3 PASS.

diff_sha256: 0a165affd96f092cb689be62068cb905814d49c98800a805c3b16584f50159ae

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + decision-rights: all 11 changed paths are within scope_paths (`dbt_project/**` models/tests/docs +
  `.claude/task/**`); no §10 decision made silently — the consolidation strategy, per-club grain, layer
  placement, and the int_player_career__metrics retirement are the CPO-approved plan; Career screen spec,
  export wiring, backfill, and precomputed subtotals are correctly held in decisions_reserved. All 3
  amendments record their reviewer authority and add no scope_path. Held.
- team_sk determinism (int_player_season__metrics.sql:35): the secondary tiebreak (`last_kickoff_at desc,
  team_sk desc`) is deterministic; team_sk is unused by both live consumers (mart_player_profile sources
  team from int_player_season__team; mart_leaderboards omits it), and the metric atoms are summed before the
  team_sk pick, so output is byte-identical regardless. Load-bearing boundary, correctly handled.
- Appearance-gate test (shared.yml:1284, `appearances >= 1`): load-bearing — guards against a future
  regression that admitted zero-appearance roster rows; the base is INNER-JOIN gated on finished matches and
  the mart adds only dimension left-joins, and the mapping distinction is now documented in the mart header.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Byte-stability of int_player_season__metrics: independently reconstructed the OLD compiled baseline
  (target/compiled/.../int_player_season__metrics.sql) and diffed it token-for-token against the current
  final SELECT — identical for every atom, ratio, per-90, composite, the per-fixture ROUND-weighted
  passes_accurate, and the finishing_efficiency CASE. The only logic change is the source CTE (per_fixture →
  the re-summed base): a sound SUM(SUM(x))=SUM(x) re-association for additive atoms; passes_accurate rounds
  per-fixture in the base before re-summing, so it is invariant to the grouping level.
- team_sk non-consumption: confirmed mart_player_profile sources team_sk from an independent
  int_player_season__team CTE and mart_leaderboards has zero team_sk references — the tiebreak touches a
  column dead to both consumers, so byte-stability is not undercut by a hidden dependency.
- Grain, tests, drift guard, layer, governance: unique_combination (player_sk, team_sk, season_sk) on both
  the base and the mart; `appearances >= 1` confirmed load-bearing (not tautological); the drift guard
  extends cleanly (every non-exempt base atom is a pre-existing catalogued player row; last_kickoff_at
  correctly exempted); no ref('mart_*') in either intermediate file; zero dangling refs to the deleted
  int_player_career__metrics; no hardcoded league; no export/*.py touched.
- Noted (non-blocking, pre-existing, NOT introduced here): mart_player_career carries several SELECT columns
  without individual column descriptions in shared.yml (engineering_standards §2) — predates this diff
  (round-2 approved the same set); open tech debt for a follow-up, does not overturn PASS.

## escalations
(none) — all reviewer findings were addressed in-cycle (team_sk determinism + test; impact_map format;
contract accuracy; tautology + doc). No §10 question surfaced; the CPO-class items are reserved to separate
PRs (Career screen spec, export wiring, backfill).
