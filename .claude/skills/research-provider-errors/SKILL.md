---
name: research-provider-errors
description: |
  Research the rows of mart_competition_research_list from allowed sites and report proposed
  correction-seed rows: withheld results, goals, scorers, assisters, cards and line-up goals.
  Each match gets two separate reads. Reads that disagree go no further. Never reads a stopped
  site. Use it for the morning research of the list. It edits no seed and opens no merge request.
  Do NOT use it for line-up research.
---

# research-provider-errors

The nightly withholds a value that fails a check of the provider's data. The value stays blank
until sourced research stands in a correction seed. `mart_competition_research_list` lists every
such value. This skill researches the list rows and reports what to put in the seeds.

## What this skill never does

- It never edits a seed file, commits, pushes or opens a merge request.
- It never reads a site that is not in the site table below.
- It never reads a stopped site, by a fetch or by the browser.
- It never reads a page that refused a plain fetch with a 403, by another route.
- It never signs in, accepts a cookie banner, or follows a link off the match page.
- It never guesses a value, never answers from memory, and never takes a value from an aggregator.
- It never writes a name, a team or a player id it did not read on an allowed page or in the provider's data.

## 1. Read the list

1. Read the table's last build time with `bq show`, and give it in the report.
2. The list is cumulative. A night with no new data does not rebuild it, and an older list still
   holds every open row.
3. Dry-run the query below, then read the list. The read is about 1 MB.

```sql
select item_key, check_name, seed, correction, fixture_sk, team_sk, league_code,
       season_api_year, fixture_date, research_tier
from `football-data-pipeline-gcp.marts.mart_competition_research_list`
where is_current_season
order by research_tier nulls last, fixture_date
```

- Research only the current season. A row with no `research_tier` is not researched.
- Report every row you do not research, with its reason, in the final report.
- A `correction_no_longer_needed` row needs no research. Go to section 8.

## 2. Choose the matches

1. Take the matches in list order: tier 1, then 2, then 3. One match can hold several rows.
2. Research at most the number of matches the task's prompt names.
3. Leave a match open when its competition is not in the site table. Say so in the report.
4. Group a match's rows by seed. The seed row set of a match replaces the provider's.
5. A card match needs every card of the match, not only the disputed card.

## 3. Find the official page

1. Name the competition's site from the site table, by `league_code`.
2. Open that site's own fixtures page for the date, or search with the site's host in the query.
3. Open only a page whose host is in the site table. Treat any other host as not allowed.
4. Check the page shows this match: both teams, the competition and the date when it prints one.
5. A page that does not show the match is not readable.

A result, goal or award can also come from two match reports. Both must be on hosts in the
news-outlet part of the site table. Each report must be on a different host.
Cards come only from the competition's official record.

## 4. Read each page twice

1. Spawn two readers for the match. Neither sees the other's answer.
2. Official record: both readers read the same page. Match reports: each reads a different host.
3. A page that holds its data in the HTML: use the plain fetch reader (`web-fetch`).
4. A page that renders by script: use the desktop app's built-in browser, one tab per reader.
5. The browser reader opens its own tab with `tabs_create` and closes it when it finishes.
6. Run at most four browser readers at once. The pane has a tab cap, and a reader that cannot open a tab reads nothing.
7. On the first visit, refuse non-essential cookies. Never accept them.
8. A page that shows no match data after a reload and a wait is not readable.
9. Try such a page once more later in the same run. Otherwise report it as not readable.
10. Each reader returns JSON only. It sets `page_ok` to false, with a reason, when the page does not show the match or the asked values.

What a reader returns:

- Cards: player as the page prints him, team as the page shows it, minute, added minute and card.
  The card is `yellow`, `second_yellow` or `red`. A coach's or official's card is not a card.
- Result: full-time goals of each side, and whether extra time was played with its score.
  Also the shoot-out score, whether the result was awarded, the awarded score and the score on the pitch.
- Goals: scorer as printed, team the goal counts for, minute, added minute, penalty, own goal.

## 5. Compare, then stop or go on

Stop the match, and report why, when any of these holds:

- either read could not read the page, or the page does not show the match;
- the two reads differ in any value;
- the page does not print a value the seed row needs, such as a minute or the score on the pitch;
- the page shows a card with no minute, or shows a card only as an icon with no text;
- a carded or scoring player is not listed as playing on the page, or on the provider's sheet.

