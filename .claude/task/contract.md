# Task contract — feat: player-endpoint ingestion CODE (profiles + teams + squads) — PR-a1

> Player-data initiative, PR-a (the plan's "PR-ii — player endpoints ingest"), sliced
> finer per the CPO this session into PR-a (ingest) → PR-b (dim_player bio + appearance
> fact) → PR-c (affiliation timeline). PR-a is itself split (CPO this session) into
> **PR-a1 = ingestion CODE only** (this task) and PR-a2 = staging models, because the new
> staging models would reference raw tables that do not exist until the loaders run — so
> code lands first, a backfill creates + populates the raw tables (cost checkpoint then),
> rows are INSPECTED, and only then do the staging models build green (honors this session's
> transfers lesson: a green build on missing/empty source masks a fetch bug).
> Touches NO protected paths and NO dbt models. Reviewers: scope-auditor + data-engineer.
> See docs/working_agreement.md §2/§5/§10; .claude/task/escalations.log 2026-06-15 (this branch);
> the approved plan C:\Users\Rami\.claude\plans\player_data_ingestion_plan.md (§2/§4/§5/§8).

objective: >
  Build the ingestion CODE for three new API-Football player endpoints and wire them into the
  orchestrator — NO dbt models, NO backfill execution in this PR:
  (1) `/players/squads` per team (current squad + shirt number), per-competition like transfers,
      landing into a new unified raw table `RAW_APIF_SQUADS`.
  (2) `/players/profiles` per player (rich bio) and (3) `/players/teams` per player (career
      team×seasons), run as a GLOBAL per-player phase over the current universe (players rostered
      in season >= 2025, ~31.9k), gathered from `RAW_APIF_PLAYERS`, deterministic provenance
      `league_code` = MIN(league_code) per player, SKIP-IF-ALREADY-INGESTED so the daily run stays
      cheap (bio/career are static/slow), landing into `RAW_APIF_PLAYER_PROFILES` /
      `RAW_APIF_PLAYER_TEAMS`. All three respect the ingest lock, the daily quota guard, and a
      per-endpoint skip env var.
  (4) Document the three new raw tables (Unified raw tables + Endpoints + Pagination + Plan-vs-product)
      in docs/data_contract.md.

refs: >
  CPO cost-approval gate + scope/universe/axis rulings this session (AskUserQuestion, 2026-06-15):
  scope = profiles + teams + squads (DROP /players/seasons); universe = current players season>=2025
  (~31.9k); bio axis = per-player. Structural split (code-first → staging) = CPO this session.
  All recorded in .claude/task/escalations.log 2026-06-15 (this branch). Builds on the approved
  initiative plan (§2 endpoints, §4 raw table names, §5 cost, §8 PR breakdown).

scope_paths:
  - ingestion/api_football/fixture_scheduling.py
  - ingestion/api_football/loads/player_squads.py
  - ingestion/api_football/loads/player_profiles.py
  - ingestion/api_football/loads/player_teams.py
  - ingestion/api_football/loads/player_universe.py
  - ingestion/api_football/loads/competition_runner.py
  - ingestion/api_football/orchestrator.py
  - docs/data_contract.md
  - .claude/task/contract.md

decisions_taken: >
  Raw table names (`RAW_APIF_SQUADS`, `RAW_APIF_PLAYER_PROFILES`, `RAW_APIF_PLAYER_TEAMS`) are
  settled by the approved plan §4 and follow the RAW_APIF_{entity} convention; landing schema is
  the standard `league_code STRING, payload JSON, ingested_at TIMESTAMP` via `load_json_to_bq(...,
  as_json_payload=True, append=True, league_code=...)` (mirrors squads/transfers). HTTP helpers use
  `fetch_merged_paged(..., paginate=False)` — all three reject `page=` / return one page for the
  keyed forms (verified live 2026-06-15: squads team=157 total=1, profiles player=5 total=1, teams
  player=5 total=1). The existing `loads/squads.py` (which fetches `/players` → `RAW_APIF_PLAYERS`)
  is UNCHANGED; the new `/players/squads` loader is a distinct module `loads/player_squads.py`.
  Per-player profiles+teams run as ONE global phase (not per-competition) because the axis is
  per-player, not per-team; the universe is read from raw `RAW_APIF_PLAYERS` (raw→raw, no dbt
  dependency). Provenance `league_code` = deterministic MIN per player (mirrors the transfers
  ingest-provenance rule — league_code is provenance, not identity). SKIP-IF-ALREADY-INGESTED
  (anti-join against the target table; full universe when the target does not yet exist) implements
  the approved ongoing-cost model (~1.4–3.7k/day) — a static-bio refresh policy beyond first-seen is
  NOT introduced here.

decisions_reserved: >
  - Anything beyond raw landing (staging/base/core/marts, any derive/transform/dedup) is PR-a2+ —
    not in this PR.
  - If a reviewer finds the global per-player phase needs a CPO product/cadence ruling beyond the
    skip-if-present default (e.g. a periodic forced bio/career refresh policy), STOP and surface
    blinded — do not self-rule.
  - Loader/module naming follows the approved plan + convention; a genuine naming ambiguity a
    reviewer raises is a CPO call, not a builder default.
  - The backfill DISPATCH that will populate these tables is a separate cost checkpoint AFTER this
    PR merges — not taken here.

done_when:
  - Three loaders (`player_squads.py`, `player_profiles.py`, `player_teams.py`) + a universe
    gatherer (`player_universe.py`) + three `*_response_for_*` helpers in `fixture_scheduling.py`;
    each guarded by the quota flag + a per-endpoint `API_FOOTBALL_SKIP_*` env var.
  - `orchestrator.py` wires `/players/squads` per competition (after the existing squads/transfers
    phases) and a global profiles+teams phase; `competition_runner.py` adds the per-comp squads
    wrapper (mirrors `run_transfers_for_competition`).
  - NO files under `dbt_project/**` are touched (PR-a2); CI `ci-data-build` stays green because no
    new dbt source is referenced.
  - `docs/data_contract.md` lists the three new raw tables in: Unified raw tables, Endpoints and
    raw tables, the Pagination note, and Plan-vs-product.
  - `python -m py_compile` on every touched/added module passes; validate-local clean.
  - reviewers: scope-auditor (always) + data-engineer-reviewer (ingestion/** + data_contract.md)
    both PASS (≥2 named risks each); no FAIL; any ESCALATE has a recorded CPO ANSWER.

amendments: []
