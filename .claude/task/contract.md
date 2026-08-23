# Task contract — #82 MR3: wire the shared definitions, and keep them wired

objective: >
  Nine shared definitions live in `dbt_project/models/docs/shared_columns.md`, one per repeated
  column, written so a column documented in many models has ONE definition rather than many
  drifting ones. They are only half applied: 99 columns reference theirs, 2 deliberately reference
  a different block, and **195 whose name has a definition are blank**.

  MR3 wires those 195 and adds the gate rule that keeps it true: a column whose name matches a docs
  block must reference a docs block. It mechanises a rule that is already WRITTEN in
  `dbt_project/docs/engineering_standards.md` §2 Form — "a column documented in more than one model
  gets one docs block, referenced from each. Do not restate it" — and that has never been enforced.

refs: >
  GitLab #82. Programme plan `C:\Users\Rami\.claude\plans\cozy-orbiting-quail.md`, MR3. Approved
  plan for THIS MR, which also carries the layer-scope decision:
  `C:\Users\Rami\.claude\plans\serialized-enchanting-frost.md`.
  Authority for the programme: `.claude/task/escalations.log`, the 2026-08-21
  `feat/description-coverage-objects` entry, RULING 3 — "We use docs blocks but only if we have a
  mechanism to apply it consistently."
  Standard being enforced: `dbt_project/docs/engineering_standards.md` §2 Form, bullet 2.
  Branched from main `6e3ee57`, clean tree, no open MRs.

scope_paths:
  - scripts/declare_missing_columns.py
  - scripts/check_description_hygiene.py
  - tests/test_declare_missing_columns.py
  - tests/test_description_hygiene.py
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_season__team.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/team/int_team_market_value.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ STAGING AND BASE ARE IN SCOPE HERE AND WERE NOT IN MR2. That is a decision, not drift — see
# decisions_taken. The 16 yml paths are listed one by one rather than globbed so an accidental edit
# to a model file outside this set is still caught by the gate.

impact_map: >
  writers: NONE. No SQL changes and no model computes anything differently. The diff adds one
    `description:` line under 195 existing `- name:` entries, plus two script changes and their
    tests.

  downstream: NO lineage change. A description is not a dependency; `depends_on` is built from
    `ref()`/`source()` in the SQL and no SQL is touched. Shown rather than asserted as a
    `done_when` step: the parsed manifest before and after must have an identical node set and
    identical `depends_on` for every node, exactly as MR2 demonstrated.

  layer_rules: `check_layer_contract.py` polices per-competition staging subdirectories and the
    staging/base materialisation policy. This MR creates no model, no directory and no
    materialisation config. Staging and base ymls are EDITED but no `+materialized` is touched.
    Run repo-wide as a `done_when` step.

  deploy_order: none, and no migration. The wiring takes effect the next time each model is built,
    which is the `persist_docs` path traced below.

  blast_radius: ONE real effect and it is the intended one. `persist_docs` is on for every model,
    so 195 columns that currently carry an EMPTY description in BigQuery will carry the block's
    rendered text after the next build. Traced to `dbt/adapters/bigquery/impl.py:578`, which sets a
    declared column's description to `column_config.get("description")` — today None for these 195,
    hence empty; after this MR, the rendered block.
    NOTHING IS OVERWRITTEN: all 195 are blank by measurement, and 0 of them hold text today. The
    99 already wired and the 2 pointing at `league_code_ingest_provenance` are not touched.
    LENGTH CANNOT BREAK THE BUILD: BigQuery rejects a column description over 1,024 characters and
    a rejection fails the model. The longest block renders to **314** characters (`league_code`),
    so the worst case leaves 710 characters of headroom. Measured, not assumed, and the gate
    measures the rendered length independently on every run.
    ⚠ STAGING AND BASE ARE INCLUDED, so 44 columns in those layers also gain text in BigQuery. Both
    layers are TABLES, so `persist_docs` reaches them.

  gate_blast_radius: the new rule is a NEW WAY FOR A TURN AND A PIPELINE TO GO RED. Leaving a
    shared-name column blank, or restating its definition inline, now fails
    `check_description_hygiene.py`, which runs in `validate:governance` and in `stop_gate.py`'s
    FAST_GATES. That is the point. It needs NO new wiring and NO protected-path edit, because both
    already invoke this script. Green-on-day-one is required and is a `done_when` step.

