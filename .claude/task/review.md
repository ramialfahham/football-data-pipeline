# Review — fix/231-tag-narrow-form — 2026-11-01

diff_sha256: bcbf94d91bf68fd0f7a9674dffb5f5d4eab07080e6781cc71e1e9bdea79d1a2f

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file in the diff is in scope_paths, and no file outside it changed.
- The narrow form, the plan and the two block standard texts are named in decisions_taken as approved in chat, 2026-11-01; the Tag row sentence matches acceptance criterion 3; nothing else is decided in the diff.
- The new "tagged" kind is a block type inside the existing shared fit script, declared as no new mechanism; no library, hook, service, run or API volume is added; no recurring cost.
- The impact map's three callers were checked by grep: HeroFixtures.astro, MatchdaySchedule.astro and TeamFixtureGroup.astro are the only callers passing topMatch or nextMatch; approved_design names exactly their three pages.
- The green.html fit-one mark and the history pin moving from 48 to 47 match the contract amendments and the diff.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- No data, export, component markup or user-visible string changes; the tag text still comes from compNextTag and compTopMatch.
- The rendered evidence gives measured boxes over 108 pages at 280, 360, 560, 768 and 1010px: 52 failing views before, 0 of 1,620 after, the narrow tag at x=16 above the home name.
- The fit-one overrides are strictly more specific than the narrow base rules, so the wide form wins when marked and the narrow form is the default without the script; no other file styles `.fxrow` or `.topmatch`.
- No metric row, tier, order, percentage, null or window label is touched.

## platform-reviewer
VERDICT: PASS
risks_checked:
- fit() in fitBlocks.mjs is idempotent for the "tagged" kind: it measures only the wide form, always finds a `.sides` child, and the ResizeObserver re-run settles without oscillating; hidden rows are re-measured on `change`.
- The CSS cascade in system.css: the fit-one rules out-rank the narrow defaults, and DOM order puts the tag before the kick-off in the wide form.
- The measure is valid: an unbreakable word wider than the `minmax(0, 1fr)` column makes `.sides` scrollWidth exceed clientWidth.
- Coverage: the Fitted block row's fit-marked assertion fails a tagged row left unmarked; the narrow placement itself is pinned only by the task's measurement, as for every other fitted block.
- check-built-pages.mjs reads the server-rendered class only, which fit-one does not touch; no dependency, credential, hook or CI change.

## escalations
(none)
