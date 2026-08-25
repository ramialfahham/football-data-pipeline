# Task contract — #82 MR4b-2: promote the definitions that already exist

objective: >
  **31 column names** already carry a definition somewhere in the project and nothing anywhere
  else. Measured from the raw YAML on `fa61b46`: **123 sites**, of which **92 are blank** and **31
  carry the sentence** — and all sites of a given name say the same thing byte for byte, so there
  is no choosing to be done. This MR moves each sentence into ONE docs block and points every site
  at it, so the name is defined once instead of once per model.

  **It authors nothing.** Every block's body is the sentence those columns already carry, copied
  verbatim. That is the whole reviewable claim, and it is checked by machine: the text the block
  resolves to must equal the text it replaced.

  Blank in-scope columns fall from **508 to 422**.

  ⚠ EVERY FIGURE ABOVE IS THE POST-REVIEW ONE. The MR was planned at 37 names / 146 sites / 508 to
  409, and **six names were pulled across two rounds**: a sentence true where it was written can be
  FALSE at a blank site it is then pointed at, and the machine check cannot see that. Amendments 3
  and 4 name all six and why. The planned figures survive nowhere else in this contract.

refs: >
  GitLab #82, the description-coverage programme (`!82`-`!89`, `!91`, `!95`, `!97`, `!98`, `!100`,
  `!101` merged). Approved plan: `C:\Users\Rami\.claude\plans\serialized-enchanting-frost.md`.
  Standard: `dbt_project/docs/engineering_standards.md` §2 Form — "a column documented in more than
  one model gets ONE docs block, referenced from each. Do not restate it — restated definitions
  drift apart, which is how `league_code` came to be documented 76 times in 22 different wordings."
  This MR is that rule applied to the 31 names where it is currently broken AND where the sentence
  is true at every model it would reach.
  Branched from main `fa61b46`, clean tree, no open MRs.

scope_paths:
  - scripts/declare_missing_columns.py
  - tests/test_declare_missing_columns.py
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
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

# ⚠ THE YML PATHS ARE LISTED ONE BY ONE, not globbed, so an edit to any other model file is still
# caught by the gate. ⚠ STAGING AND BASE ARE IN THIS LIST and that is NOT a coverage decision: the
# gate's shared-block rule has no layer filter, so creating a block makes a blank column of that
# name a finding in EVERY layer. See impact_map. ⚠ `metric_catalogue.csv` is absent: untouched.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: NONE. No SQL changes, no model computes anything differently, no column added, renamed
    or removed. The diff appends 31 docs blocks, adds a `description:` line under 92 existing
    `- name:` entries, REPLACES the `description:` value at 31 more, and extends one script and its
    tests.

  downstream: NO lineage change. A description is not a dependency; `depends_on` is built from
    `ref()`/`source()` in the SQL and no `.sql` file is touched. Proven, not asserted: the parsed
    manifest before and after must carry an identical node set and identical `depends_on` per node.

  ⛔ WHY THIS CANNOT SHIP IN HALVES, and it is the reason staging and base are in scope.
    `check_description_hygiene.py`'s `_shared_block_coverage` walks EVERY model yml with no layer
    filter. The moment a block named `X` exists, every blank column named `X` is a finding and
    every column restating it inline is a different finding. So creating the blocks, wiring the
    blanks and replacing the written sites are ONE commit or the gate fails. Same constraint the
    generated-metric MR ran under; the mechanism working as designed, not scope creep.

  ⛔ THE GUARD BEING CHANGED, stated plainly because it is load-bearing.
    `declare_missing_columns.py` is APPEND-ONLY BY CONTRACT — its docstring says so and `_verify`
    rejects any diff carrying a non-insert opcode. A promotion is not an insert. The guard is
    NARROWED rather than loosened: in the new mode a `replace` opcode is allowed ONLY on a line the
    plan named, every other opcode must still be `equal` or `insert`, the parsed result must still
    equal the old file plus exactly the intended change, AND a check the append-only mode has no
    need for is added — THE TEXT THE BLOCK RESOLVES TO MUST EQUAL THE TEXT IT REPLACED, whitespace
    normalised. That is what makes "promoted, not rewritten" a fact rather than a claim.
    ⚠ The script's stated contract moves from "only adds" to "only adds, or substitutes text that
    means the same thing". Reviewers should attack that; the alternative was a second script
    duplicating the line-ending preservation, the atomic write and the append-only proof.

  layer_rules: `check_layer_contract.py` polices per-competition staging subdirectories and the
    staging/base materialisation policy. This MR creates no model, no directory, no materialisation
    config.

  deploy_order: none, no migration. Each description reaches BigQuery the next time its model
    builds.

  blast_radius: `persist_docs` is on for every model, so **92 columns** that carry an EMPTY
    description in the warehouse today will carry text after the next build. THE 31 REPLACED SITES
    ARE THE ONLY PLACE EXISTING MEANING COULD BE LOST, and the machine check above forbids it: the
    rendered result is required to be identical, so those 31 columns' warehouse text does not
    change at all. ⚠ ONE of them is FOLDED across lines and is edited BY HAND (`dim_team.team_slug`
    — the second folded site, `opponent_shots_total`, is one of the five pulled in amendment 3), so
    it gets the same before/after comparison in the evidence rather than the machine's.
    ⚠ AND THE 92 BLANKS ARE THE OTHER RISK, which review found and my proof could not: pointing an
    existing sentence at a blank column ASSUMES the sentence is true there. Every promoted block
    was re-checked against every model it reaches; SIX names failed that and were pulled, across
    two rounds — the second only after a reviewer traced the SQL rather than reading the sentence.
    LENGTH CANNOT BREAK THE BUILD: nothing gets longer. Each block's body is text that already
    passes the 1,024-character cap as an inline description, and the gate measures rendered length
    independently on every run.

