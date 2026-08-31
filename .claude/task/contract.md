# Task contract — rename the seven player goals metrics (step 4, MR 7 — THE LAST BATCH)

objective: >
  **STEP 4 of the metric catalogue naming programme, MR 7 of seven. This closes step 4.**

      goals           →  goals_player            assists       →  assists_player
      goals_penalty   →  goals_penalty_player    scorer_points →  scorer_points_player
      goals_open_play →  goals_open_play_player  penalty_won   →  penalty_won_player
      contribution_share →  contribution_player_pct

  `!125` `shooting`, `!127` `discipline`, `!128` `defending`, `!129` `passing`, `!130` `duels`,
  `!131` `goalkeeping`. Nothing remains after this.

  ⛔⛔ **THE RULE IS UNCHANGED AND IS STILL THE WHOLE DESIGN: A REFERENCE FOLLOWS ITS SOURCE.**

  ⭐⭐ **THE BIGGEST BATCH OF THE PROGRAMME: 1,519 occurrences across 93 swept files and 94 distinct
  maximal tokens** (`!131`: 676 / 76 / 50), landing on **38 changed files**. Decided once each:
  **279 renames · 63 `doc()` re-points (19 TEAM-side) · 1,177 protected.** Protections outnumber
  changes better than 3 to 1, because `goals` is the most generic stem in the domain.
  ⚠ These are the ROUND-2 counts. Round 1 read 442 changed / 1,077 protected; the prose rule in
  `decisions_taken §9(d)` moved exactly **100** occurrences into PROTECT.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**, its table
  "⛔ PLAYER, 35 REMAINING" — all seven renames appear in it verbatim. Cited by CONTENT.
  ⭐ **`contribution_player_pct` IS RULED**, and the entry that rules it is dated **2026-08-29**:
  *"RULING, verbatim: **contribution_player_pct is fine, go with it**"*. The same entry states that
  the 35-row player list is now FULLY RULED and that the older caveat — *"Flag it rather than quote
  it as his"* — is **DISCHARGED and does not need to travel further**.
  ⛔ I wrote that discharged caveat into this contract, its evidence and its log entry anyway.
  Corrected in all three; found by `football-analytics-expert-reviewer`. The entry names the rule I
  broke: **living document → replace; dated log → append.**
  ⚠ Seed-verified: `player`/`goals` is **10 rows** — these seven plus `goals_per90`, `assists_per90`
  and `scorer_points_per90`, which do not change.

  ⭐ **TWO STANDING CPO RULINGS applied unchanged**: **"re-point them"** (63 references here, **19 of
  them TEAM-side**) and **"yes"** (provider surfaces keep the provider name — ten `.sql` files
  excluded, 126 tokens).

  ⭐ **ONE RULING TAKEN THIS SESSION, recorded with what it answered.** Asked: `_shape_squad_member`
  writes `"goals": career.get("goals")` — the mart column moves, so must the published payload KEY?
  Answered: *"Naming conventions in the warehouse are one thing. What we show on the website is
  another."* **The key stays; only the warehouse-facing half moves.** See `decisions_taken` §2.

  ⭐ **ONE RULED CLASS APPLIED, not re-decided**: `!129`'s ruling that derived yoy columns rename
  with their metric. Eight of them here — see `decisions_taken` §1.

scope_paths:
  # ⚠ `mart_roster.sql` was declared here before implementation and REMOVED in round 2: its only
  # hit is a SQL comment naming the Squad tab's PAYLOAD fields in display shorthand
  # ("appearances / mins-per-app / goals / assists"), which §2's ruling protects. Zero changes, so
  # it claims no permission — `!131`'s precedent for a file that falls to zero renames.
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - docs/content_architecture.md
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/11_team_squad.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/13_player_career.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - scripts/export_site_data.py
  - scripts/sync_metric_docs_blocks.py
  - tests/test_export_site_data.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ The EXACT changed set, reconciled against `git diff --name-only` in both directions. 37 come
