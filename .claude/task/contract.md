# Task contract — #82 MR4b: close every column that needs no new definition

objective: >
  The description programme's remaining work was recorded as "204 names to author, then switch the
  rule on". Measured from the raw YAML on 2026-08-24 that is wrong twice over, and both corrections
  are the reason this MR exists.

  FIRST, the count. In scope (`3_core`, `4_intermediate`, `5_marts` — the 2026-08-21 ruling),
  **635 columns are still blank**, not 458: **196 names blank at EVERY site (417 columns)** plus
  **67 names blank at SOME sites and written at others (218 columns)**. That second group was never
  counted. It is the same column name carrying a sentence in one model and nothing in another —
  precisely the drift this programme exists to remove — and it would have surfaced as a wall of
  failures the moment MR5 switches presence on.

  SECOND, the shape. The blank-everywhere names are not independent facts. **72 of them (147
  columns) are a catalogue metric plus a standard affix** — `goals_against_sum_season`,
  `duels_won_pct_this_season`, `shots_on_goal_per_match_delta_yoy`. The metric half is already
  defined in `metric_catalogue.csv`; only the affix carries new meaning, and there are eleven
  distinct affixes in use. And of the 67 partials, **40 (104 columns) say the SAME thing at every
  site that has text**, so their definition already exists and only needs to live in one place.

  THIS MR CLOSES THE FIRST GROUP ONLY, AND AUTHORS NOTHING. **130 columns** — 127 derived columns
  wired to their entity's generated block, and 3 more that already carried text, which keeps it
  with the reference placed in front. Blank in-scope falls from **635 to 508**.
  ⚠ THIS FIGURE HAS MOVED FOUR TIMES AND EVERY MOVE IS AN AMENDMENT BELOW. 251 planned → 214
  (amendment 1: seven catalogue metrics are defined for players only, so 48 team columns have no
  definition to point at) → 110 (amendment 4: the promotion half needs a line-REPLACING mode this
  append-only tool does not have, and moves to its own MR) → 132 (amendment 5: a decomposition fix
  found by mutation testing unblocked 22 more) → **130** (amendment 6: totalling a rate is a
  different quantity, so `clean_sheets_sum_season` gets no block). The promoted columns are NOT in
  this MR at all. Everything requiring a judgement call is MR4c's: see decisions_reserved.

refs: >
  GitLab #82, the description-coverage programme (`!82`-`!89`, `!91`, `!95`, `!97`, `!98`, `!100`
  merged). Approved plan: `C:\Users\Rami\.claude\plans\serialized-enchanting-frost.md`, whose
  measured split into "work that needs no judgement" and "work that is nothing but judgement" is
  the organising rule here.
  Standard: `dbt_project/docs/engineering_standards.md` §2 — in particular "a metric's definition
  is GENERATED, never written by hand", "a column documented in more than one model gets ONE docs
  block", and "where one name carries two meanings, there are two blocks and no default".
  Branched from main `1c909ad`, clean tree, no open MRs.

scope_paths:
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - scripts/declare_missing_columns.py
  - tests/test_declare_missing_columns.py
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
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

# ⚠ THE 11 YML PATHS ARE LISTED ONE BY ONE, not globbed, so an edit to any other model file is
# still caught by the gate. They are exactly the files holding the 251 columns, computed from the
# YAML rather than guessed. ⚠ `dbt_project/seeds/metric_catalogue.csv` is DELIBERATELY ABSENT: it
# is CPO-governed and this MR reads it without changing a character.

