# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-29**. **main `cdd2218`** (after `!122`). METRIC CATALOGUE NAMING PROGRAMME
**step 3 is COMPLETE with this branch**: batch **F** — `finishing_efficiency` →
`finishing_efficiency_pct` (team) — is on `refactor/metric-rename-team-finishing-efficiency`, the
twelfth and last team rename. The other eleven merged via `!114` `!116` `!119` `!120` `!121`.
(`!111`/`!112` did three earlier renames that PREDATE the "12 REMAINING" table; do not count them.)
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: the FINAL export-sample refresh — and it is the CPO's call WHEN

⛔ **DO NOT START IT WITHOUT TELLING HIM.** He decides when it runs.
⛔ **THE OBVIOUS RECIPE IS A TRAP.** "Rerun the export and the committed payloads update" CANNOT
work: `fetch_fixture_payloads` (`scripts/export_site_data.py:806`) emits UPCOMING fixtures only
(`status_short in ('NS','TBD') and fixture_date >= current_date()`), and a kicked-off fixture has
**0 rows** in `mart_team_momentum` / `mart_team_season_record` (queried, not reasoned about), so a
past id can never be re-exported. The export exits **0**, reports thousands written, and changes
**nothing** you care about. **ROLL THE WHOLE SET FORWARD** — recipe in `site_v2/src/data/README.md`.
⚠ It can only run once prod carries the renamed columns, i.e. after `data:build:main` on F's merge.
⚠ `git clean -fX` is BLOCKED here. Use `git ls-files --others --ignored --exclude-standard <dir>` as
the delete set — `--others` makes it structurally unable to pick a tracked file. Dry-run first.
⚠ Rendered fixture rows across the programme: 16 → 15 (C) → 13 (D) → 13 (E) → **12 (F)**.
Honest-absent, not broken; the refresh closes it and should take it back to 16.

## ⭐ THEN STEP 4 — the 35 PLAYER renames, and step 5

