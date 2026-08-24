# Task contract — #82 MR4a: generate the metric column definitions from the catalogue

objective: >
  Step 4 of #82 writes the column definitions that do not exist yet. Measured from the `.yml`
  files on 2026-08-24, **262 column names are blank everywhere**, covering **869 columns**.

  A large share of them are the metric vocabulary, and that vocabulary is ALREADY DEFINED in
  `dbt_project/seeds/metric_catalogue.csv`, which the repo already treats as the only source of a
  metric's definition. This MR gives every one of the catalogue's **76 metrics** a docs block
  GENERATED from the seed, and points **501 columns** at them: **478 that are blank** and **23
  that carry their own text today**, which keep their sentence with the reference placed in front
  of it.

  It authors no metric definition of its own. The 204 hand-written names that no seed defines are
  MR4b's and none is written here.

refs: >
  GitLab #82, step 4 of the description programme (`!82`-`!89`, `!91`, `!95`, `!97` merged).
  Approved plan: `C:\Users\Rami\.claude\plans\jaunty-herding-harp.md`, as amended by two CPO
  decisions taken during planning and one during implementation — see decisions_taken.
  Authority for the programme: `.claude/task/escalations.log`, the 2026-08-21
  `feat/description-coverage-objects` entry, RULING 3 — "We use docs blocks but only if we have a
  mechanism to apply it consistently."
  Standard: `dbt_project/docs/engineering_standards.md` §2.
  Branched from main `b15b501`, clean tree, no open MRs.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/docs/metric_columns.md
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - dbt_project/docs/engineering_standards.md
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ THE 11 YML PATHS ARE LISTED ONE BY ONE, not globbed, so an accidental edit to a model file
# outside this set is still caught by the gate. They are exactly the files holding the 501 columns.
# ⚠ `.gitlab-ci.yml` and `.claude/hooks/stop_gate.py` are DELIBERATELY ABSENT — both are PROTECTED
# and wiring the new check into them needs a `protected_override` the CPO has not been asked for
# yet. See decisions_reserved.

impact_map: >
  writers: NONE. No SQL changes, no model computes anything differently. The diff corrects prose in
    a seed's unread `description` column, adds one generated `.md` file, one script and its tests,
    appends one `description:` line under 478 existing `- name:` entries, and rewrites 23 existing
    `description:` values to put a block reference in front of the text already there.

  downstream: NO lineage change. A description is not a dependency; `depends_on` is built from
    `ref()`/`source()` in the SQL and no SQL is touched. Shown, not asserted: the parsed manifest
    before and after must have an identical node set and identical `depends_on` for every node.

  seed_reader_change: ⚠ THE ONE REAL PREMISE OF THIS MR, verified rather than assumed.
    `metric_catalogue.csv`'s `description` column is read by NOTHING today — no dbt model selects
    it (the models that `ref()` the seed take the formula and the metric list), the export scripts
    do not touch it, and the site's metric descriptions come from `metrics.<id>.description` in the
    i18n locale files, which is a different surface. This MR makes the generator its FIRST reader.
    That is the reason correcting it is safe and also the reason it had drifted.

  layer_rules: `check_layer_contract.py` polices per-competition staging subdirectories and the
    staging/base materialisation policy. This MR creates no model, no directory and no
    materialisation config. Run repo-wide as a `done_when` step.

  deploy_order: none, no migration. The wiring takes effect the next time each model is built.

  blast_radius: ONE real effect and it is the intended one. `persist_docs` is on for every model,
    so 478 columns that carry an EMPTY description in BigQuery today will carry the block's
    rendered text after the next build, and 23 that carry text today will carry the block's text
    plus the sentence they already had.
    ⚠ THE 23 ARE THE ONLY PLACE MEANING COULD BE LOST, so none is replaced: the existing sentence
    is KEPT and the reference is placed before it. A site whose existing text merely restates the
    catalogue keeps only the reference, and each such case is named individually in the evidence.
    LENGTH CANNOT BREAK THE BUILD: BigQuery rejects a column description over 1,024 characters and
    a rejection fails the model. The 23 combined strings are the longest this MR produces, so each
    is measured before commit; the gate measures rendered length independently on every run.
    The seed itself is rebuilt with `+full_refresh: true`; correcting `description` changes the
    seed's own stored text and nothing downstream of it.

  gate_blast_radius: adds a NEW WAY FOR A TURN AND A PIPELINE TO GO RED, once wired: the generated
    file drifting from the seed fails `sync_metric_docs_blocks.py --check`. ⚠ UNTIL the protected
    paths are wired it runs only when invoked by hand, which is why the wiring is treated as part
    of the mechanism and not an optional extra — see decisions_reserved.
    A SECOND, IMMEDIATE effect needs no wiring at all: creating a block named `duels_won` makes
    every blank column of that name a finding in `check_description_hygiene.py`, and every column
    that restates it a second kind of finding. That gate already runs in CI and in FAST_GATES. It
    is what forces write-and-wire into one commit, and what proves the wiring is complete by
    machine rather than by my claim.

