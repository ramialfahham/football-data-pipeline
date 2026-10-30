# Review — claude/236-rank-flip-5797c5

diff_sha256: 653757218f4b74d6b4bc0a48a40c1dbd50378276a86da43bdddf1f9b5b7440ef

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; amendments is "(none)" and nothing outside scope is in the patch.
- No caller of displayRank, rankFill or beatsMedian remains; Direction and isNum are still used, and no document names the removed helpers.
- No copy, label, order or shown number changes; the only markup change is an invisible data-metric attribute; the mock shows the served rank (A1, A5 clear).
- No new mechanism or recurring cost: the rule joins check-built-pages.mjs, which npm run build already runs; decisions_taken names the approval.
- The short-form impact map matches the diff: one renderer, no model, export or payload change.
- approved_design names team: #134, the only page affected; decisions_reserved is none and nothing reserved is decided.
- Rounds 2 and 3: the added main test and its rowless-page step are in scope, add no copy, mechanism or cost, and strengthen coverage.

## platform-reviewer
VERDICT: PASS
risks_checked:
- main() only reads dist and the data dir, so a rerun or an interrupted run leaves no state.
- The check fails closed: main returns 1 on any issue; a row with no data-metric, no served rank or no shown rank is an issue; an unknown slug reports no served rank.
- The parse matches the emitted shape of TeamLeagueStrips.astro: no scoped style, so no data-astro-cid breaks the rs-val match; the row lookahead accepts class:list output in any attribute order.
- Path and slug: readDist yields /<lang>/<teams word>/<slug>/, and the destructure reads lang and slug correctly; the page and the check read the same featured season.
- format.ts uses only erasable syntax, and Node 24 strips types; CI runs node:24.
- No package, credential, workflow or hosting change; the check keeps only a rank map in memory.
- Round 1 found main's Team wiring untested; round 2 added a main tree test (flipped 18th fails, 1st passes), which catches deleting the Team block or breaking the slug destructure.
- Round 2 found the checkTeamRowsFound call in main unpinned; round 3 added a rowless Team page step that fails with "no Team page carried a league row", which catches deleting that call.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- mart_team_competition_benchmarks ranks by the metric's direction (lower_better ranks the lowest value 1), so the served rank needs no flip; TeamLeagueStrips renders ordinal(b.rank, lang) unflipped.
- No displayRank, rankFill, beatsMedian or count - rank pattern remains in site_v2 or design-mocks; bars.ts keeps its used exports.
- data-metric carries the existing metric_id the row already looks up; no new field, number, label or copy is drawn.
- The check compares the shown text with ordinal of the served rank, the function the block renders with, so it is no second implementation of a flip.
- No metric is added, removed or reordered; the strip plot and its better cues are unchanged.
- rendered_page_evidence.md reads the shown ranks from the built HTML in EN, DE and FI, which fits a change that draws nothing new.

## escalations
(none)
