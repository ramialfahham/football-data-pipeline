# Review — feat/40-top-players-block — 2026-09-09

diff_sha256: bdd80cb092f37208702f13d9a7e9ca318e4e96922c2667f557e9e66660452c06

rounds: 3

Round 1: FOUR FAILS, one from every reviewer. Round 2: two PASS, two FAIL. Round 3: all four PASS.
This is round 3 of a cap of 3. No `rounds_cap_override` is needed and none is claimed.

⛔ TWO OF THE THREE ROUNDS WENT ON A QUESTION THE BUILDER GOT WRONG TWICE, and that is the honest
summary. `analytics-engineer-reviewer` failed rounds 1 and 2 on the same underlying defect — ranking
in the consumption layer — and both times the response was a partial fix resting on a false premise
(that the cross-league order could not live in the mart because it is pool-scoped). It was escalated
after round 1, the CPO ruled that all ranking and ordering lives in the warehouse, and the reasoning
that survived round 2 then turned out to be wrong on the merits: a total order restricted to a
subset keeps its sequence, so the pool never mattered. Two separate warehouse MRs (`!164`, `!165`)
came out of it, and this branch now compares nothing at all.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL, now fixed — the German board labels shipped on a ruling narrated in `contract.md`
  and present nowhere in `escalations.log`. Verified this round that the ruling is in the log
  verbatim and matches both the contract and the strings `strings.ts` actually ships. Confirmed the
  unrelated `assists: "Vorlagen"` elsewhere in that file is a different key (the fixture-preview
  short label), not a collision.
- Verified both 2026-09-09 rulings against `escalations.log` line by line rather than by paraphrase,
  guarding the repo's recorded `feedback_dont_attribute_repo_practice_to_cpo` failure class.
- Checked the struck `decisions_reserved` entry on the cross-league order: it cites a real merged MR
  (`!165`, `7cac157`) and gives a sound reason, so it is resolved rather than silently dropped.
- Checked each amendment records real authority and labels a STANDING RULE as such rather than
  dressing it up as a CPO answer.
- Confirmed every file in the cumulative patch is inside `scope_paths`, and that no
  `dbt_project/**` file appears here — the model work genuinely lives in the two merged MRs.
- Swept the whole patch for credential-shaped strings across all rounds: none.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL — `_board_order` picked between joint rank-1 players using a key that existed nowhere
  in the warehouse. Round 2 FAIL — the fix left the same rule as a three-key `ORDER BY` in the
  export. Both are gone: the query is `order by l.board_leader_order`, one served column.
- Confirmed no ranking, comparison, tie-break or ordering computation remains anywhere in the
  consumption layer — checked `scripts/export_site_data.py`, `TopPlayers.astro` (its `{i + 1}` is a
  display ordinal over an already-ordered array, not a computed rank) and the player route's
  `getStaticPaths` (slug dedup for routing, not a ranking).
- Confirmed the shaper only groups, preserves and caps, and that its "does not reorder" contract is
  pinned by a test fed rows in an order no sort would produce.
- Confirmed the two deleted Python tests were replaced by warehouse coverage rather than dropped,
  and that the note left in their place names both dbt tests by path.
- Read the merged mart for context: `league_leader_order` and `board_leader_order` use the same
  ruled keys, and the latter is NULL on non-leaders so a consumer cannot order by a sequence a row
  is not part of.
- Spot-checked the committed `landing.json` for monotonic value order consistent with the served
  order.
- Confirmed `decisions_reserved` names the prior justification as FALSE rather than asserting some
  new authority in its place.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL, now fixed — the widened `_METRIC_ENTRY_RE` had no test pinning it. Hand-traced the
  mutation: narrowing it back leaves `parsed[loc]` without the `playerMetrics.*` keys and reds the
  new test, while `check_copy_gate.main()` still prints a clean pass — exactly the hole named.
- Confirmed all three widened parsers have independent trip-wires, not only the Python one: the
  pre-existing "the two metric-key parsers disagree" test now compares on `k.includes(".")`, so
  reverting either JS regex alone desyncs the sets and reds it.
- Confirmed the two deleted Python tests' invariants are LIVE, not promised — read
  `assert_mart_leaderboards_one_leader_per_league.sql` in full in the merged tree.
- Re-run and idempotence: the export is a read-only SELECT plus a JSON write with no incremental
  state. The one new determinism risk the changed ORDER BY raises is whether `board_leader_order`
  can tie; the merged dbt test's uniqueness invariant is exactly what forecloses that.
- Coverage division for the changed SQL line, examined rather than waved through: no pytest
  exercises the literal ORDER BY, because this codebase has no BigQuery mock layer — and that was
  equally true of the three-key form it replaces, and of the `league_leader_order = 1` and
  `is_current_season` filters beside it. The behaviour that changed moved INTO the warehouse, where
  it is pinned. Not a fresh coverage hole introduced by this delta.
- Third-party asset fetch, dependency changes, guard mechanics, hosting config and build page count:
  checked across rounds; nothing in scope changed, and the player route dedupes by slug before
  fanning out over locales.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL — `rendered_page_evidence.md` documented a different branch. Round 2 FAIL — its §5
  carried counts from a build captured before the payload was re-exported. Both fixed, the second by
  re-deriving EVERY figure in the file rather than only the one that was caught.
- Re-derived the round-2 defect independently rather than trusting the fix: hand-counted all 28
  player slugs across the four boards in the committed `landing.json` — 28 distinct, no repeats, so
  84 player pages, matching the corrected evidence.
- Independently summed the page-count driver line to 251 against a stated 250, then traced
  `audit-seo.mjs`'s `walkDist` and confirmed only `.html` files count as pages, so `robots.txt` is
  correctly excluded. Not a defect; recorded because the arithmetic looks wrong until you check it.
- Binding rule: traced every field the component, the player page and the TypeScript types declare
  back to the shaper and the mart query. No fabricated field, nothing sourced only from the sample.
- Locked board order matches `10_home.md`; board labels come from the catalogue seed rather than
  being hand-typed; the DE/FI strings match the rulings quoted in the contract.
- Checked the rendering claims in the evidence against `system.css` itself — the
  `@container (max-width: 480px)` rule blockifies `.ent`/`.nm`/`.sub` together (per-board stacking,
  not per-row) and `a.brow:focus-visible { outline-offset: -2px }` matches the claimed ring fix.
- Home-page wiring guards the block on the key being ABSENT rather than empty, matching the export
  which omits it entirely when no board survives. No empty state, no metric creep, no naked
  percentage.

## escalations
(none open)

The §10 questions this branch raised were escalated after round 1 and ANSWERED — the two 2026-09-09
rulings recorded in `escalations.log`. What it deliberately does not answer is in
`decisions_reserved`, and the last-resort tie-break is GitLab #112 at minor priority.
