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
That trap sprang once inside this branch's own life. The allowlist in `.gitignore:249-270` is the
authoritative list of what is tracked.

Tracked today, 17 files:

- `fixtures/*.json` — **13** real exported fixtures, produced verbatim by
  `python scripts/export_site_data.py --entities fixtures`. `1492306` (BSA · Palmeiras vs
  Atlético-MG, MD20, kickoff 2026-07-26) is the ground truth for the fixture-payload schema
  (`shape_fixture_payload`): BL1 was the first pick but is off-season, with no live W1 form, so a
  fully-populated in-season fixture was chosen to exercise every component. The other 12 are the
  matches `landing.json` links to.
- `teams/*.json` — **1** real exported team, `33` (Manchester United), the team-page sample. Six
  more were tracked until 2026-08-08; they existed only because the landing's trending rows linked
  to them, and that block was cut. No page on the site links to a team page today.
- `competitions.json` — `league_code → { name, slug }` for all **45** registry entries (the
  registry's authored slug; the frontend never generates slugs). At scale this is the export's
  `nav.json` / `slug_map.json`.
- `landing.json` — the home page's payload, produced verbatim by
  `python scripts/export_site_data.py --entities landing` (#367), then reduced by hand to the keys
  the writer still emits. Real export output, not a fixture: 12 upcoming matches across 4
  competitions and the full registry browse axes, as of 2026-08-03. The `trending` key it carried on
  that date is gone with the block (2026-08-08), as is the `stats` key removed the same day.

## Refreshing the sample

⚠ **Refresh as a set.** `landing.json` is a snapshot of whatever matches happen to be next, so
regenerating it changes WHICH fixture and team ids belong here. Regenerate `landing.json`, then
update the `.gitignore` allowlist and the committed files to match it, in the same commit.

⚠ **Nothing enforces that today.** The allowlist is hand-maintained and the only thing that catches
a mismatch is `audit-seo.mjs` in CI, after the fact. The real fix is for CI to build from a live
export instead of stored samples, which is infrastructure work outside #367.
