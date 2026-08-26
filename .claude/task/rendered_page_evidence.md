# Rendered page evidence — export sample refresh after #90

Read from `site_v2/dist/` after `npm run build` (60 pages, `audit-seo: 61 built page(s) checked.
OK.`), not from source and not from `outerHTML`. HTML comments stripped before collapsing text,
because Astro splits interpolated text with `<!-- -->`.

## Team page, all three locales

`dist/{lang}/teams/manchester-united-fc/index.html`

| | EN | DE | FI |
|---|---|---|---|
| "vs the league" rows | 0 | 0 | 0 |
| "vs last season" rows | 0 | 0 | 0 |
| tab state | not-rankable message | not-rankable message | not-rankable message |

EN, verbatim: **"Not enough games this season to rank Manchester United FC against the league."**
DE and FI render their own translations of the same string.

**This is the correct state, not a regression.** The featured season is now PL 2026 with 1 game
played; `mart_team_competition_benchmarks` ranks nothing below 3 games, so the season carries 0
benchmark rows and `TeamPerformance.astro`'s `hasBench` guard renders the whole tab as absent
rather than fabricating bars. PL 2025 remains in the payload with its 22 benchmark rows and will
render again for whichever season the pipeline features once three games are played.

## URL

The page moved from `/{locale}/teams/manchester-united/` to
`/{locale}/teams/manchester-united-fc/`, following the slug in the refreshed payload. `audit-seo`
passes because the tracked file set is unchanged and nothing on the site links to a team page.
Registered in `decisions_reserved`.

## What this evidence does NOT show

It cannot show the clean-sheet row ranked under `% Clean sheets`, because no season on this page
is rankable today. That check lives in `acceptance_evidence.md`, against the payload: 22
`clean_sheets_share` benchmark rows and 0 `clean_sheets` ones.
