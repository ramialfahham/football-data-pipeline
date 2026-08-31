# Acceptance evidence — step 4, MR 6: the four player `goalkeeping` metrics

Branch `refactor/metric-rename-player-goalkeeping`, from main `9ee88a4`.

    saves                 →  saves_player
    save_pct              →  saves_player_pct
    goals_against         →  goals_against_player
    shots_on_goal_against →  shots_on_goal_against_player

**676 tokens across 76 files — 210 renamed, 466 protected.** The largest and most entangled batch of
step 4 (`!130`: 537 / 46), and the first where protections outnumber renames more than two to one.
All four names are in the record verbatim; no new CPO ruling was needed.

⛔⛔ **THIS IS ROUND 2. ROUND 1 FAILED 5–0 ON TWO REAL DEFECTS, BOTH MINE.** Counts moved
217/459 → **210/466**. Four reviewers found the first independently, three the second. **Every gate
in the list below was GREEN with both defects present** — the reviewers were the only thing between
them and production. Full account in "Round 1" below.

Every gate below was run **unpiped, with its exit code read bare**.
⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate but is **NOT evidence** here.

criteria_demonstrated:

  - **The unguarded frontend chain, verified by reading every link.** `mart_player_momentum.sql:47,68`
    emits `saves_player` / `saves_player_pct`; `shared.yml:266,301` declares them; `_TOPPLAYER_DROP`
    does not drop them so the payload key follows with no export edit; `types.ts:50-51` declares them
    on `TopPlayer`; `PlayerRow.astro:37` reads them. Reported as a manual verification of a path no
    gate covers — no typecheck exists, no test references `PlayerRow`/`TopPlayer`/`top_players`.
  - **Criterion 1 is a CONFIRMATION, declared as such before the work.** The GK saves line renders on
    **0 of 67** built pages, measured over `dist` with comments stripped, so the dist comparison
    cannot catch a `PlayerRow.astro` mistake. What it does prove: base vs branch, **12/12/12 rows,
    7/7/7 headings, none added, none removed** in EN/DE/FI across 19 fixture pages, both sides built.
  - **The two rendered team labels survive.** `"% Save percentage"` (`saves_pct`) and
    `"Ø Goals against"` (`goals_against_per_match`) are among the seven names also declared in the
    CPO-validated `site/i18n/*.json` corpus and were compared word for word against it — identical in
    all three locales. `save_pct` and `shots_on_goal_against` appear in **0** files under `dist`.
  - **Frontend containment: exactly two files, four tokens.** `git diff --name-only -- site_v2/`
    returns `PlayerRow.astro` and `lib/types.ts` only, 6 changed lines. The other **ten** swept
    frontend files were each checked individually and are byte-identical, and `types.ts` moves 2 of
    its 11 occurrences — only `TopPlayer`'s.
  - **Both doc gates pass and both were watched going RED.** `sync_metric_docs_blocks --check`
    EXIT=0 at 167 blocks and EXIT=1 on a stale seed `metric_id`; `check_description_hygiene` EXIT=0 at
    1604 descriptions and EXIT=1 on a dangling `doc()` (`unresolved docs block:
    'saves_player_NO_SUCH_BLOCK'`). Both reverted and re-run green.
  - **Every dotted and bare reference resolves, and the projection check was mutated in BOTH forms.**
    The resolver reports zero broken references; `check_yml_vs_projection` reports zero mismatches,
    went **RED (EXIT=1)** on the strong form (name absent from the final SELECT) and **stayed GREEN**
    on the known-weak form (dropped from the projection but still inside a `safe_divide` on that same
    SELECT) — `!130`'s bound re-stated rather than re-discovered.
  - **The three 22-name TEAM `accepted_values` lists are byte-identical**, each keeping all three of
    its hits (`goals_against_per_match`, `shots_on_goal_against_per_match`, `saves_pct`). Compared
    base-vs-branch in FILE ORDER with a length assertion: 6 lists carry a swept token, **3 entries
    move across 3 lists**, no list changed length.
  - **No half-rename anywhere.** All 45 `doc()` re-points verified mechanically to preserve entity —
    zero crossovers — and after the round-1 fix, **zero** lines carry `goals_against_player` beside
    `goals_for`. The seed differs from base in `metric_id` only, on every row.