decisions_taken: >
  CPO, 2026-08-23, approving `serialized-enchanting-frost.md`. That plan put ONE decision under its
  own heading — whether the wiring covers staging and base or only core downstream — stated the
  split (151 in core/intermediate/marts, 44 in staging/base), recommended all five layers, and
  named the alternative. He approved the plan. Recorded as the option approved and nothing more.
  ⚠ THIS DOES NOT REOPEN THE 2026-08-21 COVERAGE RULING. That ruling ("core, intermediate and marts
  -> business meaning starts in core downstream") governs which columns must have a description
  AUTHORED, and it stands. This MR authors nothing; it points columns at text that already exists.

  CPO, 2026-08-21, RULING 3, verbatim: "We use docs blocks but only if we have a mechanism to apply
  it consistently." The gate rule IS that mechanism, and the plan for MR3 has said so since
  2026-08-21.

  THRESHOLD DECLARATION — NEW MECHANISM, TWO OF THEM, both named in the approved plan.
  (a) A new `--wire-shared-docs` mode on `scripts/declare_missing_columns.py`. It is a mode on the
      mechanism the CPO approved on 2026-08-23, not a second script, deliberately: that script's
      line-level editing, line-ending preservation, append-only verification, atomic write and
      found-no-work guard are exactly what must not be reimplemented.
  (b) A new ENFORCED RULE in `check_description_hygiene.py`. A new rule changes what may be
      committed, which is why it is declared here rather than left for a routing row to find.
  THRESHOLD DECLARATION — RECURRING COST: NONE. No CI job, no schedule, no new dependency. The gate
  already runs in both places; this adds a rule to it, not a run of it.

decisions_reserved:
  - WHICH block a column points at is deliberately NOT policed. The rule requires a `{{ doc(...) }}`
    reference and no more, so a column whose meaning genuinely differs opts out by referencing a
    different block — which is what the two existing `league_code_ingest_provenance` sites already
    do. The opt-out costs writing a second block. That friction is intended and is not a decision
    taken here; if it ever proves too strict, the fix is a CPO call, not a loosened rule.
  - The ~249 definitions that do not exist yet are MR4's, and none is written here. MR3 points only
    at the nine blocks that already exist and creates no new block.
  - ⚠ A LATENT TRAP CLOSED HERE, raised because closing it is a behaviour change rather than a
    cleanup. `_docs_blocks()` walks all of `dbt_project/**/*.md`, but dbt reads only `docs-paths`,
    which is unset and so defaults to `models/`. `dbt_project/docs/` is outside it. Today the two
    agree by accident: `engineering_standards.md:112` contains the literal text `{% docs name %}`
    inside a sentence explaining the syntax, and the gate misses it only because its regex requires
    a closing `{% enddocs %}` and that file has none. Adding one anywhere under `dbt_project/docs/`
    would invent a block named `name` and, under the new rule, demand that every column called
    `name` reference a fragment of the standards document. Nothing is named `name` today, so it is
    latent rather than live. Discovery is restricted to `models/` here so the gate and dbt cannot
    disagree.

done_when:
  - All 195 columns whose name matches a docs block reference a docs block, MEASURED from the raw
    YAML and never predicted. ⚠ The manifest CANNOT answer this: it stores the RESOLVED
    description, so a wired column is indistinguishable from an inline one. That mistake was made
    once while scoping this and was caught only because "0 already wired" contradicted a known 99.
  - `git diff --numstat` over the 16 yml files shows **0 deleted lines**.
  - The parsed manifest before and after has an identical node set and identical `depends_on`.
  - The new gate rule is SEEN RED on both of its halves before it is trusted (#904): blank a wired
    column, and restate one inline. The block-discovery fix is seen red by adding an
    `{% enddocs %}` under `dbt_project/docs/` and watching a block appear that dbt does not have.
  - The gate is green repo-wide BEFORE the rule is relied on, so main never goes red.
  - `dbt parse` clean, every `{{ doc() }}` resolves, and ZERO unrendered `{{ doc(` survives into
    the manifest.
  - A second run of the wiring mode reports it found nothing and exits non-zero.
  - `python -m pytest tests/` at its measured baseline of 925 passed / 1 skipped, plus the new tests.
  - The six offline gates pass, read from their OUTPUT and not their exit code.
  - Handover updated in the SAME commit as the code.

amendments:
  - >
    1. 2026-08-23, CPO DECISION AT THE ROUND CAP: `league_code` IS DROPPED FROM THIS MR. The
    objective's 195 becomes **146**, and the 49 `league_code` columns stay blank, tracked in
    GitLab #87.
    THE ASK, put to him after analytics-engineer-reviewer's THIRD failing round: either drop the
    name and ship the rest, or fix the sixth site and authorise a fourth round with a recorded
    override. His answer: "drop league_code, ship the 146". Recorded as the option chosen and
    nothing more.
    WHY IT WAS PUT TO HIM RATHER THAN DECIDED: the review cycle caps at 3 rounds and
    `docs/working_agreement.md` requires stopping and bringing the open findings to the CPO instead
    of looping. Three rounds had found SIX wrong sites, every one of them in that single name, none
    of them found by me, and I had twice asserted the set was complete and been wrong.
    WHAT IT BUYS, which is why it was the recommendation and not merely an option:
      (a) The 146 have not been challenged once across three rounds. Every defect was `league_code`.
      (b) It removes a contradiction this MR would otherwise ship: the guard added here forbids a
          machine guessing at a name that means two things, while the diff carried 49 machine-made
          guesses at exactly that name, hand-corrected six times under review.
      (c) It makes the diff REPRODUCIBLE. platform-reviewer's round-2 PASS observed that the guard,
          scoping by name globally, means a fresh run would withhold every `league_code` site — so
          the shipped state could not be regenerated by the tool that supposedly produced it. With
          the name gone, `git restore --source=main -- dbt_project/models` plus one
          `--wire-shared-docs` run reproduces this diff exactly, which is literally how it was
          produced.
    ⚠ THE GATE HAD TO FOLLOW THE GENERATOR, and that is a rule change carried by this amendment
    rather than a consequence of it. `_shared_block_coverage` now SKIPS a name that already
    references more than one block. Without that the gate would demand a reference for the 49
    blanks, and the only route to green would be the guess the generator refuses to make — the same
    defect re-entering from the opposite side. Skipped names are counted and printed on EVERY run,
    never silently dropped, and `test_the_two_ambiguity_rules_agree` pins the gate's opinion to the
    generator's so the two halves cannot drift apart.
    ⚠ NOT A LOOSENING, and the distinction matters. The rule was "if a name has a definition,
    reference it". For a name whose meaning is site-dependent that rule is WRONG rather than merely
    strict: it mandates a coin flip. Narrowing it states where the rule actually holds, which is
    what `feedback_never_loosen_a_guard` asks for. Presence for the 49 is still caught later by
    MR5, by which time #87 should have removed the ambiguity at its source.
  - >
    2. `rounds_cap_override` below is claimed on that same answer. The findings were TAKEN to the
    CPO at the cap, as the rule requires, and his decision changed the scope rather than
    authorising another lap of the same loop. Round 4 therefore reviews a materially different and
    smaller diff — 49 fewer wired columns and a narrowed gate rule — not a re-run of round 3's.

rounds_cap_override: >
  CPO, 2026-08-23, at the round-3 cap: "drop league_code, ship the 146". The open findings were
  brought to him rather than looped on, and his answer reduced the scope. Round 4 judges the
  smaller diff that decision produced.
