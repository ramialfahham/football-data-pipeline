# Review — feat/150-competition-matchdays — 2026-09-19

diff_sha256: c7afb1d4d8676823a5f73a6d16868f9e1ab6b94e09a62f34e476268978292b22

rounds: 3

Round 1 (five reviewers on the whole branch): scope-auditor FAIL (the impact_map's downstream was a
promise, not pasted output; `docs/wireframes/00_overview.md` row 04 still named four tabs);
analytics-engineer FAIL (`fixture_slug` described a null case beside `not_null`; the export ordered
rows by a Python comparator; `is_next_round` re-derived the next round per season instead of reading
mart_next_matchday's); platform FAIL (the built-pages row regex required `class` first and so never
matched a real linked row; the `.gitignore` range admitted seven ids below its documented start);
bi-analyst PASS; cto PASS. Every finding fixed and recorded in the contract's amendments.
Round 2 (delta, four reviewers): scope-auditor PASS, bi-analyst PASS, platform PASS;
analytics-engineer FAIL by review then — the `fixture_order` yml block had displaced
`is_match_that_matters`'s tests under a duplicated key — resolved at round 3.
Round 3 (delta, one reviewer): analytics-engineer on the yml block.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every path in the cumulative diff is in `scope_paths`; the four documents the tab touches (block
  standard, wireframe overview, site and content architecture) agree with each other and with #129.
- Every §10 decision (the slug, the played rows, the three-tab naming) carries its dated CPO ruling;
  the round-number and next-round choices trace to pre-existing warehouse definitions.
- Both thresholds (the build-done check, the export's reads) declared for cto-reviewer; nothing in
  `decisions_reserved` decided in the diff; the copy shipped as drafts pending the MR.
- The round-1 fixes verified in code, not prose: the pasted `dbt ls`, the rewritten row 04, the
  served `fixture_order`, `is_next_round` joined not re-derived, the row regex, the allowlist start.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the mart reads `fct_fixture`, `dim_team`, `int_legs__team_match` and
  `mart_next_matchday` only; league_code carried; no partition or cluster key; no hardcoded league.
- `fixture_order` end to end: `row_number()` per competition-season by round_sequence, kick-off,
  fixture_sk; unique per season at the model level; the export sorts by it alone and drops it from
  the shipped rows; the unit test pins that kick-offs out of step with it do not change the order.
- `is_next_round` read from `mart_next_matchday`'s round; the singular test recomputes the
  league-wide rule from `fct_fixture` and echoes every `mart_next_matchday` row; the surviving
  per-season mutation is disclosed (no league with upcoming fixtures in two seasons today).
- `fixture_slug`: description and `not_null` consistent; the singular test recomputes it from
  `dim_team`. The consumption layer selects, groups and renames only; the Python slug builder is gone.
- Round 3: the yml block of `mart_competition_fixtures` read in full — every column's tests match
  its class, no duplicated or displaced key; the test count matches the contract's paste.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `check-built-pages.mjs`: the row regex matches the real built output (`<a href="…" class="fxrow">`)
  in any attribute order, cannot over-match (`class="fxrow"` or `"fxrow played"` quote-anchored) or
  under-match; mutation-tested on the real dist (an inert unplayed row, a linked played row) and by
  unit tests including unrelated `<a class="lnk">` and `<div class="dh">` on the page.
- The manifest comparison: sampled export, committed sample beside a full export, no manifest.
- `.gitignore`: the six bracket ranges compose to exactly 1575167–1575445; both boundaries probed.
- The integration mirrors seo-audit (child process, stdio inherit, throw on non-zero); `node --test`
  discovers the new test; `readDist` holds no page beyond one iteration; CI's `build:site-v2` builds
  the committed sample with no heap flag, as before.
- The export raises on a missing `fixture_order` rather than misordering silently — the right failure.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every field the Matchdays components render traced to a served mart column through the export and
  the committed payload; no hand-typed value in the sample; `fixture_order` consumed, not shipped.
- The picker, the tag, the score by weight, the inert played row and the linked unplayed row match
  the block standard's rows and the mock's row markup; no `<style>`, no inline style.
- The tab bar links only emitted pages; the header identical on both tabs; copy present in EN/DE/FI
  and listed as drafts for the MR; the UTC label a disclosed deferral (#146).
- Round 2: `docs/wireframes/00_overview.md` row 04 agrees with `docs/content_architecture.md` line
  124 and with #129 as the tracker backup holds it.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The new mechanism (the build-done check) is declared, reuses the seo-audit pattern, fails closed,
  adds no package; the recurring cost is declared and measured (0.088 GiB, ~$0.0005 per run), the
  deploy export not widened; no dependency, no protected path; the mart-to-mart ref and the
  intermediate semi-join are allowed same-layer / upstream refs with precedent; the h1 narrowing is
  the narrowest rule admitting the ruled case and is pinned both ways.

## escalations
(none) — the two rulings this branch rests on (the slug from the warehouse; played rows inert until
the report page exists) were put to the CPO in chat on 2026-09-18 and are recorded in
`contract.md` (`decisions_taken`, `amendments`). Open for the MR head: the copy, the match-title
collision found at full scale (filed as its own issue), and whether #150 waits on it.