decisions_taken: >
  THRESHOLD DECLARATION — NEW MECHANISM: none. `shared_columns.md`, the block pattern and the
  wiring mode all shipped in MR3; the atomic-write machinery shipped in MR2. This MR adds a mode to
  an existing script.
  THRESHOLD DECLARATION — RECURRING COST: none. No new job, schedule, dependency or BigQuery scan.

  BUILDER'S CALL 1, and the one to reject if any: THE REPLACE PATH GOES IN THE APPEND-ONLY SCRIPT.
  See impact_map. A second script would duplicate every guard that matters, which is the
  duplication platform-reviewer hunts for; this instead narrows the existing guard and adds a
  stricter one on top.

  BUILDER'S CALL 2: THE REPLACE MODE IS STRICTLY SINGLE-LINE. Measured: 30 of the 31 written sites
  are one physical line; **1** is a folded scalar (`dim_team.team_slug`). Rewriting a folded scalar
  by line is how a file gets mangled, so it is edited BY HAND and listed individually in the
  evidence — the same treatment the three kept-sentence sites got in `!101`.

  BUILDER'S CALL 3: A NAME IS PROMOTED ONLY IF ITS WRITTEN SITES AGREE **AND** THE SENTENCE IS TRUE
  AT EVERY MODEL THE BLOCK WILL REACH. The first half is machine-checked; the second is not
  machine-checkable and is a judgement recorded in the evidence per name.
  ⚠ THE SECOND HALF WAS MISSING IN ROUND 1 and cost SIX names across two rounds — amendments 3 and
  4. Agreement among the sites that already HAD the sentence says nothing about the blanks the
  block is then pointed at, which is where `is_home` was false at four models.
  ⚠ AND READING THE SENTENCE IS NOT THE CHECK. Round 2 found a seventh case my own sweep had marked
  safe: `result` claims to come from a named model, and one of its sites never reads that model.
  A PROVENANCE claim is checkable only in the SQL.
  The 26 names whose written sites DISAGREE, and the six pulled here, are all MR4c's: choosing
  between variants and rewording a sentence are both authoring.

decisions_reserved:
  - ⛔ THE 48 TEAM COLUMNS BLOCKED ON THE CATALOGUE ARE THE CPO'S and are untouched here. Seven
    metrics are `entity = player` only while team models use the same names.
  - MR4c owns every judgement call: the 134 names no seed defines, and the 26 partials whose
    written sites disagree and must be reconciled into one sentence each.
  - MR5 switches presence on. It cannot pass until MR4c lands.
  - The 5 nested `recent_meetings.*` fields cannot be docs blocks at all (a name with a dot is not
    addressable by dbt) and must be written inline whenever they are done.

