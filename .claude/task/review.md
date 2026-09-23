# Review — design/matches-hub — 2026-09-23

diff_sha256: f2c714f317714fe820ed7e5ef607f1c364d28efdb0eea7cdc7b8b4860e7579a8

rounds: 2

Round 1: scope-auditor FAIL, bi-analyst-reviewer PASS. The FAIL was that the second render (Home's
fold) and its switch were not declared in the contract, which reserves that choice for the CPO.
Round 2 declared them as the two sides of the reserved question, named both renders in done_when,
recorded the amendment, and reworded the README row so the switch reads as an open question, not a
feature. The generator and both renders did not change between rounds, so the bi-analyst's round-1
PASS covers them as reviewed.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL closed: `decisions_taken` names both renders and the `MATCHES_HUB_FOLD=3` switch as the two sides of the reserved fold question, drawn for the CPO to answer by looking; `done_when` names `_01` and `_02`.
- The reserved question itself stays reserved: `decisions_reserved` still lists "All matches with no fold, versus Home's three and a fold", and nothing in the delta resolves it.
- The `amendments:` entry discloses the method and its trigger and claims no prior CPO approval, so it is not a `protected_override` and needs no approval quote.
- The README row now reads as an open question on #130, not a settled feature (the Appendix A2 shape of the round-1 finding).
- Scope: every file in the diff matches a `scope_paths` glob; no credential-shaped string; no structural path, so no impact map required; the one `bq` read is declared.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every field drawn traces to a mart column: fixture fields to `mart_competition_fixtures`, competition fields to `mart_competition_index`; no key in `matches_2026-09-19.json` is absent from either.
- Every reused string (`navMatches`, the filter and confederation labels, `homeShowAll`, the Schedule block name) matches `site_v2/src/i18n/strings.ts` EN and FI verbatim; nothing invented.
- The filters use the existing `.seg-in` / `.categories [data-*]` CSS with no CSS of the mock's own, and genuinely work because each group carries the matching data attributes.
- The fold's "Show all N" counts the group's total, as Home's `HeroFixtures.astro` does; the render keeps all 152 rows in the page, 16 groups folded.
- The UTC label matches the built `MatchRow.astro`; render 01 has 152 rows in 19 groups, matching the contract.
- The block standard's one added Pages row expects elements the mock actually renders.

## escalations
(none)
