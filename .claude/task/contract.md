# Task contract — the current-season pick and the board DQ guard (#40, warehouse half)

objective: >
  Serve the two warehouse facts the Top players block needs: **which season a competition is
  currently showing** (`is_current_season` on `mart_leaderboards`), and **a guard that notices a
  board with no league leader** — which the page deliberately will not, because #40 rules that a
  board with no data is not rendered at all.

refs: >
  **GitLab #40** is the block's design authority. This is its WAREHOUSE HALF ONLY.
  ⚠ **SPLIT ON THE CPO'S CALL, recorded in `.claude/task/escalations.log`, entry
  `2026-09-04 — feat/40-leaderboards-current-season-and-board-dq — SPLITTING #40`.** That entry
  carries the three options he was given and which he chose; it is the checkable record, and this
  line cites it rather than restating it.
  ⛔ It was written LATE, on `scope-auditor`'s FAIL — the assertion stood here with nothing behind
  it, which is the **fifth** instance of that class in one session. He ruled a SEQUENCING, not a
  design: nothing about #40's block design changed.
  The reason for the split: the block cannot render until `is_current_season` is in prod (merge plus
  the 04:00 `fdp-nightly`), so shipping the export and component together would have left most of
  the block's criteria undemonstrable at commit time. Same sequencing !150 → !151 used.
  The export, the component, the player scaffold and the copy are BUILT and PARKED in the stash
  `TEMP-40-mrB`; they are MR B, after this merges and the nightly runs.
  Plan: `C:/Users/Rami/.claude/plans/unified-seeking-waffle.md` (approved 2026-09-04) — its §3-§6
  are MR B's.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - .claude/active_work.md
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_leaderboards_every_home_board_has_a_leader.sql
  - dbt_project/tests/assert_one_current_season_per_league.sql

impact_map: >
  writers: no ingestion loader changes; no staging or base model touched.
  downstream: **`mart_leaderboards` IS A LEAF.** Pasted, not asserted —
  `dbt ls --select mart_leaderboards+ --resource-type model` returns exactly one line:
      football_data_pipeline.5_marts.shared.mart_leaderboards
  and the same selector without the resource filter returns only the model plus its own schema
  tests (not_null / unique / relationships / expression_is_true). Nothing reads it but the export.
  The change is ADDITIVE — one boolean appended after the existing select list — so no consumer's
  column set moves and no existing test's expression changes.
  consumers: `scripts/export_site_data.py` reads this mart directly. It does NOT read the new
  column yet; that is MR B. So this MR is inert at the frontend by construction.
  ⚠ `_LEADERBOARD_METRICS` / `_LB_KEEP` in the export serve the SEPARATE per-league leaderboards
  payload and are untouched here (their untested state is #99's, not this task's).
  layer_rules: `check_layer_contract.py` — a mart may serve a decided fact, and deciding WHICH
  season a surface shows is exactly that. The alternative, filtering by season in the export, is
  the window selection `analytics-engineer-reviewer` FAILed twice under GAP-32 and that #846
  settled by serving `is_featured_season` as a tested boolean on `mart_player_profile`.
  deploy_order: the column exists in prod only after merge + the 04:00 `fdp-nightly`. Nothing
  breaks meanwhile: no consumer reads it. MR B is gated on that rebuild.
  blast_radius: one added boolean column on a VIEW; two added singular tests. No existing row,
  count, rank or metric changes — verified by running the compiled model against prod and comparing
  its row count to the live table.

acceptance_criteria:
  - `is_current_season` is true for exactly one `season_api_year` per `league_code`, measured on
    LIVE PROD DATA, not asserted from the SQL.
  - It is true for EVERY row of that season, not one row of it — the flag answers a question about
    the competition, so a per-row `row_number()` would be wrong. Shown by comparing the flagged row
    count to the season's total row count for a sample league.
  - Adding the column changes NOTHING else: the model's row count against prod is identical with
    and without it. Shown by running both.
  - `assert_one_current_season_per_league` fails when the flag is made per-player instead of per
    league-season. Watched RED under that mutation.
  - `assert_mart_leaderboards_every_home_board_has_a_leader` fails when an elite league loses its
    rank-1 on one of the four boards. Watched RED under that mutation.
  - Both tests pass on live prod data unmutated — so each guard is not merely capable of failing,
    it is green on the real warehouse.
  - `dbt parse` exits 0 and SQLFluff passes under the templater CI uses, with the exit code read
    BARE rather than through a pipe.

decisions_taken: >
  Serving the season pick rather than filtering downstream follows #846's precedent
  (`mart_player_profile.is_featured_season`), which settled this exact shape after the export-side
  version was FAILed twice. Not a new mechanism; the second instance of a documented one.
  ⭐ **`rank()` not `row_number()`, and that is a correctness choice, not a style one.** The flag
  marks a SEASON, so every row of a league's latest season must carry it. `row_number()` would flag
  exactly one arbitrary row, and a consumer filtering on it would then get one player per league
  across ALL boards rather than one per league per board. Recorded because the two functions look
  interchangeable here and are not.
  ⭐ **Latest by `season_api_year` alone — it does NOT ask whether the season has started.** #101's
  in-season gate (">= 3 finished games") is a GROUP-level question belonging to the rotation MR;
  conflating them would bake a rotation rule into a column that answers a simpler question. The
  column's own description says so, so a reader cannot mistake it for an in-season test.
  THRESHOLD DECLARATIONS: no new mechanism, no new dependency, no recurring cost (one boolean on an
  existing view; the nightly's scan does not measurably change). No guard is loosened — two ADDED.

decisions_reserved:
  - **#101's group rotation and its in-season gate.** Decided, unwired, and deliberately NOT what
    this column models.
  - **Whether "latest season with data" is the right notion of current for the rotation.**
    ⛔ An earlier version of this item said a league whose latest season has not kicked off "is
    therefore current, by construction, and its boards are empty". **That was wrong**, and
    `analytics-engineer-reviewer` traced why. The chain, named precisely because the first version
    of this correction cited the wrong link in it: this mart reads `int_player_season__metrics`
    (`mart_leaderboards.sql:61`), which is a pure re-aggregation adding no filter of its own; the
    finished-match rule lives one step further up in `int_player_club_season__metrics`
    (`status_short in ('FT','AET','PEN')`, inner-joined). So the property holds TRANSITIVELY: a
    season with no completed football produces no rows and cannot reach this mart at all. The flag
    therefore falls back to the last season that HAS data — real leaders from the previous season,
    not an empty board. The runtime behaviour is safe; my description of it was not, and my first
    correction of it pointed at a model this mart does not directly read.
    What genuinely remains open for the rotation MR: showing last season's leaders under a heading
    that reads "Season totals to date" is misleading once a new season is under way but has no
    finished matches yet. #101's in-season gate (">= 3 finished games") is the mechanism that would
    settle it. Flagged, not decided.
  - **DE/FI for the four board labels** (written and parked in MR B, needing the CPO's
    confirmation) — `10_home.md` §10 records that they are needed before go-live, not before build.

done_when:
  - `.venv/Scripts/dbt.exe parse` exits 0.
  - SQLFluff passes under the dbt templater from `dbt_project/`, exit code read bare.
  - The compiled model runs against prod read-only; row count matches the live table.
  - Both new tests measured on prod: green unmutated, RED under their named mutation.
  - `python -m pytest tests/ -q` passes as a regression check (nothing here touches Python).

amendments: (none)