# from the classifier's DRY RUN; `metric_columns.md` is regenerated; `sync_metric_docs_blocks.py` is
# rewritten BY HAND (decisions_taken §6); six are review paperwork.
#
# ⭐⭐ NO `site_v2/` ENTRY, AND THAT IS A MEASURED RESULT, NOT AN INHERITED CLAIM. Thirteen frontend
# files carry a swept token and **every one protects**: `PlayerRow.astro` reads the PROVIDER columns
# `goals_total`/`goals_assists` (unlike `!131`, where it read renaming payload fields); the rest are
# team scoreline fields, TEAM metric label keys, or UI words. `TeamSquad.astro` and `types.ts` are
# untouched because of the CPO ruling in §2.
#
# ⚠ SWEPT BUT NOT CHANGED — 56 files, every token PROTECTED, kept IN the sweep so a decision is
# printed for each:
#  · the whole TEAM tree, including `mart_standings`, `mart_fixture_standing_context`,
#    `mart_head_to_head`, `mart_team_fixtures` and the two fixture-goal singular tests
#  · THIRTEEN frontend files (see above)
#  · ⭐ NINE documentation files where `goals` is an ENGLISH WORD — `CLAUDE.md`,
#    `docs/north_star.md`, `docs/data_contract.md`, `dbt_project/docs/layering.md` and five more
#  · `dbt_project/seeds/schema.yml` — see decisions_taken §5
#  · `declare_missing_columns.py` and both docs-block test modules: `!131` already made their
#    worked example historical, so they need no further edit this batch
#
# ⚠ NOT IN SCOPE: `.claude/task/review_input.patch` (regenerated paperwork, hash-excluded);
# `site_v2/src/data/**` and `site/**`; the ten provider `.sql` files (126 tokens, the "yes" ruling).

protected_override: >
  none. No guard, threshold, schedule or exemption is loosened. `fct_fixture_player_stats` is again
  the only `incremental` model carrying these names and its COLUMNS are not renamed — only `doc()`
  pointers — so no `--full-refresh` is implied.

impact_map: >
  ⭐ **RUN ON THIS BRANCH BEFORE THE FIRST EDIT, PASTED VERBATIM.**

      $ dbt ls --resource-type model --select int_player_season__metrics+ \
          int_player_club_season__metrics+ int_player_momentum__metrics+ \
          int_player_season_position__metrics+ int_player_season_record+ \
          int_player_profile__yoy+ int_player_profile__contribution+ mart_leaderboards+ \
          mart_player_career+ mart_player_momentum+ mart_player_profile+ \
          mart_player_season_record+ mart_roster+

      football_data_pipeline.4_intermediate.domestic_league.team_season.int_player_season__metrics
      football_data_pipeline.4_intermediate.shared.int_player_club_season__metrics
      football_data_pipeline.4_intermediate.shared.int_player_competition_benchmarks
      football_data_pipeline.4_intermediate.shared.int_player_momentum__metrics
      football_data_pipeline.4_intermediate.shared.int_player_profile__contribution
      football_data_pipeline.4_intermediate.shared.int_player_profile__yoy
      football_data_pipeline.4_intermediate.shared.int_player_season_position__metrics
      football_data_pipeline.4_intermediate.shared.int_player_season_record
      football_data_pipeline.5_marts.shared.mart_leaderboards
      football_data_pipeline.5_marts.shared.mart_player_career
      football_data_pipeline.5_marts.shared.mart_player_competition_benchmarks
      football_data_pipeline.5_marts.shared.mart_player_momentum
      football_data_pipeline.5_marts.shared.mart_player_profile
      football_data_pipeline.5_marts.shared.mart_player_season_record
      football_data_pipeline.5_marts.shared.mart_roster

  **15 models** — two more than `!130`/`!131`, because `int_player_profile__contribution` (where
  `contribution_share` is computed as `scorer_points / team_goals_season`) and `mart_roster` join for
  the first time. ⚠ **`int_player_competition_benchmarks` and `mart_player_competition_benchmarks`
  change only through `player_benchmark_metrics()`**, and unlike every previous batch there is **no
  over-count**: every model in this lineage carries at least one of the seven names.

  Downstream: `scripts/export_site_data.py` and `tests/test_export_site_data.py`. **No `site_v2/src`
  source consumes a renamed name** — measured, not assumed.

