# Acceptance evidence — design mocks into the repo

Read from running the tooling, not from reading it. Every generator and check below was executed.

criteria_demonstrated:
  - TRACKED: 27 `.py` + 2 `.csv` + `README.md` under `design-mocks/`. `git status --short | grep -c
    '\.html'` = **0**. The ~950 KB of rendered HTML is `.gitignore`d as build output, alongside
    `__pycache__/`.
  - THE HOME GENERATORS RUN, WHICH THEY DID NOT BEFORE. `gen_top_players.py` and `gen_top_teams.py`
    both wrote their mock (69,320 and 68,969 bytes); `gen_home.py` composed them (106,281 bytes).
    Before this branch all three raised `FileNotFoundError` — verified by running one against the
    old path. `check_players.py`, `check_teams.py` and `check_home.py` each report `ALL PASS`.
  - THE REGENERATED MOCKS MATCH THE REVIEWED DESIGN STRUCTURALLY: `top_players_mock.html` and
    `top_teams_mock.html` are each **4 boards / 28 rows / 28 value cells**. That count is also what
    settled the docstring contradiction below — one value column, not two.
  - ⛔ THE FIRST PASS AT THIS CRITERION FAILED, AND `bi-analyst-reviewer` CAUGHT IT. The criterion
    says EVERY 2026-08-10 ruling in a generator docstring; I transcribed the board-composition ones
    and missed three that govern both blocks — the crest being the CLUB badge even on player rows,
    every board ranking descending without exception (and the conditional reason: the two
    `lower_better` boards were dropped the same session), and stacking being per-board, "they all
    stack together or not". I swept the paragraph I was working in, not the docstring.
    Re-done as a SWEEP: `grep "CPO 2026"` across both generators returns 15 attributed lines, which
    reduce to EIGHT distinct rulings. Where each now lives:
        1-3  the board sets, order and cut list ............. `10_home.md` §0 (already there)
        4    ONE metric per board -> no header row, ONE value column ... `10_home.md`, added
        5    the board title spells the sigil out ........... `metrics_display.md`, by its charter
        6    the crest is the CLUB badge, player rows too ... `10_home.md`, added
        7    every board ranks descending, no exception ..... `10_home.md`, added
        8    a board stacks as a whole ...................... `10_home.md`, added
    ⚠ (5) living elsewhere is not an omission — `metrics_display.md`'s charter owns how a metric is
    displayed, and it being correctly routed is what made the other three read as missed rather
    than deliberately placed.
  - THE 2026-08-10 RULINGS ARE IN THE WIREFRAME. `10_home.md` already carried the Top players set,
    what it cut, and the no-goalkeeper-board consequence. The Top teams paragraph was missing four:
    Ø Key passes dropped from the passes board; deserved-vs-actual dropped WITH the CPO's reason
    (deserved points needs one ladder, a pooled board cannot carry it); the shots board ranking on
    `shots_on_goal_per_match` rather than the difference; the Passes column order reversed. Plus the
    warehouse consequence — `sot_difference_per_match` and `finishing_efficiency` unused by the
    block. All now stated there.
  - GAP-24 CITES THE WIREFRAME. `99_gaps_register.md`'s void previously rested on
    "`design-mocks/gen_top_players.py`'s header" — a file outside the repo. It now cites
    `10_home.md` §0.
  - NO DOCSTRING CLAIMS TWO VALUE COLUMNS. `gen_top_teams.py`'s header said "two value columns
    throughout" 227 lines above its own code comment saying "ONE value column and no header row".
    Replaced with the single-column statement and the rendered counts that prove it.
  - THE OFFLINE GATES ARE GREEN, and one of them was newly engaged:
        pytest tests/                 1031 passed, 1 skipped, 14 subtests
        ruff check . (CI's config)    All checks passed
        npm test (site_v2)            83 passed

## What bringing them in actually cost, and why that is the point

Adding 27 files to the repo put them under gates they had never faced. `ruff check .` — which CI
runs over the whole tree — reported **18 errors**. 13 were real defects and were fixed:

| rule | n | what it was |
|---|---|---|
| F401 | 4 | dead imports, including `ZONE` in a file whose own comment says importing "in case" is the scaffolding that reads as a live feature |
| F841 | 3 | unused locals — one of them, `example` in `gen_competitions.py`, was a REAL BUG: the table header promises `example / n` and the row emitted only `n`, so the computed example was dropped on the floor. Now rendered |
| E741 | 3 | `l` as a loop variable (W/D/L) → `lost` |
| E731 | 2 | `strip = lambda …` → `def` |

The remaining 5 are `gen_home.py`'s `sys.path` shim — legitimate, and marked `# noqa: E402` at each
import, which is the pattern every other shim site in this repo already uses. `.ruff-ci.toml` is not
touched: its per-file table is documented as complete at four, and adding to a guarded config to
silence a new file is the wrong direction.

## Drift found and NOT fixed — the competitions-index surface

`gen_competitions.py` still fails, and its own guard is why: `intercontinental_super_cup` is in the
shipped `dbt_project/seeds/competition_types.csv` and missing from the mock's
`competition_types.proposed.csv`, so the "undeclared type change" assertion fires. That is the guard
working — it exists so a mock cannot be designed against a taxonomy that is not real.

Left failing deliberately. `competition_types.proposed.csv` is a PROPOSAL that is meant to differ
from the shipped seed, so syncing the two is a taxonomy judgement, not a mechanical fix — and this
task's objective is the home page, with the competitions index (#54) already in
`decisions_reserved`.

## Five ways the store had rotted, all from living outside the repo

1. Every generator dead — `REPO` pointed at `D:/Projects/fdp-product`, which has no `dbt_project/`.
2. The player metric ids were renamed underneath it (`goals` → `goals_player`, ×4).
3. Two checks hardcoded `"Shots on target per match"` after the CPO renamed it to **on goal**.
4. The four Finnish player labels are marked "PROBE, NOT approved copy"; they shipped and were
   approved. NOT fixed — see below.
5. `competition_types.proposed.csv` fell behind the shipped seed (above).

⚠ (4) is left alone on purpose. The renderer discards the probe flag and hardcodes
`class="fi probe"`, so un-dotting them means changing what the mock renders — a design change to an
artifact the CPO reviewed, which is not this task's job. The stale claim is corrected in the data
and flagged at the line.

## What is NOT demonstrated

- No visual check of the mocks. They are HTML that must be served over HTTP to view (the README
  records that `file://` times out in the browser pane); structure is asserted by the three checks
  and by the element counts above, not by looking.
- `gen_competitions.py`, `gen_competition_hub.py`, `gen_matches.py`, `gen_navmap.py`,
  `gen_sitemap.py`, `gen_taxonomy.py` and their checks are brought in and lint clean, but only the
  three HOME generators are asserted to run correctly. The others belong to surfaces this task
  reserves.
