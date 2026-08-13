# Task contract — #33 items 9 + 10: staging becomes a table, and the guard follows

objective: >
  `1_staging` is `+materialized: view`, so it stores nothing and every reader re-executes the
  JSON parse of the raw table underneath. There are **59 staging tests** across 15 staging
  models, plus ~20 base models reading those views, so each raw table is scanned roughly five
  times a night per staging model to answer questions a stored table would answer for the 10 MB
  minimum.

  Item 9 sets `1_staging: +materialized: table`. Item 10 extends the existing per-model
  materialisation ban from `2_base` to `1_staging` so the layer decision cannot be overridden
  model by model and silently stop being re-costed with the rest of its layer.

  This is the SAME change #547 made to `2_base` on 2026-08-02, one layer up, for the same
  measured reason.
refs: >
  GitLab #33 items 9 and 10. Precedent and measurement method: #547 (`2_base`), recorded in
  `dbt_project/docs/layering.md` §2_base and pinned by `tests/test_materialisation_policy.py`.

scope_paths:
  - dbt_project/dbt_project.yml
  - ingestion/api_football/bigquery.py
  - ingestion/api_football/loads/teams.py
  - scripts/check_layer_contract.py
  - tests/test_materialisation_policy.py
  - dbt_project/docs/layering.md
  - dbt_project/docs/engineering_standards.md
  - CLAUDE.md
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  Not gate-required — `dbt_project/dbt_project.yml` is not `dbt_project/models/**`, and no model
  file is edited. Written in full anyway, because a one-line config change here alters how every
  staging model is BUILT and what every staging test READS, which is a far wider blast radius
  than the diff suggests.

  what changes physically: 15 staging models stop being views and become tables in the `staging`
    dataset, rebuilt each run. Verified there are **zero** per-model materialisation overrides in
    `1_staging` today (`grep -rn "materialized" dbt_project/models/1_staging/` → no matches), so
    nothing conflicts with the layer default and item 10 has nothing to fix retroactively.

  downstream: no lineage changes. `ref()` graph, column names and row semantics are untouched —
    a view and a table over the same SELECT return the same rows. What changes is WHERE the
    result is read from. Confirmed by `dbt ls --select 1_staging --resource-type test` → 59
    tests, all of which continue to test the same models.

  layer_rules: `scripts/check_layer_contract.py` currently bans per-model
    `config(materialized=...)` in `2_base` only (`BASE_DIR`, the `BASE_MATERIALIZED` regex).
    Item 10 extends that to `1_staging`. `tests/test_materialisation_policy.py` is the offline
    twin and carries `EXPECTED["1_staging"] = "view"`, which is the policy record and must move
    in the same commit — the test is deliberately built so changing `dbt_project.yml` alone
    fails.

  ⚠ THE DOC SITES ARE PART OF THE CHANGE, NOT TIDYING. `test_materialisation_policy.py` exists
    because in May 2026 a cost fix landed, an unrelated refactor reverted it two days later, and
    nothing failed for two months because every other test asks whether a NUMBER is right and
    none asks whether something became expensive. Three sites state the staging rule and become
    FALSE with this change:
      · `dbt_project/docs/layering.md:12` — "`1_staging` dbt models (views by default)"
      · `dbt_project/docs/engineering_standards.md:108` — "Prefer views for lightweight `staging`"
      · `dbt_project/dbt_project.yml:79` — "# 1. Staging: Raw cleanup (Views for speed and low cost)"
    `CLAUDE.md:73` is updated too: its sentence is past-tense and stays historically true, but it
    is the always-loaded orientation file and would leave a reader believing staging is a view.

  ⚠ DELIBERATELY NOT TOUCHED, and this keeps the task out of governance territory:
    `.claude/hooks/dbt_layer_gate.py` is a PROTECTED path. Checked line by line — its
    `1_staging` message says nothing about materialisation, and its `2_base` message mentions
    staging views only in past tense as the #547 rationale, which remains accurate. No
    `protected_override` is needed. `scripts/report_bq_cost.py:77` and
    `dbt_project/docs/layering.md:162` are likewise past-tense history and stay.
    `.claude/active_work.md` mentions the staging view twice and is NOT edited — the product
    stream owns it (#33 says so); state goes on #33 instead.

  deploy_order: nothing breaks at any point and no `--full-refresh` is needed. Staging models are
    not incremental, so dbt replaces each view with a table on the next build. The first prod run
    after merge pays one extra scan per staging model to populate the tables; every run after
    that is cheaper. ⚠ THE NIGHTLY RUNS AN IMAGE — merging does not deploy this. It needs
    `gcloud run jobs deploy fdp-nightly --source . --region europe-west1` from `main`
    (#39 Stage 3 not built).

  blast_radius: no number in any mart moves. This changes cost and build mechanics only.

decisions_taken: >
  CPO ruling, in-thread 2026-08-12: **"definitely"**, in answer to "Shall I do item 9 + 10 now?"
  Recorded in `.claude/task/escalations.log` (entry "2026-08-12 — #33 ITEMS 9 + 10 …") BEFORE
  this contract was written.

  ⚠ A PREMISE CHECK THE CPO DEMANDED, AND THE ANSWER IS IN THE LOG. Asked whether staging had
  previously been a table and was made a view for cost reasons — which would make this a
  reversal needing justification. It was NOT: `1_staging` has been `view` at every commit that
  ever touched `dbt_project.yml`, from `1f422c0` (2026-04-10) to `4899025` (2026-08-02),
  extracted by replaying the block per commit. The recollection was of `2_base`, which was a
  view and became a table under #547 — the precedent FOR this change, not against it.

  # THRESHOLD DECLARATIONS
  RECURRING COST — **yes, and it is a net REDUCTION, measured rather than assumed.**
    · added storage: ~0.5 GiB. Measured basis: the whole `dbt_analytics` base layer, which is
      staging's parsed output, is **0.415 GiB across 43 tables**, while the `staging` dataset is
      **0.0 GiB across 259 objects** because views store nothing. At EU active-storage rates that
      is single-digit cents per month.
    · removed query cost: measured on the last 24h of prod builds, tests **$0.17** vs models
      **$0.07** — the 2.4x view-rescan signature. Expected saving ~**$3-4/month**.
    ⚠ SMALLER THAN #33 CLAIMS, stated here so nobody sizes future work off the issue. #33
      justified this on `RAW_APIF_TRANSFERS` at 6.99 GiB rescanned per test; item 8b has since
      shrunk that table to **0.178 GiB**, a 39x reduction, so the largest scan the item was
      written about is already gone. The case now rests on the MULTIPLIER (≈5 scans per staging
      model per night collapsing to 1), which applies to whatever raw grows to — and the CPO
      confirmed in the same thread that more competitions are coming.
  NEW MECHANISM — no. A layer config value changes and an existing guard's directory list gains
    one entry. No new file, dependency, service or lifecycle hook.
  GUARD LOOSENED — no; this ADDS one. `check_layer_contract.py` and its offline twin gain a
    staging case that does not exist today.
  SHIPPED NUMBERS — no. Same rows, same columns, same lineage; only the storage changes.

decisions_reserved:
  - `RAW_APIF_INJURIES` is now the LARGEST raw table (1.975 GiB) with zero consumers — no source
    declaration, no model, nothing reads it. That is #33 item 15 and the CPO approved it
    ("yes") as a SEPARATE task in the same thread. Deliberately not bundled here: it stops an
    ingest and deletes a raw table, a different blast radius from a materialisation policy.
  - The `staging` dataset holds **259 objects for 15 models**, which implies a large number of
    orphaned views from renamed models. Not investigated, not in scope; worth its own look.
  - Whether any of the 59 staging tests are redundant against equivalent base tests. Cutting
    tests is loosening a guard and is not proposed.

done_when:
  - `tests/test_materialisation_policy.py` passes with `EXPECTED["1_staging"] == "table"`.
  - ⚠ ITEM 10 VERIFIED BY BREAKING ITS SUBJECT — see the 2026-08-12 amendment below for the
    method actually used, which the contract gate forced to change. Both the CI script and the
    offline twin must go RED on a per-model override and name the file. A guard that has never
    fired is decoration.
  - `pytest tests/ -q` exits 0 (baseline on this branch's base, main @ a2b4184: 789 passed).
  - `ruff --config .ruff-ci.toml scripts/ tests/` exits 0.
  - `dbt parse` succeeds against the edited `dbt_project.yml`.
  - Every doc site listed in the impact_map is updated in THIS commit, and a repo sweep finds no
    remaining present-tense claim that staging is a view.
  - ⚠ NOT VERIFIABLE FROM THIS BRANCH, and recorded so it is not mistaken for done: the actual
    cost saving. `dbt build` is forbidden locally and CI cannot run it here. The saving is
    confirmed only by `python scripts/report_bq_cost.py --days 1` AFTER the first prod build on
    the redeployed image, where `tests` should fall below `models`.

amendments:
  - 2026-08-12: `done_when`'s break-test METHOD changed — no scope widened, no path added.
    Authority: none needed; this records a method the repo's own guard made impossible, and the
    replacement is strictly stronger than what it replaces.
    WHAT HAPPENED: the original wording said to add `config(materialized='view')` to a real
    staging model, watch the guard fire, and revert. The CONTRACT GATE denied that edit —
    `dbt_project/models/1_staging/api_football/stg_apif__teams.sql` is not in `scope_paths`,
    and adding it would have put a production model in scope purely to vandalise it temporarily.
    That is the gate working: a temporary break in a real model is exactly the kind of edit that
    gets forgotten and shipped.
    WHAT WAS DONE INSTEAD: the REAL script, the REAL regex and the REAL
    `check_staging_materialisation` function were run against the REAL body of
    `stg_apif__teams.sql`, copied into a temp directory with `STAGING_DIR`/`REPO_ROOT` pointed
    at it. Three cases, and the third is the one that matters:
      · unmodified real model            -> 0 errors   (the guard is not firing on everything)
      · + config(materialized='view')    -> 1 error, naming the file
      · + config(materialized='table')   -> 1 error, naming the file
    The `table` case proves the rule is "no per-model override AT ALL", not "no override to the
    wrong value" — a model pinned to the layer's current value would otherwise pass while
    silently opting out of the next re-costing. `tests/test_materialisation_policy.py` carries
    the same check as a committed test so it runs in CI, not only here.
  - 2026-08-12: + `ingestion/api_football/bigquery.py`, + `ingestion/api_football/loads/teams.py`.
    Authority: the STANDING CPO RULE recorded in this log on 2026-08-08 — "Updating a reference
    that an approved change itself breaks is part of that change, not a scope extension —
    provided the update is confined to the reference and changes no behaviour."
    Both are COMMENTS made false by this change, and nothing else in either file is touched:
      · `bigquery.py:121` "so staging views can still do full scans"
      · `loads/teams.py:63` "staging views read $.league.season per row"
    HOW THEY WERE FOUND, and why this matters more than the two lines: NOT by the manual sweep
    in `done_when`, which missed them. They were found by the generalised drift guard added in
    response to the round-1 review, on its FIRST run. Two reviewers independently FAILed round 1
    for extending only the per-model-override half of the guard to staging and leaving the
    doc-drift half hardcoded to `2_base`; generalising it immediately produced three offenders a
    human grep had walked past. That is the argument for the guard, made by the guard.
    `.claude/active_work.md` was the third offender and is NOT edited — the product stream owns
    it (#33) — so it joins `_is_bookkeeping()`, which already excludes `.claude/task/**` for the
    same reason: a handover file is state, not a policy site. It is flagged to that stream
    instead.
