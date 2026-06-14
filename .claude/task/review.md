# Review — feat/transfers-chain — 2026-06-14

> PR-i of the player-data initiative (APPROVED plan + escalations.log 2026-06-14): rebuild the
> retired transfers chain (reverses #420). Ingestion: `loads/transfers.py` pulls `/transfers`
> by team (one call = all a team's moves) and appends to `RAW_APIF_TRANSFERS`, wired into the
> orchestrator as Phase 4 after squads; `transfers_response_for_team` mirrors
> `players_response_for_team`. dbt: `stg_apif__transfers` (latest-snapshot + 1:1 unnest) →
> `base_apif__transfers` (dedup) → `fct_transfer` (dated-moves fact). `docs/data_contract.md`
> un-retires transfers. The affiliation timeline + current-team derivation are a LATER PR.
> Local validation: layer contract PASS, registry sync PASS, dbt parse PASS, sqlfluff clean,
> py_compile clean.
>
> Review cycle: FOUR cold iterations (scope-auditor + data-engineer-reviewer + analytics-engineer-
> reviewer). Iter 1 all FAIL → fixes: data_contract.md doc-sync (un-retire transfers; added to
> scope via amendment), deterministic dedup + `league_code` documented as ingest provenance,
> staging grain-test waiver. Iter 2: scope-auditor PASS; data-eng FAIL (data_contract intro count
> "seven"→"eight"; transfers freshness) + analytics FAIL (NULL surrogate/grain collision) → fixes:
> count fixed, freshness added, base now filters both-team-null + `fct_transfer_has_a_side` test.
> Iter 3 all FAIL on governance/test-policy interpretation → resolutions: the DEDUP RULE is now a
> recorded CPO ruling (escalations.log 2026-06-14 feat/transfers-chain, "do it"; dedup lives in
> BASE) and the contract amendment cites it; data_contract.md landing-zone prose now includes
> transfers; the two §3 findings (staging warn-test; "redundant" fact tests) were REJECTED with
> reason — staging omission-with-documented-waiver is the project pattern (fixture-detail models
> + header waiver; a warn test on expected-duplicate staging is perpetual noise), and the
> dual fact tests follow the documented `core.yml` fact-test policy (surrogate unique + natural-key
> combination). Iter 4: all three PASS against the hash below. Standing (pre-existing project-wide
> patterns, not new defects): partial-write-on-quota mirrors squads (transient — full re-fetch each
> run); no `tests/fixtures/apif/` offline-parser-test precedent (validation = dbt build + DQ tests).

diff_sha256: eb26721d4c4097b15064400eab961ceb31ae930b1a5f0102d5398a6e2b258e0c

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 authority trail: the dedup-rule choice (which records are "the same move") is now a RECORDED
  CPO ruling (escalations.log 2026-06-14 feat/transfers-chain) and the contract's dedup amendment
  cites it (no longer "data-cleaning latitude"); cost/cadence is within the recorded approval
  (transfers runs as Phase 4 of the existing daily run, like squads — no new run/schedule); no
  invented transfer-type taxonomy (raw string); affiliation-timeline/current-team logic is ABSENT
  (reserved for a later PR). All changed files are within scope_paths (data_contract.md added via
  a recorded amendment).
- Appendix A + reinstatement accuracy: no new mechanism (mirrors the squads by-team loader pattern,
  no UDF/hook — A3 clear); data_contract.md un-retire is accurate and complete (eight-table count,
  table row, landing-zone prose, endpoints row, retired→reinstated note, plan-vs-product row);
  league_code is documented as ingest provenance, not a semantic partition.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Ingestion correctness vs the squads pattern (loads/transfers.py:31-58): SKIP env, quota-break,
  per-team try/except, single append `load_json_to_bq(as_json_payload=True, append=True,
  league_code=...)` after the loop creating the unified table; `transfers_response_for_team`
  (fixture_scheduling.py) is by-team via fetch_merged_paged; orchestrator Phase 4 after squads uses
  result.team_ids; no new run/schedule. Partial-write-on-quota is the pre-existing squads pattern
  (transient — full re-fetch each run), not a new defect.
- data_contract.md reinstatement completeness: all six touch-points verified on disk — intro count
  "eight", RAW_APIF_TRANSFERS table row, landing-zone reshaped-payload prose ({team_id,
  transfers_payload}), endpoints row, retired→reinstated note, plan-vs-product row; raw landing
  follows RAW_APIF_{entity} + {league_code, payload, ingested_at}. The staging full-scan QUALIFY
  (no date pre-filter) mirrors stg_apif__players exactly — pre-existing pattern, not introduced here.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- NULL-key dedup/surrogate correctness (base_apif__transfers.sql:19,31-33 + fct_transfer.sql:23-28
  + core.yml/base.yml grain tests): single-side-null moves are legitimate and hash distinctly;
  the both-team-null filter removes the only grain-collision case; BigQuery groups nulls in the
  PARTITION BY and the unique_combination test, all consistent with the surrogate key. The
  `fct_transfer_has_a_side` test guards the at-least-one-side invariant.
- Layer + test-policy compliance: staging = latest-snapshot (partition by league_code) + 1:1 unnest
  only (no dedup); base = dedup, view, reads stg; core = reads base, no json/unnest/union_all,
  grain enforced, materialized table. Staging uniqueness-test omission matches the documented
  header waiver + the four existing fixture-detail staging models (expected duplicates). The dual
  fct_transfer uniqueness tests follow the core.yml header fact-test policy (surrogate unique +
  natural-key combination) — not redundant by project standard. transfer_type kept raw (no A1).

## escalations
(none — four cold iterations; all three routed reviewers PASS against the locked hash. The one §10
question raised in review (the dedup-rule classification) was ruled by the CPO and recorded in
escalations.log (2026-06-14 feat/transfers-chain, "do it"); the contract's dedup amendment cites it.
No open ESCALATE verdict remains. The affiliation timeline + current-team derivation, and the
canonical transfer-type taxonomy, remain reserved for later work.)
