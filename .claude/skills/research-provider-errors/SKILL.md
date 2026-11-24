---
name: research-provider-errors
description: |
  Research the rows of mart_competition_research_list from allowed sites and report proposed
  correction-seed rows: withheld results, goals, scorers, assisters, cards and line-up goals.
  Each match gets two separate reads. Reads that disagree go no further. Never reads a stopped
  site. Use it for the morning research of the list. It lands the rows as a seed-only
  research-fix merge request and merges it once its review and pipeline pass.
  Do NOT use it for line-up research.
---

# research-provider-errors

The nightly withholds a value that fails a check of the provider's data. The value stays blank
until sourced research stands in a correction seed. `mart_competition_research_list` lists every
such value. This skill researches the list rows and lands what it proves in the seeds, as a
research-fix merge request (section 8).

## What this skill never does

- It never edits a file other than the rows of `fixture_card_corrections`,
  `fixture_result_corrections` and `fixture_goal_corrections`, and its own task folder.
- It never commits on `main`, never amends, and never merges a merge request that is not its own
  research-fix MR.
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
- A `correction_no_longer_needed` row needs no research. Go to section 9.
- A `misfiled_team_withheld` row is not researched. Its seed, `fixture_team_id_overrides`, is not one this skill edits. Report the row.
- A `lineup_duplicate_withheld` row is not researched. It has no seed (`none`): a newer provider fetch removes it. Report the row.
- A `player_team_withheld` row is not researched. Its seed, `fixture_lineup_corrections`, holds line-up research, which this skill does not do. Report the row.
- A `null_key_line_withheld` row is not researched. It has no seed (`none`): a provider fetch that carries the team id removes it. Report the row.
- A `team_season_off_standings` row is not researched. It has no seed (`none`): the team-season's results disagree with the provider's standings. Report the row.

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

## 8. Land the rows

Land only rows that passed sections 3 to 7. With none, open nothing and go to section 9. Land all rows of one batch in one merge request.

1. List open merge requests with `glab mr list`. A match already in an open research-fix MR stays with that MR.
2. Branch from fresh main: `git fetch gitlab main`, then `git checkout -b research-fix/<YYYY-MM-DD> gitlab/main`.
3. Run `git branch --unset-upstream`. Never commit on `main`.
4. A second run on the same day takes `research-fix/<YYYY-MM-DD>-2`, then `-3`. The task folder takes the same suffix.
5. Never reuse, edit or continue the branch or the task folder of an earlier run, merged or not.
6. Write the contract from `.claude/task/TEMPLATE.md` to `.claude/task/262-research-fix-<YYYY-MM-DD>/contract.md` before any edit.
7. The contract's `scope_paths` are that folder and the seeds it changes. `depends_on` and `shared_files` read `none` with a reason.
8. Edit the seeds. Add rows, or change a row of a match researched in this run.
9. Never remove a row, change a header, or touch another file.
10. Every row has `source_kind`, `source` and `note`, as in section 7.
11. Every `source` URL is on a host of the site table below.
12. Run the review cycle of `docs/working_agreement.md` section 2 on the staged diff. Use the reviewers that `.claude/review_routing.json` routes for the changed paths.
13. Write `review.md` with the hash that `python .claude/hooks/git_discipline.py --staged-hash` prints.
14. When the commit gate's cap of review cycles is reached, stop and merge nothing. Put the open findings in the report.
15. Commit with `git commit -F <message file>`, as the only command of the call. The post-commit hook pushes the branch and opens the merge request.
16. Run `python scripts/check_research_fix_mr.py --base gitlab/main`. Fix a failure in a new commit and a new review cycle, never by an amend.
17. Wait for the merge request's pipeline to finish. If it is red or cancelled, stop and merge nothing. Put the failing job in the report.
18. Run `python scripts/merge_ready.py <MR number>`. If it is not ready, stop and merge nothing. Put its output in the report.
19. Merge with `glab mr merge <MR number> --yes --sha <head commit of the MR, 40 hex characters>`, from this checkout, at that commit with a clean tree.
20. The merge hook allows only this form. The pipeline must be green, `merge_ready.py` must say ready, and the diff must touch only paths of `agent_merge_paths`.
21. If the hook blocks the merge, stop and report its reason. Never try another form of merge.
22. After the merge, watch the pipeline of `main`. If it is red, revert the merge in a new MR and report it.

## 9. Report

Put in the final report, one block per seed:

- the rows landed, as CSV lines, with the merge request's link and whether it merged;
- each match stopped, with its reason and the two reads' values where they differ;
- each row not researched, with its reason;
- each `correction_no_longer_needed` row, with its seed and key;
- the tokens used per read and per match, and the sites that failed.

## NOT DECIDED — stubs that stop and report

These steps wait for the CPO. When a row needs one, stop at it, list the row in the report under
its stub, and go on with the next row.

- Removing a correction. A research-fix MR never removes a row. A `correction_no_longer_needed`
  row is reported, and the skill stops at it.
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