**STEP 4** = the 35 player renames (full list in the log's "⛔ PLAYER, 35 REMAINING").
⛔ **SETTLE `contribution_share` → `contribution_player_pct` WITH THE CPO FIRST.** It is the ONE name
in that list he did not rule on directly — my proposal, unobjected. Not a mid-batch decision.
⛔ **THE DOC-BLOCK MERGE FIRES AGAIN, IN REVERSE.** F left `finishing_efficiency` as a PLAYER-only
`metric_id` with a BARE block; step 4 renames it to `finishing_efficiency_player_pct`. Whenever a
shared `metric_id` stops being shared, `sync_metric_docs_blocks.py`'s `_blocks()` collapses
`__team`/`__player` to bare and **every `doc()` pointing at the suffixed name dangles** — including
on the entity the MR is NOT renaming. F re-pointed 6 team + 3 player refs for this reason.
`check_description_hygiene.py` is what catches it; regenerate, then run it.
⚠ **The label guard covers almost NONE of the 35** — the player surface is largely unbuilt — so
criterion 3 needs a different mutation target. Read the guard before choosing one (below).
**STEP 5** = the 9 English `label_en` rows, "on target" → "on goal". `finishing_efficiency_pct`'s
label is one of them and still reads "% Goals per shot on target" today, deliberately.
⚠ **STEP 5 HAS A TARGET THE 9-ROW LIST MAY MISS**: the EN hero sentences at
`site_v2/src/i18n/strings.ts:94-95` read "shots-on-target difference". UI SENTENCE strings, not
catalogue `label_en` rows.

## ⭐ THE RENAME METHOD — proven over C, D, E and F. Use it verbatim.

⛔⛔ **`\b` FAILS AGAINST `_`.** A word-boundary replace cannot reach `home_<id>_recent`,
`<id>_this_season`/`_prev_season`/`_delta_yoy`, or `std_team_<id>_in_range`.
⭐ **CLASSIFY EVERY TOKEN CONTAINING THE STEM ONCE, AND PRINT THE DECISION.** (D: 147/34. E: 77
renamed. F: 108 renamed / 36 protected, each with its reason.) **ABORT before writing if a protected
token's count would change**, and verify the post-transform token multiset per file.
⭐ **SCOPE BY OWNING MODEL, NOT BY FILE NAME, AND ABORT ON AN UNLISTED MODEL.** `mart_leaderboards`
is a PLAYER mart whose name contains neither "player" nor "team"; a substring rule mis-scopes it.
⚠ **A NO-OP WRITE IS STILL A WRITE.** F's script rewrote 8 files whose every occurrence was
protected. Content byte-identical, `git diff` clean — but the contract gate watches the FILE SYSTEM
and refused. Skip files with zero renames, or `git checkout --` them.
⭐ Sweep before AND after: `git grep -ohE "[a-z_0-9]*(<old>)[a-z_0-9]*" | sort | uniq -c`.
⭐ **Re-count every protected token against `git grep <base-sha>`, never against a note.**
⛔ **PROTECT ANYTHING AN i18n STRING INTERPOLATES** (E's `sotd`) and any MVP `live_id`
(`<id>_recent` STANDING ALONE, in `metric_bindings.csv`; the `home_`/`away_` forms are NOT protected).
⛔ **THE `accepted_values` LISTS COME IN TEAM *AND* PLAYER FLAVOURS.** Three 22-name TEAM lists
(`int_competition_benchmarks.yml:27`, `:66`, `shared.yml:2080`) — and three PLAYER ones
(`int_competition_benchmarks.yml:105` 18, `shared.yml:2186` 18, `shared.yml:1756` 14). F found the
player three; the record had only ever named the team three.
⚠ **`git grep` SCOPES TO THE CWD** and CWD persists between Bash calls. Assert `cd <repo root>` in
the same command as any counting grep.

## ⭐ THE PER-MR RECIPE

⭐ **THE FOUR ACCEPTANCE CRITERIA WERE STANDING FOR B–F** (CPO "do it", in the log) — that mandate
ENDS with F. Step 4 needs its own, and criterion 3 must name a mutation target the guard reaches.
1. Branch from main. Contract on a CLEAN tree, with the `dbt ls --select <model>+` lineage PASTED.
   ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST** — it under- AND over-counts.
2. Rename: seed (`metric_id` AND `label_i18n_key`), models, ymls, the SIX/THREE `accepted_values`
   lists, marts, `docs/wireframes/`, `site_v2/src`.
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
printed the same reassuring line a real pass prints. Ask git per file instead. The CPO ruled the
same way rejecting build-both-trees-and-diff.
⛔ **A SUBSTRING TEST IS NOT A PRESENCE TEST**, rendered (`Ø Corners` matches inside
`Ø Corners against`) or in source (`grep -o points_capture` returned 25, all inside
`points_capture_pct`; true count 0). Tally WHOLE TOKENS, or count STRUCTURALLY.
⭐ **THE LABEL GUARD COVERS `metricRows.ts`'s 16 PLUS the keys `DeservedHero.astro` asks for, and
NOTHING ELSE** — `check-metric-labels.test.mjs:36-38`, `asked = rowKeys ∪ heroKeys`. Grep BOTH before
relying on it. ⚠ It also carries an EN exemption keyed on the literal metric id at `:99` — re-point
it on any rename that touches `finishing_efficiency_pct`.
⚠ **LT05 MEASURES TEMPLATED LENGTH, NOT RAW LENGTH.** A 124-char line inside a `{# … #}` jinja
comment lints clean; a 123-char `--` SQL comment FAILS.
⛔ **THE CONTRACT MAY ONLY BE (RE)WRITTEN ON A CLEAN TREE.** `.claude/active_work.md` counts as
dirty; `.claude/task/` does not. ⚠ `git reset --hard` and `git clean` are blocked; heredoc file
writes are blocked — use Edit/Write.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** ⚠ Rewriting `review.md` for a new round DROPS the
standing verdicts — re-add every required reviewer.
⭐ **LIVING DOCUMENT → REPLACE. DATED LOG → APPEND.** `escalations.log` is a dated chronology —
never edit a merged block; append a correction.
⛔⛔ **SWEEP, DO NOT POINT-PATCH.** E took **7 review rounds**; the code was correct after round 1
and every finding was in prose. **When a reviewer names an instance, fix the CLASS**, and sweep the
whole document before dispatching the next round.
⚠ **THE ROUND CAP IS 3** (`git_discipline.py`, §3). Past it, STOP and bring the findings to the CPO;
to continue, `review.md` needs `rounds_cap_override: <his reason>`.
⚠ `--review-patch` writes to STDOUT — redirect it. `git checkout <branch>:<path>` MANGLES; export
`MSYS_NO_PATHCONV=1`. **OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics).
**FIRST ACTION: `git stash list`** — 17 entries. ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never
be rebuilt: **`feat/player-overview-tab`**.

## ⛔ OPEN, ALL THE CPO'S

- **#96 — FIVE CONSECUTIVE REPRODUCTIONS** (`!114` `!119` `!120` `!121` F). Reverting one entry of a
  22-name `accepted_values` list survives the ENTIRE offline suite; only `data:build:mr` catches it.
  `platform-reviewer` recommends closing it with a small offline test (parse the ymls, assert the
  lists match the model columns — no new CI job). That is a NEW MECHANISM and therefore his call.
  **Until then, check the lists BY EYE every batch** — team AND player.
- **THE REVIEW-LOOP COST IS STRUCTURAL.** `contract.md` is hash-bound, so a one-word prose fix voids
  all five verdicts and forces five re-runs. The evidence artifacts are already hash-excluded for
  exactly this reason. Whether a contract's NARRATIVE sections should join them (keeping
  `scope_paths` and `acceptance_criteria` hashed, since they carry authority) is a governance
  decision, not a batch task.