impact_map: >
  writers: NONE. No SQL changes. No model computes anything differently, no column is added,
    renamed or removed. The diff adds `description:` lines under existing `- name:` entries,
    extends one generator and its tests, adds a wiring mode to a second script, and regenerates
    one `.md` file. Two sites REVERT from a reference to blank (amendment 6). The regeneration
    also REWRAPS every block, which corrects the stored text of 3 that shipped in `!98` — see
    blast_radius, and amendment 7(c) for why.

  downstream: NO lineage change. A description is not a dependency; `depends_on` is built from
    `ref()`/`source()` in the SQL and no `.sql` file is touched. Proven, not asserted: the parsed
    manifest before and after must carry an identical node set and identical `depends_on` per node.

  generator_input_change: ⚠ THE ONE REAL DESIGN CHANGE, stated plainly because a reviewer should
    attack it. `sync_metric_docs_blocks.py` is today a pure function of ONE input, the seed. This
    MR gives it a SECOND: the set of column names present in the project's model YAML, used to
    decide which derived names exist. It stays fully reproducible — both inputs are files in the
    repo, and a fresh run reproduces the output byte for byte — but "regenerate after editing the
    seed" becomes "regenerate after editing the seed OR adding a derived column". The `--check`
    now in CI is what makes that safe: forgetting either one fails the pipeline.
    THE ALTERNATIVE, REJECTED: emit every metric x every affix from the seed alone. That is 76
    metrics x 11 affixes = 836 blocks, of which 147 columns' worth are real, and BigQuery would
    carry 700-odd definitions of columns that do not exist.

  layer_rules: `check_layer_contract.py` polices per-competition staging subdirectories and the
    staging/base materialisation policy. This MR creates no model, no directory, no materialisation
    config. Run repo-wide as a `done_when` step.

  deploy_order: none, no migration. Each description reaches BigQuery the next time its model
    builds.

  blast_radius: TWO effects, and the second was missing from this section until scope-auditor
    failed it in round 3 — see amendment 7(c) and 8.
    FIRST, the intended one. `persist_docs` is on for every model, so **127 columns** that carry
    an EMPTY description in the warehouse today will carry text after the next build.
    SECOND, and OUTSIDE this MR's 130 columns: disabling hyphen-breaking in the wrapper corrects
    the stored text of **3 metric blocks that shipped in `!98`** and are wired to columns this MR
    never touches. MEASURED by rendering both versions and comparing whitespace-normalised text,
    not estimated: `deserved_points` ("within-" + "group" becomes "within-group"),
    `shots_per_match` ("off-" + "target" becomes "off-target") and `sot_points_gap` ("over-" +
    "performing." becomes "over-performing."). No other block's text changes, and no block's WORDS
    change anywhere: the same comparison found 0 blocks with identical words and different line
    breaks, because the wrapper reflows to the same points except where a hyphen was involved.
    ⚠ FIVE YAML SITES CHANGE TEXT THAT ALREADY EXISTS, and with the 3 rewrapped blocks above they
    are the only places meaning could be lost. THREE keep their own sentence with the reference
    placed IN FRONT of it, so
    nothing is dropped except one clause banned by §2 as a downstream-consumer claim; each is
    listed in the evidence with its before and after. TWO revert from a reference to BLANK
    (amendment 6), which loses no meaning because the block they pointed at was wrong.
    ⚠ NO COLUMN IS PROMOTED IN THIS MR. An earlier version of this section described 104 promoted
    columns whose inline sentence would be replaced by a reference; amendment 4 moved all of that
    to its own MR and this paragraph was not swept with it. Caught by scope-auditor in round 2,
    having already been caught once in round 1 as the same defect one section away.
    LENGTH CANNOT BREAK THE BUILD: BigQuery rejects a column description over 1,024 characters and
    the rejection fails the model. The composed strings (metric definition + affix phrase) are the
    longest this MR produces and are measured before commit; the gate measures rendered length
    independently on every run.

  gate_blast_radius: creating a block named `X` makes every blank column named `X` a finding in
    `check_description_hygiene.py`, and every column restating it a second kind of finding. That
    gate runs in CI and at turn end, so generating and wiring MUST land in one commit. It is also
    what proves the wiring is complete by machine rather than by my claim.
    ⚠ AND THE HOLE IN THAT PROOF, which is why the split names are asserted separately below: once
    two blocks exist under one name the gate SKIPS it as ambiguous and stops policing it.