Two reads that agree can both be wrong. Section 6 is the check for that.

## 6. Take team and player ids from the provider

1. Read the match's two team sheets from `base_apif__lineups` on
   `football-data-pipeline-gcp.dbt_analytics`, by `fixture_id`.
2. Take `team_id`, `player_id` and `player_name`.
3. Match each name from the pages to one player on those two sheets.
4. Where the sheets do not hold a name, use the club's squad list of that season.
5. That list is `base_apif__player_team_season`, by `team_id` and `season_year`.
6. Take `team_id` and `player_id` from the provider's row. Never take a team from where a page
   prints a card.
7. Stop the match when a name matches no player, or matches two players of the same match.
8. Check each team against the match's two teams in `base_apif__fixtures_next`.

## 7. Write the proposed rows

Column formats are in `dbt_project/seeds/schema.yml`. Conventions that matter:

- `fixture_card_corrections`: one row per card, in minute order, `card_order` from 1.
- A second yellow is two rows at the same minute: `Yellow Card` and `Red Card`.
- A straight red is one row.
- `fixture_result_corrections`: one row per match. An award needs its kind.
- A played or abandoned award needs the score on the pitch.
- `fixture_goal_corrections`: one row per goal, `goal_order` from 1. A match with no goal has one
  row at 0.
- `source_kind` is `official` for one official page, `match_reports` for two pages on two hosts.
- `source` is the https URLs read, separated by a space.
- `note` names the match, the competition and the date, and says what was checked.

## 8. Report

Do not edit a seed. Put in the final report, one block per seed:

- the proposed rows, as CSV lines;
- each match stopped, with its reason and the two reads' values where they differ;
- each row not researched, with its reason;
- each `correction_no_longer_needed` row, with its seed and key;
- the tokens used per read and per match, and the sites that failed.

## NOT DECIDED — stubs that stop and report

These steps wait for the CPO. When a row needs one, stop at it, list the row in the report under
its stub, and go on with the next row.

- Landing a fix. How a proposed seed row reaches the seed is not decided.
- Do not edit a seed, commit, or open a merge request.
- Removing a correction. A `correction_no_longer_needed` row is removed from its seed by the same
  step as above. Report the row and stop.
- A standings or points row. What a standings mismatch withholds is not decided. Report the row
  and stop.

## Site table

A site is read only when it is in this table. A change to this table is a change to this skill.
Each site's terms and `robots.txt` were read once. None bans automated reading, and none
disallows the match page.

| Site | Competitions (`league_code`) | How to read |
|---|---|---|
| `www.premierleague.com` | PL | browser |
| `ligue1.com` | L1 | browser |
| `www.ligaportugal.pt` | LP | browser |
| `www.ligaprofesional.ar` | APD | browser |
| `www.kleague.com` | KL1 | browser |
| `data.j-league.or.jp` | J1 | fetch |
| `www.tff.org` | TSL | fetch |
| `www.dfb.de` | DFBP | fetch |
| `www.cafonline.com` | CAFCL | fetch |
| `www.concacaf.com` | CNL, WCQCA | fetch |

News outlets serve a result or goals that need two reports on two hosts. Read them by fetch.

- Germany: `www.sport1.de`, `www.zdfheute.de`, `www.spox.com`, `t-online.de`.
- Britain and the US: `www.skysports.com`, `www.vavel.com`, `www.aljazeera.com`, `www.si.com`.
- Elsewhere: `www.koreajoongangdaily.com`, `www.koreatimes.co.kr`, `sport.sky.it`, `bold.dk`, `www.rtp.pt`.

Not read, and the reason:

- Stopped sites: FIFA, UEFA, MLS, Bundesliga, Serie A, Saudi Pro League, Eredivisie, ESPN and
  `resultados.rfef.es`. Their terms ban automated reading, or their `robots.txt` closes the host.
- Refused the plain fetch: `www.fff.fr` and `www.conmebol.com`, with `gol.conmebol.com`.
- Left out until the CPO rules: Ekstraklasa and Veikkausliiga.
- Aggregators: Wikipedia, Transfermarkt, Sofascore, Flashscore, FotMob, Soccerway, BeSoccer, RSSSF,
  worldfootball and FBref never count as a source.

A competition whose record is on a site outside this table is not researched. The CPO decides
whether it is added.