## Gates

  - `python scripts/sync_metric_docs_blocks.py --check` — **EXIT=0**, 167 blocks.
  - `python scripts/check_description_hygiene.py` — **EXIT=0**, **1604 descriptions**, 229 blocks
    resolved (234 at base, −5 matching the deleted orphans).
  - `python scripts/check_layer_contract.py` — **EXIT=0**.
  - `python scripts/check_registry_var_sync.py` — **EXIT=0**.
  - `dbt parse` — **EXIT=0**.
  - `python -m pytest -q` — **1009 passed, 1 skipped, 14 subtests**, matching the `9ee88a4` baseline.
  - `sqlfluff lint` on the ten changed models, from the REPO ROOT, jinja templater, full rule set —
    **byte-identical** to a re-lint of the same files stashed back to base. LT05 0→0; rule tally
    `['LT02','PRS','ST11','TMP']` both sides.
  - `npm test` — **76/76**. `node scripts/check-page-specs.mjs` — **EXIT=0**.
  - The site built **TWICE**, base and branch: 66 pages, `audit-seo: 67 built page(s) checked. OK.`

## ⛔⛔ Round 1 — two defects, both mine, both a scope coarser than the entity it had to resolve

**(a) THE TEAM SCORELINE PAIR, 6 SITES.** `goals_for` / `goals_against` is the TEAM per-fixture
scoreline from `int_legs__team_match`, reaching `mart_team_fixtures`, `mart_head_to_head` and
`mart_team_momentum_window` — none of which this MR renames. I scoped `export_site_data.py`,
`tests/test_export_site_data.py`, `01_fixture_page.md` and `03_player_profile.md` as PLAYER files,
so all six occurrences were renamed.

`export_site_data.py:166`'s `_TEAM_FIXTURE_FIELDS` is a KEEP-list applied to `mart_team_fixtures`
rows via `{k: row.get(k) …}`. Renamed, it would have emitted `goals_against_player: null` for every
team's `next_fixture` and every `recent_results` entry — **forever, with no crash** — while
`TeamFixtureRow.astro:23` still read `fx.goals_against`, a field the export had stopped emitting.
⚠ **The test was mutated to match the bug**: `test_export_site_data.py:367`'s fixture dict key was
renamed in lockstep, so `pytest` stayed green. That is the "verify the test fails" trap in its purest
form — the sweep edited the test and the code together, so the test could not disagree.

⭐ **THE FIX IS A FACT ABOUT THE DOMAIN, NOT AN EXEMPTION LIST.** There is no player `goals_for` — a
player does not score or concede "for" in the scoreline sense — so wherever the pair appears,
`goals_against` is the team field. `in_team_scoreline()` is scoped to the PARAGRAPH in markdown and
the enclosing statement elsewhere, because a line-scoped test on a construct that wraps is exactly
how `!128` round 1 failed. Measured against the round-1 diff: **it separates all 6 wrong renames from
all 60 correct ones, exactly.** Verified after the fix: **0** lines carry `goals_against_player`
beside `goals_for`.

⚠ A consequence worth recording: once the six were protected, `export_site_data.py` and
`tests/test_export_site_data.py` fell to ZERO renames — so the no-op-write guard never reopened them
and they kept their round-1 text on disk. **A file that drops to zero renames must be restored from
base explicitly.** Both were, and both left `scope_paths` (45 → 43 entries, 42 changed files).

