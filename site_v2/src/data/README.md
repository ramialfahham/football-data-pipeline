# site_v2/src/data — committed build inputs (temporary)

Static JSON the Astro build reads at build time. In the finished v2 site these come from the
per-entity export (`scripts/export_site_data.py`) wired as the build data source (#365 deploy);
until then a single real sample is committed here so the build (and `ci-site-v2`, which has no
BigQuery) is self-contained.

- `fixtures/1492306.json` — ONE real exported fixture (BSA · Palmeiras vs Atlético-MG, MD20,
  kickoff 2026-07-26), produced verbatim by `python scripts/export_site_data.py --entities fixtures`.
  Ground truth for the fixture-payload schema (`shape_fixture_payload`). Replace with the wired
  export at #365. (BL1 was the first pick but is off-season — no live W1 form right now — so a
  fully-populated in-season fixture was chosen to exercise every component.)
- `teams/42.json` — ONE real exported team (Arsenal, PL 2025-26, rank 1), from
  `python scripts/export_site_data.py --entities teams --sample 200`. Ground truth for the
  team-payload schema (`shape_team_payload`). The full multi-season payload (incl. squad +
  benchmarks for the Squad/Stats tabs) is present; the Overview renders only the default season.
- `competitions.json` — `league_code → { slug, name }` from `docs/competition_registry.yml` (the
  registry's authored slug + display name; the frontend never generates slugs). Only the featured
  competitions are listed for this increment; at scale this is the export's `nav.json` / `slug_map.json`.
