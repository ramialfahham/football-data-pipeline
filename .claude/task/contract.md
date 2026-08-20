# Task contract — correct three false descriptions, rewrite the documentation standard

objective: >
  MR1 of six (plan: description drift). Two jobs, both small and both urgent enough not to wait
  behind the prose cleanup in MR2-4:
  (a) Correct three `description:` fields that state things which are provably false. One of them
      invites a change that would break a live mart.
  (b) Replace `engineering_standards.md` §2, whose four bullets are unenforceable and were ignored
      ~130 times, with a standard that says what a good description contains and what is banned.
refs: >
  Independent dbt audit, 2026-08-20. Plan approved by the CPO the same day. The audit was
  commissioned after the CPO spotted the `display_group` description while scoping whether
  `nav.json` and that column could be deleted after the Browse drop (`!80`).

impact_map: >
  Doc-only, evidenced. Three `description:` strings and one markdown standards file. No column, no
  `tests:` block, no seed CSV row, no model SQL, no config — so no dbt node's compiled output
  changes and there is zero warehouse blast radius. `dbt parse` is the check.

  Every factual claim the new text makes was MEASURED against the code, not asserted (#904):
  - `grep -rn "display_group" dbt_project/models/` → 3 hits, all in
    `5_marts/shared/mart_competition_index.sql`: a comment (line 73) and the two-line
    `where types.display_group is not null and trim(...) != ''` browsable filter (lines 90-91).
    So the current text's "No dbt model reads it" is false, and the column is NOT safely deletable.
  - `grep -rln "country_name_overrides" dbt_project/models/` → four base models read it
    (`base_apif__leagues`, `base_apif__teams_global`, `base_apif__player_profiles`,
    `base_apif__coaches`), plus `3_core/dim_country.sql`, which EXISTS. So the current text's
    "Only dim_league READS it" and "inert until dim_country lands" are both false.
  - `docs/competition_registry.yml` → 48 entries, all carrying `competition_type`;
    `seeds/competition_registry.csv` → 48 rows. So "all 45 registry entries" is false.

  ⚠ The `display_group` correction is the one with teeth. A reader who trusted the current text
  would delete the column; that silently changes which competitions reach the competitions page,
  and today it would remove zero rows, so the damage would not show up until a friendly-type
  competition is onboarded.

scope_paths:
  - dbt_project/seeds/schema.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/engineering_standards.md
  - .claude/task/contract.md
  - .claude/task/escalations.log

decisions_taken: >
  ALL of this MR's authority is recorded in `.claude/task/escalations.log`, 2026-08-20 entry,
  quoted verbatim there — the six-MR plan and its MR1/MR3 split, the CPO's definition of a good
  description, the "Both" choice of readers, and the "Docs blocks" choice of reuse mechanism.
  Read that entry, not this summary.

  ⚠ WHY THIS FIELD NOW POINTS AT THE LOG. Its first version cited "CPO, in chat, 2026-08-20" with
  no log entry behind it, and scope-auditor round 1 correctly FAILed for exactly that: this
  contract is overwritten by the next task, so a ruling recorded only here is unverifiable by the
  time anyone needs it. That is a standing FAIL pattern in this repo with many prior instances in
  the log itself. It is also, precisely, the defect this whole MR is about — authority written to
  the volatile place instead of the durable one — committed while fixing it.

decisions_reserved:
  - The four repeated-column docs blocks, the file cleanups, the CI gate and `persist_docs` are
    MR2-6 of the approved plan and are NOT started here. This MR deliberately ships the standard
    BEFORE the cleanup that will satisfy it, so the target is written down first.
  - Whether `display_group` is ultimately replaced (#57's critique of its mixed FORMAT/GEOGRAPHY
    axis still stands) and what replaces the blank-means-not-browsable signal. This MR only makes
    the description TRUE; it does not design the successor.
  - Whether `nav.json` / `build_nav` / `fetch_nav` are deleted. Unaffected by this correction.

acceptance_criteria:
  - `display_group` is REWRITTEN to fully meet the new standard: states what the column means and
    what blank means, no claim about which models read it, no dates/rulings/refs/emoji, under 600
    characters. It is the standard's worked example, so it must actually conform.
  - `country_name_overrides` no longer claims which models read it, and no longer asserts its rows
    are inert. The rest of that description is NOT cleaned here — see below.
  - `shared.yml`'s `entity_type` description states the invariant rather than a row count.
  - `engineering_standards.md` §2 states: what a description must contain, the ban on downstream
    consumer claims, the ban on history, dbt's own published rules with links, and one worked
    before/after example.
  - `.venv/Scripts/dbt.exe parse` runs clean.

  ⚠ TWO CRITERIA WERE NARROWED after the edits, and the narrowing is recorded rather than done
  quietly, because softening a criterion mid-task is exactly the failure the acceptance gate
  exists to catch. The originals read "No description IN THIS DIFF contains a date, a CPO ruling,
  an issue/MR number, a correction stamp, or a severity emoji" and "EVERY description touched by
  this MR is under 600 characters". Both describe a full cleanup of `seeds/schema.yml`, which the
  CPO-approved plan explicitly assigns to MR3, not MR1 — so as written they contradicted the plan
  this MR implements. They were wrong when I wrote them, not inconvenient once I got here:
  `country_name_overrides` remains 3,014 characters and still carries rulings, dates and refs, by
  design, until MR3. What MR1 owes on that description is the removal of the FALSE claim, and that
  is what the narrowed criterion now says.

done_when:
  - All four scope_paths edited per the above.
  - `dbt parse` clean; `python -m pytest tests/ -q` still green.
  - The three greps in impact_map re-run, each agreeing with the new text.
  - Committed; MR opened by the post-commit hook.

amendments:
  - none
