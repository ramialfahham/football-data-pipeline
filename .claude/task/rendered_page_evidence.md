# Rendered page evidence — `feat/150-competition-matchdays` (#150)

## 1. The measured check, sample build

`npm run build` on the committed sample → 1195 pages; `audit-seo: 1195 built page(s) checked. OK.`;
`check-built-pages: 849 match page(s) = 283 payload(s) x 3 (no manifest: sample build); 3 fixtures
page(s) checked. OK.` Then `python scripts/check_design_inventory.py --dist site_v2/dist --langs
en,fi,de` → `19 pages · 2 viewports · 3 languages · 88 renders · 0 failures · 0 warnings`. The new
built row "Competition matchdays" (`en/bundesliga/fixtures/index.html`, de and fi by path) is
measured at 375px and 700px; the new element row "Schedule block" (`.md > section`, visible=1,
36px above) and the three picker rows ruled on #129 are measured on the built page and on the mock.

Mutation: `checked` removed from the built EN page → the check prints `Competition matchdays · 375 ·
en · Schedule block · expected visible=1 · measured 0`, `Matchday picker · expected visible=1 ·
measured 0`, and "expected on this page · measured 0 matches" for Block heading, Tag and the picker;
restored → 0 failures.

## 1b. The warehouse behind the page, after review round 1

`is_next_round` reads mart_next_matchday's round; `fixture_order` is the served reading order. The
three singular tests against prod with the compiled mart inlined: PASS, PASS, PASS (64,661 rows). RED
under: dropping postponed fixtures / duplicating played rows (one_row_per_fixture); flagging a round's
unplayed fixtures only / flagging the round across seasons (next_round_is_one_round); slug from the
name / sides swapped (team_slugs_resolve). One mutation survives on today's data: re-deriving the
next round per season instead of reading it — no league has upcoming fixtures in two seasons today
(measured: 0), so the two agree; the test counts distinct flagged (season, round) per league and
fires the day one does. The re-exported BL1 payload: 34 rounds, rows in `fixture_order`, the first
round's ids 1575140, 1575143, 1575144 (by kick-off).

## 2. The page in the browser (dev server, `preview_start` v2)

375px, Finnish: `nav.tabs` 343/343 (fits, no sideways scroll; each tab one line, 46.5px), the
picker `.mdstep` 343/343, `title "KIERROS 4 SEURAAVA"`, the page 375/375 wide, the flagged row
"Eintracht Frankfurt | SC Freiburg | HUIPPUOTTELU | 13.30 | UTC" 81px tall, every row fits. The
screenshot (kept out of the tree) shows the picker line, OTTELUOHJELMA, PE 18.9.2026 and the rows
with the tag before the kick-off, the approved render's composition. English and German read the
same way: "MATCHDAY 4 · NEXT", "SPIELTAG 4 · NÄCHSTER".

## 3. The full-scale build, once, locally (the deploy job's heap)

Data: the export run against prod with the new mart's compiled SQL inlined as a subquery (the
method !191 used), read-only, `competitions,fixtures`: 252 competition payloads (50 MB), 5,022
fixture payloads (113 MB), manifest `counts.fixture 5022`, `source_counts.fixtures_unplayed 5022`.
The whole export read **0.088 GiB** over 19 statements (dry-run measured first: 0.009 GiB for the
competition payloads, 0.090 GiB for every unplayed match's page), about **$0.0005 per run at the
on-demand rate** — the number for the recurring-cost threshold.

Build: the 5,022 fixture payloads beside the committed sample, `NODE_OPTIONS=--max-old-space-size=8192
npx astro build` → rendering complete in 362 s, **15,078 match pages** (5,026 × 3), 15,424 pages in
all, 14 minutes wall clock including the audit; no out-of-memory. `check-built-pages` on that dist:
`15078 match page(s) = 5026 payload(s) x 3 = the warehouse's 5022 unplayed; 3 fixtures page(s)
checked. OK.` `audit-seo` on that dist: **36 violations, all one kind** — two unplayed meetings of
the same two clubs share the match preview page's `<title>` ("{home} vs {away}: Preview"): 12
pairings × 3 locales (a cup tie and a league match, or two league meetings in one season). Nothing
else is red at full scale. Filed as its own defect on GitLab (the match page's title, Matches
milestone) on 2026-09-19; whether #150 is blocked on it is the CPO's call, put on the MR.