decisions_taken: >
  CPO, 2026-08-24, on the sizing: the catalogue-backed names get their blocks GENERATED from
  `metric_catalogue.csv` with a check that fails on drift, rather than hand-written from it or
  written fresh. Recorded as the option chosen and nothing more.

  CPO, 2026-08-24, on the field: the generator reads the seed's EXISTING `description` column,
  whose window phrasing is corrected in this MR, rather than a new `column_definition` column
  beside it. THE PREMISE PUT TO HIM: the seed's own description declares the catalogue
  "window-free — the window and any null policy are applied where the metric is computed, never
  here", while 48 of its 80 `description` values say "in the form window". The field contradicts
  its own contract. This reversed the "no change to the existing description field" line in the
  approved plan, which is why it was put to him rather than decided.

  CPO, 2026-08-24, on generator scope: it emits a block for EVERY catalogue metric, all 76, not
  only the 58 whose columns are blank everywhere. THE PREMISE PUT TO HIM: restricting output to
  the 58 requires telling the generator which metrics to skip, and a hand-maintained skip list is
  the exact anti-pattern this programme rejected when it chose a refusal over an exemption list in
  MR3. Emitting all 76 keeps the generator a pure function of the seed, so a fresh run reproduces
  the file exactly — the reproducibility property platform-reviewer required in MR3. It costs 23
  hand edits and grows the MR from 411 columns to 501. Both the cost and the alternative were
  stated; he chose all 76.

  THRESHOLD DECLARATION — NEW MECHANISM: one. `scripts/sync_metric_docs_blocks.py`, a generator
  with a `--check` mode. It follows the repo's existing shape for "a seed is the source, a derived
  file is generated, CI fails on drift" — `sync_dbt_vars.py` + `check_registry_var_sync.py` —
  collapsed into ONE script with a flag so the writing half and the checking half cannot compute
  the expected output differently. That pair's split into two files is the older pattern; one
  script is the same mechanism with one less way to drift.
  THRESHOLD DECLARATION — RECURRING COST: NONE. No CI job, no schedule, no new dependency, no
  BigQuery scan. The generator reads one CSV and writes one file.

decisions_reserved:
  - ⛔ WIRING `--check` INTO `.gitlab-ci.yml` AND `stop_gate.py` IS NOT DONE HERE. Both are
    PROTECTED paths and no agent may self-grant an edit to them; it needs a `protected_override`
    recording CPO approval plus cto-reviewer. The ask is prepared and will be put to him as two
    named one-line additions. Until then the drift check exists, is tested and is seen red, but
    runs only by hand — which is decoration, and is stated here rather than glossed.
  - The 204 names no seed defines are MR4b's. No definition is authored in this MR.
  - `league_code`'s 49 blanks stay blank. Its meaning is site-dependent and #87 is the fix at the
    ingestion end. Not re-litigated here.

