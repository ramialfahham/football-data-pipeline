# Acceptance evidence — sweep 1 of 4: decision history out of dbt comments

criteria_demonstrated:
  - EVERY FLAGGED LINE IN `dbt_project/` IS GONE. Before: the guard's own `count_tree` over
    `dbt_project/{models,macros,tests,seeds}` → 137 lines in 65 files (models 107, tests 26,
    macros 3, seeds 1; by marker: date 86, product owner 43, reviewer 7, MR 1). After: **0 lines,
    0 files** in those trees. Each line was rewritten by hand — 65 files, every edit passing the
    edit-time hook, which refuses any rewrite that still carries a marker. The rule applied: keep
    the why (the deviation, its cost, the analogy, the downstream contract, a pointer to a design
    doc); drop who decided and when. Examples: `stg_apif__coaches.sql` keeps "reads ALL snapshots
    faithfully … to PRESERVE every coach ever seen … latest-per-league would drop ~120 coaches" and
    the `layering.md` pointer, and loses "CPO-ruled this session" and the dated log pointer;
    `mart_leaderboards.sql` keeps "all ranking and ordering lives in the warehouse, and the page
    renders the order it is served" as the rule, not as a dated quote; the two CI-note paragraphs
    in `assert_metric_*` that narrated a rewrite ("REWRITTEN … the previous version said …") are
    replaced by the rule that holds now.
  - NO BEHAVIOUR CHANGE, PROVEN ON EVERY TOUCHED FILE. A script diffed each changed file against
    `HEAD`: for `.sql`, the text with `--`, `/* */` and `{# #}` comments stripped and blank lines
    dropped; for `.yml`, the `yaml.safe_load` document. Output: `sql identical with comments
    stripped: 56; yaml identical when parsed: 9; differing: []` — 65 files, zero differences.
    `python scripts/check_layer_contract.py` → "Layer contract checks passed." `dbt parse`
    (the repo's pinned `.venv/Scripts/dbt.exe`, a scratchpad-only profile, no connection) → no
    errors, the one pre-existing unused-config warning only.
  - THE PIN MOVES BY EXACTLY THE LINES REMOVED. Whole-tree `count_tree` before the sweep:
    (850, 174); after: **(713, 109)** — 850 − 137 = 713 and 174 − 65 = 109, measured, not
    computed. `PINNED_LINES = 713`, `PINNED_FILES = 109`; `pytest tests/test_no_decision_history_in_code.py`
    → 15 passed.
  - NOTHING LOAD-BEARING LOST. The analytics-engineer's own test case from `!176`,
    `stg_apif__coaches.sql`: the deviation (all snapshots, not latest-per-league), its cost (~120
    coaches dropped otherwise), the analogy (dim_player/dim_team entity preservation), the
    downstream contract (base dedups to one entity) and the doc pointer (`layering.md §1_staging`)
    all remain — only "CPO-ruled this session" and the dated log pointer went. Where a date was
    DATA it was kept out of prose but never lost: `assert_no_event_loss_since_cutoff.sql`'s cutoff
    is the dbt var `event_loss_detector_from`, and the comment now describes the backlog relative
    to the cutoff instead of by kickoff dates. Two stale facts corrected on the way, because the
    why was false as written: `sources.yml`'s "WHO READS THEM: nothing does today … an unmerged
    branch" now names `scripts/check_raw_freshness.py`, which reads those thresholds; the
    `assert_metric_*` CI notes now state the current CI behaviour instead of narrating the old one.

## What is NOT demonstrated

- That the comments read well to a stranger; the analytics-engineer reviewer judges that. Every
  rewrite kept the sentence grammatical and the number (`~120 coaches`, `51.4% of rows`, `12 of 28
  boards`) where it was the why.
- The other 713 lines — three more sweeps.
