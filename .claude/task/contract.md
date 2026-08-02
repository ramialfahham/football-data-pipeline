# Task contract — stop re-scanning raw on every test, and make cost measurable (#547)

> Written on a clean tree before any file was touched. Branch `fix/547-base-tables-and-cost-guard`
> from `main` at `d20c5bc`. No protected path in scope, so no `protected_override`.
> `dbt_project/` materialisation is a structural change, so `impact_map` is present.
> No `site_v2/src/` path in scope, so no `acceptance_criteria`.

objective: >
  The nightly build re-reads the raw JSON tables once per TEST, because `1_staging` and `2_base` are
  both views. Nothing stores an intermediate result, so every test on a base model re-executes the
  whole chain down to raw.

  Measured over 35 days on the prod target, from `region-eu.INFORMATION_SCHEMA.JOBS_BY_PROJECT`:
  tests cost **$23.91** and building the models cost **$5.84**. Testing costs four times what
  building costs. `RAW_APIF_TRANSFERS` is **6.82 GiB across 1,117 rows** (6.25 MB per row), it
  carries six tests plus a fact build, and it is scanned about seven times a night. Transfers alone
  is **$8.56** of the $29.79 prod total.

  This materialises `2_base` as tables so each raw table is read once per night instead of once per
  test, pins that choice with a test so it cannot be undone silently, and ships the measurement
  script so the next person can answer "what does this cost" instead of guessing.

refs: >
  #547 (the cost-optimisation program, status "not started"), and Thread 1 of
  `docs/product_direction_threads.md`, closed 2026-05-25 as "architecture signed off". This is the
  part of that thread that stopped holding. NOT in this task: #890 (the ingestion read path), and
  the CI-side spend, which #887 changes first.

protected_override: >
  CPO, 2026-08-02, in-session: shown that the base-as-view rule also lives inside
  `.claude/hooks/dbt_layer_gate.py`, where it is INJECTED into every future agent that edits a base
  model, and asked directly whether to edit that protected file. He answered **"yes"**. The same
  exchange carries his ruling on the materialisation change itself: **"Fix it and ensure that this
  will not happen again in the future."** Both are recorded verbatim in `escalations.log`.

scope_paths:
  - dbt_project/dbt_project.yml
  - dbt_project/docs/layering.md
  - scripts/check_layer_contract.py
  - CLAUDE.md
  - .claude/hooks/dbt_layer_gate.py
  - docs/roles/analytics_engineer.md
  - dbt_project/profiles.example.yml
  - tests/test_materialisation_policy.py
  - scripts/report_bq_cost.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: nothing changes what any model COMPUTES. `2_base` moves from `view` to `table`, so 16
  models that were inlined into their consumers are now stored. No SQL is edited.

  downstream: every `3_core` model that refs a base model, which is the whole warehouse. Evidence,
  from the project venv dbt (`dbt=1.7.19`, 94 models parsed):
    `dbt ls --select 2_base --resource-type model` -> 16 models
    `dbt ls --select 2_base+ --resource-type model` -> the base models plus their core/intermediate/
    mart descendants (pasted in the PR body; it is the bulk of the project).
  Semantics are identical: a view and a table over the same SELECT return the same rows within one
  `dbt build`, because the whole pipeline runs in a single ordered pass. What changes is WHEN the
  SELECT is evaluated (once, at base build) instead of once per consumer and once per test.

  layer_rules: `check_layer_contract.py` governs what logic may live in a layer, not how it is
  materialised, so it is unaffected. `dbt_project/docs/layering.md` records the base-as-view
  decision and is updated here with the measured reason, because that decision explicitly allows a
  change with a documented reason and this is it.

  deploy_order: the first prod run after merge creates 16 new tables in the `base` dataset and the
  views are replaced. dbt handles the swap in dependency order. Storage added is small: the base
  models are the deduplicated, flattened rows, far smaller than the raw JSON they read.

  blast_radius: NO number on any page changes. What changes is the bytes the nightly scans, which
  is the point. Risk if wrong: a base model that is non-deterministic would freeze at build time
  rather than being re-evaluated per consumer. Checked: base models dedupe and union, and the only
  time-dependent input is `ingested_at` from raw, which is fixed for the run.

  SECOND BUILD — the new cost this change creates, enumerated from dbt rather than from memory
  after two wrong counts. `pages-match-preview.yml` runs its own build selecting
  `+mart_team_season_insights`, and it fires on the 07:30 cron, on push to main AND on dispatch, so
  it is once a day plus once per merge, not "twice a day".
    `dbt ls --select +mart_team_season_insights --resource-type model | grep 2_base` -> **9 of 16**:
    base_apif__competition_seasons, base_apif__fixture_events, base_apif__fixture_players,
    base_apif__fixture_statistics, base_apif__fixtures_next, base_apif__leagues,
    base_apif__standings, base_apif__teams, base_apif__teams_global.
  I first wrote "four", omitting `fixture_players` and `fixture_events`, which flatten the largest
  per-fixture JSON arrays in the project. While base was a view, rebuilding all nine cost nothing —
  `CREATE VIEW` is DDL and BigQuery does not bill it. As tables they are a real scan.

  The offsetting measurement, which is what makes the net still negative: base nodes are **$14.20**
  of the $29.79 prod total over 35 days, and base model BUILDS are **$0.00** — direct evidence that
  a view is free to create and expensive to test through. Those $14.20 are the tests re-executing
  the chain, and they collapse to one build each. The new exposure is nine base builds on the
  second run; `base_apif__transfers`, the single most expensive entity at $8.56, is NOT among them
  and is built once a day as before. Net remains negative, and the number that could contradict it
  now exists. Reproduce with `python scripts/report_bq_cost.py`.

  PROTECTED PATH — `.claude/hooks/dbt_layer_gate.py`. It is not machinery being changed, only a
  string it injects. Traced what depends on it: `_LAYER_RE` matches a `2_base` path, `main()` looks
  the layer up in `_LAYER_RULES` and calls `emit_context`, so the ONLY effect is which text an agent
  is shown before it edits a base model. Nothing parses the string, no gate branches on it, and it
  fails open. What stops being enforced if it is wrong: nothing mechanical, but every future agent
  editing a base model is told the superseded rule, which is precisely the drift this task exists to
  end. On failure the hook already fails open, and that is unchanged.