done_when:
  - The seed's `description` for every emitted block is window-free, matching the contract the seed
    itself declares. Verified by searching the emitted blocks for window phrasing and finding none.
  - All 501 columns whose name matches a generated block reference that block, MEASURED from the
    raw YAML and never predicted. ⚠ The manifest CANNOT answer this: it stores the RESOLVED
    description, so a wired column is indistinguishable from an inline one.
  - ⛔ `goals_open_play` IS HAND-WIRED AND MEASURED, not left to the gate. It carries TWO different
    definitions in the catalogue — for a team the authoritative scoreline minus penalties, for a
    player total goals minus penalties — so it gets two blocks and its 3 sites are pointed by hand
    (2 team, 1 player). ⚠ ONCE two blocks are referenced under one name the gate SKIPS that name as
    ambiguous, so a fourth blank site would go undetected. Zero blank `goals_open_play` columns is
    therefore asserted from the YAML directly.
  - The 23 sites that already had text are listed individually in the evidence with their before
    and after, so the reviewer can judge information loss without re-deriving the set.
  - `git diff --numstat` over the 11 yml files shows deleted lines ONLY at those 23 sites, and the
    count matches exactly. ⚠ `git diff` normalises line endings and has hidden a CRLF→LF rewrite of
    14 files before — cross-check `--stat` against `--numstat` and confirm the file count matches.
  - The parsed manifest before and after has an identical node set and identical `depends_on`.
  - The drift check is SEEN RED before it is trusted (#904): change one seed description without
    regenerating, run `--check`, confirm it fails AND names the offending row, then restore.
  - The generator ABORTS rather than guessing when one `metric_id` carries two different
    definitions and it cannot tell them apart, and that abort is seen red.
  - The generator reports and exits non-zero when it finds no work, so a broken read can never
    pass green (the `declare_missing_columns.py` precedent).
  - `check_description_hygiene.py` green repo-wide, read from its OUTPUT and not its exit code.
  - `dbt parse` clean, every `{{ doc() }}` resolves, and ZERO unrendered `{{ doc(` survives into
    the manifest.
  - The longest rendered description is measured and stated, against BigQuery's 1,024-char cap.
  - `python -m pytest tests/` at its measured baseline of 941 passed / 1 skipped, plus the new
    tests, each new test seen red by mutation before being believed.
  - The six offline gates pass, read from their OUTPUT.
  - Handover updated in the SAME commit as the code.

amendments:
  - >
    1. 2026-08-24, CPO APPROVAL FOR THREE SEED `description` EDITS BEYOND THE WINDOW CORRECTION.
    Asked after scope-auditor and analytics-engineer-reviewer both FAILed round 1 on it, from
    different angles. His answer: "approve all three". Recorded as the option chosen and nothing
    more.
    WHAT WAS APPROVED, each named because the original `decisions_taken` authorises only the
    window-phrasing correction and nothing else in this field:
      (a) `penalty_committed` — expanded from "Penalties committed." to record that the player
          conceded them and that the provider spells the source field `penalty.commited`,
          misspelled at source.
      (b) `pass_accuracy_pct` — expanded to state accurate over attempted, SUMMED rather than
          averaged, so a heavier passing game weighs more.
      (c) `contribution_share` — the words "CPO-accepted" removed. This one is FORCED rather than
          chosen: the content gate bans decision language in a description, so leaving it fails
          the build. The substance is retained.
    ⚠ WHY (a) AND (b) EXISTED AT ALL. Both facts were carried by model-level column text that this
    MR deletes. Putting them in the seed rather than back in the yml is the design working as
    intended — if a column carried a fact the catalogue lacked, the catalogue was incomplete — but
    editing a metric definition is CPO-class whatever the motive, and I took it without asking.
    Both reviewers were right to fail it.
    ⚠ AND A FALSE CLAIM OF MINE, corrected in `acceptance_evidence.md` rather than left standing:
    that file said it had accounted for every content change and found exactly two. It had not
    audited the seed's own diff, so (c) went unrecorded.
  - >
    2. A FOURTH SEED EDIT, inside the ORIGINAL window-phrasing authority rather than this
    amendment, recorded because the MR's own verification missed it.
    `finishing_efficiency` (team) still said "window" three times — "over a fully shot-covered
    window", "numerator and denominator share the window", "when the window is not fully
    shot-covered". The generator's guard enumerated three phrasings (`form window|in the
    window|same-window`) and matched none of them, and this contract's `done_when` verified
    window-freeness by searching with THAT SAME PATTERN, so it could only ever agree with the
    guard. A too-narrow grep reported as a clean sweep, with the verification circular.
    Found by football-analytics-expert-reviewer, which also noted the block is wired to a
    season-CUMULATIVE model as well as a form-window one, so the ambiguity was live.
    FIXED BOTH WAYS: the row is reworded, and `WINDOW_PHRASING` now matches the bare word, since
    the seed declares itself window-free and there is no phrasing to enumerate. Verified by an
    independent search of the generated file for "window", not by the guard's own pattern.
  - >
    3. NOT AN AMENDMENT, recorded because it was found while reviewing this MR and is NOT fixed
    here. The CPO read the catalogue and asked why `tackles_total` exists when defensive actions
    are tackles + interceptions + blocks. The arithmetic is right — `defensive_actions` is
    `sum(tackles_total + tackles_interceptions + tackles_blocks)` — but the player metric ids carry
    the PROVIDER's JSON object name (`$.tackles.total`, `$.tackles.interceptions`,
    `$.tackles.blocks`, staged verbatim at `stg_apif__fixture_players.sql:64-66`), so
    `tackles_total` means only tackles. The team side of the same catalogue already uses our own
    vocabulary (`tackles_per_match`, `interceptions_per_match`, `blocks_per_match`). Two
    conventions, one file. Filed as GitLab #88; renaming a metric id is a naming decision and
    touches the i18n keys, the metric bindings and, since this MR, the generated docs blocks.
