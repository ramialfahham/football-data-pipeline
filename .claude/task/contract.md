# Task contract — GAP-20: wire mart_roster into the team export (squad[] block)

> Written on a CLEAN tree (branch feat/391-gap20-squad-export off main @ e454c9f).
> CODE change (scripts/export_site_data.py + tests). Turns the built-but-orphan mart_roster into
> a WIRED block on the v2 team payload — the "cheap green" that follows the #617 Squad wireframe spec.
> See docs/working_agreement.md §2 (contract), §10 (decision rights). Plan mode + ExitPlanMode required.

objective: >
  #391 track A green: carry mart_roster (#503) into scripts/export_site_data.py so the Squad screen
  (docs/wireframes/11_team_squad.md, spec'd #617, GAP-20) has a payload. Attach a per-season squad[]
  block to the team payload, mirroring the GAP-15 fixtures pattern (fetch_team_payloads +
  shape_team_payload attach per (league_code, season_api_year)). The export SELECTS/RESHAPES only —
  no derivation (consumption-layer contract). Two reviewer advisories from the #617 spec baked in:
  (a) OMIT null-identity members (a roster membership whose dim_player LEFT-join is unresolved →
  player_name null; the mart's player_sk→dim_player relationships DQ test guards it); (b) the
  GK/DEF/MID/ATT position grouping is a DISPLAY concern left to the frontend — the export carries the
  raw player_position, it does NOT group.

refs: >
  Template = GAP-15 (#607): fetch_team_payloads (export_site_data.py:420-434) queries mart_team_fixtures,
  groups by team_sk, passes to shape_team_payload (:146-188) which attaches next_fixture/recent_results
  per (league_code, season_api_year). Test template = test_shape_team_payload_attaches_fixtures_per_season_newest_first
  (tests/test_export_site_data.py:202-242). mart_roster grain = (team_sk, league_code, season_api_year,
  player_sk), club-only, identity fields: player_name, player_position, player_nationality,
  player_birth_date, player_photo_url. Member shape per wireframe 11 §5.

impact_map: >
  UPSTREAM: dbt marts.mart_roster (read-only; no model change — the mart already exists, #503).
  CHANGED SURFACE: scripts/export_site_data.py — shape_team_payload gains a 3rd param (roster_rows);
  new pure helper _shape_squad_member; fetch_team_payloads gains a mart_roster query + per-team group +
  sample scoping (mirrors the fixtures query). Team JSON payload gains seasons[].squad[] (a new key;
  additive — existing keys unchanged).
  DOWNSTREAM: the v2 team payload (artifacts/site_data/teams/*.json) — additive new key, consumed by the
  future frontend (Phase E) + the Squad screen. No live-MVP impact (separate export_pages_data.py).
  No manifest/slug-map change (squad members nest inside the existing team payload). No dbt/CI-data-build
  impact (no model touched). Verified by pytest tests/test_export_site_data.py (pure shaping unit tests).

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .claude/task/**

decisions_taken: >
  Export-only wiring. Attach a per-season squad[] on the team payload, keyed by (league_code,
  season_api_year), each member = {player_id, name, position, nationality, birth_date, photo}
  — **id + name only, NO slug** (CPO plan-mode ruling: the frontend slugifies from player_id + name;
  ALL slug derivation stays deferred to GAP-19). Null-name (unresolved-player) members are OMITTED.
  Position is carried raw (no GK/DEF/MID/ATT grouping — that is frontend display). squad[] emitted in a
  deterministic byte-stable order **by player_sk** (CPO plan-mode ruling — mart_roster has no rank
  column; the frontend does display grouping/ordering). The GAP-20 "shipped" status + the
  content_architecture.md §3 roster ✓-wired flip are a SEPARATE follow-up doc-sync PR (CPO plan-mode
  ruling), NOT in this PR. No dbt/model/metric/catalogue change; no live-MVP change.

decisions_reserved:  # §10 — the three plan-mode design choices were RULED by the CPO (ExitPlanMode); see decisions_taken
  - (ruled) squad member = id+name only, NO slug — the frontend slugifies; slug derivation stays GAP-19.
  - (ruled) squad[] ordering = by player_sk (byte-stable); player_name display order stays frontend.
  - (ruled) GAP-20 shipped-status + content_architecture §3 roster ✓-flip = a SEPARATE doc-sync PR, not
    folded here (this PR stays pure code + tests; docs/wireframes/** + content_architecture.md are NOT in
    scope). The broader fold-generalization question stays open (CPO call), untouched by this ruling.

done_when:
  - shape_team_payload attaches seasons[].squad[] (per-season, null-name omitted, display-only fields,
    byte-stable order); fetch_team_payloads reads mart_roster + scopes to sampled teams; a unit test
    mirrors the fixtures test (per-season attach, null-name omission, internal-key stripping, empty state).
  - pytest tests/test_export_site_data.py green; python scripts/check_layer_contract.py green.
  - scope-auditor + analytics-engineer + cto PASS (>=2 risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
