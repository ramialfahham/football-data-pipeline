# Review — refactor/500-entity-rename-sweep — #500 entity-first model rename sweep

> G3 Lock artifact. Five reviewers spawned cold (blinded) on the staged diff
> (`.claude/task/review_input.patch`). Required set for the staged paths: scope-auditor (always) +
> analytics-engineer-reviewer (`dbt_project/**`) + cto-reviewer (`scripts/export_*.py`) +
> bi-analyst-reviewer (`docs/wireframes/**`) + data-engineer-reviewer (`docs/competition_registry.yml`).
> scope-auditor + analytics-engineer re-reviewed the final diff (after the CPO-ruled layering row was
> added); cto / bi-analyst / data-engineer reviewed the prior diff — their owned surfaces
> (export / wireframes / registry) are byte-identical in the final diff, so their PASS stands.

diff_sha256: dcc79163c53e79a09a1463af1f5e49e50d61912a852df74dcf4da387dc433675

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file is within scope_paths — including the recorded amendment for
  `mart_player_match_log.sql` and the CPO-ruled `layering.md` player-benchmark row (both in scope).
  No out-of-scope drift; the `int_legs__*` family is left untouched per decisions_reserved.
- Pure rename / §10: only file renames + `ref()` retargeting + `name:`/description/comment edits +
  the one CPO-ruled descriptive doc row; no SQL logic/formula/grain change. The entity-first
  convention is CPO-locked (execution, not a new decision). The LIVE MVP mart `mart_matchday_insights`
  is downstream TRANSITIVELY (not a direct ref to a renamed model) → byte-identical; all 8 renamed
  models are non-incremental (no --full-refresh).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The added `mart_player_competition_benchmarks` row in `layering.md` is ACCURATE: grain
  `(player_sk, season_sk, position_group, metric_key)`, view, composes `int_player_competition_benchmarks`
  — cross-checked against the model SQL + its `shared.yml` unique-combination test. The team-benchmark
  row was renamed correctly alongside it.
- Pure rename + no leakage: the exact done_when pattern `(int|mart)_(momentum_window|fixture_stats|
  competition_benchmarks)__(team|player)` returns ZERO in `dbt_project/`, `scripts/`, `docs/`. The two
  `mart_fixture_stats__{team,player}` / `__*` hits in `content_architecture.md:71` + `99_gaps_register.md:18`
  are brace/wildcard NOTATION (not the literal suffix) → do not match the criterion. fixture_stats marts
  show 100% similarity (literal renames); refs resolve (`dbt parse` clean); no intermediate refs a mart.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Consumption-layer contract: the four changed lines in `scripts/export_site_data.py` are pure table-name
  string substitutions inside f-string query literals (`mart_momentum_window__team`→`mart_team_momentum_window`,
  fixture_stats team/player → entity-first). The `where`/`select`/`group` shapes, the key-drop sets, and the
  slug/identity logic are byte-for-byte unchanged — no computation/ranking/derivation introduced.
- Old-name residue: zero matches for the old mart names in the export; all four call sites use the exact
  new mart names; rename + export update are atomic, keeping the paused v2 export consistent with the graph.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The ONLY change to `docs/wireframes/99_gaps_register.md` is `int_momentum_window__team` →
  `int_team_momentum_window` in GAP-18 (two occurrences); no GAP ruling, disposition, scope, status, or
  display-contract item was altered, and no other GAP row was touched.
- The `int_legs__team_match` reference in GAP-15 is correctly LEFT unchanged (the excluded family).

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- The ONLY change to `docs/competition_registry.yml` is a YAML comment (`int_momentum_window__team` →
  `int_team_momentum_window`). No registry DATA field — league_code, provider_league_id, history_seasons,
  ingest_active, parent_competition — was added, removed, or altered.
- Registry↔seed sync intact: a comment is invisible to the YAML parser, so `active_competition_league_codes`
  / `check_registry_var_sync` are unaffected; the zero-file + single-source rules hold.

## escalations
- question: analytics-engineer FAILed (first round) because `dbt_project/docs/layering.md`'s "exhaustive"
  mart inventory listed the renamed team benchmark but OMITTED a row for the (pre-existing)
  `mart_player_competition_benchmarks` — a doc gap that predates this PR (the mart was never inventoried,
  even under its old name), not rename debt. Add the missing row now (complete the surface), or defer it
  as a separate doc-completeness fix?
  CPO ANSWER: Add the missing row now (CPO ruling, 2026-06-26). Done — a `mart_player_competition_benchmarks`
  row was added to the inventory (mirroring the team-benchmark row, derived from the existing model);
  analytics-engineer re-reviewed the final diff → PASS.
