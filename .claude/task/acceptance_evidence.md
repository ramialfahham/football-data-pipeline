# Verification — the deploy exports every data set the pages read

Read from a scratch worktree of main (the year fix included) whose `site_v2/src/data` was emptied
with the job's own `find` command, then filled with exported files only: the teams and fixtures of
deploy job 17243256610 (16 Oct, selected by that export's manifest) and a local export of the six
added entities (17 Oct, 54s). The build ran with the deploy job's heap.

criteria_demonstrated:
  - 1 The jobs: `.gitlab-ci.yml` deploy:export runs `python scripts/export_site_data.py --entities teams,fixtures,competitions,competition_index,landing,matches,metric_groups,metric_rows --out site_v2/export_data`, its artifact; deploy:site-v2 runs `find site_v2/src/data -mindepth 1 ! -name README.md -delete` and `cp -R site_v2/export_data/. site_v2/src/data/` before `npm ci` and the build; both jobs' `rules:` are unchanged; `glab ci lint` reports the file valid.
  - 2 Full scale: astro builds 221,721 pages in 880s at `--max-old-space-size=8192` (peak node working set 2.27 GiB, dist 7.8 GiB). audit-seo lists 0 of the 54 dead links that came from the committed sample, and 551 violations, each named with its cause: 453 player pages sharing an h1 (444) or a title and description (9) with a player of the same short name; 9 from the two Nyasa Big Bullets team ids; 8 competition tab titles past the 660px cap; 3 dead links to an Eritrea team page that is not built; 78 dead links from the two exports a day apart (8 DFB-Pokal ties moved from 27 to 28 Oct, PSG–Rennes with home and away swapped, Braga–Gil Vicente, NS on 2026-10-19 in today's mart, so one export writes its page). check-built-pages did not run, because audit-seo failed first.
  - 3 README: site_v2/src/data/README.md opens "The real sample committed here is the input of the MR and main builds (`build:site-v2`, which has no BigQuery). The deploy never builds from it: `deploy:site-v2` removes it and copies in the full export (`scripts/export_site_data.py`) that `deploy:export` writes."
  - 4 MR pipeline: lint, tests and the sample build, read on the MR once it runs.
