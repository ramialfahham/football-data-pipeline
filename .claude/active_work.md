# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-26**. **main `0ec8360`.** #82 MR1-MR4c and the catalogue MR (`!104`) MERGED.
**Nothing is in flight.** **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT: the clean_sheets rename. CPO-ruled, scoped, NOT started (2026-08-26)

⭐ **READ `escalations.log`'s 08-20 to 08-26 entries FIRST.** The 08-26 entry carries four CPO
rulings verbatim and this task's whole findings list. **Do not re-scope or re-audit any of it.**

⛔ **CPO RULING, verbatim: "use clean_sheets (for the number of matches with clean sheets) and
clean_sheets_share (for the percentage of matches with clean sheets)."** It fixes a LIVE defect —
one name means two numbers today:
· `int_team_season__metrics_cumulative.sql:91` `safe_divide(clean_sheet_games, games_played) as
  clean_sheets` — a RATE. Flows to `int_team_season__metrics` (final-row projection), then to
  `mart_team_profile.sql:86` and `mart_team_season_insights.sql:57`.
· `mart_team_season.sql:41`, `mart_team_season_record.sql:72` (`m.clean_sheets_sum_season`) and
  `mart_team_momentum.sql:44` (`b.clean_sheet_games`) — a COUNT.
⭐ **THE FRONTEND ALREADY AGREES WITH THE RULING**: `metricRows.ts:50` serves `clean_sheets` as
`count_fraction` with a `denom` mapping, and the committed fixture JSON carries `"clean_sheets": 2`.
So the WAREHOUSE is the side out of step. ⚠ **UNVERIFIED, CHECK IT FIRST**: `mart_team_profile`
serves the RATE under a name the frontend renders as a count — establish whether the team page reads
that mart or `mart_team_season`, because if it reads the profile that is a live display bug.

**SCOPE MEASURED, not started.** Rename the RATE to `clean_sheets_share`; the COUNT keeps
`clean_sheets`. Touches: the seed (the existing row is the RATE and is renamed; a COUNT row is
added); `int_team_season__metrics_cumulative.sql:91`; the yoy family
(`clean_sheets_this_season/prev_season/delta_yoy` in `int_team_profile.yml`,
`mart_team_profile.sql:140-142`); range tests at `int_team_season.yml:53,186` and
`int_team_profile.yml:27`; TWO `accepted_values` lists in `int_competition_benchmarks.yml:27,66`
(the 22-metric team benchmark set); `mart_team_season_insights.sql:57`; the i18n key
`metrics.clean_sheets.label` in `strings.ts` (3 locales) and `types.ts`.
⚠ It MOVES A PUBLISHED COLUMN, so it is its own MR.

## ⭐ THEN: the value-equivalence test. BUILT, PARKED, needs 5 aliases

⛔⛔ **THE CATALOGUE DOES NOT DRIVE THE SQL. No model `ref()`s the seed — only tests do.** Formulas
are hand-copied and nothing compares them: of 68 model expressions carrying a metric_id, 20 match
the catalogue formula and 48 differ. Most differences are benign (leg-grain formula vs composed
atoms; the player zero-fill the 2026-06-25 ruling requires). **ONE is real: `finishing_efficiency`
clamps to NULL when goals-minus-penalties is negative or exceeds shots on target, and the catalogue
says nothing about it.**