acceptance_criteria:
  - ⛔ **THE TEAM SCORELINE FAMILY IS UNTOUCHED.** `goals_for`, `goals_against`, `goals_home`, `goals_away`, `goals_diff`, `standing_goals_diff`, `goals_own`, `last_meeting_goals_*` and their yoy forms all survive byte-identical, and **zero** renamed tokens sit in a construct with any of them. This is the class that FAILed `!131` round 1 with one token; here the stem reaches all of them.
  - ⭐ **NO `site_v2/` FILE CHANGES**, re-derived for this batch: thirteen frontend files carry a swept token and every one protects. `PlayerRow.astro` reads PROVIDER columns this time; `TeamSquad.astro` and `types.ts` are untouched under the §2 ruling. No name is HALF-renamed — every surviving old name is a provider read, a TEAM column, an English word, or a UI key.
  - ⭐ **The published payload key `"goals"` is still emitted** by `_shape_squad_member` and `_shape_player_career_season` while their `.get()` reads move — the ruling in §2, verified on both sides of both lines.
  - `sync_metric_docs_blocks.py --check` and `check_description_hygiene.py` both pass AND are each watched going RED; the seed differs from base in `metric_id` only, on every row.
  - Every dotted AND bare reference resolves; the yml-vs-projection check reports zero mismatches and is mutation-tested in BOTH its strong and its known-weak form.
  - ⛔ **All 16 `doc()` references to the eight derived player yoy blocks re-point** — none dangles, which `check_description_hygiene` proves by going green.

