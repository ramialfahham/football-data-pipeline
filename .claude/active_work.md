# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-29**. **main `3c302af`** (after `!123`). **METRIC CATALOGUE NAMING PROGRAMME
— STEP 3 IS COMPLETE.** All twelve team renames are merged and live: `!114` `!116` `!119` `!120`
`!121` `!123`. (`!111`/`!112` did three earlier renames that PREDATE the "12 REMAINING" table; do not
count them.) `data:build:main` on the merge was green — **97 models, 882 tests PASS=881 WARN=1
ERROR=0** — so PROD now carries every renamed column. The one WARN is
`accepted_values_fct_fixture_status_short` (2 rows, a provider status code in `3_core`), pre-existing
and unrelated. **Nothing is in flight.** **GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: STEP 4 — the 35 PLAYER renames

Full list in `.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME",
table "⛔ PLAYER, 35 REMAINING". ⛔ **CITE THAT BLOCK BY CONTENT, never by line number and never a
plan file** — two MRs were FAILed for citing a plan file, one for a decayed line number.
⭐ **WHEN A RULING IS A PATTERN, THE PATTERN IS THE AUTHORITY** for every name it determines:
`noun [_qualifier] [_against] [_player] [_form]`. Cite it up front; D burned three rounds hunting a
per-name quote the pattern had already settled.

⛔ **BLOCKED ON ONE CPO RULING, and it must be settled BEFORE the work, not mid-batch:**
`contribution_share` → `contribution_player_pct` is the ONE name in the 35 he did not rule on
directly — my proposal, unobjected.

⛔ **#99 — THE EXPORT SILENTLY NULLS OUT ON THIS RENAME.** `scripts/export_site_data.py` reads two
catalogue PLAYER metrics by literal key with `.get()` and no default: `_shape_squad_member`
(`:192-193`, the team page Squad tab) and the career shaper (`:443-444`, the player payload), both
off `mart_player_career`. Step 4 renames `goals → goals_player` and `assists → assists_player`, after
which `.get()` returns `None` for every row — **no KeyError, no failing test**, payload keys unchanged
and every value null. Move both read keys with the rename.

⛔ **THE DOC-BLOCK MERGE FIRES AGAIN, IN REVERSE.** `!123` left `finishing_efficiency` as a
PLAYER-only `metric_id` with a BARE block; step 4 renames it to `finishing_efficiency_player_pct`.
`sync_metric_docs_blocks.py`'s `_blocks()` splits `__team`/`__player` ONLY where the rows disagree,
so whenever a shared `metric_id` stops being shared the blocks collapse to bare and **every `doc()`
pointing at a suffixed name dangles — including on the entity the MR is NOT renaming.** `!123`
re-pointed 6 team + 3 player refs for exactly this. `check_description_hygiene.py` catches it;
regenerate, then run it.
⚠ **The label guard covers almost NONE of the 35** — the player surface is largely unbuilt — so
criterion 3 needs a different mutation target. Read the guard before choosing one (below).
⚠ **The four acceptance criteria were standing for B–F only.** That mandate ENDED with `!123`.
Step 4 needs its own set, approved before the work.

**STEP 5** = the 9 English `label_en` rows, "on target" → "on goal". `finishing_efficiency_pct`'s
label still reads "% Goals per shot on target" today, deliberately.
⚠ **STEP 5 HAS A TARGET THE 9-ROW LIST MAY MISS**: the EN hero sentences at
`site_v2/src/i18n/strings.ts:94-95` read "shots-on-target difference" — UI SENTENCE strings, not
catalogue `label_en` rows.

## ⛔ THE SAMPLE REFRESH — OWED, AND IT RUNS **AFTER STEP 4**, NOT BEFORE

⛔ **DO NOT RUN IT NOW, AND DO NOT START IT WITHOUT THE CPO.** Measured 2026-08-29: **step 4 stales
the sample again.** `site_v2/src/data/teams/33.json` carries a `squad` block whose members hold
`goals` and `assists` — both catalogue PLAYER metrics (seed rows 29/30), renamed in step 4. So
refreshing before step 4 means refreshing twice. Step 5 touches only `label_en`, which never reaches
a payload key, so it stales nothing. **One refresh, after step 4.**
⚠ Current damage, and it is invisible: the committed sample still serves the OLD keys, so
`MetricComparison.astro`'s `hasData()` drops **4 of the 16 locked fixture rows** —
`shots_inside_box_pct`, `passes_accuracy_pct`, `passes_key_per_match`, `finishing_efficiency_pct`.
Built fixture pages render **12**. Honest-absent, never blank, never a fabricated zero. Nothing
public degrades: the site is unlisted and `deploy:site-v2` is manual-only.
⛔ **THE OBVIOUS RECIPE IS A TRAP.** `fetch_fixture_payloads` (`export_site_data.py:806`) selects
`status_short in ('NS','TBD') and fixture_date >= current_date()` — UPCOMING ONLY — and a kicked-off
fixture has **0 rows** in `mart_team_momentum` / `mart_team_season_record` (queried). A rerun exits
**0**, reports thousands written, and changes **nothing** you care about. **ROLL THE WHOLE SET
FORWARD** — full recipe in `site_v2/src/data/README.md`. New ids mean new page URLs.
⚠ It needs upcoming fixtures in the marts, which needs INGESTION to have run. **There is still no
nightly SCHEDULE on GitLab** — `data:nightly` is manual-dispatch only — so RAW is only as fresh as
the last manual run. Check before promising a refresh can happen.
⚠ `git clean -fX` is BLOCKED here. Use `git ls-files --others --ignored --exclude-standard <dir>` as
the delete set — `--others` makes it structurally unable to pick a tracked file. Dry-run first.

## ⭐ THE RENAME METHOD — proven over C, D, E and F. Use it verbatim.

⛔⛔ **`\b` FAILS AGAINST `_`.** A word-boundary replace cannot reach `home_<id>_recent`,
`<id>_this_season`/`_prev_season`/`_delta_yoy`, or `std_team_<id>_in_range`.
⭐ **CLASSIFY EVERY TOKEN CONTAINING THE STEM ONCE, AND PRINT THE DECISION.** (D: 147/34. E: 77.
F: 108 renamed / 36 protected, each with its reason.) **ABORT before writing if a protected token's
count would change**, and verify the post-transform token multiset per file.
⭐ **SCOPE BY OWNING MODEL, NOT BY FILE NAME, AND ABORT ON AN UNLISTED MODEL.** `mart_leaderboards`
is a PLAYER mart whose name contains neither "player" nor "team"; a substring rule mis-scopes it and
would rename `mart_leaderboards_<id>_in_range`, the one range test that must not move.
⛔ **THE `accepted_values` LISTS COME IN TEAM *AND* PLAYER FLAVOURS.** Three 22-name TEAM lists
(`int_competition_benchmarks.yml:27`, `:66`, `shared.yml:2080`) — and three PLAYER ones
(`int_competition_benchmarks.yml:105` 18, `shared.yml:2186` 18, `shared.yml:1756` 14, the rate
boards). F found the player three; the record had only ever named the team three.
⚠ **A NO-OP WRITE IS STILL A WRITE.** F's script rewrote 8 files whose every occurrence was
protected — content byte-identical, `git diff` clean — and the contract gate refused, correctly,
because it watches the FILE SYSTEM. Skip zero-rename files, or `git checkout --` them.
⭐ Sweep before AND after: `git grep -ohE "[a-z_0-9]*(<old>)[a-z_0-9]*" | sort | uniq -c`.
⭐ **Re-count every protected token against `git grep <base-sha>`, never against a note.**
⛔ **PROTECT ANYTHING AN i18n STRING INTERPOLATES** (E's `sotd`) and any MVP `live_id`
(`<id>_recent` STANDING ALONE in `metric_bindings.csv`; the `home_`/`away_` forms are NOT protected).
⚠ **`git grep` SCOPES TO THE CWD** and CWD persists between Bash calls. Assert `cd <repo root>` in
the same command as any counting grep.
⚠ **`data:build:mr` SELECTS `state:modified+`**, so surfaces the MR does not touch are NOT built or
tested there — only `data:build:main` exercises them. Do not read an MR-green as full coverage.

## ⭐ THE PER-MR RECIPE

1. Branch from main. Contract on a CLEAN tree, with the `dbt ls --select <model>+` lineage PASTED.
   ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST** — it under- AND over-counts.
2. Rename: seed (`metric_id` AND `label_i18n_key`), models, ymls, the SIX `accepted_values` lists,
   marts, `docs/wireframes/`, `site_v2/src`, and any literal read key in `export_site_data.py`.
3. Frozen `site/` — ONLY where a live gate forces it, and only catalogue-id plumbing. Never wording,
   never page code (`site/team-season/index.html` is deliberately stale), never `live_id`.
4. Regenerate, never hand-edit: `sync_metric_docs_blocks.py`, `export_metric_definitions_json.py`.
5. Gates + mutations watched going RED. Evidence read from the BUILT site.
6. **Measure the built pages STRUCTURALLY** — `<div class="mrow">` per row, `<div class="mgroup">`
   per heading, two blocks per fixture page. Never by substring.

## ⛔ TRAPS THAT COST REAL TIME — read before reporting anything green

⛔⛔ **NEVER PIPE A GATE THROUGH `tail`/`head`, AND NEVER READ A CLOSING BANNER AS A VERDICT.**
`sqlfluff … | tail -3` truncated away an `LT05` FAIL leaving `All Finished!`, which it prints on
failure too; the pipe also masked the exit code. **CI caught that one, not me.** Same class: the
export printed `exit 0` + "5,066 written" while changing none of the 17 files that mattered.
Redirect to a file and grep the failure token, or run bare and read the exit code UNPIPED.
⛔⛔ **A CHECK THAT PASSES EQUALLY ON THE WORK AND ON ITS ABSENCE IS NOT A CHECK.** On F a `sed` in
an intersection check failed to compile, so the flagged-file list came back EMPTY and the check
printed the same reassuring line a real pass prints. Ask git per file instead.
⛔ **A SUBSTRING TEST IS NOT A PRESENCE TEST**, rendered (`Ø Corners` matches inside
`Ø Corners against`) or in source (`grep -o points_capture` returned 25, all inside
`points_capture_pct`; true count 0). Tally WHOLE TOKENS, or count STRUCTURALLY.
⭐ **THE LABEL GUARD COVERS `metricRows.ts`'s 16 PLUS the keys `DeservedHero.astro` asks for, and
NOTHING ELSE** — `check-metric-labels.test.mjs:36-38`, `asked = rowKeys ∪ heroKeys`. Grep BOTH before
relying on it. ⚠ It also carries an EN exemption keyed on a literal metric id at `:99`.
⚠ **LT05 MEASURES TEMPLATED LENGTH, NOT RAW LENGTH.** A 124-char line inside a `{# … #}` jinja
comment lints clean; a 123-char `--` SQL comment FAILS. No YAML line-length gate exists.
⛔ **THE CONTRACT MAY ONLY BE (RE)WRITTEN ON A CLEAN TREE.** `.claude/active_work.md` counts as
dirty; `.claude/task/` does not. ⚠ `git reset --hard` and `git clean` are blocked; heredoc file
writes are blocked — use Edit/Write.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** ⚠ Rewriting `review.md` for a new round DROPS the
standing verdicts — re-add every required reviewer.
⭐ **LIVING DOCUMENT → REPLACE. DATED LOG → APPEND.** `escalations.log` is a dated chronology —
never edit a merged block; append a correction.
⛔⛔ **SWEEP, DO NOT POINT-PATCH.** E took **7 review rounds**; the code was correct after round 1
and every finding was in prose. **When a reviewer names an instance, fix the CLASS**, and sweep the
whole document before dispatching the next round. F took **1 round, five PASSes, no findings** —
that is what pre-empting the known finding classes in the contract buys.
⚠ **THE ROUND CAP IS 3** (`git_discipline.py`, §3). Past it, STOP and bring the findings to the CPO;
to continue, `review.md` needs `rounds_cap_override: <his reason>`.
⚠ `--review-patch` writes to STDOUT — redirect it. `git checkout <branch>:<path>` MANGLES; export
`MSYS_NO_PATHCONV=1`. **OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics).
**FIRST ACTION: `git stash list`** — 17 entries. ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never
be rebuilt: **`feat/player-overview-tab`**.

