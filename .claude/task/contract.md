# Task contract — #82 MR4c: write the definitions that do not exist yet

objective: >
  Every merge in this programme so far MOVED text that already existed — generated from the metric
  seed, or promoted from one model to a shared block. **This one authors it.** 422 in-scope columns
  are blank and no sentence exists anywhere to copy, so each one is a judgement about what the
  column actually holds, written from the SQL that produces it.

  **56 column names, 99 in-scope columns.** 22 names appear in more than one model and get ONE
  shared block each (67 sites wired, 2 of them in base, which is outside the in-scope count); 34
  names appear once and are written inline. Blank in-scope columns fall from **422 to 323**.

  ⚠ 21 OF THE PLAN'S NAMES ARE NOT HERE. It sized this merge at 77 names / 183 columns, and the
  measurement behind that number could not see what only a reading of the SQL shows. Each excluded
  name is listed in decisions_reserved and none is silently dropped: **13 mean different quantities
  at different sites** (`goals_for` is one match's goals in one model and a running season total in
  another), **7 belong to the head-to-head and opponent-mirror families** the plan defers, and **1
  is a catalogue metric under another column name**. 77 − 13 − 7 − 1 = 56 names;
  183 − 71 − 11 − 2 = 99 columns. Writing one sentence for a name that means two things is the
  exact defect that pulled six names from the previous merge.

refs: >
  GitLab #82, the description-coverage programme (`!82`-`!89`, `!91`, `!95`, `!97`, `!98`, `!100`,
  `!101`, `!102` merged). Approved plan:
  `C:\Users\Rami\.claude\plans\serialized-enchanting-frost.md`.
  Standard: `dbt_project/docs/engineering_standards.md` §2 — written for a stranger querying the
  table, no thin filler, no downstream-consumer claims, and a column documented in more than one
  model gets ONE docs block referenced from each.
  Branched from main `bf0e23c`, clean tree, no open MRs.

scope_paths:
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/team/int_team_market_value.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/schema.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ THE YML PATHS ARE LISTED ONE BY ONE, not globbed, so an edit to any other model file is still
# caught by the gate. ⚠ `base.yml` is in the list and that is NOT a coverage decision: the gate's
# shared-block rule has no layer filter, so creating a block makes a blank column of that name a
# finding in EVERY layer. See impact_map. ⚠ `seeds/schema.yml` carries the ONE deletion in this
# MR — see decisions_taken, BUILDER'S CALL 3. ⚠ NO SCRIPT IS TOUCHED: this MR adds no mechanism
# and changes none, so `scripts/` and `tests/` are deliberately absent.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: NONE. No SQL changes, no model computes anything differently, no column added, renamed
    or removed. The diff appends 22 docs blocks, adds a `description:` line under 67 existing
    `- name:` entries as a `{{ doc() }}` reference and under 34 more as inline text, and replaces
    ONE line in the seed schema.

  downstream: NO lineage change. A description is not a dependency; `depends_on` is built from
    `ref()`/`source()` in the SQL and no `.sql` file is touched. Proven, not asserted: the parsed
    manifest before and after must carry an identical node set and identical `depends_on` per node.

  ⛔ WHY THIS CANNOT SHIP IN HALVES, and it is the reason base.yml is in scope.
    `check_description_hygiene.py`'s `_shared_block_coverage` walks EVERY model yml with no layer
    filter. The moment a block named `X` exists, every blank column named `X` is a finding and
    every column restating it inline is a different finding. So creating the blocks and wiring
    every site of those names are ONE commit or the gate fails. Same constraint the previous three
    merges ran under; the mechanism working as designed, not scope creep.

  ⛔ THE RISK THIS MR CARRIES, stated plainly, because it is different from every merge before it.
    Those moved text whose truth had already been established somewhere. This one writes 56 new
    claims about what a column holds, and **nothing in the repo can check a claim about meaning.**
    `dbt parse`, the hygiene gate and the length cap all pass on a sentence that is confidently
    wrong. The only control is that every sentence was written from the SQL at every model the
    text reaches, and that trace is recorded per name in the evidence for a reviewer to re-walk.

  layer_rules: `check_layer_contract.py` polices per-competition staging subdirectories and the
    staging/base materialisation policy. This MR creates no model, no directory, no materialisation
    config.

  deploy_order: none, no migration. Each description reaches BigQuery the next time its model
    builds.

  blast_radius: `persist_docs` is on for every model and seed, so **99 in-scope columns plus 2 in
    base** that carry an EMPTY description in the warehouse today will carry text after the next
    build, and one seed column's text is replaced by an identical rendering of itself. Nothing that
    currently has meaning loses it: 101 of the 102 sites touched are blank today, and the 102nd is
    the seed's, whose rendered text is unchanged. So the worst case here is a wrong new sentence,
    never a lost right one. LENGTH CANNOT BREAK THE BUILD — the longest
    rendered description is measured against the 1,024-character cap that fails the model, and the
    gate measures rendered length independently on every run.

