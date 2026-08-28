# site_v2/src/data — committed build inputs (temporary)

Static JSON the Astro build reads at build time. In the finished v2 site these come from the
per-entity export (`scripts/export_site_data.py`) wired as the build data source (#365 deploy);
until then a real sample is committed here so the build (and `ci-site-v2`, which has no BigQuery)
is self-contained.

**The committed sample is a SET, not a pile of examples.** `landing.json` links to specific match
pages, and those pages exist only if the entity payload behind each one is committed.
`audit-seo.mjs` fails the build on an internal link that resolves to no emitted page, so a missing
payload turns CI red. A local build does not catch it: a full export leaves hundreds of untracked
files in these directories, so every link resolves on disk while only the tracked ones reach CI.
That trap sprang once inside this branch's own life. The allowlist in `.gitignore` — the
`site_v2/src/data/**` block — is the authoritative list of what is tracked. (It is cited by block
rather than by line range: the range written here was `249-270`, and it had already rotted.)

Tracked today, 24 files:

- `competition_index.json` — the competitions index page's payload (#62 step 5), produced
  verbatim by `python scripts/export_site_data.py --entities competition_index`. All **48**
  browsable rows from `mart_competition_index` — small enough to commit whole rather than sample.
  Refreshed the same way as the others below: rerun the export, replace the file, in one commit.
- `fixtures/*.json` — **19** real exported fixtures, produced verbatim by
  `python scripts/export_site_data.py --entities fixtures`. They are exactly the matches
  `landing.json` links to: the **2026-08-28** matchday, 19 fixtures across 13 competitions.
  **17 of the 19 carry a fully-populated W1 form window** (29/29 non-null), so the sample still
  exercises every component; `1575140` (BL1) has a null W1 — pre-season, no form yet — which
  exercises the absent path deliberately rather than by accident.
  ⛔ **A PAST FIXTURE CAN NEVER BE RE-EXPORTED, so this set is REPLACED and never appended to.**
  `fetch_fixture_payloads` selects `status_short in ('NS', 'TBD') and fixture_date >=
  current_date()`, and once a match kicks off its pre-match form rows leave `mart_team_momentum`
  and `mart_team_season_record` altogether (queried on 2026-08-28 against the previous set: **0
  rows** in both marts for `1492306` and `1622620`). A stale id left in the allowlist therefore
  pins a payload that no rerun can ever update — which is exactly how the previous set came to
  serve column names that had been renamed two merge requests earlier.
- `teams/*.json` — **1** real exported team, `33` (Manchester United), the team-page sample. Six
  more were tracked until 2026-08-08; they existed only because the landing's trending rows linked
  to them, and that block was cut. No page on the site links to a team page today.
- `competitions.json` — `league_code → { name, slug }` for all **48** registry entries (the
  registry's authored slug; the frontend never generates slugs). At scale this is the export's
  `nav.json` / `slug_map.json`.
- `landing.json` — the home page's payload, produced verbatim by
  `python scripts/export_site_data.py --entities landing` (#367). ⚠ It is NOT hand-reduced, and this
  line used to say it was — `shape_landing_payload` returns `{"type", "upcoming"}` and nothing else,
  so there is nothing left to trim, and the instruction three paragraphs down is never hand-edit a
  payload. Real export output, not a fixture: **19** upcoming matches across **13**
  competitions, the 2026-08-28 matchday — the same 19 the `fixtures/` allowlist pins, which is what
  makes the set self-consistent.
  The `trending` key it carried earlier is gone with the block (2026-08-08), as is the `stats`
  key removed the same day, and the `browse` key ("the full registry browse axes") removed
  2026-08-19 with the Browse block. `landing.json` today carries `type`/`upcoming` only.

## Refreshing the sample

⚠ **Refresh as a set.** `landing.json` is a snapshot of whatever matches happen to be next, so
regenerating it changes WHICH fixture and team ids belong here. Regenerate `landing.json`, then
update the `.gitignore` allowlist and the committed files to match it, in the same commit.

⛔ **AND THERE IS NO OTHER KIND OF FIXTURE REFRESH — this is the trap that cost a merge request.**
The obvious move, rerunning the export and expecting the committed payloads to update in place,
CANNOT work: `fetch_fixture_payloads` emits upcoming fixtures only, and a kicked-off fixture's
pre-match form rows are gone from `mart_team_momentum` and `mart_team_season_record` (0 rows,
queried). So a rerun writes thousands of new payloads and silently leaves every committed one
exactly as it was. On 2026-08-28 that is precisely what happened: the export exited 0, reported
5,066 fixture payloads written, and not one of the 17 tracked files changed — they were still
serving two column names renamed two merge requests earlier. Roll the whole set forward, or the
sample does not move.

The full recipe, in order:

1. `PYTHONPATH=. python scripts/export_site_data.py --entities teams,fixtures --out site_v2/src/data`
   from the repo root — the `--entities` list is copied verbatim from `.gitlab-ci.yml`'s
   `deploy:export`, where a comment marks it load-bearing. Never hand-edit a payload.
2. `... --entities landing --out site_v2/src/data` to move the set's definition forward.
3. Rewrite the `.gitignore` fixture allowlist to exactly the ids the new `landing.json` links —
   **replacing** the old entries, never appending, since a stale id pins a payload no rerun can
   ever update.
4. `git rm` the payloads that left the set.
5. Drop the ignored bulk before building (`git clean -fX site_v2/src/data`): a full export leaves
   thousands of payloads, `astro build` OOMs at that scale, and a local build resolves links that
   CI — which sees only the tracked set — cannot.

⚠ **Nothing enforces that today.** The allowlist is hand-maintained and the only thing that catches
a mismatch is `audit-seo.mjs` in CI, after the fact. The real fix is for CI to build from a live
export instead of stored samples, which is infrastructure work outside #367.
