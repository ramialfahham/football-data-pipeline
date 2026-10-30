# Verification — the Team page shows the served league rank

Read from the built output of `npm run build` in site_v2 on the committed sample (prebuild: 144 site
tests pass and 10 page specs validate; 2,268 pages built; audit-seo OK). `check-built-pages.mjs`
reports "3318 league row(s) on 102 team page(s) checked. OK." The sample page is SC Freiburg,
Bundesliga, 18 clubs, at `/en/teams/sc-freiburg/`, `/de/mannschaften/sc-freiburg/` and
`/fi/joukkueet/sc-freiburg/`, read from `site_v2/dist`.

criteria_demonstrated:
  - Less is better: SC Freiburg's fouls per match is 9.43, the league strip's lowest of 18 clubs; the payload serves rank 1 and the built row shows "1st" (DE and FI "1."). Its other less-is-better rows show the served rank: goals against 4th, shots on target against 3rd, yellow cards 9th, red cards 12th.
  - More is better: SC Freiburg's goals per match is 2.29 with 3 clubs higher on the strip; the payload serves rank 4 and the built row shows "4th" (DE and FI "4.").
  - Every build fails on another rank: `npm run build` runs `check-built-pages.mjs`, which held all 3,318 league rows on the 102 built Team pages to the served rank. With SC Freiburg's built EN page changed to show fouls per match "18th", `checkTeamPage` reports "the league row of fouls_per_match shows 18th, the payload serves 1st". The test "main fails a Team page with no league row or a flipped served rank, and passes it once the row shows the served one" holds the same through `main` on a built tree.
  - The test "a less-is-better row shows the served rank: 1 of 18 is 1st, and a flipped 18th fails" in `site_v2/scripts/check-built-pages.test.mjs` passes, beside a more-is-better case and the cases for a row with no metric or no served rank.
  - The mock generator: `design-mocks/gen_team_mock.py` writes `_ord(b["rank"])` in the league row; the flip and the unused `low_rank` helper are gone; `python -m py_compile` passes.
  - No flipping helper: `displayRank`, `rankFill` and `beatsMedian` are deleted from `site_v2/src/lib/bars.ts`; `grep -rn "displayRank\|rankFill\|beatsMedian" site_v2/src design-mocks` finds nothing.

pytest: 1,614 passed, 4 skipped. The offline gates of validate-local pass.