done_when:
  - Blank in-scope columns MEASURED from the raw YAML fall from **508 to 422**. ⚠ The manifest
    CANNOT answer this: it stores the RESOLVED description, so a wired column is indistinguishable
    from an inline one.
  - All 123 sites of the 31 names reference their block: **0 blank, 0 inline**, asserted from the
    YAML across ALL layers, not only the three in scope for authoring.
  - ⛔ EVERY ONE OF THE 31 REPLACED SITES IS COMPARED BEFORE AND AFTER and the resolved text is
    identical to what it replaced. Machine-checked for the 30; the 1 folded site done by hand goes
    through the same comparison rather than my word.
  - ⛔ EVERY PROMOTED BLOCK IS CHECKED AGAINST EVERY MODEL IT REACHES **BY READING THAT MODEL'S
    SQL**, not only the ones that already carried the sentence and not by reading the sentence. It
    cannot be machine-made, so the judgement is recorded per name. Round 1 found this check missing
    entirely; round 2 found that doing it by reading the prose still missed a provenance claim.
  - `git diff --numstat` over the model ymls shows **319 added and exactly 39 deleted**, and the 39
    decompose by construction: **30** one-for-one line swaps by the script, plus **9** from
    `team_slug`'s folded scalar collapsing to one line. No other file carries a deletion.
    ⚠ THE DELETION COUNT IS NOT THE SITE COUNT, and reasoning from the site count got it wrong
    once: only the script's swaps are one-for-one, while a folded scalar replaces many lines with
    one. Measure it. ⚠ `git diff` also NORMALISES line endings and has hidden a whole-file CRLF→LF
    rewrite in this programme — cross-check the CRLF/LF byte counts directly.
  - `dbt parse` clean, every `{{ doc() }}` resolves, ZERO unrendered `{{ doc(` in the manifest, and
    the manifest's node set and `depends_on` identical before and after.
  - `check_description_hygiene.py` green repo-wide, read from its OUTPUT and not its exit code.
  - The new guard is SEEN RED before it is trusted (#904): a replacement whose text differs from
    what it replaced must be refused, and a `replace` opcode on an unplanned line must be refused.
  - Every new test seen RED by mutation before it is believed. ⚠ Four of my own tests could not
    fail in `!101`; when a mutation SURVIVES, ask whether the guard is reachable and whether the
    rule is right, not only whether the assertion is strong enough.
  - `python -m pytest tests/` at a baseline MEASURED on this branch (collection with the diff
    stashed and applied), never quoted from a previous MR's log.
  - Six offline gates green plus `ruff check . --config .ruff-ci.toml`, a separate CI job.
  - Handover updated in the SAME commit, under the 16,000-CHARACTER cap measured with Python
    `len()`.

amendments:
  - >
    4. 2026-08-25, ROUND 2: A SIXTH NAME, IN ONE MY OWN SWEEP HAD MARKED SAFE.
    analytics-engineer-reviewer FAIL. `result`'s sentence says "W/D/L from `int_legs__team_match`
    for finished rows" — a claim about PROVENANCE, not just about the value. Four of its five sites
    trace there correctly. The fifth, `mart_player_match_log`, never references that model at all:
    `mart_player_match_log.sql:136-140` recomputes the value itself from `fct_fixture` with a
    `case when goals_for > goals_against` expression. Verified independently before acting —
    `grep -c int_legs__team_match` on that model returns 0.
    ⛔ THE LESSON, and it is about my round-1 fix rather than the original defect. I swept the class
    by shortlisting blocks whose TEXT carried a scope word or named a model, then READING the
    sentence against the model list. That is why `result` survived: its sentence reads perfectly
    well at a match-log model, and only the SQL shows the provenance is wrong.
    **A PROVENANCE CLAIM IS CHECKABLE ONLY IN THE SQL. Reading the sentence is not the check.**
    `result` is pulled, bringing the total to six. `team_slug` — the other block naming a source
    model — was then verified the same way: its claim is about where the value is DERIVED, which
    holds wherever it flows, so it stays.
    ⚠ platform-reviewer PASSed and flagged a stale figure in a CODE COMMENT ("41 promotable written
    sites, 39 are one line") as non-blocking. Fixed rather than accepted: that is the exact class
    scope-auditor failed three times, and it slipped through in the same round that recorded it.
    ⚠ scope-auditor PASSed, having independently reconciled the arithmetic including a step I had
    not written down — 6 of the filled sites are in staging/base, which sit outside the in-scope
    count, so 508 minus 90 is 418. That number has since moved again with `result` pulled.
  - >
    3. 2026-08-25, ROUND 1: THREE FAILS, AND THE FIRST IS THE LESSON I WROTE INTO MEMORY AN HOUR
    EARLIER AND THEN BROKE.
    (a) analytics-engineer-reviewer FAIL — **`is_home` is FALSE at four of the models it was newly
    wired to.** Its sentence, "true when team_sk is the home side of the UPCOMING fixture", is
    correct at the four momentum models where it was already written and grained on
    `upcoming_fixture_sk`. This MR pointed it at `mart_team_fixture_stats`,
    `mart_player_fixture_stats`, `mart_player_match_log` and `mart_team_fixtures`, every one of
    them grained on a FINISHED or arbitrary fixture.
    ⛔ THE HOLE IN MY OWN PROOF, which is the real finding. The machine check compares a block's
    text with the text it REPLACED, so it proves nothing was rewritten at the sites that already
    had a sentence (32 as this amendment was written, superseded by amendment 4's 31). It says
    nothing about whether that sentence is TRUE at the blank sites it is then pointed at — and
    BUILDER'S CALL 3 measured only agreement among the written sites. "A shared block is only as true as its widest call site" is a rule I recorded in the
    previous MR and did not apply to this one.
    SWEPT AS A CLASS, not as one name: every promoted block was re-checked for a scope-specific
    claim (a tense, a grain word, a named model) against every model it reaches. FOUR MORE were
    found the reviewer had not named — `opponent_shots_total` says "cumulative ... through this
    match" while `int_legs__team_match.sql:124` holds the per-match value and only
    `int_team_season_record.sql:134` sums it; and `games_with_opp_stats`,
    `games_with_player_stats` and `goals_against_in_save_games` all say "window legs" while
    reaching `int_team_season_record`, whose own header calls itself the complement of the
    five-match window. ALL FIVE ARE PULLED from this MR — and amendment 4 pulls a sixth, so every
    figure in this amendment (32 written sites, 96 blanks) is superseded there. Rewording them is
    authoring, so they
    belong to MR4c.
    (b) platform-reviewer FAIL — the `all()` in the replace guard was untested. Every test replaced
    ONE isolated line, where `all` and `any` are identical, so a mutation weakening it to "at least
    one planned line in the opcode" survived the whole suite and would let an unplanned line ride
    along inside a legitimate swap. Found by READING, not running; it had no execution tools.
    Fixed with a test that makes two adjacent lines change together so difflib emits one multi-line
    replace, and it kills the mutation.
    (c) scope-auditor FAIL — the script's own docstring still said "APPEND-ONLY, AND THAT IS THE
    WHOLE POINT ... the acceptance test is simply that the diff has zero deleted lines", in the MR
    that adds a replacing mode. I had flagged the tension in this contract and fixed it only here,
    leaving the artifact whose contract it is stating the old invariant. **Fourth instance of that
    class in two MRs.** Fixed in the docstring, and the rest of the file swept for the same claim.
  - >
    1. 2026-08-25, DURING IMPLEMENTATION, from mutation testing: THE WRITER ASSUMED A DESCRIPTION
    IS ALWAYS THE LINE IMMEDIATELY AFTER `- name:`. Mutation P4 — deleting that assumption's guard
    — left all 40 tests green, so the assumption had no test. Chasing why then showed the
    assumption is also WRONG: `- name:` / `tests:` / `description:` is legal YAML and this repo
    already uses that ordering elsewhere, and the assuming version would have aborted the whole
    FILE for it rather than skipping one site. REDESIGNED to search the column's own lines for the
    exact line the plan read, which is both safer (it cannot hit a different line) and more
    permissive. ⭐ SECOND TIME IN TWO MRs that a surviving mutation meant the RULE was wrong rather
    than the assertion weak. That is now the standing question to ask when one survives.
  - >
    2. 2026-08-25, ALSO FROM RUNNING IT: THE PLAN SEARCHED THE WHOLE FILE FOR THE LINE, and a
    description is only unique WITHIN its model. `is_home` carries the same sentence under five
    models of `shared.yml`, so a whole-file search returned five candidates and the mode skipped
    all five as unidentifiable — reported honestly, but five sites it should have promoted. Fixed
    by scoping the search to the model's own block, which also removed a duplicated copy of the
    block-range logic: `_model_block` is now one function used by both the planner and the writer.
    Promotable sites went from 34 to 39, leaving exactly the 2 folded scalars for a human.
    ⚠ THOSE ARE THE FIGURES AS THEY STOOD AT THIS AMENDMENT, before amendments 3 and 4 pulled six
    names. The final state is 30 script promotions and 1 folded site; see the objective and
    done_when.
