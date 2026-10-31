# site_v2/src/data — committed build inputs (temporary)

Static JSON the Astro build reads at build time. The real sample committed here is the input of
the MR and main builds (`build:site-v2`, which has no BigQuery). The deploy never builds from it:
`deploy:site-v2` removes it and copies in the full export (`scripts/export_site_data.py`) that
`deploy:export` writes.

**The committed sample is a SET, not a pile of examples.** `landing.json` links to specific match
pages, and those pages exist only if the entity payload behind each one is committed.
`audit-seo.mjs` fails the build on an internal link that resolves to no emitted page, so a missing
payload turns CI red. A local build does not catch it: a full export leaves hundreds of untracked
files in these directories, so every link resolves on disk while only the tracked ones reach CI.
That trap sprang once inside this branch's own life. The allowlist in `.gitignore` — the
`site_v2/src/data/**` block — is the authoritative list of what is tracked. (It is cited by block
rather than by line range: the range written here was `249-270`, and it had already rotted.)

Count what is tracked with `git ls-files site_v2/src/data`. Today: the six root files below, the
Bundesliga competition payload, 50 Matches page days, 548 fixture payloads and 34 team payloads.

- `competition_index.json` — the competitions index page's payload (#62 step 5), produced
  verbatim by `python scripts/export_site_data.py --entities competition_index`. All **48**
  browsable rows from `mart_competition_index` — small enough to commit whole rather than sample.
  Refreshed the same way as the others below: rerun the export, replace the file, in one commit.
- `teams_index.json` — the Teams page's payload, from
  `python scripts/export_site_data.py --entities teams_index`, its rows unchanged but cut to fit
  the repo's 1,024 KB file limit: every national team, every club in a covered league and every
  ranked club (`top_club_rank`). The top lists are the full export's; the country groups hold
  fewer clubs. A row links only to a team with a payload in `teams/`.
- `fixtures/*.json` — real exported fixtures, produced verbatim by
  `python scripts/export_site_data.py --entities fixtures`. The **537** every unplayed row of a
  committed page links to: each day of the Matches page, the Bundesliga sample's Matchdays tab and
  Home's Next matches, because the build refuses a link to a page it did not emit. Refresh them
  together with `matches/*.json`, `competitions/BL1/2026.json` and `landing.json`, from one
  export, and regenerate the `.gitignore` patterns. The **11** played fixtures are the played
  match page's samples and are not part of that refresh.
  ⛔ **A PAST FIXTURE CAN NEVER BE RE-EXPORTED, so this set is REPLACED and never appended to**.
  `fetch_fixture_payloads` selects `status_short in ('NS', 'TBD') and fixture_date >=
  current_date()`. Once a match kicks off, its pre-match form rows leave
  `mart_team_window_metrics` and `mart_team_season_record` altogether. A stale id left in the
  allowlist therefore
  pins a payload that no rerun can ever update — which is exactly how the previous set came to
  serve column names that had been renamed two merge requests earlier.
- `matches/*.json` — the Matches page's days (#160), one file per day in reach, produced verbatim
  by `python scripts/export_site_data.py --entities matches` from `mart_match_days`: 50 days, 31
  competitions. The file flagged `is_opening_day` is the page at `/{locale}/{matches word}/`; every
  other day has its own dated page. Days drop off as rounds are played, so the whole directory is
  replaced on a refresh, never appended to.
- `teams/*.json` — **34** real exported teams: `33` (Manchester United), the team-page sample; the
  teams the Home Top teams boards link to; the clubs of the Bundesliga sample's table. These 34 can
  be refreshed alone, from `fetch_team_payloads` written by `write_entity`. Every slug must stay the
  same, because the Home and Bundesliga pages link to them.
- `competitions/BL1/2026.json` — the one competition payload, the Bundesliga 2026/27 season, all
  three tabs of the competition page in one file (`standings`, `deserved`, `summary`, `fixtures`,
  `team_boards`, `player_boards`), produced verbatim by
  `python scripts/export_site_data.py --entities competitions`, with five matchdays played. Every
  unplayed row of its Matchdays tab has its match payload in the `fixtures/` allowlist above.