## ⛔ OPEN, ALL THE CPO'S

- **`contribution_share` → `contribution_player_pct`** — settle before step 4 (above).
- **#96 — FIVE CONSECUTIVE REPRODUCTIONS** (`!114` `!119` `!120` `!121` `!123`). Reverting one entry
  of a 22-name `accepted_values` list survives the ENTIRE offline suite; only `data:build:mr` catches
  it. `platform-reviewer` recommends a small offline test (parse the ymls, assert the lists match the
  model columns — no new CI job). NEW MECHANISM, therefore his call. **Until then, check the lists BY
  EYE every batch — team AND player.**
- **THE REVIEW-LOOP COST IS STRUCTURAL.** `contract.md` is hash-bound, so a one-word prose fix voids
  all five verdicts and forces five re-runs. The evidence artifacts are already hash-excluded for
  exactly this reason. Whether a contract's NARRATIVE sections should join them (keeping
  `scope_paths` and `acceptance_criteria` hashed, since they carry authority) is a governance
  decision, not a batch task.
- **#98** — the seven metric GROUP HEADINGS render in ENGLISH on DE/FI
  (`MetricComparison.astro:40`, `TeamPerformance.astro:89`/`:110`). §10 (the words are his).
  `TeamSquad.astro:99` already does it right — copy that pattern.