decisions_taken: >
  All seven names come from the record, `contribution_player_pct` included — it was ruled verbatim on
  2026-08-29 (see `refs`), which is where an earlier draft of this contract was wrong.

  ⭐⭐ **ONE QUESTION, ASKED OF EVERY OCCURRENCE.** 1,519 occurrences classified once, each decision
  printed with its resolved entity — **279 renames, 63 re-points, 1,177 protected** across 93 swept
  files, landing on 38 changed ones. 6,533 tokens
  repo-wide: 4,888 untouched (the sample, `.claude/**`, `site/**`, `docs/audits/**`, the regenerated
  `metric_columns.md`), 126 in provider `.sql`.

  ⭐⭐ **§1. EIGHT DERIVED PLAYER YOY COLUMNS MOVE — AND THEY ARE NOT ORPHANS.** `!131`'s five
  deleted `__player` blocks had zero references. These eight do not: `goals_{this_season,
  prev_season, prev_season_full, delta_yoy}` and the same four for `assists` each carry **two live
  `doc()` references** on `int_player_profile__yoy` and `mart_player_profile` — 16 in all. Leaving
  the columns behind would delete their blocks and dangle every one, turning
  `check_description_hygiene` red. This is the class the CPO ruled on for `!129`'s `key_passes_*`
  ("rename them with the metric"), so it is applied, not re-decided. Verified team-side safe: the
  team uses `goals_for_*`, never `goals_*`.

  ⭐⭐ **§2. A CPO RULING TAKEN THIS SESSION, AND WHAT IT ANSWERED.** `_shape_squad_member` writes
  `"goals": career.get("goals")` — a published payload key on the left, a warehouse column on the
  right. I asked whether the key moves with the column. He ruled: *"Naming conventions in the
  warehouse are one thing. What we show on the website is another."* **So only the right half
  moves.** Implemented as a ROLE rule rather than a file scope: the argument of `.get(...)` follows
  the mart; a bare `"x":` dict key stays; anything else in those two files is a `metric_key` VALUE
  and follows the mart's own column. Measured: **19 payload keys protected, 4 warehouse reads
  renamed, 22 metric_key values renamed.**
  ⚠ The same rule is what protects `export_site_data.py:1044/1046` — `"goals": r.get("goals_home")`,
  a payload key that is a TEAM scoreline, in the same file as the player board keys. **`!131` shipped
  exactly that class of mistake** by scoping this file wholesale.

  ⭐⭐ **§3. `goals_for` CONTAINS THE STEM, SO `!131`'s DEFECT CLASS IS EVERYWHERE.** The scoreline
  guard is widened from one companion token to the whole family — `goals_for`, `goals_against`,
  `goals_home`, `goals_away`, `goals_diff`, `standing_goals_diff`, `goals_own` — and still scoped to
  the CONSTRUCT (the paragraph in markdown, the enclosing statement elsewhere), because a
  line-scoped test on a wrapping construct is how `!128` failed. The discriminator remains a fact
  about the domain, not a heuristic: **there is no player `goals_for`.**

  ⭐ **§4. A TOKEN-LEVEL RULE, JUSTIFIED BY A PROPERTY OF THE WHOLE REPO.**
  `docs/content_architecture.md` mixes English `goals`/`assists` with one genuine backticked
  `` `contribution_share` ``, so a file-level scope is wrong for it in BOTH directions. Rather than
  exempt the file, I verified that `contribution_share` (12 occurrences) and `scorer_points` (39) are
  **only ever this metric id** — never an English word, a provider column, a team metric or a UI key
  — and decided them by token, before file scope. The property is checkable by grep.

  ⭐ **§5. THE BACKTICK SETTLES WHERE THAT RULE STOPS, AND THE SEED'S ALLOWLIST OUTRANKS IT — both
  found by measurement, not reasoning.**
  (a) `seeds/schema.yml:339` says, in plain prose, *"Redundancy at tier 1 is deliberate — goals,
  assists and scorer_points"*. Three PLAYER metric names in one readable list, but `goals` and
  `assists` are protected there (line 330's `metric_group` enum value `goals` must not move), so the
  token rule alone would have shipped **"goals, assists and scorer_points_player"** — an internally
  inconsistent sentence. In a DOC file the backtick decides: an identifier reference moves, running
  prose does not. **`seeds/schema.yml` therefore does not change at all.**
  (b) ⛔ **AND THE FIRST APPLY SHIPPED A REAL DEFECT THAT THE SEED CHECK CAUGHT**: the
  `contribution_share` row's own `description` glosses the formula as *"the player's goals + assists
  (scorer_points)"*, and the token rule — checked before the seed's field allowlist — rewrote it to
  `(scorer_points_player)`. **A rule placed before the allowlist silently reopens the hole `!131`
  closed.** The seed allowlist now outranks it, and the check that found it is a done_when item:
  the seed must differ from base in `metric_id` ONLY, on every row. Verified: 0 other fields differ.

  ⭐⭐ **§6. THREE COLLAPSES AT ONCE, AND THE MECHANISM LOSES ITS LAST LIVE INSTANCE.** Simulated
  against the real generator before any code, with both the seed renames and the eight derived
  column renames applied in memory:

      167 → 163 blocks   (22 removed, 18 added)
      REMOVED  goals__{player,team} · goals_penalty__{player,team} ·
               goals_open_play__{player,team} · assists · penalty_won · scorer_points ·
               contribution_share · the 8 goals_/assists_ yoy __player blocks ·
               4 goals_*__team derived orphans (verified 0 references)
      ADDED    goals · goals_player · goals_penalty · goals_penalty_player ·
               goals_open_play · goals_open_play_player · assists_player ·
               penalty_won_player · scorer_points_player · contribution_player_pct ·
               the 8 renamed yoy __player blocks

  **63 `doc()` re-points, 19 of them TEAM-side.** ⛔ **After this MR the `__team`/`__player` split
  has NO live instance in the catalogue** — all six dual-entity ids have been renamed across step 4.
  `sync_metric_docs_blocks.py`'s module docstring uses `goals_open_play` as its worked example of the
  collision, which this batch falsifies; it is rewritten by hand to state the rule and mark the
  example historical. ⛔ **Nothing is deleted** — `_derived()` still suffixes by entity, `_blocks()`
  still splits and still aborts, and the synthetic test fixtures stay. Whether a mechanism with no
  live instance should remain is carried to the CPO, not acted on.

  ⭐ **§7. #99 COMES DUE, AS THE HANDOVER PREDICTED.** `_LEADERBOARD_METRICS` / `_LB_KEEP` carry the
  literal player board keys `"goals"`, `"assists"`, `"scorer_points"`; they follow the mart's
  `metric_key` and move. Still pinned by no test — the gap is carried, not closed.

  ⛔⛔ **§9. FIVE DEFECTS THE IMPLEMENTATION SURFACED — each found by a different means, and
  each fixed as a RULE rather than an edit.** They are recorded because the means matter more than
  the defects. **(d) and (e) are the blinded review's: round 1 FAILed 5–0, round 2 FAILed 4–1.**

  **(a) Found by a CHECK.** The seed's `contribution_share` row glosses its own formula as *"the
  player's goals + assists (scorer_points)"*, and the token rule — placed before the seed's field
  allowlist — rewrote it to `(scorer_points_player)`. **A rule checked before the allowlist silently
  reopens the hole `!131` closed.** The allowlist now outranks it, and the check that caught it is a
  `done_when` item: the seed must differ from base in `metric_id` ONLY. Verified: 0 other fields.

  **(b) Found by READING the applied diff.** `mart_player_career.sql:130` documents the catalogue row
  as *"(entity=player, group=goals, tier 1)"*. The first apply turned that into `group=goals_player`
  — naming a metric_group that does not exist. `goals` is a metric_GROUP value as well as a
  metric_id (`seeds/schema.yml:330` lists it beside "shooting" and "defending"), so the rule is now
  positional: `goals` immediately after `group=` / `group:` is the group. **No total, count or gate
  would have shown this** — only reading the diff.

  **(c) Found by the TEST SUITE, which is the one that matters.** I put
  `tests/test_export_site_data.py` in the same payload-key/warehouse-read role set as the export, and
  **pytest failed three tests**. The rule was not stale — it was inverted: in the TEST file a dict
  KEY is a FIXTURE (a `mart_player_career` row, i.e. a warehouse column that must move), while the
  payload keys appear as SUBSCRIPTS (`squad[9]["goals"]`) and as members of an expected-key set. No
  single subscript rule works either, because `boards["goals_player"]` subscripts a dict keyed by
  metric_key, which does move. So the test file follows the mart like any other player file, and the
  four assertions about `_shape_squad_member` / `_shape_career_row` OUTPUT are corrected BY HAND — a
  visible separate edit implementing §2's ruling rather than a rule contorted to serve both roles.
  ⭐ **`!131` recorded that an automated rename editing code and test together leaves the suite
  unable to disagree. Here the suite disagreed** — because the ruling deliberately holds one side
  still, so the two sides could no longer move in lockstep. **A rule that forces the code and its
  test apart is what makes the test able to fail.**

  ⛔⛔ **(d) Found by the BLINDED REVIEW — round 1 FAILed 5–0, and I got this class wrong TWICE.**
  `goals` and `assists` are ordinary English words, and the sweep rewrote them inside running prose.
  `scope-auditor`, `analytics-engineer` and `football-analytics-expert` each found it independently:
  *"the club's WHOLE-SEASON goals_player"*, *"own goals_player"*, *"Involved in 45% of Bayern's
  goals_player"*, *"goals_player against"* — and because `+persist_docs` is on for every model, those
  ship to BigQuery as the model's real documentation. `int_player_profile__contribution`'s docstring
  said it BOTH ways in one paragraph: the prose mislabelled, the formula line beneath it correct.
  ⛔ **Then my first fix over-corrected**, and `bi-analyst` caught the other side in the same round:
  requiring the token to BE a whole backticked span left `` `mart_player_career.goals` ``,
  `` `goals − goals_penalty_player` `` and the `Atomics` column's `goals, assists` stale — the last
  two rows above metric ids `!130` had already renamed.
  ⭐ **The rule that holds is ROLE, not punctuation** — the same lesson step 4 has been learning
  since `!131`. A census over EVERY markdown table cell in the repo carrying the bare stem returned
  **16 distinct column headers in three roles**:
      IDENTIFIER  `Source column` · `Atomics` · `numerator` · `denominator`   → moves
      PAYLOAD     `Payload key` · `JSON key`                                  → stays (§2's ruling)
      PROSE       Element · Ruling · Gap · Notes · Display string · …         → stays
  Outside a table the backtick still decides; `{goals}` is excluded as a template slot, proved by its
  own sibling row where `{won} of {total} · {pct}%` sits against atomics `duels_won_player,
  duels_player, duels_won_player_pct` — **the slots were never the ids.**
  ⭐ `11_team_squad.md:120` carries BOTH rulings in one line and is now right in both halves:
  `` `squad[].goals` `` stays, `` `mart_player_career.goals_player` `` moves.
  **Measured across all 51 in-table occurrences: exactly 6 move, 45 stay.** Every one of the seven
  prose sites the reviewers named is verified back to English.

  ⛔ **(e) Found by the BLINDED REVIEW AGAIN — round 2, 4 PASS / 1 FAIL, and it is (d)'s rule meeting
  a construct outside its reach.** `analytics-engineer` found two SQL comments —
  `int_player_season__metrics.sql:112` and `int_player_season_position__metrics.sql:155` — reading
  `-- ... open-play conversion = (goals − goals_penalty_player) / shots_on_goal_player`
  directly above code that correctly computes `(goals_player - goals_penalty_player)`. A **formula
  quoted in a comment**, half-renamed: every other name in the sentence had already moved, so the
  comment contradicted the three lines beneath it.
  ⭐ **This is the identical construct (d) fixed at `12_player_stats.md:142` via the `numerator`
  column — the role rule simply had no reach outside a markdown table.** `in_operand_position()`
  gives it one: a token inside a parenthesised arithmetic expression that ALSO names an underscored
  identifier is an operand, not a word. Both conditions are required, and together they are what
  separates a quoted formula from English — prose says "penalty goals" and "own goals" with no
  operator and no underscored neighbour, and never inside parentheses holding both.
  ⭐ **Census over every comment line in the repo carrying a bare swept token — 26 occurrences: the
  rule moves exactly 2 and keeps all 24**, including "own goals", "Penalty goals", "goals/subs",
  `group=goals`, and `mart_player_momentum.sql:72`'s "goals, then assists, then key passes", which
  describes an ORDER BY over the PROVIDER columns `goals_total`/`goals_assists`.
  ⛔ **Stated plainly, because it is the lesson: I set this one rule THREE times** — too wide (prose
  rewritten), too narrow (identifier references left stale), then right in tables and blind outside
  them. Same root each time, a scope coarser than the role it had to resolve; found by review each
  time, by a gate never.

  ⭐ **§8. ONE SINGULAR TEST**, name and expression together:
  `player_contribution_share_within_unit` → `player_contribution_player_pct_within_unit`. The `!131`
  precedent (`player_profile_saves_lte_faced`) applied to a second non-`*_in_range` name. **#96 is
  narrow this batch**: only `shared.yml:1756`'s 14-name board list moves, 2 entries; five other lists
  carry protected-only hits.

decisions_reserved:
  - none NEW on naming beyond the ruling in `refs`, taken before any code and recorded with what it
    answered. `contribution_player_pct` is HIS, ruled verbatim on 2026-08-29.
  - ⭐ **NOW REALISED, AND STILL THE CPO'S: the `__team`/`__player` split has no live instance after
    this MR.** Carried since `!130`, and `!131` showed the cost is concrete — four files documented
    the mechanism with an example that no longer existed. This batch makes it five. Nothing is
    proposed and nothing is removed.
  - ⚠ CARRIED: the column-reference resolver as a committed CI gate — `!129` argued against it,
    `!130` and `!131` bounded it further. Not proposed.
  - ⚠ CARRIED: **#99** — the export's literal board keys move here but remain pinned by no test.
  - ⚠ CARRIED: `_LEADERBOARD_METRICS` / `_LB_KEEP` untested; **#96**, eleven reproductions; **#87**,
    which `!131` established this programme does NOT advance; **#98**.

done_when:
  - `sync_metric_docs_blocks.py --check` passes at **163** blocks, reconciled term by term against the simulation in §6 — 22 removed, 18 added.
  - `check_description_hygiene.py`, `check_layer_contract.py` pass, `dbt parse` is clean, and the description count is measured against base. **All 16 derived-block references resolve** — the gate proves it.
  - The seed differs from base in `metric_id` ONLY, on every row.
  - The scoreline family is byte-identical and no renamed token shares a construct with it.
  - `python -m pytest -q` matches the `6f0ee07` baseline; `npm test` green; the site built TWICE.
  - `sqlfluff lint` on every changed model, from the REPO ROOT, UNPIPED, byte-identical to a re-lint of the stashed base.
  - Mutations watched RED, including the yml-vs-projection check in both its strong and known-weak form.
  - ⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate but is **NOT evidence** here.
