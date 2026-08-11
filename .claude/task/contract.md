# Task contract — #33 item 14: re-fetch cadence for transfers and coaches

objective: >
  `transfers` and `coaches` re-download identical data every night. Measured on the 2026-08-09
  nightly: 26.7 + 18.7 = **45 of 105 ingestion minutes**, and roughly 3,800 of ~8,300 daily API
  calls, spent fetching data that has not changed. Transfers move in bursts (January, summer);
  managers change rarely.

  This task makes both re-fetch on a **7-day cadence per league** instead of nightly.

  NOT A REGRESSION FIX, and the record matters because the CPO asked for it as one. `git log -S`
  across ALL history for `already_captured`, `captured_`, `skip_if_present`, `cached_response`
  and `players_needing`, scoped to `loads/transfers.py` and `loads/coaches.py`, returns ZERO
  commits. Neither loader has ever carried skip-if-present logic. The CPO's recollection of a
  "don't fetch what we already have" design is nonetheless correct — it exists and is deliberate
  in FIVE other loaders (`players`, `player_squads`, `player_profiles`, `player_teams`,
  `fixtures`, `fixture_details`). These two never got it. This finishes the job rather than
  restoring something.
refs: GitLab #33 item 14

scope_paths:
  - ingestion/api_football/refetch.py
  - ingestion/api_football/loads/competition_runner.py
  - ingestion/api_football/orchestrator.py
  - dbt_project/models/1_staging/api_football/sources.yml
  - tests/test_refetch_cadence.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  writers: unchanged. `loads/transfers.py:69` and `loads/coaches.py:83` remain the sole writers
    of their tables and are NOT edited. What changes is whether `competition_runner.py` calls
    them at all on a given night.

  downstream: `dbt ls --select source:api_football.raw_apif_transfers+
    source:api_football.raw_apif_coaches+ --resource-type model` (dbt 1.7.19, 94 models parsed):

      1_staging: stg_apif__coach_career, stg_apif__coaches, stg_apif__transfers
      2_base:    base_apif__coach_career, base_apif__coaches, base_apif__transfers
      3_core:    dim_coach, dim_coach_team_mapping, fct_transfer

  blast_radius on those 9 models: NONE. A skipped league writes NOTHING, so its existing row is
    untouched and staging reads exactly what it read yesterday. The only observable change is
    that a row's `ingested_at` advances weekly instead of nightly. `stg_apif__transfers` selects
    latest-per-league and `stg_apif__coaches` reads all snapshots — neither cares how old the
    latest is.

  the sources.yml edit changes NO SQL. `freshness:` is metadata; it does not appear in compiled
    model SQL and cannot alter lineage or results.

    ⚠ WHO READS IT, stated precisely because an earlier draft of this contract got it wrong and
    `data-engineer-reviewer` was right to FAIL that. ON THIS BRANCH: **nobody**. `dbt source
    freshness` is invoked nowhere in the repo, and a grep for `warn_after|error_after` outside
    `sources.yml` returns only this task's own test. The consumer —
    `scripts/check_raw_freshness.py`, the hourly out-of-band sentinel — lives on the UNMERGED
    branch `feat/39-nightly-freshness-alert` (#39 Stage 2, MR !30, commit 42ba08f) and is NOT
    in this diff. A blinded reviewer cannot verify it from here, and the earlier draft asserted
    it as present-tense fact, which is exactly the assert-before-checking pattern Appendix A6
    names.

    THE CHANGE IS CORRECT EITHER WAY, and that is the point:
      · if !30 never merges — nothing reads these thresholds, so raising them is INERT. No
        behaviour changes anywhere.
      · if !30 merges — the sentinel reads `error_after` and would email daily about a pipeline
        behaving exactly as ruled, until somebody muted it. Raising them prevents that.
    So merge order genuinely does not matter, which is what `deploy_order` below claims.

  ⚠ WHY THE SKIP MUST SKIP THE WRITE TOO, not just the fetch: both loaders write ONE row per
    league. Fetching a subset and writing it would produce a partial row — the SQUADS defect
    (#37) — and since #33 item 8b these tables are MERGE-ON-WRITE, so that partial write would
    DELETE the complete row. Skipping the phase entirely means no fetch, no write, no delete,
    and no carry-forward needed. This is the whole reason the design is safe.

  deploy_order: nothing breaks at any point and no backfill is needed. On the first nightly
    after merge, every league has a fresh row from tonight, so all of them skip until their
    staggered due-date arrives. Independent of #39 !30 — either can merge first.

decisions_taken: >
  CPO ruling, in-thread: **"re-fetch transfers and coaches every 7 days"**. That is the cadence
  and it is not the builder's to adjust.

  TWO CONSEQUENCES THE CPO WAS SHOWN AND APPROVED IN THE PLAN, because neither follows from a
  literal reading of the ruling:

  1. THE FRESHNESS THRESHOLDS MOVE WITH IT. `sources.yml` declares warn 30h / error 54h for both
     tables. Under a 7-day cadence they would sit permanently past `error_after`. Raised to
     warn 8 days / error 10 days for these two tables ONLY; the other 9 sources stay at 30h/54h
     because they are still daily.
     WHEN THAT MATTERS is conditional and is spelled out in the impact_map above: nothing on
     THIS branch reads these thresholds, so the change is inert here. It takes effect only once
     #39 Stage 2's sentinel (MR !30, not in this diff) merges — at which point unraised
     thresholds would page daily about correct behaviour.

  2. STAGGERED BY LEAGUE. Every league shares tonight's `ingested_at`, so an unstaggered cadence
     makes all 45 due on the same night — one night in seven costing the full 45 minutes against
     a 3h timeout, six costing nothing. `hash(league_code) % 7` spreads it to ~6-7 leagues a
     night. Each league still re-fetches every 7 days exactly as ruled; only the offset differs.

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — no. Skip-if-present is an established pattern here (five loaders), and the
  hoisted one-read-per-run shape copies `captured_player_team_seasons` (`orchestrator.py:201`),
  the fix #33 item 1 made for the same class of problem. No new service, dependency or
  lifecycle. `API_FOOTBALL_INGEST_FORCE_FULL` is reused rather than a second flag invented.

  RECURRING COST — this REDUCES it: ~45 min/night of ingest becomes ~6-7, and ~3,800 daily API
  calls disappear. No new spend.

  ⚠ A GUARD IS BEING LOOSENED, declared because this repo's standing rule is never to loosen one
  quietly. Raising `error_after` from 54h to 10 days means genuine breakage of transfers or
  coaches ingestion now goes unnoticed for up to 10 days instead of 54 hours. The rule's actual
  requirement is to NARROW a guard to where it still holds rather than delete the assertion, and
  that is what this is: 54h is simply false once the intended refresh interval is 7 days, and a
  guard that fires daily on correct behaviour gets muted, which is a worse outcome than a wider
  true one. The other nine sources are untouched, so the narrowing is confined to exactly the
  two tables whose contract changed. `tests/test_refetch_cadence.py` then pins the relationship
  so cadence and threshold cannot drift apart again.

decisions_reserved:
  - Whether the cadence should be window-aware (daily during January/summer transfer windows,
    weekly otherwise). Truer to the data, more complexity; the CPO ruled a flat 7 days and this
    implements exactly that.
  - `player_squads` / `squad` (38 min combined) are NOT touched. They already skip; their cost
    is the current season, which genuinely changes nightly.
  - `injuries` — #33 item 15 proposes dropping the endpoint entirely; not decided here.

done_when:
  - `pytest tests/ -q` exits 0 (baseline on this branch's base, main @ 5e1a672: 725 passed).
  - `ruff --config .ruff-ci.toml ingestion/ tests/ scripts/` exits 0.
  - Every new test verified by BREAKING ITS SUBJECT — production code, never a test helper —
    and confirming WHICH cases go red.
  - `dbt parse` succeeds against the edited `sources.yml` (a malformed freshness block is a
    parse error, and nothing else in CI would catch it while `data:build` cannot run).
  - No ingest, no `dbt build`, no `gcloud` resource touched from this branch.

amendments:
  - 2026-08-10: + `ingestion/api_football/orchestrator.py` — authority: **the CPO-approved plan
    for this task**, which specifies "called ONCE per table per run and passed down, mirroring
    `captured_player_team_seasons` (`orchestrator.py:201`)". The hoist can only live in the
    orchestrator — that is where the per-competition loop and every existing hoist are — so the
    approved design already required editing this file and the omission from `scope_paths` was
    clerical, not a widening. Caught by the contract gate on the first edit, which is the gate
    working: the plan and the contract disagreed, and the contract is what governs.
    Content: read `latest_ingest_per_league` once per table before the loop and pass the two
    dicts into `run_cheap_phases` and `run_transfers_for_competition`. No other change.
