# Task contract — Home: build the approved design (matchday window with fold, no team floor, documents corrected)

objective: >
  The CPO approved the Home design on GitLab #127 (2026-09-13). This branch builds the parts Home
  owns: the Next matches block shows each competition's whole next matchday (its next round) with
  3 rows visible and the rest folded; a team ranks on a Home team board from its first finished
  game; the wireframe, the overview and the mock generator are corrected to the approved design.
  The header, footer and metric-name links are NOT built here (each goes live when its page is
  built — #127); the rotation (#101), the team tie-break (#114) and the Leaderboards hub (#139)
  are owned elsewhere.

refs: >
  GitLab #143 (this task, `Task` template; the What exactly lines below are its acceptance
  criteria verbatim). GitLab #127 "The approved design" (the rulings, consolidated in the issue
  description; approved in chat 2026-09-13: "approved", then "do it" on #143's How).

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_landing.py
  - site_v2/src/components/home/HeroFixtures.astro
  - site_v2/src/components/home/FixtureRow.astro
  - site_v2/src/data/landing.json
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/lib/types.ts
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_next_matchday.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_next_matchday_is_each_competitions_earliest_round.sql
  - dbt_project/docs/layering.md
  - docs/wireframes/99_gaps_register.md
  - docs/site_architecture.md
  - docs/wireframes/10_home.md
  - docs/wireframes/00_overview.md
  - design-mocks/gen_home.py
  - design-mocks/check_home.py
  - design-mocks/home_mock.html
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: `scripts/export_site_data.py::fetch_landing_payload` (the landing query — the only
    writer of `landing.json`'s `upcoming[]`); `mart_team_leaderboards` (one WHERE clause);
    `HeroFixtures.astro` (the only renderer of `upcoming[]`).

  downstream: `mart_team_leaderboards` is a LEAF — `dbt ls --select mart_team_leaderboards+
    --resource-type model --resource-type test` (run 2026-09-13 against a scratchpad dev profile,
    target `dev_scratch`) lists the model, its 19 schema tests and 3 singular tests
    (`assert_mart_team_leaderboards_all_boards_present`, `…_every_board_has_a_leader`,
    `…_one_leader_per_league`) and NO downstream model. Its only other reader is the export's
    Top teams query (`league_leader_order = 1 and is_current_season`), which selects and does not
    compute. The `season_games_played >= 3` expression test in `shared.yml` and the column
    description that says "Always >= 3" move with the gate; the benchmark models' own gate
    (`int_team_competition_benchmark_metrics_long`, `int_team_competition_benchmarks`,
    `int_team_season__deserved_vs_actual`) is a different rule and is untouched — two-sided
    sweep of `>= 3` under `dbt_project/models`: 2 move (the mart's WHERE and its yml test), 6 stay
    (all benchmark or deserved-vs-actual). `landing.json`'s `upcoming[]` keeps its shape (the
    `round` key already exists on every fixture); the only frontend reader is `HeroFixtures.astro`
    plus `orderUpcomingGroups`, whose input is unchanged.

  layer_rules: marts = consumption; the mart keeps ranking and ordering, the export keeps
    selecting (the round is chosen in SQL, not Python — the #846 rule), the page keeps rendering
    (the 3-row cut is presentation; every fixture stays in the payload and in the HTML).
    `check_layer_contract.py` unaffected (no per-model materialisation change, no new file).

  deploy_order: none. The mart is a view; removing the gate widens its rows at the next nightly
    and the export reads whatever is there. No migration, no incremental model touched.

  blast_radius: `mart_team_leaderboards` gains rows for teams with 1–2 finished games; a league
    whose new season has 1–2 finished games flips `is_current_season` to the NEW season
    earlier than before (today it waits for 3 games and shows last season's leaders under a
    current-season label — the trap #101 records). Home's Top teams may therefore show a
    one-game rate in the first week of a season, which is the ruling. `landing.json` changes
    content (whole rounds instead of one day: measured 2026-09-13, 20 competitions, 94 matches
    on the old rule vs the union of their next rounds on the new one); no other export target
    changes.

acceptance_criteria:
  - The Next matches block shows, for every competition with a fixture not yet started, that competition's whole next matchday (the round of its earliest upcoming fixture), not the earliest calendar day. On a Monday the Bundesliga shows next weekend's nine matches.
  - Each competition shows its 3 earliest kickoffs; the rest are folded under a "show all" on the block, opened without JavaScript.
  - The order of competitions is unchanged: the day the matchday starts, then region rank, then kickoff, then code.
  - A team appears on a Home Top teams board from its first finished game: `mart_team_leaderboards` no longer requires 3 games.
  - `docs/wireframes/10_home.md` describes the page as approved on #127 and names #127 as the authority; `docs/wireframes/00_overview.md` points at #127 for Home.
  - `design-mocks/gen_home.py` renders three blocks; the Browse block and its markup are gone from the generator and the mock.

decisions_taken: >
  1. THE WINDOW IS THE ROUND, chosen in SQL. #127: "Window: each competition's next matchday, not
  a calendar day — the round (the fixture's round name) of its earliest fixture not yet started."
  Implemented as: upcoming = not started (`NS`/`TBD`) and dated today or later; per competition,
  the round of the earliest such fixture (by date, then kickoff); every upcoming fixture of that
  round is served. Stated consequence, measured on prod over the 2025 season: a postponed match
  keeps its original round name, so for the days between a round's end and its straggler the
  block shows that competition as a one-match matchday (BL1 3 stragglers over 7 days late in
  306 fixtures, PL 1, BSA 16, MLS 13). Accepted as the ruled definition; recorded on #143.
  2. THE FOLD IS PRESENTATION. #127: "3 visible, the rest folded under a 'show all' on the block;
  no JavaScript needed." A native `<details>`/`<summary>`; the 3 are the first three rows of the
  kickoff-ordered list the export serves; the constant lives in the component, ruled on #127.
  The summary copy "Show all {n}" (DE "Alle {n} anzeigen", FI "Näytä kaikki {n}") is new i18n
  copy for a control the CPO described in those words ("something like a show all button").
  3. NO FLOOR. #127: "No floor. A team appears on a Home team board from its first finished game."
  The mart's WHERE, its yml expression test and the column description move together; the
  expression test becomes `season_games_played >= 1` (a guard narrowed, not deleted). The
  benchmark gate stays. The docstring paragraph on qualification is rewritten to say the
  mart has no games floor and why.
  4. THE WIREFRAME IS CORRECTED, NOT REWRITTEN. #100 (reduce `10_home.md` to the current design)
  stays open; this branch adds a header line naming #127 as the authority and strikes/corrects
  the passages that now disagree (§5 (1) the one-day window; the `>= 3` gate on the team boards;
  the unlinked board titles), and the overview's inventory row for Home. No new mechanism, no
  recurring cost.
  5. THE MOCK RENDERS THE APPROVED DESIGN: three blocks, Browse gone, and the Next matches block
  shows one competition with 3 visible rows and a fold — the mock is the rendering of #127
  (`00_overview.md`: "the GitLab issue for that surface, with design-mocks/ as its rendering").
  `check_home.py`'s assertions move with it.

decisions_reserved:
  - none open for this branch: the design is CPO-approved on #127 and #143's How is the plan he said "do it" to. The straggler consequence in decisions_taken (1) is REPORTED to him in the MR head, not decided here — if he wants a different definition of "next matchday" it is a #127 amendment.

done_when:
  - `python -m pytest tests/test_export_landing.py tests/test_export_site_data.py -q` green, including a new test that pins the round selection to the query (no `min(fixture_date)`, a per-competition round pick).
  - `.venv/Scripts/dbt.exe parse` green; `python -m sqlfluff lint dbt_project/models/5_marts/shared/mart_team_leaderboards.sql --templater jinja --dialect bigquery` clean.
  - `python scripts/check_description_hygiene.py` green (the column description changed).
  - `python design-mocks/gen_home.py && python design-mocks/check_home.py` → ALL PASS, with no `Browse` in `home_mock.html`.
  - Dev server: `/en/` renders every competition group with ≤3 `.fxrow` outside `<details>` and the remainder inside; `read_page` shows the summary text; `/de/` and `/fi/` show the translated summary.
  - `rendered_page_evidence.md` / `acceptance_evidence.md` demonstrate each criterion from the built output.

amendments:
  - 2026-09-13: + site_v2/src/components/home/FixtureRow.astro — authority: standing rule (one
    row markup, rendered twice — visible and folded; Astro frontmatter cannot hold JSX, so the
    shared row is a component, the way `rows.py` already shares it across the mocks); content:
    the fixture row extracted verbatim from HeroFixtures.astro.
  - 2026-09-13: + site_v2/src/data/landing.json — authority: standing rule (`site_v2/src/data/README.md`:
    the committed sample is a SET rolled forward as maintenance, never on a block's way past);
    content: NOT committed on this branch — the fresh export is placed here only to render the
    fold in the dev server for `rendered_page_evidence.md`, then reverted with
    `git checkout -- site_v2/src/data/landing.json` before the commit. The committed sample
    (max 2 fixtures per competition) keeps its shape and cannot show the fold.
  - 2026-09-13: + dbt_project/models/5_marts/shared/mart_next_matchday.sql,
    dbt_project/tests/assert_mart_next_matchday_is_each_competitions_earliest_round.sql,
    docs/wireframes/99_gaps_register.md, docs/site_architecture.md, dbt_project/docs/layering.md
    — authority: the CPO, in chat 2026-09-13, on the blinded question "who decides which round is
    a competition's next matchday — the warehouse, or the export": "Path A" (the warehouse serves
    it as a mart; the export only filters; GAP-32 closes). Raised by analytics-engineer-reviewer
    round 1 (the round selection in the export's SQL is window selection in the consumption layer,
    and GAP-32 left the classification unsettled). Content: `mart_next_matchday` — one row per
    upcoming fixture in its competition's next round, from `fct_fixture`, nightly, pinned by the
    singular test; the landing query becomes a plain `select … from mart_next_matchday`; GAP-32
    marked CLOSED; the landing row of `site_architecture.md`'s mart map and the mart table in
    `layering.md` name the mart; `10_home.md`'s model bindings corrected. `decisions_taken` (1) is
    superseded by this amendment where they differ. The mart's NAME is the builder's proposal from
    the CPO's own words ("the next matchday of every competition"), stated in the MR head for him
    to rename.
