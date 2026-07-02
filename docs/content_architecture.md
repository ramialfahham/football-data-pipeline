# Content architecture — blocks, tabs, navigation

> The modular content model for the website: how a few reusable **blocks** (each backed by one
> mart) compose into **tabbed entity pages**, wired by a **navigation graph**, to produce a deep,
> multi-language, programmatic-SEO site from a small set of moving parts. CPO-ruled across the
> 2026-06-17 design conversation.
>
> This is the IA the wireframes *arrange* and the marts *feed*. It builds on:
> - `docs/site_architecture.md` — the v2 site IA (fixtures-first home + browse, epic #361).
> - `docs/metrics_context_model.md` §8 — the player performance surface + the shared window/aggregation model.
> - the `metric_catalogue.csv` seed (metric definitions — the SSoT) / `docs/wireframes/metrics_display.md` (the locked display contract).
>
> SPEC ONLY. Each build named here (the new marts, the backfill, coaches) is its own later PR with its
> own review; number-changing builds get analytics-engineer + football-analytics sign-off then.

---

## 1. Principles

1. **Three layers.** **Blocks** (reusable content units) → **tabs** (per-entity compositions) →
   **navigation graph** (entity↔entity links). Nothing computes in a page — pages only *arrange* blocks.
2. **One block = one mart**, parameterised by `league_code` / season / entity. Adding a competition,
   team, player, or season is *more rows → more pages → zero new marts* (the zero-file rule, extended
   to the site).
3. **"Profile" is not a thing** — it's the **Overview tab**, a compact digest. Each entity page is a
   set of tabs.
4. **Languages are free.** Blocks are locale-independent data; labels resolve at build time from the
   metric-catalogue i18n keys + entity names (`export_site_data.py` already works this way). N
   languages = same data × label sets.
5. **Density is built in.** Every block carries a *compact* and a *full* form; the placement picks
   (compact on Overview/teasers/home-hooks, full on dedicated tabs). The compact rule differs by
   subject, per the locked display contract: **team blocks = tier-1 rows only** ("tier = visibility
   under constraint"); **player blocks have no tiers — they use per-surface rules** (e.g. the
   fixture top-players strip ranks goals → assists → key passes). See
   `docs/wireframes/metrics_display.md`.
6. **Honest limits.** No xG (we substitute our own chance-quality metrics), no news source, no
   transfers tab. We never fabricate; a block that has no data simply doesn't render.

---

## 2. Entity types (the programmatic-SEO templates)

Five rich templates + two thin ones; everything else is rows.

| Entity | Tier | Example URL | Page-count driver |
|---|---|---|---|
| **Competition** | rich | `/bundesliga/2025-26` | competitions × seasons |
| **Team** | rich | `/bayern-munchen` (+ season) | teams (× seasons) |
| **Player** | rich | `/harry-kane` (+ season) | players (× seasons) |
| **Fixture** | rich | `/bayern-dortmund-2025-10-04` | fixtures |
| **Matchday** | thin SEO | `/bundesliga/2025-26/spieltag-7` | competitions × rounds |
| **Coach** | thin SEO | `/vincent-kompany` | coaches (API-Football provides them) |
| Nation, Stadium | deferred | — | — |

Teams + players + fixtures + competition-seasons + matchdays × **languages** = the thousands of
indexable pages. Each is one template fed by `league_code`-keyed marts.

---

## 3. The block library (block ↔ mart)

> **Status legend** (reconciled 2026-07-02, post-#634). **✓** = mart built AND wired to the v2 export
> (`scripts/export_site_data.py`) — the spec'd screens (fixture / team / player / Squad / Stats-percentile /
> Career) are green. **⚠ orphan** = mart BUILT but NOT wired because its screen is not spec'd yet — today
> only the **team** (rank-based) benchmark. **✗** = mart not built (Phase C/D). The v2 export queries 17 marts.

| Family | Block | Subject | Backing mart | Status |
|---|---|---|---|---|
| **Identity** | Team header | team | `dim_team` (+ founded/venue, + standing chip) | ✓ (founded/venue #613; coach pending) |
| | Player header | player | `dim_player` (+ current club, + birth date) | ✓ (current club #611, birth date #609) |
| | Competition header | comp | registry / dim | partial |
| **Performance** | Form (recent) | team, player | `mart_momentum__{team,player}` (+ `_window` drill-down) | ✓ (player `_window` gap) |
| | Season (this season; per-game toggle) | team, player | the Season block (player: #480) | ✓ team · ⚠ player (#480 per-club grain = Phase C) |
| | Season-over-season | team, player | YoY model | ✓ team · gap player (Phase C) |
| | Vs-benchmark (bars vs league avg + percentile) | team, player | `mart_{team,player}_competition_benchmarks` | ✓ player wired (#627; screen 12 spec'd #625) · ⚠ orphan team (rank-based, screen unspec'd) |
| | Single fixture | team, player | `mart_team_fixture_stats`/`mart_player_fixture_stats` | ✓ |
| **Standings / rank** | League / group table | team | standings mart (#322) | ✓ |
| | Standing-as-context | team | standings mart | ✓ |
| | Leaderboards (scorers + the metric set) | player | `mart_leaderboards` | ✓ (built + wired) |
| **Schedule** | Upcoming / Results | team, player | `mart_team_fixtures` (filter) | ✓ (team fixtures #607) |
| | Matchday schedule | comp | fixtures by round (derive) | ~ |
| **Listings** | Squad / roster | team→players | `mart_roster` (from the team↔player mapping) | ✓ (identity-only squad wired to the team payload, #619; screen 11 spec'd #617) |
| | Team directory | comp→teams | `dim_team_competition_season_mapping` | ✓ source |
| | Player career (clubs + per-comp totals) | player | `mart_player_career` (needs backfill) | ✓ wired (#634; screen 13 spec'd #632) — still thin until backfill |
| **Matchup** | Match preview (two sides) | fixture | composed (W1 `mart_team_momentum` + W2 `mart_team_season_record` + standing + h2h) | ✓ (v2; `mart_matchday_insights` = the separate live-MVP feed) |
| | Lineups / key players | fixture | fixture player stats / `mart_leaderboards` | ✓ |
| | Head-to-head | fixture | `mart_head_to_head` | ✓ embedded (standalone `/h2h/` target = GAP-06, deferred) |
| **Insight** | Deserved-vs-actual *(flagship)* | team (player v1.x) | `mart_team_profile` differentiator | ✓ team (rank-space #606) |
| | Vs-own-history / YoY *(flagship)* | team (player v1.x) | YoY model | ✓ team |
| | Opponent / schedule context *(flagship, v1.x)* | team, player | (uses the benchmark engine) | ✗ not built (Phase D) |
| | Contribution-share *(bonus)* | player↔team | **NEW** mart-computed (share of team output; definition reserved to build) | ✗ not built (Phase D) |
| | Streaks | team (player?) | `int_*_profile__streaks` | ✓ team |

A block works for any competition and either subject because it's just a mart sliced by
`league_code` / entity — so the same block appears on many tabs/pages, defined once.

---

## 4. Pages = tabbed compositions

> This is the **proposed default arrangement** — the starting layout the wireframes refine. The tab
> *set* per entity is settled; the exact block placement within each tab (and which compact blocks an
> Overview shows) is a wireframe-time detail, not locked here.

| Entity | Tabs → blocks |
|---|---|
| **Team** | **Overview** (header + form + season highlights + standing + next + key players + deserved-vs-actual teaser) · **Matches** (upcoming + results) · **Stats** (season per-game + vs-benchmark + season-over-season + deserved-vs-actual + streaks) · **Squad** (roster) · **History** (past-season records, all-time, coach) |
| **Player** | **Overview** (header + form + season highlights + position + next) · **Matches** (log → fixture) · **Stats** (season per-game + percentile-vs-peers + season-over-season) · **Career** (clubs + per-competition totals + caps) |
| **Competition** | **Table** · **Fixtures** (by matchday) · **Scorers** (leaderboards) · **Teams** (directory) · **Seasons** (archive) · **Stats** (league-wide → benchmark) |
| **Coach** | **Overview** (current club + clubs managed) |
| **Fixture** | match preview + key players + (post-match) fixture stats + lineups |
| **Home** | fixtures-first + browse entry points |

---

## 5. Navigation graph (what makes it a site)

Every entity links to its neighbours — the "always one click to the related thing" feel.

| From | Links to |
|---|---|
| Home (upcoming) | → Fixture |
| Fixture | → each Team · → Players (lineups / leaderboards) · → Competition |
| Team | → Competition (its table) · → Players (squad) · → its Fixtures · → Coach |
| Player | → current Team · → Competition · → his Matches |
| Competition | → Teams (directory) · → Fixtures · → Players (scorers) |
| Coach | → current Team |

This closed graph covers upcoming matches → team stats → clubs → players → their upcoming matches → …

---

## 6. Flagship reads (the differentiators)

vs-benchmark / percentile is **table stakes** (kicker does bars-vs-average, fbref does
percentile-vs-peers) — necessary **context**, the **engine**, not the headline. The flagship is a
small set of *smart reads* the raw-number sites don't synthesise.

1. **Deserved-vs-actual** *(v1)* — underlying play (chance dominance: shot share + danger-zone + shots
   on target + finishing — our honest stand-in for xG) **vs** actual results (points captured + rank),
   with the gap. *"Creating like a top-2 side but sitting 7th — likely to climb."* Built for teams
   (`mart_team_profile.performance_vs_results_gap`); player analog (output vs underlying) is v1.x.
2. **Vs-own-history (year-over-year)** *(v1)* — the entity vs itself over time, **aligned by matchday**.
   *"22 points through MD10 vs 18 last year, shot share up 4 pts."* Built for teams
   (`int_team_profile__yoy`, domestic leagues); player version is a backfill-enabled gap.
3. **Opponent & schedule context** *(v1.x, the hardest)* — weight performance by opposition quality
   (via the benchmark engine). Backward: *"the unbeaten run came against the bottom half."* Forward:
   *"4 of the next 5 are top-six"* (fixture difficulty). This is the long-named "opponent-adjusted
   form" — football-analytics owns the definition; ships after the simpler two.
4. **Contribution-share** *(bonus)* — a player's share of the team's output (*"involved in 45% of
   Bayern's goals"*). Cheap, narrative, bridges team↔player pages.

The triad is a clean axis set: **vs your own play** · **vs your own past** · **vs your opponents**.
"A few signature things done well," powered by the benchmark + backfill infrastructure.

---

## 7. New marts — build status (each its own PR)

| New mart | Powers | Status (2026-07-02) |
|---|---|---|
| `mart_{team,player}_competition_benchmarks` | Vs-benchmark block + the flagship reads' league context | **player built + wired** (#627; screen 12 spec'd #625); **team built, not wired** (rank-based screen unspec'd) |
| `mart_leaderboards` (generalised `mart_top_scorers`) | Leaderboards block + key players + top performers | **built + wired** ✓ |
| `mart_roster` | Squad block | **built** (#503) + **wired** (#619, per-season `squad[]` on the team payload); screen 11 spec'd (#617) |
| `mart_player_career` (+ a team-history equivalent) | Career & History tabs | **built + wired** (#634; screen 13 spec'd #632); still needs backfill |
| `dim_coach` (+ Coach block/entity) | Coach block & page | **not built** (coaches ingest) |

The percentile **scope** (competition-wide vs position-aware, the fbref way) is a v1.x build-time
decision with football-analytics — reserved, not settled here.

---

## 8. Backfill (history depth) policy

History is a per-competition number (`history_seasons` in the registry). Budget is not the binding
constraint (a top-league decade ≈ ~12k calls; the daily API budget has spare headroom) — **value and
data quality** are. Tiered, with a quality floor:

| Competition type | Depth |
|---|---|
| Top domestic leagues (BL1, PL, PD, SA, L1…) | 10 seasons |
| 2nd-tier / smaller leagues (BL2, ED, VL, MLS…) | 5 seasons |
| Continental club (UCL…) | 10 seasons |
| World / continental championships (WC, EURO, AFCON…) | last 4 editions |
| Qualifiers | current + previous cycle |
| Domestic cups | 5 seasons |

- **Quality floor:** stop backfilling a competition once a season returns empty player-stats — don't
  ingest empty seasons (wasted budget, thin pages). Record the *achieved* depth.
- **Phased rollout:** start with the featured competitions, measure real call cost vs budget, extend.

> Applying these depths to `docs/competition_registry.yml` (`history_seasons`) and *running* the
> backfill is a **separate** registry change + cost-gated ingest task — not part of this doc.

---

## 9. Build sequence (dependency-ordered)

1. **#480** — one canonical per-club player-season model (+ confirm the season-record↔rollup
   unification, the team-side analog). The foundation; nothing clean builds on the divergent rollups.
2. **Backfill** — set per-competition depth (§8), run it. Lights up History / Career, makes
   season-over-season real everywhere, deepens benchmarks.
3. **`mart_leaderboards` + `mart_roster`** — cheap, high navigability/SEO, no governance.
4. **`mart_competition_benchmarks`** — the engine for the flagship reads (governance for percentile).
5. **Coaches ingest + `dim_coach`**, **`mart_player_career`** / team history (on the backfill).

---

## 10. Out of scope / honest limits

- **No xG** — the deserved-vs-actual flagship uses our chance-quality metrics, never a faked xG.
- **No News, no Transfers tab** — no news source; no transfers UI surface.
- **Career/History** depends on the backfill; thin until it runs.
- **Coach / Stadium** blocks only where the provider data is clean.
- **Naming consistency** (suffix `__team`/`__player` vs prefix `team_`/`player_`; `mart_team_fixtures`
  vs `mart_player_match_log`) is a known inconsistency — a separate cleanup pass, noted not fixed here.
