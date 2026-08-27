# 10 — Home (landing) (#391)

> Field-bound against `shape_landing_payload` (written 2026-08-03, revised 2026-08-08, revised
> again 2026-08-19). The page reads exactly one warehouse model today: `core.fct_fixture`, for the
> hero.
> ~~`mart_leaderboards` / `mart_standings`~~ — bound ONLY to the stats-teasers module, removed
> 2026-08-08.
> ~~`mart_team_profile` / `mart_landing_trending`~~ — bound ONLY to the trending module, cut
> 2026-08-08 for not being in the composition §0 records. `mart_landing_trending` was written for
> this page and never shipped; it is deleted, not parked, and git holds it if trending returns.
> ~~`build_nav`~~ — bound ONLY to the browse module, DROPPED 2026-08-19 (CPO: "drop the browse
> section"). `build_nav`/`fetch_nav` are not deleted — they still produce `nav.json`
> independently (`--entities nav`) — only `shape_landing_payload`'s use of them is gone.
>
> This screen is the exception to the binding rule's usual direction. Every other spec binds to a
> payload the export already writes; here the payload did not exist yet, which is exactly why the
> screen inventory says 10_home "pins the homepage spec, unblocks `landing.json`". The spec and the
> writer land in the same PR, and §5 is the contract between them: a key named here is a key the
> writer emits, verified by the §5 checklist in `00_overview.md` before the PR merges.
>
> ⚠ **§0 is the current authority.** Everything from §1 onward describes the FIRST build; where the
> two disagree §0 wins, and each superseded passage is struck where it stands rather than silently
> corrected. Five rounds of review were needed to find them all, because they were fixed one
> reported instance at a time instead of swept as a class — §1, §3, §4, §6, §8 and this header all
> carried the same stale claim.

## 0. Decisions of 2026-08-04 and 2026-08-08, and what is still open

> Written during the CPO reviews of the rendered page. This section is the record: the sections
> below still describe the FIRST build, and where the two disagree, this one is current.
> Nothing here is inferred; every line is a CPO instruction from one of those sessions.
>
> Two dated layers, oldest first. Where they conflict the later one wins and the superseded line
> says so on its own row, rather than leaving both readable as current.

### The rule a block must pass (CPO, 2026-08-04)

**A block earns its place by sending someone somewhere.** It is a hook into the page that owns the
content, never a copy of it. His example: deserved-vs-actual already has a home on the team page,
so putting it here would be duplication, not content.

Consequences: every block names its destination page type; no block may duplicate what another page
owns; and the home page is "finished" when it reaches every hub, not when it is full.

⚠ The corollary he had to correct me on twice: **do not reorder the build because a destination
page does not exist yet.** Every page on a new site links to pages that do not exist yet — that is
the starting condition of a site, not a blocker. `STUB_PAGES` in `site_v2/src/config/indexability.mjs`
exists precisely so scaffold routes can ship with real URLs, canonicals and hreflang while staying
out of the index. Build the routes, let the links resolve, fill the pages in afterwards.

### Decided

| | |
|---|---|
| **Next matches** | The next matchday — every match on the next day that has football (CPO 2026-08-18; the fixed list of 12 is retired). Date tabs and a "more matches" control are deferred to **#908**, which also records that four of the six nav items have no page to link to. |
| ~~**Browse**~~ | ~~Moves to the BOTTOM of the page, per convention on comparable sites. (§4's rail placement is superseded.)~~ **DROPPED 2026-08-19** (CPO: "drop the browse section") — superseded by a later ruling than this table records; see the composition note below. |
| ~~**Trending**~~ | ~~Teams AND players, both as STREAKS. The wording must relate to "streak".~~ **SUPERSEDED 2026-08-08**: the composition recorded below has no trending block, so the block was cut rather than reworked to this row. See the note under the composition. |
| ~~**Team streaks**~~ | ~~THREE types: longest **winning** run · longest **unbeaten** run · longest **clean-sheet** run. Winless and losing are both dropped.~~ Superseded with the block. |
| ~~**Streak scope**~~ | ~~ALL competitions, and therefore across seasons too. Stated once on the block, never per row.~~ Superseded with the block. |
| ~~**Streak rows**~~ | ~~Full start date (day, month, year — no weekday). The team's competition stays on the row as team CONTEXT, not as the streak's scope.~~ Superseded with the block. |
| **Stats block** | ~~STAYS, with different wording (words pending).~~ **SUPERSEDED 2026-08-08**: the top-scorers-plus-table block is REPLACED by the player stats block below, not reworded. |
| **Round on a fixture row** | NOT rendered — it shipped the provider's English string to all three locales (#866). |

### Decisions of 2026-08-08 — the player and team stats blocks

The CPO judged the built stats block useless because it sent nobody anywhere, and named the purpose
the home page's content serves beyond being read: **clicking a team, competition or player goes
deeper into the site**. Both blocks are designed against that purpose. This is a SPEC — nothing
below is built.

**Page composition after this session**: next matches → **Top players** → **Top teams** → browse.
The two stats blocks replace the top-scorers-plus-table block.

⛔ **SUPERSEDED 2026-08-19 — browse is dropped.** CPO, in chat: "drop the browse section". Current
composition is **next matches → Top players → Top teams**, three blocks not four. Browse's only
remaining value was reachability into the long-tail team/player pages (thousands of teams,
~154,767 players); both are already blocked on the team/player-name data-quality work (see
`.claude/active_work.md`), so a competitions-only version had nothing left to solve — the
competitions pool (~15-20 rows) is already fully covered by the competitions index page (#62).
See §5(2) for the removed module's retained record.

⛔ **FOUR blocks, and TRENDING IS NOT ONE OF THEM.** Confirmed by the CPO on 2026-08-08 when he was
shown a build that shipped it. The composition line above is the whole ruling; nothing else was
needed, and reading it as "the blocks that changed" rather than "the page" is the mistake that put
trending into the first build. Consequences, all applied:

- The trending block, `TrendingList.astro`, the `trending[]` payload key and `mart_landing_trending`
  are DELETED. The mart was written for this page on 2026-08-03 and never shipped.
- What was built was stale against the 2026-08-04 row above anyway: it served five signals including
  **winless**, which that row explicitly dropped, no player streaks and no start dates. So there was
  no version of it that could have shipped as specified.
- Six team payloads left `site_v2/src/data/teams/` with it. They were committed only because
  trending rows linked to them; with the block gone nothing on the site links to a team page.

⚠ **THIS PR THEREFORE SHIPS TWO OF THE FOUR**: next matches → browse. Top players and Top teams need
warehouse work (see the corrected gap list in §10 — the six originally named here were written
against the NINE-board set and three are now void) and a layout that is still unapproved, so they
land in their own PR and slot between the two. Browse stays LAST rather than being pulled up under
the hero: it is holding its final position, so the follow-up inserts and never rearranges.

⛔ **SUPERSEDED 2026-08-19.** That PR shipped, then browse itself was dropped (see the composition
note above) — the page today ships next matches alone, of a composition that is now three blocks,
not four. Top players and Top teams still need the same warehouse work and layout approval;
nothing about their build changes, there is simply no browse block left to slot them ahead of.

**The block names are Top players and Top teams** (CPO 2026-08-08). Plain nouns, matching the
vocabulary the page used at the time for Next matches and Browse (the latter dropped 2026-08-19,
after this naming decision), and a matched pair so the two blocks read as siblings. "Top scorers" was already on the page, so the reader has met the
pattern. Rejected: "Player leaders / Team leaders" ("leader" collides with captaincy in football and
translates awkwardly) and "Who leads / Which teams lead" (more voice, less scannable, and the two
halves stop being a pair).

**A BOARD IS NAMED BY THE METRIC THAT RANKS IT** (CPO 2026-08-08). Not by its catalogue group. ⚠ The
RULE stands; its original EXAMPLE does not. It read *"the first player board is Goal contributions,
not 'Goals', because it ranks on `scorer_points`"* — but the 2026-08-10 reduction cut
`scorer_points`, and the first board now ranks on `goals`, so under the same rule it IS called
**Goals**. The example inverted when the boards changed; the rule is what produced both answers.
Two consequences worth stating, because both were ruled:

- The name is a GOVERNED value, not new copy. It is the rank metric's `label_en` in
  `metric_catalogue.csv`, which is the same name that metric carries everywhere else on the site.
  A board heading can never drift from the metric it ranks, because it *is* the metric's name.
- **No "ranked by" annotation is rendered.** The CPO: *"no explanation needed how it's ranked, the
  user can see it"*. The name carries what the annotation was explaining.

⛔ **SUPERSEDED 2026-08-10 — THE TABLE BELOW IS THE NINE-BOARD DESIGN AND IS NOT CURRENT.** The CPO
reduced Top players to **FOUR single-metric boards, in his order: goals → assists → passes → key
passes** (recorded in `design-mocks/gen_top_players.py`'s header, which lists what was cut, and in
`99_gaps_register.md` — GAP-24/25/26 are VOID *because* of this reduction). Struck rather than
deleted, per this file's own convention.

What the reduction removed, stated so the table below is not mistaken for a menu: `scorer_points`
(goals and assists became boards in their own right, so the combined metric had nothing left to
combine), every second/context column (`pass_accuracy_pct`, `dribbles_success_pct`,
`duels_won_pct`, `save_pct`), and Shots on target, Duels, Dribbles, Tackles, Goals conceded and
Cards entirely. ⚠ **There is therefore NO GOALKEEPER BOARD** — the four survivors are all
attacking/possession metrics, so an outfield creator can top every board and a keeper can top none.
⚠ The Goals-conceded row's "ASCENDING" note is what GAP-26 was written about; that board no longer
exists and the gap is VOID.

~~**Nine player boards.** Board name = the rank metric's `label_en`, shown here for readability; the
`label_en` column is the source.~~

| Board | Shown | Ranked by |
|---|---|---|
| Goal contributions | `goals` · `assists` · `scorer_points` | `scorer_points` |
| Shots on target | `shots_on_goal` | `shots_on_goal` |
| Duels | `duels_won` · `duels_total` · `duels_won_pct` | `duels_total` |
| Dribbles attempted | `dribbles_attempts` · `dribbles_success` · `dribbles_success_pct` | `dribbles_attempts` |
| Passes | `passes_total` · `passes_accurate` · `pass_accuracy_pct` | `passes_total` |
| Key passes | `passes_key` | `passes_key` |
| Tackles | `tackles_total` · `tackles_interceptions` · `tackles_blocks` · `defensive_actions` | `tackles_total` |
| Goals conceded | `goals_against` · `shots_on_goal_against` | `goals_against`, ASCENDING |
| Cards | `cards_yellow` · `cards_red` · `cards_total` | `cards_total`, DESCENDING |

Every board ranks on a VOLUME metric, never a rate. That is deliberate and it carries a
consequence: percentages ride along as context instead of deciding position, so the qualification
floors that guard `mart_leaderboards`' five rate boards are not needed for eight of the nine.

⛔ **SUPERSEDED 2026-08-10 — the table below is the SIX-board design and is not current.** Top teams
was reduced in the same session to **FOUR boards: `goals_per_match` → `shots_on_goal_per_match` →
`passes_per_match` → `duels_per_match`** (`design-mocks/gen_top_teams.py`). % Points captured and
Ø Defensive actions are gone, and the surviving four are single-metric like the player boards.
⚠ % Points captured leaving matters beyond this block: `points_capture_pct` is built on the synthetic
3-1-0 tally, which is wrong for cup competitions.

~~**Six team boards.**~~

| Board | Shown | Ranked by |
|---|---|---|
| % Points captured | `points_capture_pct` · `points_won` · `deserved_points` | `points_capture_pct` |
| Ø Goals | `goals_per_match` · `goals_against_per_match` | `goals_per_match` |
| Ø Shots on target difference | `sot_difference_per_match` · `shots_on_goal_per_match` · `shots_on_goal_against_per_match` · `finishing_efficiency` | `sot_difference_per_match` |
| Ø Defensive actions | `defensive_actions_per_match` | descending |
| Ø Passes | `pass_accuracy` · `key_passes_per_match` · `passes_per_match` | `passes_per_match` |
| Ø Duels | `duels_per_match` · `duels_won_pct` | `duels_per_match` |

The mirror of the player rule does NOT hold here: team metrics are almost all per-match rates, so
there is no volume metric to rank on. The existing `>= 3 finished games` gate on
`int_team_competition_benchmark_metrics_long` is the small-sample guard, and it is the same number
as the pool-selection gate below.

Excluded deliberately: **Set pieces** and **Goalkeeping** (thin, no tier-1 metric), and the
Outcomes metrics `league_rank` and `deserved_rank`, which are the standings the table page owns.

⛔ **SUPERSEDED 2026-08-10 — the paragraph below is about the REMOVED % Points captured board.**
`gen_top_teams.py`'s header: *"'% Points captured' dropped as a board; `points_capture` is shown
nowhere"* and *"deserved-vs-actual dropped … takes `deserved_points` and `points_won` off the block
entirely."* Nothing on the reduced four-board block ranks on `points_capture_pct`, so its reassurance
is not merely stale, it is FALSE about the current design. Kept as the record of why that board was
fragile, because the same structural problem returns anywhere `deserved_points` is used.

~~⚠ `deserved_points` is null far more often than it is populated, and for two different reasons.
One is a coverage gap that can close: the league-season needs every team to carry shots on target,
a league rank and three finished games. The other is STRUCTURAL and will not close — MLS ranks by
conference and the Apertura/Clausura formats reset points, so there is no single ladder to fit.
That rules out MLS, LMX, APD and J1 permanently, which is four of the eight leagues in pools 2 and
3. Ranking is on `points_capture_pct`, so a null `deserved_points` never affects the order.~~

**Shared display rules.**

- ~~**Top 5 entries per board.**~~ **SUPERSEDED.** Both blocks are **one row per pool league**
  since the 2026-08-18 rulings, so pool 1 renders **seven** rows on every board — a 5-row cap
  could not show a leader from all seven leagues the approved intro copy names. ⚠ For Top teams
  this is now the reason; the row count was previously guessed from the mock alone, before the
  ruling existed, and the mock's row count of seven was right for the wrong reason — see the Open
  note: 3 of its 4 boards are actually pooled, not one-per-league, and need redoing. ⚠ Row count
  is a DIFFERENT axis from the board count corrected elsewhere in this file, which is why the
  board-count sweep did not catch it — it took a fourth review round. Any future row-count claim
  needs checking on its own.
- **A metric with no value is HIDDEN, not dashed.** CPO, 2026-08-08: a column of "-" reads as a bug
  to a visitor even when it is honest. Where a metric has no value for the pool being shown, the
  metric is removed from the board entirely, its NAME included, rather than rendered empty. This is
  a deliberate LOCAL override of the site-wide "null → -" convention in `00_overview.md`, which
  stands everywhere else. It applies at metric level, not at row level: a single missing value
  inside an otherwise populated column is still a dash.
- Every row links out. That is the whole reason these blocks exist.

**Scope.** Club league competitions only, within season. Club and national-team competitions are
never mixed — CPO: *"if that is the case somewhere then it is a defect."* Verified 2026-08-08 that
no mixing exists today: `int_player_season__metrics` groups by `league_code` and `mart_leaderboards`
ranks `partition by league_code, season_api_year`, so every competition is already its own ranking.
The rule becomes live the moment pooling crosses `league_code`. ⚠ **Under the 2026-08-18 rulings
(§10 below) it does not, for EITHER block** — both Top players and Top teams take each pool
league's own rank-1 and order the winners, so the RANKING never crosses `league_code` and every
board is 7 rows from 7 leagues by construction (Top teams: by construction once its still-unbuilt
mart is partitioned the same way — see the Open note; the CURRENT mock does not yet honour this).
The rule stays dormant for both blocks, and returns for any future surface that genuinely ranks
players or teams from different competitions against each other.

A rolling window was proposed as a way to keep every pool current year-round, and REJECTED.
CPO: *"no it must be within season, that's how you compare."*

**Four pools.**

| Pool | Leagues | Definition |
|---|---|---|
| 1 | PL · PD · BL1 · SA · L1 · LP · ED | European top, tier 1, split-year |
| 2 | LMX · SPL | rest tier 1, split-year |
| 3 | BSA · APD · MLS · J1 · KL1 · VL | rest tier 1, calendar-year |
| 4 | BL2 | second tier — NEVER a home-page candidate |

Pool 1 membership is **authored, not derived**. It cannot come from confederation plus tier: the
UEFA tier-1 leagues we carry are BL1, PL, PD, SA, L1, LP, ED **and VL**, so Veikkausliiga would
gate-crash the star pool on any derived rule. Belgium and Turkey belong in pool 1 and join when
they are ingested, with no restructuring.

Pool 4 exists so the tier split is mechanical — `tier` is already a registry field, so a new second
tier lands there with zero file edits. It is never a home-page candidate. Today it holds one
league, and a pooled ranking over one league IS that league's leaderboard, which the competition
page owns; the block rule at the top of this section forbids the copy.

**Selection.** One pool at a time, the other two reachable. A pool is in season when its
LEAST-PROGRESSED league has played at least **3** games, gated on the minimum the way
`int_team_season__deserved_vs_actual.sql:139` does with `min_games_played >= 3`. A higher floor was
proposed, on the grounds that a count leaderboard is more fragile early than the team rate metrics
that gate was written for; the CPO chose 3 for consistency with the house gate. Pool 1 wins when
more than one pool qualifies, so it holds the slot roughly September to May and pools 2 and 3 cover
the summer. If none qualifies, show the most recent completed pool 1 season and LABEL it finished
rather than dress it as current.

**What this needs from the warehouse. None of it is built.**

⛔ **THE FIRST THREE BULLETS ARE THE NINE-BOARD SET AND ARE VOID** (2026-08-10 reduction; they are
GAP-24, GAP-25 and GAP-26, all withdrawn in `99_gaps_register.md`). Every metric they ask for was
cut, so building any of it would serve nothing. Struck rather than deleted — the §10 list at the
foot of this file carries the corrected status of all of them. The bullets AFTER them are still
live and unchanged.

- ~~**Four new board keys**: `duels_total`, `dribbles_attempts`, `tackles_total`, `goals_against`.
  Five of the nine rank metrics already exist as boards: `scorer_points`, `shots_on_goal`,
  `passes_total`, `passes_key`, `cards_total`.~~ VOID — all four were cut.
- ~~**Three display columns.** `passes_accurate` and `goals_against` exist in
  `int_player_season__metrics` and are simply not selected into the mart. `shots_on_goal_against`
  is computed nowhere, but the catalogue already defines it as `sum(saves + goals_against)` and
  both inputs are present.~~ VOID — all three served boards that no longer exist.
- ~~**A reversed ranking mode.** The mart ranks descending and ranks only players with a positive
  value. Applied to `goals_against` ascending, that rule excludes every keeper on zero — exactly
  the ones the board exists for. It also needs a floor: one appearance and a clean sheet would
  otherwise top it. This is the one board where volume ranking does not protect the result.~~
  VOID — there is no Goals conceded board. ⚠ The limitation it describes is REAL and returns with
  any future ascending board; it is recorded on GAP-26's withdrawal for that reason.
- ⭐ **STILL MISSING and registered as GAP-30**: `assists` is not a ranked board at all. It is the
  second of the four surviving boards, so the reduced set cannot be built without it — a gap the
  nine-board list above never had to name, because `scorer_points` covered assists back then.
- **The club on a leaderboard row.** `int_player_season__metrics` already carries `team_sk`, the
  last club that competition-season; it is not selected into `mart_leaderboards`. Without it a row
  links to a player and nothing else, which halves the navigation purpose this block exists for.
- **Pool membership in the dbt seed.** ⚠ **HALF OF THIS IS NOW BUILT** (verified 2026-08-18):
  `competition_registry.csv` carries EIGHT columns, not three — `league_code, competition_type,
  parent_competition, confederation, slug, sort_order, tier, season_type` — so the `tier` and
  `season_type` projection this bullet asks for already shipped. ~~carries three columns
  (`league_code`, `competition_type`, `parent_competition`). Pooling needs `tier` and `season_type`
  projected from the YAML registry,~~ Only the **one authored pool field** remains.
- **A team boards mart.** All eleven team metrics already exist season-to-date in
  `int_team_season__metrics_cumulative`, and `deserved_points` is already on
  `mart_team_profile.sql:195`. What does not exist is top-N-per-metric ACROSS teams:
  `mart_team_competition_benchmarks` ranks ONE team against its own league, which is the opposite
  shape. So this is a new mart composing an existing model, not a reshape of the benchmark.

⚠ **The registry's `current_season` is stale and must not drive the season.** Compared against the
live export on 2026-08-08: APD, BSA and KL1 each read 2025 in the registry against 2026 in the
warehouse; UCL and UECL read 2024 against 2026; BL1 reads 2024 while every other pool-1 league
reads 2025. Take the season from the data. This is a defect in its own right, separate from this
block.

### Open

- ~~**How many of the fifteen boards appear on the home page**, versus a full stats page behind it.
  Nine player plus six team, at five rows each, against a page that already measured 4262px on
  mobile with four blocks.~~ **ANSWERED by the 2026-08-10 reduction**: FOUR player boards and FOUR
  team boards, at seven rows each — not fifteen boards at five rows. The length question it was
  really asking is settled by that cut, not by a separate ruling.
- **THE LAYOUT OF BOTH BLOCKS IS NOT DONE** (CPO, 2026-08-08, explicitly). A proposal was rendered
  and reviewed this session — row built from `.prow`, two columns from `.split`, a rank column, the
  extra metrics stacked in the value cell the way `.squad .pstat` already does it — and it is NOT
  approved. Nothing about the layout is recorded here on purpose. The constraint stands: compose
  from the existing design language, never a new per-page treatment.
- **All remaining copy**, in all three locales (§10). The two block names and all 80 metric names
  are now settled; the rest of this page's `strings.ts` entries are still placeholder drafts.
- **German and Finnish for the 60 new metric names.** Needed before go-live, not before the block
  is built (CPO). The label guard is therefore two-tier: `label_en` required on every catalogue row
  now, DE and FI required only for metrics a page actually renders.

Closed since 2026-08-04:

- ~~**Whether the league table stays** inside the stats block.~~ The block is replaced.
- ~~**Top-scorer scope**, per competition or across all.~~ ~~Pooled across the leagues of one pool.~~
  **RULED 2026-08-18: ONE PLAYER PER LEAGUE.** Each pool league's rank-1 player on the metric,
  collected and ordered by value — CPO: *"One per league -> yes, it's not a leaderboard in the
  defined pool."* So a board is 7 rows from 7 leagues by construction, never two from one league.
  ⚠ This is what `mart_leaderboards` ALREADY produces per league, so no pooled rank is needed
  (GAP-31 withdrawn).
- **The same question, asked of Top teams, RULED 2026-08-18: ONE TEAM PER LEAGUE.** CPO: *"one
  team per league, same as players."* Same mechanic — each pool league's rank-1 team on the
  metric, collected and ordered by value, never a rank crossing `league_code`. ⚠ **Unlike the
  players ruling, this is NOT free against the existing mock.** `top_teams_mock.html` was opened
  to check (per THE METHOD: check the mock's numbers, don't trust them): 3 of its 4 boards
  genuinely mix teams from one league — Real Madrid + Barcelona both La Liga on Goals/Shots on
  target/Passes, Arsenal + Manchester City both Premier League on Shots on target/Passes — and
  drop other pool leagues off the board entirely. Only Duels per match lands on 7 distinct
  leagues, by coincidence, not design. The players mock was already correct by accident; this one
  is not, and its placeholder rows need redoing before anyone should read a shape off it. No mart
  exists yet either way (GAP-29, still not started) — when it is built, partition the rank by
  `(league_code, season_api_year, metric_key)`, the way `mart_team_competition_benchmarks` already
  does, which is what makes "one per league" free at the SQL level, same as `mart_leaderboards`.
- **The Top teams intro copy — CPO confirmed 2026-08-18 the mock's "Ranked across pooled leagues"
  line is wrong now too**, and needs the same adjustment as the Top players line, same session.
  **Proposed, NOT yet approved** (copy is always his call — this is a draft for him to correct or
  confirm):

  > Season to date. The top team from each league: Premier League, La Liga, Bundesliga, Serie A,
  > Ligue 1, Liga Portugal, Eredivisie.

  Mirrors the approved Top players line's three constraints: states the mechanic and echoes the
  block's own name, avoids "leader" for the same reason it was rejected there, names no metric.
  Keeps **"Season to date"**, not "Season totals to date" — the team boards are per-match rates,
  not sums, so "totals" would misdescribe them, not just diverge from the players wording for no
  reason. Same caveat as the players line: the league list is the ACTIVE POOL's members, not a
  fixed seven.
- ~~**The Top players intro copy.**~~ **APPROVED 2026-08-18** (CPO: "you rephrase", then approved
  the proposal). The EN string is:

  > Season totals to date. The top player from each league: Premier League, La Liga, Bundesliga,
  > Serie A, Ligue 1, Liga Portugal, Eredivisie.

  It replaces *"Season totals to date. Ranked across pooled leagues: …"*, which described the
  pooled ranking withdrawn by the ruling above. Three constraints it satisfies, recorded so a
  rewrite does not undo them:
  - **"The top player from each league"** states the mechanic plainly and echoes the block's own
    name, so heading and sentence cannot drift apart.
  - ⚠ **"leader" is deliberately NOT used**, though it is the obvious word. The CPO rejected
    "Player leaders / Team leaders" as the block name on 2026-08-08 because *"leader"* collides
    with captaincy in football and translates awkwardly. The same objection applies to this
    sentence.
  - The sentence sits ABOVE all four boards, so it must not name a metric — "top player" carries
    goals, assists, passes and key passes equally.

  ⚠ The league list is the ACTIVE POOL's members, not a fixed seven: pools 2 and 3 hold the slot in
  the European summer, so the names change with the pool. DE and FI are written when the block is
  built, against `check_copy_gate.py` (no byte-identical-to-English values, no em dashes).
- ~~**The team stats block shape.**~~ ~~Six boards, specified above.~~ **FOUR boards** since the
  2026-08-10 reduction: `goals_per_match` → `shots_on_goal_per_match` → `passes_per_match` →
  `duels_per_match`.
- ~~**What the two blocks are called.**~~ Top players and Top teams.
- ~~**What each board is called.**~~ The rank metric's `label_en`, with no "ranked by" annotation.
- ~~**Whether trending still earns its place.**~~ It does not — it is absent from the composition,
  and the block is cut. This was never a question the CPO left open; it was written down as open by
  a build that had shipped trending and needed a reason to keep it.
- ~~**The player streak set** — the third signal, after the goalkeeper clean-sheet run was ruled
  redundant against the team clean-sheet row.~~ Moot: it blocked the player half of trending, and
  there is no trending block. Do NOT resurrect it as a Top players question — those boards rank on
  a metric's `label_en`, not on streaks.

### ~~Player streak facts established 2026-08-04, for whoever picks this up~~

⛔ **SUPERSEDED with the trending block.** Kept, struck rather than erased, because the warehouse
facts below cost real measurement and are true independently of the block that prompted them — if
player streaks are ever wanted anywhere on the site, this is what someone already found out.

- Player streaks DO NOT EXIST in the warehouse. Teams have `int_team_profile__streaks`; players have
  no equivalent. Building them is a new intermediate plus a mart, mirroring the team one.
- `mart_player_momentum` is NOT the right source. Its grain is (upcoming_fixture_sk, team_sk,
  player_sk) because it serves the FIXTURE page. It is correct at that grain (49,607 rows, 49,607
  distinct keys, zero duplicates) but a player carries ~12 rows, one per upcoming match, all with
  identical form. Collapsing it would mean deduping the very key it exists for.
- **The form window is the TEAM's last 5, not the player's last 5.** Confirmed in
  `int_player_momentum__metrics`: the selection is consumed from `int_team_momentum_window` so the
  player strip and the team form panel can never drift (#484). `games_in_window` is how many of the
  team's five the player actually appeared in. Measured distribution: 20.4% appeared in none, 20.7%
  in one, 19.8% in two, 13.2% in three, 11.1% in four, **only 14.9% in all five**. So any RANKING of
  players on that window needs a qualification gate, the way the rate leaderboards already use
  minutes >= 270.
- Player momentum displays TOTALS over the window plus four weighted ratios. It has no per-match
  rates at all (`metrics_context_model.md` §8.1, and the mart's columns confirm it).

## 1. Purpose

The front door. A reader arrives knowing nothing and leaves having chosen something to look at.
The **stop-scrolling moment** is the first screenful: real matches about to be played, with names
and crests they recognise, not a menu of links.

~~Composition is locked (CPO 2026-06-10, `site_architecture.md` §4 and `ui_design_brief.md` §6.3):
fixtures first, browse second, storylines third, stats fourth. This spec fills in the shapes, it
does not reopen the order.~~

⛔ **SUPERSEDED.** Later rulings overturned that order, so "locked" is the wrong word for it now.
Browse moved to the BOTTOM (CPO 2026-08-04); the stats module was removed and the composition
restated as **next matches → Top players → Top teams → browse** (CPO 2026-08-08, §0). Trending is
not in it and is cut. ⛔ **Browse itself was DROPPED 2026-08-19** (CPO: "drop the browse
section") — current composition is **next matches → Top players → Top teams**, three blocks.

~~**This PR ships TWO of those four: next matches → browse.** The middle pair is specified in §0,
unbuilt, and lands in its own PR. See §0 for why browse holds the bottom slot meanwhile.~~ That PR
shipped; browse then left the composition entirely — see §0.

## 2. URL

```
/{locale}/
```

- One page per locale. `de`, `en`, `fi` today.
- Every locale is prefixed; `/` is the client-side language redirect and is NOT this page
  (`site_architecture.md` §3 locale routing).
- `hreflang="x-default"` points at the `en` URL, not at `/`.
- No breadcrumb: this is the breadcrumb root every other page points back to.

## 3. Data sources

`data/landing.json`, written by `shape_landing_payload` in `scripts/export_site_data.py`.

| Payload key | Upstream |
|---|---|
| `upcoming[]` | `core.fct_fixture` (the same `status_short in ('NS','TBD')` filter `fetch_fixture_payloads` uses), joined to `core.dim_team` / `core.dim_league` for names and crests |
| ~~`browse`~~ | ⛔ **DROPPED 2026-08-19** (CPO: "drop the browse section"). Was `build_nav()` over `docs/competition_registry.yml` — the identical structure `nav.json` carries. `build_nav`/`fetch_nav` still produce `nav.json` independently; only this page's use of them is gone |
| ~~`trending[]`~~ | ⛔ **REMOVED 2026-08-08** with the trending block. `mart_landing_trending` was written for this key and is deleted; `mart_team_profile` is no longer read by this page |
| ~~`stats`~~ | ⛔ **REMOVED 2026-08-08** with the stats-teasers module. `mart_leaderboards` and `mart_standings` are no longer read by this page at all |

ONE key plus `type`. The writer emits `type`/`upcoming` and nothing else; `types.ts`'s
`Landing` carries the same two fields, and `test_shape_landing_payload_carries_only_the_built_modules`
asserts the set exactly, so a removed key coming back fails a test rather than a review. Top
players and Top teams will each add a key here when they are built.

This table is the contract this document's own header calls it — so it must name what the writer
emits and nothing else. Locale-independent, like every other payload. All display strings resolve at
build time.

## 4. Layout

⛔ **SUPERSEDED — the diagram below draws a page that no longer exists.** It shows four modules with
browse second; the page ships ONE, next matches alone. Four rulings overturned it: browse moved to
the bottom (CPO 2026-08-04), the stats teasers were removed and the composition was restated
without trending (both CPO 2026-08-08), and browse itself was dropped (CPO 2026-08-19, "drop the
browse section").

⛔ **SUPERSEDED 2026-08-19 — this table describes a page that no longer exists.** It measured the
2-block build (next matches + browse); browse is dropped, so the page today is next matches alone.
Kept for history, not re-measured — a fresh number belongs in
`.claude/task/rendered_page_evidence.md` if a future build needs one, not invented here.

~~**What ships today**, measured rather than drawn, at 375px:~~

| | block | top | height |
|---|---|---|---|
| 1 | Next matches | 95px | 1205px |
| ~~2~~ | ~~Browse~~ | ~~1336px~~ | ~~2531px~~ |

~~Page 4126px, no horizontal overflow.~~ The hero's own two numbers (95px / 1205px) are unaffected
by browse's removal — nothing above it changed. ⚠ 4126 was MEASURED, not subtracted — a first draft
of this line arrived at 4162 by arithmetic on the old total and was wrong, which is exactly why a
new page-height figure is not being arithmetic'd here either.

⚠ **No replacement diagram is drawn here on purpose.** The layout of the two blocks that replace
the removed fourth — Top players and Top teams — is explicitly NOT decided (CPO 2026-08-08), and
drawing a picture of an undecided layout is how a wireframe starts inventing one. The table above
records what the build does; it does not propose what it should do.

The original diagram is retained below, struck, because §5's module bindings still reference its
numbering.

```
┌────────────────────────────────────────────┐
│  [Matchday Pilot]      [search]  [DE▾] [◐] │  site header (09_chrome)
├────────────────────────────────────────────┤
│  NEXT MATCHES                              │  (1) fixtures hero
│                                            │
│  Brasileirão Série A                       │      competition heading
│   Tue 20:00  Palmeiras     vs  Flamengo  ▸ │      fixture row → match page
│   Tue 22:30  Grêmio        vs  Bahia     ▸ │
│                                            │
│  Major League Soccer                       │
│   Wed 01:00  Inter Miami   vs  Orlando   ▸ │
├──────────────— fold (~700px) —─────────────┤
│  BROWSE                                    │  (2) hybrid browse
│  Leagues    Cups   European   National     │      by group
│   ▸Bundesliga ▸Premier League ▸LaLiga …    │
│                                            │
│  By country                                │      by country
│   ▸Germany ▸England ▸Spain ▸Finland …      │
├────────────────────────────────────────────┤
│  TRENDING                                  │  (3) storylines
│   ⬡ 8 unbeaten   Palmeiras       ▸         │      run chip + team → team page
│   ⬡ 6 winless    Vasco da Gama   ▸         │
│   …6 rows…                                 │
├────────────────────────────────────────────┤
│  TOP SCORERS · Brasileirão Série A         │  (4) stats teasers
│   1 Pedro          14 goals    ▸           │
│   …5 rows…                                 │
│                                            │
│  TABLE · Brasileirão Série A               │
│   1 Palmeiras   20  45   ▸                 │
│   …5 rows…      ▸Full table                │
├────────────────────────────────────────────┤
│  site footer (09_chrome)                   │
└────────────────────────────────────────────┘
```

**Above the fold**: the header plus the first competition's upcoming matches. Nothing else. The
product's core feature is the match, so the match is what a reader lands on. ✅ Still true, and the
measurement above confirms it — the hero runs from 95px to 1300px, well past the fold.

~~**Desktop (≥ 900px)**: uses the shared `.shell > .page-grid` primitive from 09_chrome. Main
column carries hero, trending and stats; the rail carries browse. Below 900px browse falls back
into the single column in the order drawn above.~~

⛔ **SUPERSEDED and never built.** Browse is not in a rail; it was the last block in the single
column at every width, and neither of the blocks that were to sit beside it still exists. The page
does not use `.page-grid` at all — it uses `.inner`, the 680px single column. Whether the home page
ever adopts the two-column shell is part of the undecided layout question above. ⛔ **Browse itself
is dropped 2026-08-19** — this whole rail question is now moot for it specifically, though it
remains open for whatever Top players/Top teams end up needing.

⚠ `09_chrome.md` §4 and §10 still name "standings/trending/top-scorers" as candidate contents for
that unwired rail, quoting the `1c35e7aa` mock. All three are cut or unbuilt blocks. Those lines are
about a reference mock and a primitive wired into zero pages, not about this page's composition, and
`09_chrome.md` is outside this task's contract scope — left as found, recorded here so the next
person reading them knows they describe 2026-06, not the page.

## 5. Module bindings

### (1) Fixtures hero — `upcoming[]`

`upcoming[]` is a list of competition groups, each `{league_code, league_name, competition_slug,
region_rank, season, fixtures[]}`.

⚠ **The payload's group order is NOT the display order.** It is first-appearance (a deterministic
export diff); the page applies the site-wide ordering key at render time —
`site_v2/src/lib/competitionOrder.mjs`, the same function the competitions index uses (CPO
2026-08-18: one shared rule). The key: has-an-upcoming-fixture → **calendar day** → `region_rank`
→ kickoff time → `league_code`. `region_rank` is served from `mart_competition_index`, never
derived in the export or the frontend.

Because **day precedes region**, a competition playing earlier always outranks one playing later;
region only breaks same-day ties. That is what stops a 10:15 kickoff outranking a 19:00 one, which
is the noise this block carried until 2026-08-18.

| Element | JSON key | Format |
|---|---|---|
| Competition heading | `upcoming[].league_name` | text; links to the competition hub via `competition_slug` |
| Kickoff | `upcoming[].fixtures[].kickoff` | UTC ISO in the payload; rendered per the timezone convention in `00_overview.md` |
| ~~Round~~ | `upcoming[].fixtures[].round` | **NOT RENDERED.** The payload carries it, the hero does not show it. `fixture.round` is the provider's raw English string, so putting it here shipped "Regular Season - 18" and "3rd Qualifying Round" byte-identically to de/en/fi — verified from built output — making the home page a fourth surface for **#866**, and the most visible one. #866 states the fix cannot live in the frontend: mapping that string to a phase plus a number is taxonomy mapping, which the consumption layer forbids. The round returns here when the warehouse serves a localisable phase. |
| Home / away name + crest | `…fixtures[].home.name` / `.crest`, `.away.name` / `.crest` | crest falls back to a monogram, as on 01 |
| Link target | `…fixtures[].slug` | `/{locale}/{competition_slug}/matches/{slug}/` |

**GAP-02 resolved here — SUPERSEDED 2026-08-18. The window is THE NEXT MATCHDAY: every fixture on
the earliest upcoming kickoff date.** The original resolution was "the next 12 fixtures by kickoff,
not a calendar day"; the count is retired.

⚠ **Why the count went** (CPO 2026-08-18: *"we will show what we have, more matches will come,
because we ingest more competitions"*). Twelve was reasoned — see the measurement below — but it
does not SCALE. As competitions are onboarded, twelve slots hold fewer and fewer of them, so the
block narrows exactly as the site broadens. It also bled across days: the sample committed before
this change held 12 fixtures spanning **two** dates, which is not a matchday and reads as an
arbitrary cut.

⚠ **This does NOT reopen what the measurement settled.** "Today's matches" was rejected for
rendering one row on some days. The rule is *the next day that HAS matches*, which is a different
rule and is **never empty by construction**. The table below is retained because it is still the
evidence for that distinction, and for the honest upper bound: the busiest day sampled carried 57
fixtures. If a busy matchday reads too long, that is a CPO call on the block (**#908** parks a
"more matches" control) — not a new number reintroduced here.

⚠ **OPEN, BOTH DIRECTIONS — and the second one is easy to forget.** The rule makes the block's
length follow the football calendar, so it is variable by design:

- **Too LONG** on a busy day (57 fixtures measured worst case). Named above.
- **Too SHORT on a quiet day**, which is the direction the first build actually hit: the sample
  regenerated on 2026-08-18 held **4 fixtures across 2 competitions** — a thin front door, where the
  retired count would have shown 12 by borrowing from the following day. That borrowing is exactly
  what "we will show what we have" rejects, so this is the rule working, not failing. Whether a
  4-match day is an acceptable home page is nonetheless a PRODUCT question and is **not decided**.

Both belong to the same CPO call on the block; neither is a licence to reintroduce a count.

Measured 2026-08-03 against `core.fct_fixture`, upcoming fixtures by days ahead:

| days ahead | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixtures | 4 | 13 | 6 | 39 | 6 | 30 | 41 | 1 | 17 | 8 | 43 | 11 | 42 | 57 | 11 |

A "today's matches" hero renders four rows today and one row on day 7, and a fixed 7-day window
swings between 1 and 139. ~~A fixed count is always populated and never floods the page. Twelve
fills the first screenful across two or three competitions on every day measured.~~

⚠ That last sentence is the retired argument, struck rather than deleted so the reasoning stays
auditable. What it got right — a *fixed calendar window* is unusable — the matchday rule keeps, by
taking the earliest date PRESENT rather than today's. What it got wrong is that a count is the only
alternative: it trades an empty block for a truncated one, and truncation gets worse with every
competition onboarded.

### (2) Hybrid browse — `browse` ⛔ DROPPED 2026-08-19

⛔ **THIS MODULE NO LONGER EXISTS.** CPO, in chat: "drop the browse section". Its only remaining
justification — reachability into the long-tail team/player pages — applies to exactly the two
entity types already blocked on the team/player-name data-quality work (`.claude/active_work.md`);
the competitions pool it would otherwise serve alone (~15-20 rows) is already fully covered by the
competitions index page (#62). The home page's Browse component, the `browse` payload key and
this module's i18n keys are deleted. `build_nav`/`fetch_nav` are NOT deleted — `nav.json` is still produced
independently (`--entities nav`) and is untouched by this change.

The section is kept, struck rather than erased, for the same reason trending's is below: it
documents a real, reviewed module binding, and the reasoning behind it stays true whatever the
home page does next.

~~Identical structure to `nav.json`, so one shape serves nav and home.~~

| ~~Element~~ | ~~JSON key~~ | ~~Notes~~ |
|---|---|---|
| ~~Group heading~~ | ~~`browse.groups[].key`~~ | ~~i18n key per group; order is `_GROUP_ORDER` in the export, itself the order in `site_architecture.md` §4~~ |
| ~~Competition link~~ | ~~`browse.groups[].competitions[].slug` / `.name`~~ | ~~`/{locale}/{slug}/`~~ |
| ~~Country heading~~ | ~~`browse.countries[].country`~~ | ~~domestic types only, per `_DOMESTIC_TYPES`~~ |
| ~~Country competitions~~ | ~~`browse.countries[].competitions[]`~~ | ~~tier then sort_order, as `build_nav` already sorts~~ |

~~No competition is named in the template. A registry addition appears here with zero file edits,
which is the zero-file rule applied to the home page.~~

### (3) Trending — `trending[]` ⛔ REMOVED 2026-08-08

⛔ **THIS MODULE NO LONGER EXISTS.** It is absent from the composition the CPO set on 2026-08-08
(§0), so the block, `TrendingList.astro`, the `trending[]` key, the six i18n keys, the page-spec
entry, seven tests and `mart_landing_trending` itself were all deleted in #367.

It also never matched its own last ruling. The 2026-08-04 row in §0 called for THREE team signals —
winning, unbeaten, clean-sheet — with **"winless and losing are both dropped"**, plus player
streaks, plus a full start date on each row. What was built served five signals including `winless`,
no player streaks and no dates. So there was no version of this block that could have shipped as
specified, and reworking it was never the alternative to cutting it.

The section is kept, struck rather than erased, because the measurements below cost real BigQuery
work and stay true of the warehouse whatever the home page does with them.

~~Each row `{signal, value, team_id, team_name, team_slug, crest, league_code, league_name,
competition_slug, season}`.~~

| ~~Element~~ | ~~JSON key~~ | ~~Format~~ |
|---|---|---|
| ~~Run chip~~ | ~~`trending[].value` + `.signal`~~ | ~~integer + the signal's i18n label~~ |
| ~~Team~~ | ~~`trending[].team_name`, `.crest`~~ | ~~links to `/{locale}/teams/{team_slug}/`~~ |
| ~~Competition~~ | ~~`trending[].league_name`~~ | ~~links to the competition hub~~ |

⚠ That team link was the ONLY link to a team page anywhere on the site. Cutting it left six team
payloads in `site_v2/src/data/teams/` with nothing pointing at them; they were removed from the
`.gitignore` allowlist and deleted. `33.json` stays — it is the team page's own sample.

~~**GAP-04 resolved here, with the CPO's selection recorded.**~~ **GAP-04 is not resolved; it is
WITHDRAWN** — it asked which signals a block that no longer exists should surface. Signals below,
with the live count for every league-season that still has an upcoming fixture (359 teams, measured
2026-08-03), kept as a warehouse measurement:

| signal | column | minimum | live teams |
|---|---|---|---|
| unbeaten | `unbeaten_run` | 3 | 47 |
| winless | `winless_run` | 3 | 54 |
| wins | `win_run` | 3 | 6 |
| clean sheets | `clean_sheet_run` | 3 | 6 |
| scoring | `scoring_run` | 5 | 28 |

~~Ranking: **run length descending, at most two teams from any one competition, six rows.** Both
directions show: a winless run is a real storyline and every football site publishes it.~~ The
"both directions" argument was mine, and it is what kept `winless` in the mart after the CPO had
dropped it. Recorded, not deleted: the failure was reasoning from what football sites publish rather
than from the ruling in §0.

~~**All of that selection happens in `mart_landing_trending`, not in the export.**~~ The mart is
deleted. **The layering lesson it was written to enforce is NOT deleted**, and it outlives the
block: ranking is business logic, the consumption layer may not do it, and the precedent is
`mart_leaderboards`, whose export helper says in as many words that it "does not rank". A first
draft of the trending export ranked teams in Python from raw streak columns; that is why the mart
existed. Top players and Top teams inherit the same rule — see the corrected gap list in §10.

**Deserved-vs-actual is excluded, on data.** `sot_points_gap` is non-null for **0 of those 359
teams**. The full-table gate in `int_team_season__deserved_vs_actual.sql` requires every team in a
league-season to carry `sot_difference_per_match`; measured today KL1 is missing 12 of 12, VL 12 of
12, BSA 2 of 20 plus a missing rank, LMX 2 of 18, while MLS and APD are correctly withheld as
non-single-ladder. #810 separately holds two open CPO decisions on rendering it mid-season. It
returns to this screen when both change, not before.

### (4) Stats teasers — `stats` ⛔ REMOVED 2026-08-08

⛔ **THIS MODULE NO LONGER EXISTS.** The CPO ruled it useless on 2026-08-08 and replaced it with
the two mart-backed blocks in §0, Top players and Top teams. The component, the `stats` payload
key, the two export helpers, the i18n keys, the page-spec entry and the tests were all deleted in
#367; the home page ships three modules. The section is kept, struck rather than erased, because
its three eligibility rules were each forced by a real defect and the replacement mart must
inherit them rather than rediscover them:

| Rule | The defect it prevents, measured 2026-08-03 |
|---|---|
| season must have started | The PL's 2026 table served alphabetically with `played` 0 for every club. Rendering it stated that Arsenal were top of the league. They had played no matches. |
| single ladder only | Copa Libertadores' top five rows were five different GROUP leaders, all ranked 1, because `standing_rank` is within-group. |
| must carry player stats | ACN 2027 had a real table (played 6, 24 teams) and ZERO leaderboard rows. |

Everything below this line describes the removed module and is retained only as that record.

`stats` was `{league_code, league_name, competition_slug, season, top_scorers[], standings[]}` for
ONE competition.

**Which competition is registry-driven, not a preference**: among competitions carrying an upcoming
fixture, the one with the lowest registry `sort_order`. That field is already the CPO's authored
display ordering and already drives `build_nav`, so the home page inherits it rather than
introducing a second ranking. A registry reorder moves this block with no file edit.

| Element | JSON key | Format |
|---|---|---|
| Scorer rank / name / goals | `stats.top_scorers[].rank`, `.player_name`, `.goals` | integer, text, integer |
| Scorer appearances | `stats.top_scorers[].appearances` | integer |
| Table row | `stats.standings[].standing_rank`, `.team_name`, `.played`, `.points`, `.goals_diff` | integers + text |
| Table crest | `stats.standings[].team_logo_url` | monogram fallback |
| Full-table link | `stats.competition_slug` | `/{locale}/{slug}/table/` |

Five rows each. Both are teasers; the full lists are the competition pages.

**No team name on a top-scorer row.** `mart_leaderboards` carries no team column (verified against
the live schema: `player_sk`, `player_name`, `player_nationality`, `player_position`,
`player_photo_url`, then the stat columns). The scorer row is therefore rank, name and goals. Adding
the club would mean joining a squad mart in the export, which is derivation in the consumption
layer, so it is a warehouse change if it is ever wanted. A first draft of this table bound a
`team_name` key that does not exist, which is the binding rule doing its job.

**The standings columns are `points` / `played`, not `standing_points` / `standing_played`** (same
verification). Only `standing_rank` carries the prefix.

## 6. States

- **Null value → "-"**, never a fabricated 0 (`00_overview.md` display conventions).
- **No upcoming fixtures anywhere** (an all-competition off-season): the hero renders its empty
  state. ⚠ **CHANGED 2026-08-19 — there is no longer a browse fallback under it.** Browse used to
  keep the page non-empty in this branch ("the page still ships as browse alone, which is
  registry-driven and always renders"); with browse dropped, this branch means the page renders
  ZERO blocks. Not reachable in practice with nine tournaments and fourteen leagues active, and
  still designed rather than left to crash, but genuinely a bare page if it is ever reached — worth
  a look if that stops being true as competitions churn.
- **A competition with no upcoming fixture never appears in the hero.** It is absent, not an empty
  heading, and never a zero-filled row.
- ~~**A trending signal with no qualifying team is omitted**, not shown with an empty list.~~
  ⛔ **REMOVED 2026-08-08** with the module.
- ~~**`stats` is null** when no competition has an upcoming fixture. The module is omitted whole.~~
  ⛔ **REMOVED 2026-08-08** with the module. `stats` is not a payload key, a component or a state
  in this build; there is nothing left for the rule to describe.
- **Missing crest → monogram**, the same fallback 01 and 02 use.
- **Thin-page rule**: not applicable. The home page's block count does not depend on any one
  entity's data depth.

## 7. Interactions

Static site, no islands on this screen. Every element is a link. The kickoff timestamps get the
same progressive-enhancement timezone script the other screens use. Search lives in the header
(09_chrome), not in this page's markup.

## 8. SEO

| | |
|---|---|
| Title | `seoHomeTitle` — per locale, distinct words, not a concatenation of locale-independent payload fields |
| Description | `seoHomeDesc` — per locale |
| Canonical | self |
| hreflang | all locales, `x-default` → `en` |
| schema.org | `WebSite`. Not `SportsEvent`: the page is not one match. `BreadcrumbList` is omitted, this being the breadcrumb root |
| Inbound hub | none — this IS the root hub |
| Outbound | **fixture, and nothing else** — what `index.spec.json` declares and what the built HTML emits. NOT competition: the hero's competition heading is still an inert `<span>` until the competition hub exists, so claiming a competition edge would be declaring a link the page does not have (browse's chips made the same point until 2026-08-19, when the block was dropped rather than left inert). NOT team either, since 2026-08-08: the trending row's team link was the page's only one, and the block is cut. This line has now been wrong twice — it read "fixture, competition, team… every one of the four modules links out", then "fixture and team". Both times it described a module that had been removed. **Re-derive it from the built HTML, never from this table.** |
| Page-count driver | `count(locales)` |
| URL permanence | permanent. The locale root is the most permanent URL on the site |

Titles must differ per locale. The scaffold this replaces shipped a byte-identical
`<title>Matchday Pilot</title>` in all three, which is the defect #844's gate exists to catch.

## 9. Component census

Reused unchanged: fixture row (01), crest + monogram (02, via `Crest.astro` in the hero), section
head, internal-links footer, site header/footer (09), empty/absent state.
~~player row (01)~~ — it was here for the removed stats teasers' scorer rows.
~~form/result chip family (01), streak chip (02)~~ — both were here for the trending row, and
nothing else on the page renders either.
~~`.linkchip`~~ — was browse's only chip, dropped with the block 2026-08-19. Verified by grep over
`components/home/`: no chip of any kind is composed on the home page today, and `.prow` — the row
primitive trending composed — is likewise used by no home component.

➕ New, flagged for the design system. **ONE, not five** — see the four struck rows.

| Component | Why it is new |
|---|---|
| Competition group heading (hero) | a fixture list grouped by competition; 01 and 02 both show a single competition's fixtures |
| ~~Browse group grid~~ | ⛔ **DROPPED 2026-08-19** with the browse block. Was "the hybrid-IA block; no existing screen renders the registry" |
| ~~Country hub list~~ | ⛔ **DROPPED 2026-08-19** with the browse block. Was "same" |
| ~~Trending story row (run chip + team + competition)~~ | ⛔ **REMOVED 2026-08-08** with the trending block. Nothing on the page composes `.prow` any more |
| ~~Compact standings table~~ | ⛔ **REMOVED 2026-08-08.** It existed only for the stats teasers' `TABLE · {competition}` snippet. No shipped module renders a standings table, and the Top players / Top teams design in §0 does not reuse one either — it composes `.prow` inside `.split` with a rank column |

⚠ This row survived six review rounds because every sweep, including mine, searched for "stats",
`mart_leaderboards` and `mart_standings`. It contains none of them. `bi-analyst-reviewer` found it
in round 6 by widening to `scorer|TABLE|standing`. The lesson for the next person editing this
document: a deleted module leaves traces that do not carry its name.

## 10. Gaps

- **GAP-02** — resolved in §5(1): ~~next 12 fixtures by kickoff~~ **the next matchday** (every match
  on the earliest upcoming kickoff date; the count was retired by the CPO on 2026-08-18), with the
  per-day measurement behind
  the choice.
- **GAP-04** — **WITHDRAWN**, not resolved. It asked which `mart_team_profile` signals the
  trending/storylines feed should surface and how they rank. There is no such feed: the block is
  absent from §0's composition and was cut on 2026-08-08. A withdrawn gap is not a closed one — if
  storylines ever return to this site, the question is open again and the measurements in §5(3) are
  the head start.
- **GAP-03** — still open, and this screen no longer touches it at all. The narrative generator was
  going to add a sentence to each trending row; with that block gone, neither shipped module has a
  slot for generated prose. Its remaining claimants are the other screens.

The Top players and Top teams blocks specified in §0 need six pieces of warehouse work, none of it
built. They are registered rather than described only here, because `00_overview.md`'s binding rule
is unconditional — a gap goes to the register with a proposed disposition and is never silently
drawn — and describing one inline, however loudly, is not registering it. The precedent is
GAP-11/12/13/20/21/22/23: every one was an already CPO-approved locked design that still took a
register row.

⚠ **THIS LIST WAS STALE AND IS CORRECTED 2026-08-18.** It named six gaps written against the
nine-board design; three of those are VOID and three gaps registered since were missing. The
register is the authority — check it, not this summary.

- ~~**GAP-24** — four new board keys (`duels_total`, `dribbles_attempts`, `tackles_total`,
  `goals_against`).~~ **VOID**: all four metrics were cut by the 2026-08-10 reduction.
- ~~**GAP-25** — three display columns (`passes_accurate`, `goals_against`,
  `shots_on_goal_against`).~~ **VOID**: all three served boards that no longer exist.
- ~~**GAP-26** — ascending ranking mode plus a minutes floor for the Goals conceded board.~~
  **VOID**: there is no Goals conceded board. ⚠ It carried "the highest-risk of the six" for eight
  days after the board was deleted. The underlying limitation is real and returns with any future
  ascending board — `mart_leaderboards` ranks descending and only positive values, so a
  zero-is-best board silently excludes its own subjects.
- **GAP-27** — LIVE. The club on a leaderboard row (`team_sk`); `grep -c team_sk` on the mart = 0.
- **GAP-28** — LIVE, but SMALLER than written: `tier` and `season_type` are ALREADY projected into
  the seed (8 columns, verified). Only the authored pool field remains.
- **GAP-29** — LIVE. A team-boards mart; `mart_team_competition_benchmarks` is the opposite shape.
- **GAP-30** — LIVE, registered 2026-08-18. `assists` is not a ranked board, so the reduced set's
  second board has no rank-1 to take.
- ~~**GAP-31** — a pooled rank across the pool.~~ **WITHDRAWN 2026-08-18**: the block is one player
  per league, so the per-league rank the mart already computes is the one it needs.
- **GAP-32** — LIVE, registered 2026-08-18. Belongs to the fixtures hero, not these blocks: the
  matchday is selected in the export rather than served by the warehouse. CPO ruled ship-as-is.
