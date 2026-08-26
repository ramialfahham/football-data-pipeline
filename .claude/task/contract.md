# Task contract — refresh the committed export sample after #90

objective: >
  #90 renamed a benchmark `metric_key` and the team yoy family. The committed export SAMPLE under
  `site_v2/src/data/` was exported before that, so it still carries the old names and the team
  page's "vs the league" panel renders **15 rows instead of 16** — the clean-sheet row is dropped
  because the page looks up `clean_sheets_share` and the sample serves `clean_sheets`.

  #90 disclosed this in `decisions_reserved` as a follow-up that could not run until
  `data:build:main` had materialised the new columns. It has: pipeline `2792466771` on `7fbe8ac`
  is green on all eight jobs, and `bq show --schema marts.mart_team_profile` now lists
  `clean_sheets INTEGER` beside `clean_sheets_share_this_season / _prev_season / _delta_yoy` as
  FLOAT. So the refresh is unblocked, and the CPO authorised it this session.

  ⭐ MEASURED, AND IT MAKES THE TASK ONE FILE: only `teams/33.json` is stale. Every committed
  payload was scanned for the four renamed keys — `teams/33.json` has 94 hits and **every other
  tracked file has zero**. The 17 fixture payloads carry `clean_sheets` as a COUNT from
  `mart_team_momentum` and `mart_team_season_record`, neither of which #90 touched, so they are
  still correct and are NOT re-exported.

  ⛔ THAT IS WHY `landing.json` IS NOT REGENERATED. `site_v2/src/data/README.md:45-47` warns that
  regenerating it changes WHICH fixture and team ids belong in the sample, which would force a
  matching `.gitignore` allowlist edit and a churn of the whole set — for a reason unrelated to
  this rename. Nothing in `landing.json` is stale, so it stays.

refs: >
  Follow-up to #90 (`!107`, merged as `7fbe8ac`), named in that contract's `decisions_reserved`.
  CPO authorised the refresh in conversation this session ("refresh the sample"), after being shown
  what it means and that it carries a BigQuery read cost. That is an INSTRUCTION, not a ruling on a
  contested question, so nothing is appended to `escalations.log`.
  Procedure per `site_v2/src/data/README.md`. Branched from main `b281609`, clean tree.

scope_paths:
  - site_v2/src/data/teams/33.json
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ NO script, NO model, NO frontend source and NO `.gitignore` change. The tracked file set does
# not move, so the allowlist does not move. `site_v2/src/data/README.md` is NOT in scope — see
# decisions_reserved for its stale count.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: NONE in this repo. The changed bytes are export OUTPUT, produced verbatim by
    `python scripts/export_site_data.py --entities teams` reading five marts. No SQL, no script and
    no frontend source is edited, so nothing this repo computes changes behaviour.

  upstream, and its measured cost: the five queries `fetch_team_payloads` issues, sized by
    `bq query --dry_run` before running anything (free metadata):
      mart_team_profile                   5.9 MiB
      mart_team_fixtures                  8.3 MiB
      mart_roster                        82.4 MiB
      mart_team_competition_benchmarks    2.6 MiB
      mart_player_career                 58.5 MiB
      TOTAL                             157.7 MiB  = 0.154 GiB
    At on-demand rates that is well under $0.01 and inside the monthly free tier. It is a ONE-OFF
    read, not a recurring job, and it adds no schedule.

  downstream: the Astro build reads `site_v2/src/data/**` at build time; `teams/33.json` is the
    only committed team payload, so the blast radius is the three built team pages (en/de/fi) and
    nothing else. `audit-seo.mjs` checks that every internal link resolves to an emitted page — the
    tracked file SET is unchanged, so no link can break.

  blast_radius: the team page's "vs the league" panel goes from 15 rows to 16, with the
    clean-sheet row ranked again under `% Clean sheets`. The "vs last season" panel's row 3 gains a
    real value and delta in place of its two en-dashes. No other row moves.

  layer_rules: none engaged. Exported data is not authored data; the export selects and reshapes
    and derives no fact, and this task does not change what it selects.

  deploy_order: none. The site build picks the file up on its next run.

