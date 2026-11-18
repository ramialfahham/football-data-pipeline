# 02 — Team page

> The field contract of the Team page. The design is approved on
> [its GitLab issue](https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/134), the authority for
> what the page shows. Metric names, groups, order, direction and format come from the catalogue
> through `metric_rows.json` and [`metrics_display.md`](metrics_display.md).

## 1. Purpose

A team's season in one place: where it stands in each competition, how it plays against its league
and against last season. The stop-scrolling moment is Deserved points: the points its play
usually earns against the points it has.

## 2. URL

```
/{locale}/{teams word}/{team-slug}/
```

- `slug` from the payload, derived in the warehouse.
- Breadcrumb: Home › Teams › {team}. "Teams" links to the Teams page once the build makes one.
- One page per team and locale. The page shows one season: the featured season.

## 3. Data sources

`data/teams/{team_id}.json`:

- top level: `team_id`, `slug`, `name`, `country`, `crest`, `founded_year`, `venue`,
  `recent_matches` (`mart_team_momentum_window`), `schedule` (`mart_team_fixtures`), `seasons[]`;
- a club's `this_season` and `last_season` (`mart_team_page_window_metrics`), over all its
  competitions of the season; a national team has neither;
- `seasons[]`: one row per competition-season (`mart_team_profile`), with `benchmarks`
  (`mart_team_competition_benchmarks`) and `squad` (`mart_roster` joined to `mart_player_career`);
- the featured season only (`is_featured_season`): `competitions` (`mart_team_competitions`) and
  `deserved_scatter`;
- `league_strip`: the featured season, and each competition of its year benchmarked over its
  table rounds (`round_stage_kind` table).

A club's page is the layout below. A national team's page keeps the earlier blocks. It has no
This season, and Recent matches stands before Next matches. Its Performance tab keeps the tab's
explainer, Standing, and Compared with the league over its featured competition.

## 4. Layout

```
Home › Teams › {team}
[crest] {team}
        {country} · {venue}, {city} · Founded {year} · Season {season}
THIS SEASON         explainer listing the season's competitions
                    Matches · Wins · Goals · Goals against · Yellow cards · Red cards
[ Overview | Matches | Performance ]

OVERVIEW
  COMPETITIONS      one row per competition: name · note · standing or outcome
  NEXT MATCHES      one match per competition, the soonest tagged Next
  RECENT MATCHES    five result rows, the Player page's row
  HIGHS AND LOWS    Biggest win · Biggest loss · Longest unbeaten run · Longest winless run
  SQUAD             by position, two columns where they fit

MATCHES
  [ Filter bar: All | {competition} … ]
  NEXT MATCHES      every scheduled match, grouped by competition
  RESULTS           every result of the season, newest first, the Player page's row

PERFORMANCE
  DESERVED POINTS   "{competition} {season} only." · explainer · table of four values · scatter plot
  COMPARED WITH OTHER TEAMS       [ {league} | {competition} … ] · explainer · switch · strip plot per metric, median ticked
  COMPARED WITH LAST SEASON       explainer · switch · This season | Last season | Trend
```

The page has the site's one width, 960px, and a single column at every width.

## 5. Module bindings

### Header

| Element | JSON key |
|---|---|
| Name, crest, country | `name`, `crest`, `country` |
| Venue, founded | `venue.name`, `venue.city`, `founded_year` |
| Season | the featured season's `season_label` (`dim_competition_season`) |

### Overview

| Block | JSON keys | Notes |
|---|---|---|
| This season | `this_season`: `matches`, `wins`, `cards` (`goals`, `goals_against`, `cards_yellow`, `cards_red`), `league_codes` | six cards, a 0 included; the explainer lists the competitions in the served order |
| Competitions | `competitions[]`: `league_code`, `competition_type`, `standing_rank`, `latest_played_round_*`, `reached_round_*`, `reached_round_stage_kind`, `cup_status` | one line per competition. A table row shows the standing. A cup row shows the round reached and Through, Knocked out or Winners. An international table's note is "League phase". The row links to the competition's page |
| Next matches | `schedule.upcoming[]` with `upcoming_rank` = 1 | the competition group head and the match row; the first row carries the Next tag |
| Recent matches | `recent_matches[]` | the Player page's result row; it links to the match page when the build makes one |
| Highs and lows | `biggest_win_*`, `heaviest_defeat_*`, `longest_unbeaten_run`, `longest_winless_run` | fact rows; a match reads its score, then "vs" or "at" the opponent, the competition and the date |
| Squad | `squad[]`: `name`, `photo`, `position`, `nationality`, `birth_date`, `appearances`, `minutes_per_appearance` | the player row without goals or assists; the second line reads country · age · appearances · minutes per appearance |

### Matches

| Block | JSON keys | Notes |
|---|---|---|
| Filter bar | the competitions of `schedule` | the shared Filter bar, one choice per competition with a match |
| Next matches | `schedule.upcoming[]` | grouped by competition in the order of each group's first match; date headings; the match row |
| Results | `schedule.results[]` | the result row, newest first |

### Performance

| Block | JSON keys | Notes |
|---|---|---|
| Deserved points | `played`, `shots_on_goal_difference_per_match`, `points`, `deserved_points`, `deserved_points_gap`, `deserved_scatter[]` | the explainer opens with "{competition} {season} only."; the table's head reads "{competition}, after {n} matches"; the line joins the deserved points of the two teams at the ends of the axis |
| Compared with other teams | `benchmarks[]`: `metric_value`, `rank`, `team_count`, `league_median`; `league_strip[]`; `this_season.comparison_keys` | a choice of the league and each competition carrying a strip, shown from two; one strip per comparison metric with a value, the median ticked; the rank is the warehouse's, by the metric's direction |
| Compared with last season | `last_season`: `matches`, `matches_prev`, `metrics[]`; `this_season.comparison_keys` | this season so far against the whole of last season, per match, from the first match; the trend compares the shown values by the metric's direction and is empty when either side is |

Both comparisons show the key metrics (`is_key_metric`) until the switch "Show all metrics" is on.

## 6. States

| State | Render |
|---|---|
| A value is empty | "–" |
| A block has nothing to show | the block is absent |
| A metric row has no value | the row is absent |
| No schedule | the Matches tab is absent |
| No standing and no metric | the Performance tab is absent |
| Before the team's first match of a season | the page shows the featured season, the season just finished; both Next matches blocks show the new season |
| No match last season | Compared with last season is absent |

## 7. Interactions

- The tabs and the switches are radios and checkboxes; no script.
- The Filter bar's buttons and dropdowns are two forms of one choice (the shared Filter bar).
- The scatter plot's marks keep their pixel size (a small script); every dot and strip mark names
  its team and value on hover.

## 8. SEO

- `schema.org/SportsTeam`: name, logo, founding date, location, `memberOf` the featured
  competition.
- Title and description from `seoTeamTitle` and `seoTeamDesc`.
- `BreadcrumbList`; canonical per locale with hreflang.

## 9. Component census

- breadcrumb, entity header, tab bar, tab explainer;
- competition row, result row, competition group head, match row, tag;
- fact row, player row, squad grid, Filter bar;
- table, metric group heading, metric switch, strip plot, scatter plot, trend.

## 10. Gaps

None. Every value on the page is served.
