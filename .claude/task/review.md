# Review — fix/ingest-squads-skip-cached — 2026-07-06

> Blinded G3 review of the squad `/players` fetch-side skip. Three required reviewers for the
> staged paths (scope-auditor always; data-engineer-reviewer for ingestion/** + data_contract.md;
> cto-reviewer for tests/**). All PASS, no escalations.

diff_sha256: 7cde48951c93d9ff9696c0df364742e7f35b1a6c580fc0ae25af5e96a2d30026

## scope-auditor
VERDICT: PASS
risks_checked:
- All six changed paths fall within the contract `scope_paths`; no scope creep, no drive-by edits, transfers.py correctly untouched (deferred per decisions_reserved).
- No silent §10 decisions — skip-cached-historical, always-refetch-reference-season, the `to_fetch/skipped_cached` log format, fail-open on read error, and doc+skill-over-CI-guard are each pre-approved in the cited plan or listed in decisions_reserved.
- impact_map is honest: verified the row shape, the write path (`load_json_payload_rows_to_bq`), and the merge/delete (`_delete_superseded_player_rows`) are all unchanged and no dbt model is touched — only WHICH (team, season) keys are fetched changes.
- `reference_season` inferred via `max(result.seasons_list)` is identical to `catalog.py:60`; a wrong value would surface as stale live-season stats caught downstream, not a silent corruption.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- JSON path in `captured_player_team_seasons` (squads.py) traced against the proven `player_universe._query_universe` unnest and the writer's actual row shape (`payload.response[].team_id/.season`) — matches, no wrong-path bug.
- `plan_player_team_season_fetch`'s `season >= reference_season` guard checked for off-by-one against `reference_season = max(seasons_list)` — the reference season is always the re-fetch branch, every earlier season only when not already held; confirmed by the "reference re-fetched despite being held" unit test.
- Poll-mode/finished competitions never reach `run_squads_for_competition` (orchestrator calls it only on `run_cheap_phases` full-mode results), so the truncated `seasons_list=[reference_season]` in the poll path cannot interact with the planner unexpectedly.
- Merge-on-write delete (`_delete_superseded_player_rows`) and quota-cut PARTIAL bookkeeping (`written_keys`, `quota_cut` break) are byte-identical pre/post the nested→flattened loop refactor; no WRITE_TRUNCATE introduced anywhere in the diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New planner/reader tests are non-tautological with discriminating assertions (reference-always-fetched, historical-gap-self-heals, first-run-full-product, fail-open-on-error, fully-qualified-SQL) — a buggy planner would fail them.
- The three adapted existing loader tests stub `captured_player_team_seasons` to `set()` honestly: each uses a single-season `[2016]` list, so 2016 is the reference season and is fetched regardless of the stub — the stub is not load-bearing to hide a regression, and `ctx.errors == []` remains a real assertion.
- `load_squad_players_batch` gained an optional `reference_season` kwarg with a safe default; grep-confirmed `competition_runner.py` is the sole call site and passes `max(result.seasons_list)`; no other caller left on the old signature.
- Doc/skill references (`captured_player_team_seasons`, `players_needing`, the `to_fetch=/skipped_cached=` log format) all cross-checked against real source — not invented.

## escalations
(none)