decisions_taken: >
  THRESHOLD DECLARATION — NEW MECHANISM: none. The generator, its `--check` and its tests shipped
  in `!98`; the shared-block file and the wiring pattern shipped in MR3. This MR extends one and
  reuses the other.
  THRESHOLD DECLARATION — RECURRING COST: none. No new job, no schedule, no dependency, no
  BigQuery scan. The generator reads two sets of files off disk.

  BUILDER'S CALL 1, named so a reviewer can reject it: THE AFFIX PHRASES LIVE IN THE SCRIPT, not
  in a new seed. `metric_catalogue.csv` is the source of what a METRIC means, one row per metric;
  an affix is not a metric and has no row to live in. A second seed would be a new mechanism the
  CPO has not been asked for. The affix vocabulary is closed and code-bound: a new affix only
  appears when someone adds a column shaped that way, and the script must learn it in the same
  change either way. Under the standing rule that the transformation layer decides the FORM while
  the CPO decides the NAME, phrasing "totalled over the current season" is form.

  BUILDER'S CALL 2: A NAME DERIVED FROM A SPLIT METRIC INHERITS THE SPLIT. `duels_won_pct` and
  `finishing_efficiency` are defined differently for a team and a player, so they carry `__team`
  and `__player` blocks. Six derived names (12 columns) descend from them, and each gets one block
  per entity rather than a default. Measured: all 12 sites are team-scoped
  (`int_team_profile__yoy`, `mart_team_profile`), so all 12 wire to `__team` — but they are wired
  BY HAND and asserted from the YAML, because the gate cannot see them (see gate_blast_radius).

  BUILDER'S CALL 3: THE 40 PROMOTED NAMES ARE ONLY THOSE WHOSE WRITTEN SITES ALL SAY THE SAME
  THING. Measured across the 67 partials: 40 agree, 26 disagree, 1 (`league_code`) already points
  at a block. Promoting a disagreement means picking a winner, which is authoring — so the 26 are
  MR4c's. `window_type` carries SIX variants of one sentence and `team_name` three; that is the
  evidence the split is real and not bookkeeping.

decisions_reserved:
  - ⛔⛔ SEVEN METRICS ARE DEFINED FOR PLAYERS ONLY WHILE TEAM MODELS USE THE SAME NAMES, and that
    is the CPO's to resolve, not mine. `goals`, `goals_against`, `defensive_actions`,
    `shots_on_goal`, `shots_total`, `passes_accurate` and `passes_total` each hold exactly one
    catalogue row, `entity = player` — verified by reading the seed, not inferred. Team columns
    derived from those names (**48 columns** across `int_team_profile__yoy`, `mart_team_profile`,
    `int_team_season__metrics`, `int_team_season__metrics_cumulative`,
    `mart_team_season_insights`, `int_legs__team_match`, `int_team_momentum_window`,
    `int_team_season_record`, `mart_head_to_head`) therefore have no definition to point at.
    ⚠ I WILL NOT WRITE ONE. The metric catalogue is the only source of what a metric means and it
    is his; authoring a team definition in a model's YAML is the exact drift this programme
    exists to remove. THE QUESTION FOR HIM, in one line: are these team metrics that the catalogue
    is simply missing, or are the team columns misnamed? Same family as GitLab #88, which he
    raised himself. Filed as its own issue; these 48 columns stay blank until he rules.
  - ⛔ MR4c OWNS EVERY JUDGEMENT CALL, and it is bigger than the plan said: **94 distinct facts
    that no seed defines (270 columns)** plus the **26 disagreeing partials (91 columns)** whose
    variants must be reconciled into one sentence each, plus the 5 nested `recent_meetings.*`
    fields that cannot be docs blocks at all. Nothing here pre-empts any of it.
  - `league_code`'s 23 blank columns stay blank. Its meaning is site-dependent and GitLab #87 is
    the fix at the ingestion end. Not re-litigated.
  - MR5 switches presence on. Not started, and it cannot pass until MR4c lands.
  - GitLab #88 — player metric ids carrying the provider's JSON field name — is untouched.
    Renaming a metric id would change these generated blocks, so it belongs after this.
  - Whether the affix phrases should later move to a seed of their own is a real question and is
    left open rather than decided by this MR's convenience. See BUILDER'S CALL 1.

