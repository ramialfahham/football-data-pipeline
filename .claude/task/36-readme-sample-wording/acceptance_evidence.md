# Verification — the sample README states how a board row links

The change is two passages of text in `site_v2/src/data/README.md`; no page, payload or script moves.

criteria_demonstrated:
  - **No plain-text claim:** `git grep -n "stays plain text" -- site_v2/src/data/README.md` finds no match; the `players/*.json` entry says the sample holds every board player because `check-built-pages` fails a board row that is not a link.
  - **Recipe step 6:** the step says `--sample` must be at least the number of distinct board players, and that with fewer a board row has no page and `check-built-pages` fails the build. This is the failure the 72-player run of !530 produced (two board rows without a page, six issues).