- **#99** the export's literal player read keys (above) · **#97** `docs/roles/` sweep · **#93**
  `mart_team_momentum` duplicates ~20 formulas · **#94** naming grammar · **#89**
  `finishing_efficiency` tier · **#82** ~40 blank descriptions · **#83** no competition-classification
  dim · **#91** parked value-equivalence checker (waited for the renaming to finish — step 3 is now
  done, steps 4/5 are not; file in `parked/` beside the memory dir, yml in the stash "PARK:
  value-equivalence").
- **#92** FIXED (`!115`): CI datasets are PER MERGE REQUEST (`ci_mr<IID>_*`). ⛔ **Nothing expires or
  deletes them, by CPO instruction.** ~6 GB, ~12¢/month. Do not add a TTL or cleanup step.

## ⭐ OTHER STANDING STATE

⭐ **THE CPO'S DIRECTION, 2026-08-29:** finish the metric names, then get back to PRODUCT work — and
keep the data foundations moving alongside it rather than instead of it.
✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders next matches ALONE. TOP
TEAMS = one per league, not pooled.
⛔ **Points is a synthetic 3-1-0 tally in EVERY competition** (`int_team_season_record.sql:73`) — FA
Cup renders 0, Europa League 32 against a real 18. **The mart must emit NULL.** Blocks the team
Overview for cups.
⛔ **The deserved-vs-actual hero is EXACT ONLY for a COMPLETED season.** Two CPO decisions OPEN
before it touches live data: how to render the fitted line mid-season, and from which matchday.
⚠ **The metric rows render on NO built team page today**: the sample's featured season (team 33, PL
2026) has 1 game, below the `>= 3 finished games` benchmark floor, so the team Performance tab shows
"not enough games to rank". Never write an acceptance criterion that reads a metric ROW off the team
page. The metric NAMES do render on the fixture pages.
⛔ **#95 — read before touching any slug or team name.** `team_slug` is documented PERMANENT and is
RE-DERIVED FROM `team_name` ON EVERY BUILD, so correcting a name MOVES A PUBLISHED URL. Team 33
already moved to `manchester-united-fc`. Team-names programme PAUSED part-way (97 of ~130 Pool 1).