decisions_taken: >
  **CPO ruling, 2026-08-02: "Fix it and ensure that this will not happen again in the future."**
  That is the authority for changing the base materialisation. An earlier version of this contract
  cited the layer doc's "not without a documented reason" clause instead, and `scope-auditor`
  correctly failed it: a documented architectural decision is the CPO's to move, and treating a
  permissive clause as a delegation is the §10 meta-rule violation (analogy is not a licence).
  The measurement in `objective` is the documented reason the doc requires; it is not the authority.

  **CPO approval, same exchange: "yes"** to editing `.claude/hooks/dbt_layer_gate.py`, asked
  explicitly as a protected-path question. See `protected_override`.

  THRESHOLD DECLARATIONS. NEW MECHANISM: `scripts/report_bq_cost.py` is a new read-only reporting
  script. It is not wired into any workflow or hook and nothing depends on it; it exists so a cost
  claim can cite a number. RECURRING COST: **negative, and measured rather than asserted.** This
  removes roughly six redundant scans of every raw table per night. I am declaring it with a figure
  because writing "none" from intuition is exactly how this regression survived: I wrote
  "RECURRING COST: none" twice earlier today without measuring either.

decisions_reserved:
  - Whether the `RECURRING COST` declaration should be REQUIRED to cite a measured number rather
    than allowing the word "none". That would extend a written rule in `working_agreement.md` §2,
    which is §10, so it is the CPO's. The script this task ships is the thing that would make such a
    rule cheap to satisfy. Not done here.
  - Whether `1_staging` should also be materialised. It is the JSON explosion and therefore the
    expensive part, but it is also 17 models over the widest tables, so it is a bigger storage and
    build-time trade. Measure the effect of the base change first, then decide.
  - The threshold at which the pinning test should fail is the layer POLICY, not a tuned number, so
    there is no magic constant to reserve.

done_when:
  - `dbt parse` clean; `python -m pytest tests/test_materialisation_policy.py` passes, and fails if
    `2_base` is flipped back to `view` (verified by flipping it, running, and flipping back).
  - `python -m pytest tests/` green overall, since python-ci runs the whole directory.
  - `scripts/report_bq_cost.py` runs against the real project and reproduces the figures quoted in
    the objective.
  - `layering.md` states the materialisation policy and the measured reason.
  - `ci-data-build` green, and its prod build shows base models created as tables.

amendments:
  - 2026-08-02: + `scripts/check_layer_contract.py` and `CLAUDE.md` — authority: the objective
    itself. The base-as-view rule is written in FOUR places, and changing one leaves three
    contradicting it: `dbt_project.yml` (the real config), `layering.md` lines 13 and 160,
    `CLAUDE.md` line 56, and `check_layer_contract.py`, whose comment cites CLAUDE.md as
    non-negotiable and whose logic rejects any per-model materialisation that is not `view`. With
    the layer default now `table`, that check would reject a model for matching the default, so
    leaving it alone is not neutral, it is a new bug. The check becomes "a base model must not
    override materialisation at all; the layer default governs", which is simpler and stricter.
    Written on a clean tree; the config change was stashed for the amendment and restored after.
  - 2026-08-02: + `.claude/hooks/dbt_layer_gate.py` (PROTECTED, see `protected_override`) and
    `docs/roles/analytics_engineer.md` — authority: the CPO's "yes", after `analytics-engineer-
    reviewer` found them. ⚠ THE AMENDMENT ABOVE CLAIMED THE RULE LIVED IN FOUR PLACES AND THAT I HAD
    GREPPED RATHER THAN TRUSTED MEMORY. It lives in SEVEN. I grepped `docs/` and the dbt project and
    never searched the hooks or the role briefs, so the claim was true of the search I ran and false
    about the repo. The hook is the worst of the three misses: it INJECTS the superseded rule into
    every future agent that edits a base model.
  - 2026-08-02: + `dbt_project/profiles.example.yml` — authority: the same CPO ruling; found by
    `platform-reviewer`, which is the EIGHTH site and the THIRD time in this one task that I claimed
    a complete enumeration without running a command that could prove it (four, then seven, now
    eight). The claims are now replaced by pasted output, and the guard no longer depends on a list
    I maintain by hand:
      `dbt ls --select +mart_team_season_insights --resource-type model | grep 2_base` -> **9**
        base_apif__competition_seasons, base_apif__fixture_events, base_apif__fixture_players,
        base_apif__fixture_statistics, base_apif__fixtures_next, base_apif__leagues,
        base_apif__standings, base_apif__teams, base_apif__teams_global
      `git grep -inE "base (models? )?(are |as )?views|base views|views \+ seeds|2_base.*materiali"`
        -> the complete site list, which is what found profiles.example.yml.
    The guard now asserts repo-WIDE that no file states base is a view, so a ninth site cannot be
    added without failing, whether or not I remember to list it.
