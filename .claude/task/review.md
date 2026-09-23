# Review — design/matches-hub — 2026-09-23

diff_sha256: 46c797d735d8e54159467b2dcaa8be894f242c95b8c6b21a416f25ac38864228

rounds: 3

Round 1: scope-auditor FAIL, bi-analyst-reviewer PASS. The FAIL was that the second render (Home's
fold) and its switch were not declared in the contract, which reserves that choice for the CPO.
Round 2 declared them as the two sides of the reserved question, named both renders in done_when,
recorded the amendment, and reworded the README row so the switch reads as an open question, not a
feature. The generator and both renders did not change between rounds, so the bi-analyst's round-1
PASS covers them as reviewed.

Rebound after the rebase onto main (the cleanup, !223, merged first). The three task artifacts were
the only conflicts and were resolved to this task's side; the branch's own diff against main is
the same eight files as reviewed. The cleanup added a third width to the design check, which this
mock had never been measured at: re-run for both variants, `1 pages · 3 viewports · 6 renders ·
0 failures · 0 warnings` each, and the lint 0 findings.

Round 3, after the CPO ruled the fold ("B") on #130 and the day switcher's reach on #131: the
generator draws the fold as the design, takes the day from `MATCHES_HUB_DAY`, and renders the
national-team variant (Saturday 26 September, real fixtures) as `_03`. Delta review by the
scope-auditor, PASS. No path the bi-analyst routes on changed in this round.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3 delta: the two ruled questions leave `decisions_reserved` and are recorded as ruled with issue and date; approval of the page as a whole stays reserved; `FOLD = 3` matches the ruling and render 01 stays on file; `MATCHES_HUB_DAY` is a mock-local selector of a committed pull, no new mechanism; the flag badge is the shared row's existing national-team variant; the new data file is in `scope_paths`; the 1010px width in done_when is the existing standard; no credential-shaped text.
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
