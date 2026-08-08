# Review — chore/gate0-truth-and-dbt-deadwood — 2026-08-08

> Gate 0.2 + Wave 1 items 5 and 6 of GitLab #33. Required reviewer set for the staged paths:
> `scope-auditor` (always), `analytics-engineer-reviewer` (`dbt_project/**`),
> `data-engineer-reviewer` (`docs/data_contract.md`). No guard path is staged, so no opus
> promotion applies and all three ran on their pinned sonnet floor.

diff_sha256: 0baa0b20b5e3598eaf441403f0ed195d05a088acce2c116251c37be5b996ea20

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 was a FAIL, and it was right: the contract cited a sweeping 2026-08-08 CPO approval for
  #33 that existed nowhere in `.claude/task/escalations.log`. Same failure the repo has ruled on
  twice (escalations.log 2026-06-17 E1 and 2026-07-31 — "Recording a ruling in the contract is not
  recording it"), because `contract.md` is overwritten by the next task. Round 2 re-examined the
  cure: the new entry at `escalations.log:1581-1634` is dated, quotes the approval verbatim, names
  the §10-class items individually (7, 8, 9, 11, 2/3/4, and item 6 — the dependency removal this
  branch actually executes), records what was deliberately cut, and states its own limit. Defect
  cured; the authority is now checkable.
- `decisions_taken` now points at that log entry as the durable record rather than asserting the
  ruling inline, consistent with the precedent it cites.
- Item 5 (dropping `source_json`) checked against the §10 table: mechanically-verified zero-consumer
  column removal, not a §10 decision, so its absence from the named §10 list is not a gap.
- Scope: every changed file matches `scope_paths` — `CLAUDE.md`, `docs/data_contract.md`,
  `dbt_project/packages.yml`, `package-lock.yml`, the two deleted macros, the 9 staging models. No
  undeclared file changed.
- Factual claims in the `CLAUDE.md` diff verified against the actual files, not accepted as written:
  no model declares `partition_by`/`cluster_by`; `generate_schema_name.sql` prefixes non-prod
  targets; `profiles.example.yml` uses `dev_scratch`. All held.
- Appendix A patterns A1-A5 checked against the diff: none present.
- Round-2 delta introduces no new scope, mechanism, cost or credential surface — it is confined to
  the two `.claude/task/` files that carry authority and are legitimately reviewed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 was a FAIL, and it was right. The `impact_map` claimed "79 models: the 9 changed + 70
  downstream" and headed the intermediate layer "4_intermediate (24)" over a 23-item list. The
  reviewer independently traced the graph and identified `int_team__market_value_latest` as the one
  intermediate model NOT downstream of the 9 changed staging models. Re-counted mechanically and the
  reviewer's numbers were confirmed: `wc -l` = 78 total, and `grep -c` per layer = 9 / 12 / 11 / 23
  / 23. A #904-class recurrence — a hand count asserted as a paste. Round 2 verified all four sites
  now read 78/69 consistently (impact_map, the blast-radius line, and both `done_when` lines), with
  the stale figures surviving only inside the note recording what round 1 caught.
- Layer placement of the 9 column drops: each removes only a `to_json_string(...)`/passthrough
  `source_json` alias from a final select. No dedup, aggregation, pivot or cross-domain join added —
  consistent with `dbt_project/docs/layering.md` §1_staging.
- `source_json` zero-consumer claim re-derived independently by repo-wide grep rather than trusting
  the pasted output: no hits in models, `schema.yml`, macros, seeds, scripts, `site_v2/src` or
  `tests`. No dangling test or doc left behind.
- Macro deletions and package removals: zero live callers anywhere. The two surviving references
  (a dormant GitHub Actions path filter, a closed-thread doc log) are inert and the contract
  justifies declining to edit them under CLAUDE.md's frozen-tree rule.
- `docs/data_contract.md` rewrite checked against the actual 15 staging models: exactly 6 carry the
  `qualify row_number() ... partition by league_code` window, and zero carry a `DATE(ingested_at)`
  pre-filter — confirming the deleted 7-day prescription described behaviour that never existed.
- `CLAUDE.md` corrections independently re-derived: `partition_by`/`cluster_by` grep returns zero;
  `sync_dbt_vars.py` does write both `dbt_project.yml` and the registry seed; counting `raw_table()`
  call sites against `sources.yml` gives 12 written vs 11 declared with `INJURIES` the gap.
- Round-2 delta confined to the two `.claude/task/` files; no new SQL, model, seed or export surface
  entered the diff, so no fresh layer/catalogue/consumption check is triggered.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- The 9 changed staging models read end-to-end: in every one the underlying JSON element
  (`match_json`/`row_json`/`team_row`/`player_el`/`stat_el`/`lineup_el`) is still consumed by other
  columns, so this is a pure column drop, not a change to response parsing.
- `source_json` was a staging-layer derived column (`to_json_string()`/alias), never a RAW table
  column. The raw `payload` is untouched, so the `RAW_APIF_{entity}` schema contract is unaffected.
- No `ingestion/` write-path file is touched by this branch; `bigquery.py` append-vs-merge logic is
  unmodified. No WRITE_TRUNCATE introduced.
- `ingestion/api_football/bigquery.py:88-93` — the line range the new `data_contract.md` prose
  cites — verified to actually contain `time_partitioning`, `clustering_fields` and
  `create_table(..., exists_ok=True)`, matching the claim that partitioning is set at create time
  and never retro-fitted.
- The rewritten `data_contract.md` latest-snapshot section verified by direct grep against all 15
  staging files: exactly `fixtures_next`, `leagues`, `squads`, `standings`, `teams`, `transfers`
  match, and no staging model anywhere carries a `DATE(ingested_at)` pre-filter.
- `CLAUDE.md`'s "12 written, 11 declared, `RAW_APIF_INJURIES` unmodelled" claim verified against
  `sources.yml` and the `raw_table()` call sites across `ingestion/api_football/loads/*.py`.
- `packages.yml`/`package-lock.yml` confirmed valid YAML after the edit, `dbt_utils` retained,
  `dbt_expectations` and transitive `dbt_date` removed consistently in both.
- §10 cost/scope knobs: no `history_seasons`, `ingest_active`, fanout cap or cadence change anywhere
  in the diff, so the contract's "RECURRING COST: unchanged" declaration holds.
- Round 2 (delta): `docs/data_contract.md`, the basis of the round-1 PASS, is untouched. The delta
  is a paperwork-authority fix plus an arithmetic correction, neither reopening anything passed.

## escalations
(none)
