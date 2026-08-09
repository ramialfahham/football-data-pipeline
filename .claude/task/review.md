# Review — perf/33-raw-merge-on-write — 2026-08-09

diff_sha256: c3df806a4a5fa288c7e30e0bf1d22a925d1a3bf67d95f3de73769c64bce308dc

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file (`ingestion/api_football/bigquery.py`, `loads/standings.py`, `loads/teams.py`, `loads/transfers.py`, `tests/test_raw_merge_on_write.py`, `docs/data_contract.md`, `.claude/task/contract.md`, `.claude/task/escalations.log`) is listed in `contract.md`'s `scope_paths`; no out-of-scope file touched.
- §10 / new-mechanism check: `delete_superseded_league_rows` (`bigquery.py:262`) is the whole-league variant of the pre-existing `_delete_superseded_player_rows` (`squads.py`) and the FIXTURE_DETAILS merge-on-write pattern already documented in `docs/data_contract.md`; the contract's "NEW MECHANISM — none" claim holds against the code.
- Undeclared-threshold hunt: the recurring-cost threshold (new DML delete jobs per league per table per run) is explicitly declared in `contract.md` `decisions_taken` with a dollar estimate and rationale, tied to the CPO's 2026-08-08 approval of item 8 and the 2026-08-09 scoping entry. Not smuggled.
- `decisions_reserved` cross-check: COACHES, SQUADS, FIXTURES_NEXT, INJURIES, LEAGUES, PLAYER_PROFILES/PLAYER_TEAMS are all excluded in the code as well as the prose (grep-verified: `coaches.py` untouched, no delete import there). None silently converted.
- Impact-map honesty (A6): evidenced with actual `dbt ls --select ...+` output (29 models, 94 parsed) and `bq show` row/size baselines rather than asserted from memory; matches the structural-surface trigger for `ingestion/**`.
- Failure-mode correctness verified in the diff rather than from the contract's claim: a failed delete in `transfers.py`/`standings.py` is caught by the outer `except Exception` and reported via `ctx.errors` without raising, and `teams.py` catches it separately so the team-id extension still runs.
- Credentials/secrets sweep across the full diff: no key/token/password-shaped string; every "key" hit is a `league_code`-keyed delete or a dict key.
- Scope reduction (eight/ten tables → three) is recorded in `escalations.log` (2026-08-09 entry), not only in `contract.md`, satisfying the repo's own precedent that a contract-only record does not count.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Writer uniqueness / impact-map accuracy: confirmed `loads/transfers.py`, `loads/standings.py` and `loads/teams.py` are each the SOLE writer of their raw table, and no `scripts/` writer exists for any of the three.
- Staging grain claim verified at the SQL level rather than accepted from the contract: `stg_apif__transfers.sql`, `stg_apif__standings.sql` and `stg_apif__teams.sql` all carry `qualify row_number() over (partition by league_code order by ingested_at desc) = 1`. This is the load-bearing fact behind "nothing is lost", and it holds — deleting strictly-older-than-this-write rows cannot change what any of the 29 downstream models see.
- The #896 guard is genuinely upstream of every delete: traced all three loaders line by line. `delete_superseded_league_rows` is reachable only after `complete` is True (transfers/standings return early before the write; teams nests the delete inside `if complete:`). No path lets a partial fetch reach the delete.
- Idempotency / self-healing: the append commits via a batch LOAD job (not a streaming insert, so no streaming-buffer delete restriction) before the DELETE is attempted. A failed delete leaves both rows, staging still picks the newer one, and the next run's delete — bounded by its own later timestamp — cleans up the leftover. No duplication, truncation or permanent drift.
- Exclusion set checked against code, not prose: `stg_apif__coaches.sql:1-7` does read all snapshots, so the stated reason a league-keyed delete would destroy ~120 coaches is factually true.
- Test fidelity against this repo's documented decoration-test failure modes: the transfers case patches `fixture_scheduling.fetch_merged_paged` (not `transfers_response_for_team` itself), and `transfers_response_for_team` resolves `fetch_merged_paged` from that same module namespace — the exact bug class caught in 8a round 1 is not present. Same namespace check for standings/teams/coaches.
- Minor asymmetry examined and judged a NON-defect: `transfers.py`/`standings.py` wrap write + delete + `ctx.add_loaded(1)` in one `try`, so a delete failure skips the counter and is labelled `"transfers BQ {league}: {e}"`, conflating it with a write failure — unlike `teams.py`, which isolates it deliberately. Traced `ctx.tables_loaded`'s only consumers (`orchestrator.py`: a log line and `write_ci_output("new_data", tables_loaded > 0)`); it is a run-wide counter incremented across ~45 competitions, so one missed increment cannot flip `new_data`. The error still reaches `ctx.errors`. Cosmetic inconsistency, no concrete failure.
- Declarations cross-checked: "no new mechanism" is true against `squads.py:43-74`; the recurring-cost arithmetic (~135 jobs/night, ~$0.25/month) is the right ballpark for a 10 MB DML minimum; the three-table scope reduction is quoted in `escalations.log`, not merely asserted.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-run / interruption safety for all three loaders: if the process dies between the append and the delete, the league keeps one extra stale row; the next successful run's delete boundary removes it, so the state self-heals with no manual intervention and no accumulation across retries. Traced through `bigquery.py:262-300` and all three call sites.
- Guard ordering (8a → 8b) confirmed in source rather than from the docstring: `transfers.py:40-72`, `standings.py:38-67`, `teams.py:35-105` all set `complete = False` and return or skip before reaching `load_json_to_bq`/`delete_superseded_league_rows`. `result_is_complete()` (`http_client.py:83-107`) flags both the body-error and quota-latch shapes the test fixtures use.
- Delete-boundary invariant: `ts = datetime.now(timezone.utc)` is computed ONCE and passed to both the write (`ingested_at=ts.isoformat()`) and the delete (`before=ts`) at every call site — no second, independently-taken clock reading that could race ahead of or behind the appended row's stamp.
- Decoration-test check on every new case in `tests/test_raw_merge_on_write.py`: for each, traced the single production edit that flips it red (drop the delete call; unscope the `league_code` predicate; drop the `ingested_at <` bound; move the delete above the completeness guard; merge the delete into the outer try in `teams.py`; add a delete to `coaches.py`; import the helper into a fourth loader). None came back "no edit would fail this". The helper under test is exercised for real against a fake client recording SQL and bound parameters, not monkeypatched — unlike the prior `test_squad_players_rows.py` decoration bug.
- Initially flagged then WITHDRAWN as not a defect: the combined-try shape in `transfers.py:73-93` / `standings.py:68-86` was checked against the pre-existing sibling `loads/squads.py:216-241`, which is unmodified by this branch and has the identical combined-try shape and the identical generic error message. Matching established out-of-scope precedent is not a defect introduced here.
- Dependency hygiene, credentials, build/hosting, and the guard-hooks/CI-workflow parity items: none of those paths appear in this branch's `review_input.patch`, so there is nothing in that class to check.

## escalations
(none)