- **`contribution_share` → `contribution_player_pct`** — settle before step 4 (above).
- **#98** — the seven metric GROUP HEADINGS render in ENGLISH on DE/FI
  (`MetricComparison.astro:40`, `TeamPerformance.astro:89`/`:110`). §10 (the words are his).
  `TeamSquad.astro:99` already does it right — copy that pattern.
- **#97** `docs/roles/` sweep · **#93** `mart_team_momentum` duplicates ~20 formulas · **#94** naming
  grammar · **#89** `finishing_efficiency` tier · **#82** ~40 blank descriptions · **#83** no
  competition-classification dim · **#91** parked value-equivalence checker (waits for the renaming
  to finish — step 3 is now done, steps 4/5 are not; file in `parked/` beside the memory dir, yml in
  the stash "PARK: value-equivalence").
- **#92** FIXED (`!115`): CI datasets are PER MERGE REQUEST (`ci_mr<IID>_*`). ⛔ **Nothing expires or
  deletes them, by CPO instruction.** ~6 GB, ~12¢/month. Do not add a TTL or cleanup step.

## ⭐ OTHER STANDING STATE

✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders next matches ALONE. TOP
TEAMS = one per league, not pooled.
⛔ **Points is a synthetic 3-1-0 tally in EVERY competition** (`int_team_season_record.sql:73`) — FA
Cup renders 0, Europa League 32 against a real 18. **The mart must emit NULL.** Blocks the team
Overview for cups.
⛔ **The deserved-vs-actual hero is EXACT ONLY for a COMPLETED season.** Two CPO decisions OPEN
before it touches live data: how to render the fitted line mid-season, and from which matchday.
⚠ **The metric rows render on NO built page today**: the sample's featured season (team 33, PL 2026)
has 1 game, below the `>= 3 finished games` benchmark floor, so the team Performance tab shows
"not enough games to rank". Never write an acceptance criterion that reads a metric ROW off the team
page. The metric NAMES do render on the fixture pages.
⛔ **#95 — read before touching any slug or team name.** `team_slug` is documented PERMANENT and is
RE-DERIVED FROM `team_name` ON EVERY BUILD, so correcting a name MOVES A PUBLISHED URL. Team 33
already moved to `manchester-united-fc`. Team-names programme PAUSED part-way (97 of ~130 Pool 1).