decisions_taken: >
  THRESHOLD DECLARATION — NEW MECHANISM: none. `shared_columns.md`, the block pattern and
  `--wire-shared-docs` all shipped in MR3. No script is added or changed.
  THRESHOLD DECLARATION — RECURRING COST: none. No new job, schedule, dependency or BigQuery scan.

  BUILDER'S CALL 1, and the one to reject if any: A NAME THAT MEANS TWO QUANTITIES GETS NO
  SENTENCE HERE. 13 of the plan's names carry a per-match value at one site and a running or
  windowed total at another — `goals_for` is `f.goals_home` in `int_legs__team_match` and
  `sum(goals_for) over w` in `int_team_season_record`. One block cannot be true at both, and the
  honest fix is either two blocks or per-site text, which is the grain question the next merge
  exists to settle. They stay blank rather than take a sentence that is right in one model and
  wrong in another. Measured, not eyeballed: every site of every candidate was classified by what
  its model's own SQL does with the column.

  BUILDER'S CALL 2: A NAME AT ONE SITE IS WRITTEN INLINE, A NAME AT TWO OR MORE GETS A BLOCK.
  That is the standard's rule applied literally. It is also why the diff is 22 blocks and not 56:
  a block for a single-site column buys nothing and adds a level of indirection to read through.

  BUILDER'S CALL 3: THE SEED'S `prompt_version` IS POINTED AT THE BLOCK, WHICH COSTS ONE DELETED
  LINE. Its definition already existed in `seeds/schema.yml` and nowhere else, so the block's body
  is that sentence copied verbatim — this name is promoted, not authored. Leaving the seed's inline
  copy in place would leave the same words in two files, which is the restatement the standard
  bans. The rendered text is identical before and after; the evidence shows both.

  BUILDER'S CALL 4: `key_passes_prev_season_full` IS NOT WRITTEN. It is the catalogue metric
  `passes_key` under a different column name, which is why the generator never saw it while its
  four siblings all carry generated text. Writing it inline would define a catalogue metric outside
  the catalogue. Reported in decisions_reserved rather than fixed here, because the fix is a rename.

decisions_reserved:
  - ⛔ THE 13 MULTI-MEANING NAMES ARE THE NEXT MERGE'S, with the derived families they share the
    problem with: `goals_for`, `goals_total`, `goals_assists`, `shots_on`, `shots_inside_box`,
    `corner_kicks`, `goalkeeper_saves`, `key_passes`, `tackles`, `blocks`, `interceptions`,
    `clean_sheet_games`, `substitute_appearances`.
  - The 7 head-to-head and opponent-mirror names the approved plan counted as plumbing travel with
    their family, not with this merge: `last_meeting_at`, `last_meeting_league_code`, `pair_key`,
    `recent_meetings.kickoff_datetime`, `recent_meetings.league_code`, `opponent_name`,
    `opponent_logo_url`.
  - ⛔ THE TEAM COLUMNS BLOCKED ON THE CATALOGUE ARE THE CPO'S and are untouched here. Seven
    metrics are `entity = player` only while team models use the same names.
  - ⚠ A CLASS THIS MR SURFACED AND DOES NOT FIX: a column that IS a catalogue metric under a
    different column name is invisible to the generator, so it stays blank while its siblings are
    filled. `key_passes_prev_season_full` is one. The remedy is a rename, which is a naming
    decision and needs `--full-refresh` on an incremental model.
  - The 5 nested `recent_meetings.*` fields cannot be docs blocks at all (a name with a dot is not
    addressable by dbt) and must be written inline whenever they are done.
  - MR5 switches the presence rule on. It cannot pass until the blanks above are closed.

done_when:
  - Blank in-scope columns MEASURED from the raw YAML fall from **422 to 323**. ⚠ The manifest
    CANNOT answer this: it stores the RESOLVED description, so a wired column is indistinguishable
    from an inline one.
  - All 67 sites of the 22 block names reference their block and 34 single-site columns carry
    inline text: **0 blank**, asserted from the YAML across ALL layers, not only the in-scope ones.
  - ⛔ EVERY SENTENCE IS TRACED TO THE SQL AT EVERY MODEL IT REACHES, and the trace is recorded per
    name. Not the model that happens to be open, and not by reading the sentence and finding it
    plausible — the previous merge lost a name to exactly that, where the text read perfectly well
    at a model whose SQL contradicted it.
  - ⛔ NO SENTENCE DEFINES A CATALOGUE METRIC. The seed is the only source of a metric definition,
    so every written name is checked against `metric_catalogue.csv` — by concept, not only by
    string, since the same metric appears under a different column name.
  - `git diff --numstat` shows **exactly 1 deleted line**, in `seeds/schema.yml`, and every other
    file shows 0. ⚠ `git diff` NORMALISES line endings and has hidden a whole-file CRLF→LF rewrite
    in this programme — cross-check the CRLF/LF byte counts directly. It already caught one here:
    the first block insertion wrote 110 `\r\r\n` sequences and rendered as a 254-line rewrite.
  - `dbt parse` clean, every `{{ doc() }}` resolves, ZERO unrendered `{{ doc(` in the manifest, and
    the manifest's node set and `depends_on` identical before and after.
  - The longest RENDERED column description measured against the 1,024-character cap.
  - `check_description_hygiene.py` green repo-wide, read from its OUTPUT and not its exit code.
  - `python -m pytest tests/` at a baseline MEASURED on this branch (collection with the diff
    stashed and applied), never quoted from a previous MR's log.
  - Six offline gates green plus `ruff check . --config .ruff-ci.toml`, a separate CI job.
  - Every number in this contract and the evidence checked by extracting EVERY integer and asking
    whether it is still true — not by sweeping for the figures I remember changing.
  - Handover updated in the SAME commit, under the 16,000-CHARACTER cap measured with Python
    `len()`.

amendments: []