**(b) THE SEED'S `interpretation` COLUMN.** `SEED_REFERENCE_FIELDS` was a BLOCKLIST of five columns
to protect; the seed has fifteen. `interpretation` was not on it, so `saves_per90`'s prose became
"More **saves_player** per 90 is better…" — an internal identifier in reader-facing text
(`seeds/schema.yml` calls that column the seed of the site's good/bad reading and auto-narrative), on
a row the contract states three times does not change.

⭐ **THE FIX IS THE SHAPE, NOT THE ENTRY.** Adding `interpretation` would have left the next added
column exposed identically. It is now an ALLOWLIST — `SEED_RENAMEABLE_FIELDS = {"metric_id"}` — so a
new seed column is protected by default. Verified across every row: **zero non-`metric_id` seed
fields differ from base.**

## ⛔⛔ The one part of this MR that no gate covers — read `rendered_page_evidence.md`

The first rendering-component change of step 4. `mart_player_momentum` → `_TOPPLAYER_DROP` (a
DROP-list, so no export edit) → `TopPlayer` → `PlayerRow.astro`. There is **no typecheck**, **no test
touching `PlayerRow`/`TopPlayer`/`top_players`**, and **the GK line renders on 0 of 67 pages**. The
chain was verified by reading every link. This is reported as a manual verification of an unguarded
path, not as a passing check.

## ⭐ Predictions written into the contract BEFORE the code, then measured

  - **Doc blocks 172 → 167.** Predicted by running the real generator against the renamed seed held
    in memory. Measured: **167**, with the removed/added sets identical to the simulation term for
    term — 11 removed (6 plain/collapsed names and 5 `goals_against_*__player` orphans), 6 added.
    **CONFIRMED.**
  - **Description count holds.** Measured **1604** on both sides, by stashing the change and
    re-running. The "re-point them" ruling, a seventh measurement. **CONFIRMED.**
  - **The "means more than one thing" list drops 4 → 3.** **DISPROVED — see below.**

## ⛔⛔ The disproved prediction, and why it generalises

The list **stays at 4**; the `goals_against` entry only changes shape:

    before   goals_against: goals_against__player, goals_against__team
    after    goals_against: goals_against, goals_against_player

`_ambiguous_names()` groups by COLUMN NAME. Columns literally named `goals_against` still split two
ways: TEAM surfaces point at `goals_against`, while the PLAYER PROVIDER surfaces
(`fct_fixture_player_stats`, `int_legs__player_match`, `mart_player_fixture_stats`) keep the provider
column NAME under the **"yes"** ruling but had their `doc()` re-pointed under **"re-point them"**.

⭐ **The two standing rulings interact, and the consequence is general: a metric rename can never
disambiguate a column name the PROVIDER also uses.** `duels_won_pct` resolved on `!130` only because
it is a computed rate with no provider column of that name. `goals_against` and `saves` are provider
fields, so they cannot. **This corrects an expectation `!130`'s own contract recorded** — that the
naming programme frees some of #87's 49 blank columns. It does not: the blank count is **unchanged at
49**, and #87 is untouched by this programme rather than partly solved by it.

## The block collapse — two at once

    172 → 167   (11 removed, 6 added)
    REMOVED  saves__player · saves__team · goals_against__player · goals_against__team ·
             save_pct · shots_on_goal_against ·
             goals_against_{this_season,prev_season,delta_yoy,sum_season}__player ·
             last_meeting_goals_against__player
    ADDED    saves · saves_player · saves_player_pct · goals_against ·
             goals_against_player · shots_on_goal_against_player

**45 `doc()` re-points, verified mechanically to preserve entity in every case — zero crossovers:**
`saves__team`→`saves` ×6, `saves__player`→`saves_player` ×12, `goals_against__team`→`goals_against`
×12, `goals_against__player`→`goals_against_player` ×8, `save_pct`→`saves_player_pct` ×6,
`shots_on_goal_against`→`shots_on_goal_against_player` ×1. **18 of them are TEAM-side**, caused by a
player rename, against five on `!130`. All five deleted orphans verified at 0 references, including
`last_meeting_goals_against__player` — a PREFIX-affix orphan, a shape `!130` did not have.

## Mutations — watched RED, reverted, re-run green

  - **Stale `metric_id` in the seed** → `sync_metric_docs_blocks --check` **EXIT=1**. Reverted: 0.
  - **A `doc()` naming a block that does not exist** → `check_description_hygiene` **EXIT=1**,
    `core.yml :: core/fct_fixture_player_stats/saves - unresolved docs block:
    'saves_player_NO_SUCH_BLOCK'`. Reverted: 0.
  - ⭐ **The yml-vs-projection check mutated in BOTH forms, so `!130`'s disclosed bound is RE-STATED
    rather than re-discovered:**
      · STRONG (`saves_player` absent from the whole final SELECT) → **EXIT=1**,
        "yml declares ['saves_player'] but the final SELECT does not project them".
      · WEAK (dropped from the projection but still named inside the `safe_divide` on the same
        SELECT) → **EXIT=0, GREEN.** It tests token PRESENCE, not projection. The model still could
        not compile. The delivered tree is clean under both forms.

## Independent checks

`check_yml_vs_projection.py` over both old and new names: **zero mismatches**. The column-reference
resolver: **zero broken references**, unresolved bare reads reported rather than skipped.

## The entity discrimination, verified where it is invisible

**Two dual-entity ids this batch, not one.** The seed is the only file where an entity error leaves
no diff trace, because both rows of a pair carry the same token. `seed_entity_lines()` was verified
directly against all ten goalkeeping-stem seed rows: **0 mismatches** —
`saves` player@52 / team@85, `goals_against` player@56 / team@83.

⚠ The two entities even disagree on the provider column: team `saves` computes
`sum(goalkeeper_saves)`, player `saves` computes `sum(saves)`; player `shots_on_goal_against` is
`sum(saves + goals_against)` while team `shots_on_goal_against_per_match` is
`sum(opponent_shots_on_goal)`. All 16 seed formula occurrences protect; only the four `metric_id`s
move. `player_benchmark_metrics.sql` is the mirror case and its `num`/`den` do move.

## ⭐ A defect in my own tool, found by reading the printed reasons rather than the counts

`mart_player_season_record.sql:13`, inside a `{# … #}` docstring: "…computed here via safe_divide.
save_pct is only meaningful for goalkeepers." That `.` is SENTENCE PUNCTUATION, but `sql_shape()`
saw `safe_divide.` before the token and reported "dotted", labelling the occurrence **"RENAME read —
safe_divide. reads a metric relation that renamed it"**. The DECISION was right; the REASON was a
lie — the class `!127` fixed for bare reads and `!129` for aliases. The comment test already existed
but lived INSIDE `bare_decision()`, reachable only after `sql_shape` returned "bare", so prose could
never reach it. Hoisted ahead of shape analysis; the jinja-comment count went 11 → 13 and the false
reason is gone. **The counts were identical before and after — only reading the reasons found it.**

## `saves` is an ordinary English word — a trap class no previous stem had

All PROTECT, each a printed decision rather than an invisible exclusion:

    ingestion/api_football/bigquery.py          "the extra call costs 13 KB and saves gigabytes"
    dbt_project/docs/engineering_standards.md   "what the macro saves"
    tests/test_governance_hooks.py              "`changes:` filter saves neither"
    docs/ui_design_brief.md  ×3                 "GK: saves, goals conceded, save %"

And `goals_saves` is the PROVIDER's own field name, normalised to the leg column `saves` — protected,
sitting beside `save_pct`, which moves.

## #96 — all six lists again, and the split inverts from `!130`

  - `shared.yml:1756` (14-name board) and both 18-name player lists
    (`shared.yml:2186`, `int_competition_benchmarks.yml:105`) — **1 entry each**: `save_pct` →
    `saves_player_pct`. `saves_per90` stays.
  - The three 22-name TEAM lists (`shared.yml:2080`, `int_competition_benchmarks.yml:27`, `:66`) —
    **0 move**, each keeping all **three** of its hits (`goals_against_per_match`,
    `shots_on_goal_against_per_match`, `saves_pct`).

**3 entries across 3 of 6 lists; no list changed length.** Compared base-vs-branch in FILE ORDER with
an identity assertion — the method `!130` had to correct after a sort-keyed comparison mis-paired the
lists.

## Eight singular tests, split four and four

Player rename: `std_player_`, `player_profile_`, `mart_leaderboards_save_pct_in_range`, and
`player_profile_saves_lte_faced` — **the first test in this programme that is not an `*_in_range`
name**; its expression moved with it, `saves <= shots_on_goal_against` →
`saves_player <= shots_on_goal_against_player`. Team protect: `momentum_team_`, `std_team_`,
`mmi_home_`, `mmi_away_saves_pct_in_range`.

## Prose the rename falsifies — four sites, rewritten by hand

`sync_metric_docs_blocks.py`, `declare_missing_columns.py`, `test_declare_missing_columns.py` and
`test_sync_metric_docs_blocks.py` all argue the entity suffix is mandatory using `goals_against` as
the worked example: "the catalogue defines it for a PLAYER while every column of that name sits on a
TEAM model." **After this MR the single surviving row is the TEAM's**, so the entity matches and the
specific hazard that sentence describes is gone. Each was rewritten to state the RULE — a stem with
one catalogue row says nothing about which entity its derived columns belong to — and to mark the
example historical. ⛔ Nothing deleted: `_derived()` still suffixes by entity, the guard still
protects a future collision, and the synthetic `__team`/`__player` fixtures stay because they
exercise a mechanism that still exists. The classifier PROTECTS all 13 tokens in these files and
prints "prose the rename FALSIFIES", so the rewrite is a visible separate edit.