- `competitions.json` — `league_code → { name, slug }` for all **48** registry entries (the
  registry's authored slug; the frontend never generates slugs).
- `metric_groups.json` — the metric groups (key and order, one row per group) as the catalogue
  defines them, produced verbatim by `python scripts/export_site_data.py --entities metric_groups`
  from `metric_catalogue.csv` (no BigQuery). `metricRows.ts` reads the groups from it; the names
  per language are copy in `strings.ts`. Pinned to the seed by `tests/test_metric_groups.py`, so a
  seed change means regenerating this file in the same commit.
- `metric_rows.json` — the rows of the match page's Form comparison. Each is a team metric
  `mart_team_window_metrics` serves outside Results, in the catalogue's `metric_order`: its key, name key,
  group, order, direction, format and per-match
  flag. Produced verbatim by `python scripts/export_site_data.py --entities metric_rows` from
  `metric_catalogue.csv` (no BigQuery). Pinned to the seed by `tests/test_metric_rows.py`.
- `landing.json` — the home page's payload, produced verbatim by
  `python scripts/export_site_data.py --entities landing` (#367). ⚠ It is NOT hand-reduced, and this
  line used to say it was — `shape_landing_payload` returns only the keys the built blocks need, so
  there is nothing left to trim, and the instruction three paragraphs down is never hand-edit a
  payload. Real export output of one run: `type`, `upcoming` (**285** matches across **31**
  competitions, each competition's next matchday), `top_players` and `top_teams`.
  Every Next matches row is a match of a committed Matches page day, so its payload is in the
  `fixtures/` allowlist. Every team the Top teams boards link to is in the `teams/` allowlist. The player
  pages the Top players boards link to are generated FROM this file
  (`pages/[lang]/players/[player].astro`).

## Refreshing the sample

⚠ **Refresh as a set.** `landing.json` is a snapshot of whatever matches happen to be next, so
regenerating it changes WHICH fixture and team ids belong here. Regenerate `landing.json`, then
update the `.gitignore` allowlist and the committed files to match it, in the same commit.

⛔ **AND THERE IS NO OTHER KIND OF FIXTURE REFRESH — this is the trap that cost a merge request**.
Rerunning the export does NOT update the committed payloads in place. `fetch_fixture_payloads`
emits upcoming fixtures only. A kicked-off fixture's pre-match form rows are gone from
`mart_team_window_metrics` and `mart_team_season_record`. So a rerun writes thousands of new
payloads and silently leaves every committed one
exactly as it was. On 2026-08-28 that is precisely what happened: the export exited 0, reported
5,066 fixture payloads written, and not one of the 17 tracked files changed — they were still
serving two column names renamed two merge requests earlier. Roll the whole set forward, or the
sample does not move.

The full recipe, in order:

1. `PYTHONPATH=. python scripts/export_site_data.py --entities landing,teams,fixtures,matches,competitions --out <a scratch folder>`
   from the repo root, one run. Never hand-edit a payload.
2. Copy in `landing.json`, every `matches/*.json` day, `competitions/BL1/2026.json`, the fixture
   payload of every unplayed row of those files, and the tracked teams.
3. Rewrite the `.gitignore` fixture allowlist to exactly those fixture ids. **Replace** the old
   entries, never append: a stale id pins a payload no rerun can ever update.
4. `git rm` the payloads that left the set.
5. Drop the ignored bulk before building (`git clean -fX site_v2/src/data`): a full export leaves
   thousands of payloads, `astro build` OOMs at that scale, and a local build resolves links that
   CI — which sees only the tracked set — cannot.

⚠ **Nothing enforces that today.** The allowlist is hand-maintained and the only thing that catches
a mismatch is `audit-seo.mjs` in CI, after the fact.
