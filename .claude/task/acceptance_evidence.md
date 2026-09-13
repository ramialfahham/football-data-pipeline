# Acceptance evidence — Home: build the approved design (#143)

criteria_demonstrated:
  - THE WINDOW IS EACH COMPETITION'S NEXT MATCHDAY, SERVED BY THE WAREHOUSE. `mart_next_matchday`
    (new, `5_marts/shared`, table) holds every upcoming fixture (NS/TBD, dated on or after the
    build day) in the round of its competition's earliest upcoming fixture; the landing query in
    `fetch_landing_payload` is now `select … from mart_next_matchday` with no WHERE. The mart's
    compiled SQL run against prod `core` on 2026-09-13 (a Sunday, mid-round): 232 rows, 31
    competitions, max 1 round per competition — BL1 "Regular Season - 3" 2 left, PL "Regular
    Season - 4" 3 left, UEL "League Stage - 1" 18 (Wed–Thu), DFBP "Round of 32" 16 on
    2026-10-27, ACN "Group Stage - 1" 12 in January. The old one-day rule on the same day gave 94
    fixtures on one date and nothing beyond it. The singular test
    `assert_mart_next_matchday_is_each_competitions_earliest_round` checks the mart against
    `fct_fixture` (one round per competition, the earliest, complete): run against prod with the
    mart inlined → 0 rows; MUTATION shown red twice — the mart picking the LATEST round
    (`order by fixture_date desc`) → 28 failing rows; the mart capped to one calendar day (the
    retired rule) → 23 failing rows. `dbt ls --select mart_next_matchday+` → the model, 9 schema
    tests and the singular test, no downstream model; `data:build:mr` will build and test it on
    the MR. Unit test `test_the_hero_reads_the_next_matchday_mart_whole` pins the export: FROM the
    mart, not `core.fct_fixture`, and none of `where`/`min(fixture_date)`/`row_number`/
    `qualify`/`current_date` in the read, every served row carried through and grouped; it FAILS
    against the pre-branch export (stash-compared: 1 failed) and passes after (73 passed across
    the two export test files). The earlier fresh export (31 groups / 232 fixtures, run while the
    selection still lived in the export SQL) is byte-for-byte what the mart-backed read will
    produce once the mart exists in prod, because the SQL is the same text moved into the model.
  - 3 VISIBLE, THE REST FOLDED, NO SCRIPT. With the fresh 232-fixture `landing.json` in place the
    dev server (`preview_start` name `v2`, `/en/`) rendered 31 `.fxgroup`s, 232 `.fxrow`s, all
    232 with an `href`; `max` rows outside a `<details>` per group = 3; 18 groups carry
    `<details class="fxmore">` with the summary "Show all {n}" (Eredivisie 4, La Liga 5, Serie A 6,
    UEL 18…), 13 groups with ≤3 fixtures carry none. Clicking "Show all 6" on Serie A opened it
    (`details.open === true`, Como–Parma, Torino–Roma, Inter–Udinese appeared below the summary;
    height 43.5px closed → 124.2px open on a 4-row fold). The summary is keyboard-reachable
    (`tabIndex 0`, `document.activeElement === summary` after `focus()`), 13px/600, cursor
    pointer, chevron rotated 90° at rest (`matrix(0,1,-1,0,0,0)`), −90° when open. `/de/` and `/fi/`
    render the same 31/232 with "Alle 4 anzeigen" / "Näytä kaikki 4". No script was added: the
    only inline scripts on the page are the header drawer and Astro's dev toolbar; the production
    build's `dist/en/index.html` carries the same 2 `<script>` tags as before. The mock
    (`design-mocks/gen_home.py` → `check_home.py`) shows the same fold on a nine-match Bundesliga
    round: 3 rows out, "Show all 9", 6 rows in — ALL PASS.
  - THE ORDER IS UNCHANGED. `orderUpcomingGroups` and `competitionOrder.mjs` are untouched (not in
    the diff); on the dev server the 31 headings ran Eredivisie, Ekstraklasa, 2. Bundesliga,
    Belgian Pro League, La Liga, Veikkausliiga, Ligue 1, Premier League, Serie A, Bundesliga,
    Süper Lig, Liga Portugal (all Sunday, Europe), then Argentina, Brazil, MLS, K League 1, J1,
    Saudi Pro League, CAF CL (Sunday, other confederations by region rank), then Monday's Liga MX
    and AFC CL, Tuesday's Coppa Italia / FA Cup / Libertadores, Wednesday's UEL, and on to the
    UNL, Copa del Rey, UCL, UECL, DFB-Pokal, AFC Asian Cup — soonest matchday first, region rank
    inside a day, exactly the ruled key.
  - NO GAMES FLOOR ON THE TEAM BOARDS. `mart_team_leaderboards.sql` line 47: `where
    season_games_played >= 3` → `>= 1`; `shared.yml`: the `expression_is_true` test
    `mart_team_leaderboards_games_gate_holds` → `season_games_played >= 1`, the model description
    and the `season_games_played` column description rewritten to say there is no floor. Two-sided
    sweep of `>= 3` under `dbt_project/models`: 2 moved (this mart's WHERE and its yml test), 6
    stay (`int_team_competition_benchmark_metrics_long`, `int_team_competition_benchmarks`,
    `int_competition_benchmarks.yml` ×2, `int_team_season__deserved_vs_actual` ×2,
    `mart_team_competition_benchmarks`, `int_team_season.yml` — all the benchmark or
    deserved-vs-actual rule). `dbt parse` green; SQLFluff on the model reports the same 4
    pre-existing `dbt_utils` findings before and after (stash-compared); `check_description_hygiene.py`
    ok (1647 descriptions); `check_layer_contract.py` passed; `dbt ls --select
    mart_team_leaderboards+` → the model, its tests, no downstream model.
  - THE WIREFRAME NAMES #127 AS THE AUTHORITY AND IS CORRECTED TO IT. `docs/wireframes/10_home.md`
    opens with the authority block (#127 wins; what it changed: matchday window, always every
    competition, 3 visible + fold, no team floor, metric name → Leaderboards, Stats → Leaderboards,
    #143 builds); §5(1) GAP-02 struck and rewritten to the round rule with the 94-row measurement;
    the "#908 parks a more-matches control" sentence struck (the fold is that control); the two
    `>= 3` mentions on the team boards (§0 GAP-29 bullet, §10 GAP-29) struck with the no-floor
    rule; §7 Interactions gains the fold and the board-title link. `docs/wireframes/00_overview.md`
    inventory row 10 now links `10_home.md`, says **built**, and names GitLab #127 as the authority.
    Not rewritten: the rest of the 1,100-line file (#100 owns that reduction).
  - THE MOCK GENERATOR RENDERS THREE BLOCKS AND NO BROWSE. `design-mocks/gen_home.py`: `BROWSE`,
    `browse()` and the fourth composition slot are gone; the docstring, `<title>`, control hint and
    legend say three blocks; `python gen_home.py` writes `home_mock.html` with 0 occurrences of
    "browse"/"Browse", 3 eyebrows in order, 19 fixture rows, one `<details class="fxmore">`.
    `check_home.py` asserts the order is exactly the three, no Browse/chip markup, ≤3 rows outside
    the fold in every group, exactly one fold and it is the nine-match round (3 out / 6 in), the
    fold is native `<details>` with the chevron in the summary, 94 crests (56 board + 38 fixture)
    — ALL PASS. Mutation: with `browse()` restored in the composition the first two checks FAIL
    (order has a fourth eyebrow; "Browse" present).