`assert_metric_catalogue_value_equivalence.sql` recomputes each formula over its `base_relation` at
the model's grain and diffs the VALUES. Built, parses, 66/80 verified, 14 declared skips, ships at
`severity='warn'` because it reports `finishing_efficiency` on its first run.
⭐ **THE FILE IS AT `C:\Users\Rami\.claude\projects\D--Projects-football-data-pipeline\parked\`**
(with `verify_catalogue.py`, `eolcheck.py`, `repoint.py` — all reusable). Its yml companion (a
`unique_combination_of_columns` on `int_player_season__metrics` for `(player_sk, league_code,
season_api_year)`) is in the stash labelled **"PARK: value-equivalence test"** — match by MESSAGE.
⚠ **BEFORE IT SHIPS**: add 5 `model_column_alias` entries for the new rows (`goals_for|team` →
`goals_for_sum_season`, same shape for `goals_against`, `corner_kicks`, `goalkeeper_saves`,
`shots_inside_box`). It was written for 9 rows; 4 were dropped.
⚠ It must ship on a main that ALREADY carries the rows it reads. That is now true.
⚠ Its acceptance argument is a 7-mutation table, NOT a green run — it cannot execute offline
(`run_query` needs a warehouse; `dbt build` is forbidden).

## ⛔ OPEN, ALL THE CPO'S — none blocks the two tasks above

1. **`--defer --favor-state` (`.gitlab-ci.yml:653`) makes ALL 28 singular tests read PROD on an
   MR**, so a model change cannot go red until it has merged. The job comment at `:636` claims the
   reverse. A CI change of that class was built, FAILed twice and reverted.
2. **`mart_team_momentum.sql:42-117` is a SECOND hand-written copy of ~20 team formulas and HAS
   ALREADY DRIFTED** — its `shot_accuracy` (:56-59) gates on one coverage counter while
   `int_team_season__metrics_cumulative.sql:100-104` gates on two. Fold it into the shared model
   (the COMPOSE standard, `engineering_standards.md:58`) or keep two copies and test both.
3. **`mart_team_momentum.sql:104-106` credits leaving the player-derived team metrics ungated to
   "CPO 2026-06-25"; `escalations.log:227` that day says the opposite.** ⚠ A CONTRADICTED
   ATTRIBUTION IN SHIPPED CODE — put it to him as that, never as evidence he ruled it.
4. **#89** — `finishing_efficiency` follows neither tier rule and is tier 1 for teams, tier 2 for
   players; the only metric that differs across entities.
5. **The naming grammar.** NOT built: its own review returned FATAL (it would outlaw 146 existing
   columns, send 5 pairs to one name, and 28 of its targets were ungrammatical). ⭐ Two CPO rulings
   this session cleared most of what blocked it — **a result is not a metric**, and **context = the
   WINDOW a formula runs over, never the formula**. Worth restarting on that footing.

## ⭐ DESCRIPTION PROGRAMME (#82) — paused, 111 names / 300 columns left

48 derived families · 14 multi-meaning · 31 whose written sites DISAGREE · 11 · 7 h2h. Then **MR5**
switches the presence rule on. ⛔ Plus **~40 the catalogue MR left blank**: they resolve to
`<name>__team`, so `--wire-shared-docs` cannot match, and `--wire-metric-docs` refuses because
`int_team_momentum__metrics` is absent from `declare_missing_columns.py`'s `MODEL_ENTITY` (a
one-line fix, deliberately out of that MR's scope).
⛔ **A NAME CAN MEAN TWO QUANTITIES WITH EVERY SITE BLANK** (`goals_for`), and **a column that IS a
catalogue metric under another NAME is invisible to the generator** (`key_passes_prev_season_full`
= `passes_key`). Classify by what each model's SQL DOES.
⛔⛔ **GIVING A MULTI-GRAIN NAME A CATALOGUE ROW SILENTLY RE-ARMS THE GENERATOR.** That is how a
per-match sentence reached 18 cumulative columns in `!104`. **The catalogue says WHAT is measured;
the model says over what span** — `sync_metric_docs_blocks.py:84` enforces it by rejecting the bare
word "window" in any seed description.
⚠ **REGENERATE** `sync_metric_docs_blocks.py` after editing the seed AND after adding a derived
column — its second input is the model YAML.

## ⛔⛔ THE LESSON FROM `!104` — 5 rounds, 7 FAILs, FOUR of them one root cause

**I narrate an outcome in prose and never write it into the file that is PARSED.** The contract is
the file already open, so writing the story there feels like recording it. Instances: the contract
cited `escalations.log` for rulings the log did not hold; a tier was declared for 4 of 5 rows in the
section arguing such values must be declared; `review.md` read "pending" while the contract narrated
a finished round; the `rounds_cap_override` quoted the CPO from prose alone.
⭐ **THE RULE: a ruling is appended to `escalations.log` in the SAME TURN it is given; a verdict is
written into `review.md` BEFORE it is written about anywhere else.** Backfilling is allowed and was
judged acceptable — the entry must disclose its own after-the-fact timing on its face — but it cost
four rounds. And before claiming a file "records" something, OPEN IT AND GREP.
⚠ **NEVER SAY "YOU RULED" WITHOUT A QUOTE FROM `escalations.log`.** A seed description, a code
comment or my own memory file is REPO PRACTICE. Said as his ruling, it drew a flat "No, I didn't".

## ⭐ OPERATIONAL

⛔ **A TOO-LONG DESCRIPTION BREAKS PROD.** `persist_docs` on for 97 models + 9 seeds. **1,024**
chars/column, **16,384**/relation; one over = HTTP 400 and the model FAILS.
⚠ **`git stash push -- <paths>` SNAPSHOTS THE WHOLE INDEX**, so popping it clobbers files edited
meanwhile. Extract with `git checkout stash@{0} -- <paths>`, then drop. Hit twice in one session.
⚠ **`--review-patch` writes to STDOUT** — without a redirect the patch is silently the PREVIOUS
task's. `escalations.log` is in `hash_exclude_paths` but NOT `review_exclude_paths`: reviewers see
it, the hash ignores it.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** Send it and WAIT.
⚠ **A too-narrow grep reported as a clean sweep**, and a keyword scan is blind to a claim using no
keyword. **A bulk-edit script reporting success while matching nothing** — assert it found work.
⛔⛔ **INVERT THE NUMBER SWEEP**: pull EVERY integer out of the artifacts and ask of each "is this
still true", rather than sweeping for the ones you remember changing. A figure was stale across
three revisions in `!104` and only a reviewer's hand-count found it. **#71**.
⚠ **OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics, contract stash
dance, CWD/fnmatch/heredoc traps) — not capped, do not copy back.
**FIRST ACTION: `git stash list`.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never be rebuilt:
**`feat/player-overview-tab`**.

## ⭐ OTHER STANDING STATE

⛔ **TEAM NAMES — paused.** `team_name_overrides` (`base_apif__teams_global.sql`) fires on
completeness OR collision. **97 of ~130 Pool 1 corrected**, each citing an English Wikipedia URL.
⚠ **Bayern München EXCLUDED ON PURPOSE**. NOT done: ~15 Pool 1, teams outside it, `dim_player`
short-names. **#81** = duplicates for ONE club.
✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders next matches ALONE. TOP
TEAMS = one per league, not pooled.
⛔ **#83** — competition classification has no core dim; 12 models join the seed direct.

## ⭐⭐ THE METHOD, standing rule for every page (CPO's words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element:
(1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, and reading one from a
page is the same violation as computing in the frontend; (2) no mart column = a GAP, registered in
`99_gaps_register.md` BEFORE building; (3) check the mock's OWN numbers against the spec.
⚠ **The handover rides in the SAME commit as the code it describes.**
⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/CI facts check the system that owns them
(`bq ls`, `glab api`, `gcloud` — free metadata). Bit twice.
**Audits: GitLab #30, DO NOT run another** (a TARGETED blind assessment IS allowed).