decisions_taken: >
  THRESHOLD DECLARATION — NEW MECHANISM: none. An existing script, run as documented.
  THRESHOLD DECLARATION — RECURRING COST: none. One-off read, measured above at 0.154 GiB.

  BUILDER'S CALL 1: `--entities teams` ONLY, not the full set the README's "refresh as a set"
    sentence describes. That sentence exists because regenerating `landing.json` moves the sample's
    membership; it is not a rule that every file must be re-exported whenever any one of them
    changes. Measurement decides it here — 94 stale hits in one file, zero everywhere else — and
    re-exporting files whose content is provably still correct would put churn in the diff that no
    reviewer could distinguish from a real change.

  BUILDER'S CALL 2: THE EXPORT WRITES TO `artifacts/site_data` (its default `--out`) AND ONLY
    `teams/33.json` IS COPIED ACROSS. A full teams export emits a payload per team, all of them
    untracked and gitignored; copying the whole directory over `site_v2/src/data` would leave
    hundreds of untracked files on disk. `README.md:9-13` records that exact trap — every internal
    link then resolves LOCALLY while only the tracked ones reach CI, so a local build cannot catch
    what CI will fail on.

decisions_reserved:
  - ⚠ **THE TEAM'S NAME AND SLUG MOVED, AND THE SLUG IS THE URL.** The fresh export carries
    `Manchester United FC` / `manchester-united-fc` where the committed sample has
    `Manchester United` / `manchester-united`, so this commit relocates the built team page from
    `/{locale}/teams/manchester-united/` to `/{locale}/teams/manchester-united-fc/`.
    `dim_team.sql:7` calls `team_slug` "the team's permanent, locale-independent URL segment" and
    #852's intent is assigned-once-and-stored; it moved anyway. NOT caused by #90 and NOT
    investigated here — a data refresh is the wrong diff to bury it in. Nothing links to a team
    page today (`README.md`), so no internal link breaks. Worth its own issue against #852.
  - `site_v2/src/data/README.md` says "Tracked today, 18 files" and 22 are tracked (21 JSON + the
    README). A stale count, noticed while establishing what the sample is. NOT fixed here: it is
    unrelated to the rename, and folding an unrequested doc edit into a data-refresh diff is the
    scope drift this contract exists to prevent. Worth a one-line fix when that file is next
    touched for its own reasons.
  - The 17 fixture payloads, `landing.json`, `competitions.json` and `competition_index.json` are
    NOT re-exported. Each was scanned and carries none of the renamed keys.
  - CI still builds from stored samples rather than a live export. `README.md:49-51` calls that the
    real fix and puts it outside #367. Untouched.

acceptance_criteria:
  - The refreshed payload carries the post-#90 names — `metric_key: "clean_sheets_share"` on the
    benchmark rows of every season that HAS benchmarks, and `clean_sheets_share_this_season` /
    `_prev_season` / `_delta_yoy` on the season rows — while still carrying `clean_sheets` (the
    count) and `clean_sheet_run`, which the rename did not touch.
  - The BUILT team page renders without error in all three locales, read from `site_v2/dist`.
  - The tracked file SET is unchanged — exactly one file differs from main, and no `.gitignore`
    allowlist edit is needed.
  - No untracked payload is left behind under `site_v2/src/data/`.

# ⛔ THE FIRST DRAFT OF THESE CRITERIA WAS WRONG AND IS REPLACED, NOT ANNOTATED. It asserted the
# built page would show 16 ranked rows with a real percentage. It will not, and the reason is not
# this task's doing: the export's featured season has rolled to PL 2026, which has 1 game played,
# and the benchmark mart's floor is 3 games — so that season carries 0 benchmarks and the
# Performance tab renders its "not enough games to rank" state whole. PL 2025 is still in the
# payload with its 22 benchmarks; it is simply no longer the season the page opens on (#846
# working as designed). A criterion that the data cannot satisfy is a criterion I guessed.

done_when:
  - `git status` shows exactly ONE changed file under `site_v2/src/data/`, and `git diff --stat`
    confirms no other tracked sample file moved.
  - The refreshed payload carries `metric_key: "clean_sheets_share"` and the three
    `clean_sheets_share_*` season keys, and STILL carries `clean_sheets` (the count) and
    `clean_sheet_run`, which the rename did not touch.
  - `npm run build` green with `audit-seo` OK, and the row counts read from `site_v2/dist`.
  - No untracked file is left behind under `site_v2/src/data/` — checked with
    `git status --porcelain --ignored` before committing, because a stray local payload makes every
    link resolve locally while only the tracked ones reach CI.
  - ⚠ EVERY INTEGER IN THE ARTIFACTS RE-DERIVED before commit (#71).