done_when:
  - Blank in-scope columns MEASURED from the raw YAML fall from **635 to 508**. ⚠ The manifest
    CANNOT answer this: it stores the RESOLVED description, so a wired column is
    indistinguishable from an inline one.
  - All 130 wireable derived columns reference their entity's block — 127 wired by the script and
    3 that already carried text keeping it behind the reference; **0 blank, 0 inline** within that
    set, asserted from the YAML.
  - Every column the generator REFUSES a block for is named in its output on every run, and
    confirmed still blank in the YAML rather than quietly given a neighbouring definition.
  - ⛔ EVERY DERIVED BLOCK IS ENTITY-SUFFIXED, so the gate treats every one of those names as
    ambiguous and stops policing them entirely. Their coverage is therefore asserted from the YAML
    directly, name by name, and the fact that the gate is blind here is stated in the evidence
    rather than discovered later.
  - ⛔ THE MODEL_ENTITY TABLE IS CHECKED ENTRY BY ENTRY against each model's own SQL header, and
    the entries whose model name does not state the entity carry the quote. A wrong entry attaches
    the wrong definition and nothing downstream can see it.
  - Every decomposition is READ AND RECORDED, all 76, because a wrong one silently attaches the
    wrong definition — which is exactly what happened and is amendment 1. Longest-affix-first
    verified against `duels_won_pct_this_season`, which a naive stripper reads as `duels_won` +
    `_pct`, and against `goals_against_per_match_this_season`, whose stem is not a metric.
  - The 48 columns blocked on the catalogue are LISTED, and each is confirmed still blank rather
    than quietly given a neighbouring definition.
  - The 3 sites that keep their own sentence are listed in the evidence with before and after, so
    information loss is judged rather than assumed. Anything dropped is named and justified.
  - The generated file reproduces byte for byte from a fresh run, and `--check` is SEEN RED before
    it is trusted (#904) — one seed edit and one added derived column, each seen to fail and name
    the block, then restored.
  - ⛔ SEEN GREEN ON THE BYTES CI CHECKS OUT, not this machine's. `git show <ref>:<path>` gives the
    stored LF blobs; a CRLF-only pass proved nothing on `!98` and made CI red.
  - `git diff --numstat` over the model ymls shows **130 added and exactly 3 deleted**, and every
    deletion is named: the old `description:` line at `goals_delta_yoy` and `goals_prev_season_full`
    in `int_player_profile.yml`, and at `points_won_sum_season` in `int_team_season.yml` — the
    three sites that keep their sentence behind a reference. ⚠ The two `clean_sheets_sum_season`
    reverts do NOT appear as deletions, because those lines never existed on main: they were added
    by this branch and removed again, so the diff against main is silent about them. Confirm them
    from the YAML instead. ⚠ `git diff` also NORMALISES line endings and has hidden a whole-file
    CRLF→LF rewrite in this programme — cross-check the CRLF/LF byte counts directly.
  - `dbt parse` clean, every `{{ doc() }}` resolves, ZERO unrendered `{{ doc(` in the manifest, and
    the manifest's node set and `depends_on` identical before and after.
  - The longest rendered description is measured and stated against BigQuery's 1,024-char cap.
  - `check_description_hygiene.py` green repo-wide, read from its OUTPUT and not its exit code.
  - `python -m pytest tests/` at a baseline MEASURED on this branch, never quoted from a previous
    MR's log — one such quote was already stale. Measured: **977 collected with the diff stashed,
    993 with it applied**, the 16 being this MR's new tests; run result 992 passed, 1 skipped.
  - Every new test seen RED by mutation before it is believed.
  - Six offline gates green plus `ruff check . --config .ruff-ci.toml`, which is a separate CI job
    and NOT one of the gates.
  - Handover updated in the SAME commit, under the 16,000-CHARACTER cap measured with Python
    `len()`.

amendments:
  - >
    1. 2026-08-24, DURING IMPLEMENTATION, AND IT IS THE FINDING OF THIS MR. Composing the first
    generated blocks and READING them showed `goals_against_sum_season` — a column that exists only
    on TEAM models — carrying the catalogue's `goals_against`, which the catalogue defines for a
    PLAYER: "goals conceded by the team while the player was on the pitch (GK-relevant)".
    **21 of 76 derived names had that shape.** A fifth of them would have carried a player's
    definition into a team column, into the warehouse, silently. No check in this repo would have
    caught it: the block resolves, the length is fine, the YAML parses, `dbt parse` is clean.
    ⚠ THE OBVIOUS FIX WAS THE WRONG ONE. Teaching the generator which models are team-scoped is the
    classifier this repo has already failed at three times (`active_work.md`: "NO CLASSIFIER
    WORKS"). A fourth attempt, written to measure the damage, left two of twelve models unresolved.
    FIXED BY MAKING IT UNABLE TO BE WRONG, not cleverer: EVERY derived block is now emitted with an
    entity suffix, whether or not the stem is split. A metric the catalogue never defined for the
    entity a column belongs to therefore has NO block to point at, so the column stays blank and
    visible to the coverage gate instead of documented and wrong.
    ⚠ THE COST, stated rather than buried: **48 columns cannot be closed by this MR** — see
    decisions_reserved. The scope drops from 251 columns to **214**.
  - >
    2. 2026-08-24, SCOPE: `scripts/declare_missing_columns.py` and its tests added to scope_paths,
    caught by the contract gate at the first edit rather than by me. The wiring needs a mode that
    maps a column to `<name>__<entity>` rather than to a block of its own name, and it goes in the
    script that already owns line-level YAML editing, line-ending preservation, append-only
    verification and the atomic write. A second script re-implementing those is the duplication
    platform-reviewer hunts for. It carries the hand-decided `MODEL_ENTITY` table, each entry
    checkable against the model's own SQL header.
  - >
    4. 2026-08-24, THE PROMOTION HALF IS SPLIT OFF INTO ITS OWN MR, and this is a builder's call
    that scales the work down, so it is stated plainly rather than presented as a plan detail.
    The 37 promotable names touch **146 sites, of which only 99 are blank**. Wiring the blanks
    alone would leave the other 47 carrying an inline copy of the very sentence the block now
    holds — two sources again, and `check_description_hygiene.py`'s shared-block rule fails on
    exactly that, so a half-promotion does not even build. Doing it properly needs a mode that
    REPLACES an existing description line, which `declare_missing_columns.py` does not have and
    was deliberately built not to have: it is append-only, and `_verify` asserts zero deletions
    before anything reaches disk. Adding a rewrite path is a real change to the one tool trusted
    to edit these files by line, and folding it into an MR that has already rewritten the
    generator would make both harder to review than either alone. So: this MR ships the generated
    half, MR4b-2 ships the promotion with the replace mode and its own mutation tests.
    ⚠ SCOPE THEREFORE DROPS AGAIN, from 214 columns to **110**, and blank in-scope from 635 to
    **528** rather than 424. The remaining 104 are not lost, they are the next MR's, and the
    numbers in `done_when` are corrected to what was actually measured after the change.
  - >
    5. 2026-08-24, MUTATION TESTING CHANGED THE DESIGN, TWICE, AND DELETED A GUARD. Seven
    mutations were run against the new code; four were killed by the test aimed at them and
    **three survived, each exposing a real defect**:
      (a) REVERSING THE AFFIX ORDER changed nothing, because `_decompose` tries every affix and
          only accepts a stem that is a real metric — so ordering is irrelevant unless TWO
          decompositions are valid, and the test asserting "longest affix first" could not fail.
          Worse, the RULE was wrong: `goals_per_match_this_season` decomposes as `goals` + "per
          match, this season" or as `goals_per_match` + "this season", and longest-affix-first
          picks the FIRST — composing a sentence while silently dropping the null policy the
          catalogue wrote for that rate. Changed to LONGEST STEM WINS, i.e. the most specific
          metric. ⭐ THIS IS ALSO WHY THE COUNT WENT UP: 22 further columns became wireable,
          because they now resolve to a team-scoped rate metric instead of a player-only count.
      (b) DELETING THE DOTTED-NAME FILTER changed nothing: a dotted name cannot decompose at all,
          since the dot always lands in the stem and no metric id contains one. Dead guard, and
          a test that could not fail. Replaced with a check on the EMITTED names, which is
          reachable the moment anyone adds an affix containing a dot — and that check dies to its
          own mutation.
      (c) DELETING A SAME-ENTITY-DISAGREEMENT GUARD changed nothing: `_blocks()` runs first and
          already aborts on it. The guard was unreachable and its test was in fact exercising the
          older one. Both DELETED rather than kept as decoration.
    ⚠ And a fourth, found by a test on its first run rather than by mutation: four entries in
    `MODEL_ENTITY` named models that do not exist, carried over from a scratch script without
    checking. Removed.
  - >
    6. 2026-08-24, ROUND 1: THREE FAILS, ALL REAL, NONE FOUND BY ME.
    (a) analytics-engineer-reviewer FAIL — **a composed sentence that contradicted itself.**
    `clean_sheets` is defined in the catalogue as the RATIO of clean-sheet games to games played,
    and its text carries that ratio's display convention, "shown as a count of games played (e.g.
    3/5)". The column `clean_sheets_sum_season` is the raw count. Composed, the block asserted in
    one breath that the value is a small fraction AND a season total. It read fluently, resolved,
    fitted the length cap and parsed. FIXED AS A CLASS, not a case: an affix that TOTALS is now
    refused on any metric with a `denominator_expr` — the catalogue's own marker of a rate.
    Exactly one name is affected today; the rule is what stops the next.
    ⚠ AND A SECOND DEFECT INSIDE THE FIX: with no block at all, the wiring tool could not see the
    column either — it reads "no candidate block" as "not a derived name" — so the refusal was
    silently invisible. The generator now REPORTS its refusals on every run, `--check` included.
    (b) football-analytics-expert-reviewer FAIL — **a false NULL claim on four player columns.**
    The `_delta_yoy` phrase said NULL could arise from "a gap in statistical coverage". True for a
    team; IMPOSSIBLE for a player, because a player's null per-match stat MEANS ZERO, so a running
    sum never goes null for coverage — and `int_player_profile__yoy.sql` names only the absent
    prior season at that club. This is the same failure the generator's own docstring warns about:
    prose inherited without reading the model beneath it. FIXED with entity-specific phrasing,
    plus a guard that refuses an entity with no phrase rather than letting it take another's.
    ⚠ THIS REVIEWER WAS ROUTED BY JUDGEMENT, NOT BY PATH — its trigger is the seed, which this MR
    never touches. Routing it anyway is what caught this.
    (c) scope-auditor FAIL — the contract's own `objective:` still described the pre-amendment MR.
    Corrected above, with every move of the figure now traceable.
    platform-reviewer PASSed, disclosing that it had no execution tools and had traced the code by
    hand instead. It independently re-derived all three mutation claims and ran a fourth of its
    own rather than believing the write-up.
  - >
    7. 2026-08-24, ROUND 2: TWO MORE FAILS, and both are my round-1 FIXES being wrong in a new way.
    (a) football-analytics-expert-reviewer FAIL — **the fix to a false claim dropped a true one.**
    The player `_delta_yoy` sentence I wrote in amendment 6 is accurate inside
    `int_player_profile__yoy`, which is domestic-league-only at the row level. But the block is
    REUSED at `mart_player_profile`, where the domestic-only yoy rows are left-joined onto a mart
    carrying every competition-season a player has. A cup or international-tournament row is NULL
    there for a reason the sentence never names: that competition carries no year-on-year
    comparison at all. The team sentence kept exactly this cause; removing the false coverage cause
    from the player side took a true one with it. ⚠ THE MIRROR IMAGE OF THE ORIGINAL DEFECT — first
    a cause wrongly added, then a cause wrongly removed — and the reason is the same both times:
    I read one model and wrote a sentence that is attached to two. A shared block is only as true
    as its WIDEST call site. FIXED by naming the non-domestic case in the player sentence, with the
    test extended to pin it.
    (b) scope-auditor FAIL — **I corrected the headline and left the same stale claim in two other
    sections.** `impact_map`'s blast_radius and two `done_when` bullets still described 104 promoted
    columns and deletions at 104 promoted sites, in an MR that promotes nothing. This is the repo's
    named failure "corrections replace, never accumulate ... and must replace EVERYWHERE", and it
    happened INSIDE the round that flagged it: round 1 caught the objective, I fixed the objective
    and nothing else. FIXED by sweeping the whole file for the concept rather than the sentence,
    and the deletion accounting is now stated by name — including that the two reverted
    `clean_sheets_sum_season` sites do NOT appear as deletions at all, because those lines never
    existed on main.
    analytics-engineer-reviewer PASSed round 2, having independently enumerated all 16 `_sum_season`
    stems rather than trusting the "exactly one affected" claim. platform-reviewer PASSed, again
    disclosing it had no execution tools, and traced all three mutations symbolically instead.
    (c) FOUND WHILE FIXING (a), BY THE TEST FAILING FOR THE WRONG REASON: `textwrap.wrap` defaults
    to `break_on_hyphens=True` and split "year-on-year" into "year-on-" / "year". This text is not
    laid out for a reader of the file — `persist_docs` pushes it into the warehouse, where the
    newline collapses and the term renders with a space inside it. **FIVE such breaks were already
    live on main from `!98`** ("on-target, off-" / "target", "a within-" / "group table"), so this
    fixes those too: same generated file, same one-parameter cause, and leaving five mangled while
    fixing eight identical ones would be arbitrary. Zero remain, pinned by a test on the shipped
    file and by a synthetic one — whose FIRST version survived the mutation, because at width 95
    the wrapper never happened to choose that hyphen. Rewritten with a token that leaves it no
    other break point.
  - >
    8. 2026-08-24, ROUND 3: scope-auditor FAIL, THE SAME CLASS FOR THE THIRD TIME, and the third
    time it is right. My own round-3 fix — disabling hyphen-breaking in the wrapper — changes the
    stored text of blocks OUTSIDE this MR's 130 columns, and I disclosed it in an amendment while
    leaving `impact_map` still saying "ONE intended effect" and "ONLY FIVE SITES". Its words:
    "disclosed in an amendment is not the same as reflected in the impact map that a reviewer is
    told to trust for blast radius."
    ⚠ THE PATTERN, stated because three instances is no longer an accident: round 1 it was the
    objective, round 2 the blast_radius and done_when, round 3 the blast_radius again for a
    different reason. Each time I corrected exactly what was named. The repo already has a rule for
    this — "corrections replace, never accumulate, and must replace EVERYWHERE" — and reading it
    did not stop me doing it three times in one MR.
    FIXED, and this time MEASURED rather than described: both versions of the generated file were
    rendered and compared whitespace-normalised, which gives 3 affected blocks by name and proves
    no other block's text moves at all. `writers:` and `blast_radius` both now carry it.
    ⚠ The measurement also corrected my own count: I had told two reviewers "five pre-existing
    breaks" from counting LINES ending in a hyphen. Three BLOCKS are affected; some breaks shared
    a block and one was a standalone minus sign in a formula.
    ⭐ football-analytics-expert-reviewer PASSed round 3, noting one non-blocking imprecision: the
    player sentence illustrated non-domestic competitions as "a cup or an international tournament"
    while a QUALIFYING campaign is naturally neither, and six active competitions are qualifiers.
    It judged the governing clause independently complete and declined to fail on it. Taken anyway
    — the wording now names a qualifying campaign — because a cheap fix offered by the reviewer who
    owns the domain is not a thing to leave for later.
  - >
    3. 2026-08-24, A NAME WITH A DOT CANNOT BE A DOCS BLOCK. Five columns are nested fields spelled
    `recent_meetings.goals_against`; one is catalogue-derived. Both this repo's block parsers match
    `\w+`, so such a block would be unaddressable — and the drift reporter would not even list it
    as missing, because its own regex skips the dot: a defect invisible to the tool that exists to
    report defects. Excluded explicitly, and the `recent_meetings.` affix removed rather than left
    as dead configuration.
