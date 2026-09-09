# Task contract — ranking lives in the warehouse: the layering rule + the tie-broken league leader

objective: >
  Write the CPO's 2026-09-09 rulings into the places that enforce them, and give `mart_leaderboards`
  the column they require. Two rulings, both recorded in `.claude/task/escalations.log` on the day:
  (1) ALL RANKING AND ORDERING LIVES IN THE WAREHOUSE — the page renders the order it is served;
  (2) A TIE IS BROKEN BY FEWER MINUTES PLAYED, falling back to `player_sk` where minutes are equal.
  This is MR A of two. It stands alone and merges first; #40 MR B (the Home Top players block,
  parked in stash `TEMP-40-mrB-block` on `feat/40-top-players-block`) rebases onto it, because an
  export cannot query a column that is not yet in prod.
refs: >
  `.claude/task/escalations.log`, 2026-09-09 `feat/40-top-players-block` — both rulings, with the
  measurements behind them. It supersedes the 2026-08-18 `chore/record-top-players-ruling` entry's
  reservation ("NOT DECIDED, do not assume either way: whether ordering the seven winners by value
  lives in the mart or the page") and corrects that entry's false premise — it says each league's
  number one already exists, and DENSE_RANK means it does not.
  `dbt_project/docs/layering.md` (the consumption-layer contract this sharpens),
  `docs/metric_layer.md` (read before touching anything metric-related; no metric changes here).
  GitLab #40. Round-1 FAIL from `analytics-engineer-reviewer` on `feat/40-top-players-block` is what
  surfaced it.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_leaderboards_one_leader_per_league.sql
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: `mart_leaderboards` is written only by the dbt build — nightly `fdp-nightly` /
    `data:build:main`, and per-MR `data:build:mr`. No ingestion path touches it. It is
    `materialized='view'`, so "writing" it is a view redefinition, not a table rebuild.

  downstream: LEAF. Evidence, run in this session against this checkout
    (`.venv/Scripts/dbt.exe ls --select mart_leaderboards+`, dbt 1.7.19 / bigquery 1.7.2,
    DBT_PROFILES_DIR pointed at a scratchpad profile carrying only a `dev`/`dev_scratch` target —
    `~/.dbt/profiles.yml` on this machine holds ANOTHER project's `dbt_analytics` profile and was
    not touched):
      `--resource-type model` -> football_data_pipeline.5_marts.shared.mart_leaderboards  (itself, only)
      `--resource-type all`   -> 27 nodes = the model + 26 tests, ZERO downstream models
    The only non-dbt consumer is `scripts/export_site_data.py`, which SELECTs named columns; adding
    a column cannot break it. `assert_mart_leaderboards_every_home_board_has_a_leader` (shipped in
    !153) already asserts a rank-1 row exists per elite league per Home board and is unaffected —
    the new column is an ordering within that same partition.

  layer_rules: `check_layer_contract.py` applies (a `dbt_project/models/**` path is in scope); no
    per-competition subdirectory is created and no `+materialized` is overridden per model, so it
    passes unchanged. The new column is computed in the MART, which is where a leaderboard rank
    already lives — this moves logic INTO the layer the contract names, not out of it.

  deploy_order: this MR must merge and `data:build:main` must run before #40 MR B can re-export
    `landing.json`, because that export queries prod `marts.mart_leaderboards`. Cheap: the model is
    a VIEW, so the column exists the moment the view is recreated — no table rebuild, no
    `--full-refresh`, and none of the three incremental facts is touched. Nothing is owed
    operationally if this merges between nightlies; the next `data:build:main` picks it up.

  blast_radius: NO existing column changes and NO number moves. `rank` keeps its DENSE_RANK
    definition, so ties still share a rank and the top-10 cut stays inclusive of ties — that is a
    documented consumer contract and this MR deliberately does not touch it. One column is ADDED.
    ⚠ `mart_team_leaderboards` has the same DENSE_RANK shape and therefore the same latent tie, and
    it is NOT fixed here: Top teams (#41) is unbuilt, and widening this MR to a second mart would
    put an unreviewed change in a model nothing consumes yet. Flagged, not folded in.

decisions_taken: >
  RULING 1, verbatim and quotable: the CPO answered "yes, that's the rule" to *"All ranking and
  ordering lives in the warehouse. The page renders the order it is served."* This is
  `layering.md`'s existing consumption-layer rule applied without exception rather than a new rule,
  so this MR SHARPENS the wording rather than inventing a mechanism. The cost was put to him before
  he ruled: a block needing a new ordering waits on a mart column.

  RULING 2, and the reasoning he accepted: a tie is broken by FEWER MINUTES PLAYED — the same tally
  in less time is the better performance, and it reads identically on all four Home boards. Measured
  against prod 2026-09-08/09 before asking: of the 28 league-boards the Home block renders, 12 carry
  a tie, minutes resolves 11 of the 12, one survives, and 0 have a NULL `minutes`.
  The survivor falls to `player_sk`, which is MEANINGLESS AND SAID TO BE — stable, invisible, and
  making no claim about the players. Player NAME was offered as the fallback and NOT taken, because
  names in this pipeline are a known-unreliable identity surface and an alphabetical fallback would
  reorder a board when a name is corrected.

  ⛔ A FILE'S EXISTENCE IS NOT AUTHORITY. Arguing the previous round I cited
  `site_v2/src/lib/competitionOrder.mjs` — a shipped frontend module with a five-key sort — as
  precedent for keeping ordering on the page. CPO: *"I don't even know what it is. Definitely no
  authoritative document for business logic."* Under Ruling 1 that module is a VIOLATION, not a
  precedent. It is NOT fixed here — it is a separate task, and folding it in would put an unrelated
  frontend rewrite inside a warehouse MR.

  THRESHOLD — NEW MECHANISM: none. `row_number()` beside an existing `dense_rank()` in a model that
  already ranks; no new model, macro, seed, dependency, job or gate. The singular test added is the
  standard dbt shape and sits beside the sibling this mart already has.

  THRESHOLD — RECURRING COST: negligible and stated rather than assumed. `mart_leaderboards` is a
  VIEW, so nothing is stored; the added cost is one more window function over the same scan when a
  consumer queries it, and one extra singular test per build. Measured neighbour for scale: the
  export's whole Home query over this view is 29.8 MB by dry run, against ~129 GB/day for the two
  scheduled jobs.

decisions_reserved:
  - THE ORDER OF THE ROWS ACROSS LEAGUES, which this column does not settle and cannot. A board
    shows one leader per league ordered by value, and that ordering ties too (measured: two leagues
    level on 4 assists). The tie RULE is now settled — value, then fewer minutes, then `player_sk` —
    but the ordering is pool-scoped, and the pool (`competition_group = 'elite'`, rotating nightly
    under #101) is not a concept `mart_leaderboards` knows. So MR B applies those three ruled keys
    as an ORDER BY over served columns. Making even that live in the warehouse needs a pool-aware
    mart, which is exactly what the CPO questioned on 2026-08-18 ("do we really need a separate mart
    for it ... it's repetitive work, not sure about it"). Stated here so MR B's reviewer sees it
    declared rather than discovering it.
  - Whether `mart_team_leaderboards` gets the same column, and when. Same latent defect, no consumer
    yet. Not decided here.
  - Whether `competitionOrder.mjs` is rewritten or deleted. It is a violation under Ruling 1; which
    it is depends on what the competitions index is supposed to order by, which is not this MR's.

done_when:
  - `dbt parse` clean, and SQLFluff passes on the changed model from the REPO ROOT with the full rule
    set (`python -m sqlfluff lint <model> --templater jinja --dialect bigquery`, exit code read bare
    and unredirected — it exits 1 on success when stdout is redirected).
  - `python scripts/check_layer_contract.py` and `python scripts/check_description_hygiene.py` exit 0
    (the new column carries a description and `persist_docs` is on, so BigQuery's 1,024-character
    column limit applies and a breach fails the prod build).
  - The new singular test is MUTATION-TESTED, not merely green: dropping the `minutes` leg from the
    window's ORDER BY must turn it RED, and the evidence must show it red.
  - Measured against prod through a compiled query: exactly one row per (league_code,
    season_api_year, metric_key) has the new column = 1, and for the 12 tied Home league-boards the
    row it picks is the one with fewer minutes.

amendments: (none)
