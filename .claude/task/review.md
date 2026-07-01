# Review — feat/391-gap20-squad-export — 2026-07-01

> G3 Lock artifact. #391 GAP-20: wire mart_roster into the v2 team export — a per-season squad[] block
> on the team payload (identity-only, mirroring the GAP-15 fixtures pattern). Export-only (no dbt/model
> change). Required set (routing): scope-auditor (always) + analytics-engineer + cto
> (scripts/export_*.py + tests/**).
>
> Round 1 (hash 0a781b5) — analytics-engineer PASS, cto PASS, scope-auditor FAIL: the contract's
> decisions_taken wrongly claimed the squad member carries a "slug" (the code has none, per the CPO
> plan-mode ruling), and decisions_reserved still listed the slug choice as open — a self-contradictory
> contract. CODE was correct; only the contract was wrong.
> Round 2 (hash 86a4bc1, THIS lock) — contract-only fix: decisions_taken → "id+name only, NO slug";
> decisions_reserved → the three plan-mode choices recorded as "(ruled)" (no-slug; player_sk order;
> doc-status a separate PR). CODE byte-identical. All three reviewers PASS.

diff_sha256: 86a4bc1ad0ca54fbc3a96264585f21b69f19def723e4d1f6a4ce0bf44f72a501

## scope-auditor
VERDICT: PASS
risks_checked:
- Upstream DQ gate for unresolved-player filtering — the export filters `player_name is not None`,
  trusting mart_roster's player_sk→dim_player relationships DQ test to guard corrupt/unresolved rows.
  The contract documents the upstream guard; dbt CI runs it; the unit test confirms the filter. Structural
  assumption sound (consumption never re-validates the mart). Held.
- Season-key consistency between mart_team_profile and mart_roster — the attach joins on (league_code,
  season_api_year); a lineage/ingestion key mismatch would silently decouple the squad (honest absence via
  `.get(..., [])`). The code's grouping tuple matches mart_roster's stated grain exactly; the shared
  upstream fact-grain guarantees key synchrony. Round-1 slug contradiction FIXED; scope is exactly
  scripts/export_site_data.py + tests/** + .claude/task/** (no docs/wireframes or content_architecture).
  Held.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Consumption-layer purity — `_shape_squad_member` is a pure field select/rename; the null-name filter is
  selection (backed by the DQ test), the player_sk sort is a byte-stable tie-break (not a computed rank),
  player_position is a raw passthrough (no GK/DEF/MID/ATT mapping), and no slug is generated. Satisfies the
  layer contract. Held.
- Grain/attachment — roster_by_season keys on (league_code, season_api_year), the same tuple as the proven
  GAP-15 fixtures pattern; mart_team_profile.seasons[] drives the loop so a roster row for an absent season
  is dropped (no orphan season); club-scope congruence between the two marts holds; payload change is
  additive-only. Code byte-identical to round-1 PASS. Held.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Python correctness — the 3rd param defaults None (backward-compatible; proven by the defaults-empty
  test); player_sk is non-null by mart grain so `int()`/sort are safe (matches the existing unguarded
  `int(row["team_sk"])` GAP-15 precedent); empty/None roster fully guarded (`roster_rows or []`). Held.
- Query construction + test quality — the mart_roster sample-scoping mirrors the accepted GAP-15 fixtures
  query (int-cast internal team_ids, no new injection surface; idempotent re-run); both new tests assert
  real behavior (out-of-order input forces the sort, an explicit null-name row forces the omission, a
  zero-roster season forces the empty default, set-based key check catches leakage). Code byte-identical to
  round-1 PASS. Held.

## escalations
(none) — export-only wiring implementing the three CPO plan-mode rulings (no-slug; player_sk order;
doc-status kept to a separate follow-up PR). The GAP-20 "shipped" status + content_architecture §3 roster
✓-flip are RESERVED to that separate doc-sync PR (CPO); no §10 decision taken here.
