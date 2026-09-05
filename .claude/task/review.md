# Review — feat/navigation-rules-competition-shell — 2026-09-04

diff_sha256: 6ced7772f52a2d7da6a479c3f3f06f38e5c1319ab94a5940164614c4f9eb2bc2

rounds: 3

⚠ **THE HASH ABOVE IS THE FOLLOW-UP BOOKKEEPING COMMIT, not the code commit.** The task's code
landed at `af55c38` (hash `dcf72b01…`), where all three verdicts below were obtained. This commit
adds only `.claude/active_work.md` (the handover) and one `contract.md` amendment authorising that
edit. It is NOT artifact-exempt — `contract.md` sits in `artifact_only_never` — so `scope-auditor`,
the only reviewer whose routing the staged paths trigger, was re-run against it and **PASSed**. The
`platform-reviewer` and `bi-analyst-reviewer` sections below are bound to `dcf72b01…`; their
territories (`site_v2/scripts/**`, `site_v2/src/**`) are untouched by this delta.

⭐ **One thing the re-run did NOT verify, and said so.** It reported that it could not adjudicate my
claim that the handover's 16,000-character trim dropped no current-state fact — the pre-trim text is
not available to it and the handover is excluded from reviewer judgment (CPO 2026-08-01). Because it
declined to certify rather than waving it through, I checked the removed lines myself. **The claim
was false**: three current-state facts had gone (the #100 pointer, `shots_on_goal_player`'s current
label/description, and the four `strings.ts` chrome strings rendering on zero pages). All three are
restored and the commit message is corrected. A reviewer refusing to certify is worth as much here
as a finding.

⚠ **THE THREE VERDICTS WERE NOT ALL OBTAINED AT THIS HASH, and that is stated rather than glossed.**
`scope-auditor` and `bi-analyst-reviewer` both PASS at `dcf72b01…`, the hash above.
`platform-reviewer` PASSed at `0217e44…`, one hash earlier. Nothing in its territory changed
between the two: `site_v2/scripts/**` is byte-identical, and the only code delta was
`system.css`'s `a.cnm` padding (BI's territory, and BI re-reviewed it afterwards). `scope-auditor`
WAS re-run for exactly this reason — it had passed at `a879ff6…`, before the new test and the CSS
fix, and a PASS bound to a superseded diff is not a PASS.

⚠ **Rounds are counted per reviewer, and they differ**: scope 3, platform 3, BI 4. The cap of 3 was
exceeded on the BI thread alone, and each of its rounds found something real — see below. Recorded
because a single `rounds:` number understates what happened here.

## scope-auditor
VERDICT: PASS
risks_checked:
- Confirmed every file in the delta (`audit-seo.mjs`, `audit-seo.test.mjs`, `system.css`) is
  already inside `scope_paths` (contract.md:13-30), so the claim that no fifth amendment was needed
  holds and no scope creep occurred across four amendments.
- Verified the `[2,2,1]` fixture (audit-seo.test.mjs:790-814) against the real implementation
  (audit-seo.mjs:624-652) — it genuinely distinguishes `Math.max` from `Math.min`, so it closes the
  finding it claims to close rather than merely citing it.
- Checked the CSS delta against the LOCKED criteria "chevron present AT REST" and "match row
  remains a single link" (contract.md:143-146) — criteria unchanged, still satisfied, none softened
  or reworded to accommodate the fix.
- Swept both evidence files for a THIRD measured-vs-derived overclaim, the defect found twice on
  this branch and once on its sibling. Found none undisclosed: every derived number is flagged as
  derived, and the corrected focus numbers match real `getComputedStyle`/DOM reads.
- Verified the tie-break rule and the padding split are attributed to ME, not written as CPO
  decisions — they are engineering responses to reviewer findings, not §10 calls.
- Confirmed the four earlier rulings in `escalations.log` are quoted verbatim and that each stated
  consequence matches what the diff builds; the cite-the-record vs create-the-record distinction
  against the sibling branch is real, not a rationalisation.
- Scanned all changed files for credential-shaped content; none.

## platform-reviewer
VERDICT: PASS  (at `0217e44…`; `site_v2/scripts/**` byte-identical at the hash above)
risks_checked:
- Re-verified the `[2,2,1]` fixture closes round 2's gap by hand-tracing both branches: `Math.min`
  gives `top=1`, one winner, `[]`; `Math.max` gives `top=2`, two winners, tie reported.
- Hand-mutated every other plausible operator in `specForPath`/`specTie` — `matches.length === 0`
  → `!== 0`, `find`'s `===` → `!==`, `winners.length > 1` → `>= 1` and `> 0`, `matches.length < 2`
  → `< 3`, and both filters' `===` → `!==`. **No surviving mutation found.**
- Traced fail-CLOSED end to end: `specTies` → `issues[]` (audit-seo.mjs:507-511) → non-empty issues
  → `return 1` (:557-561) → `process.exit` (:567) → `seo-audit.mjs:39-47` rethrows on non-zero →
  `astro:build:done` fails the build. Not merely logged.
- Confirmed the fixture is self-verifying: it asserts its own computed specificities are `[2,2,1]`
  and that all three regexes match the shared path, so a change to `routeSpecificity` or
  `specRouteRegex` fails those assertions rather than silently ceasing to exercise the branch.
- Confirmed `specForPath`'s `Math.max`+`find` rewrite changed no behaviour for any real spec route,
  in either array order, and that the `null` no-match return matches the old `find`'s `undefined`
  at its one call site.
- Checked the ambiguity message is actionable (names the URL and both spec `page` fields) and is
  arity-agnostic, so a three-way collision reports correctly without special-casing.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Confirmed the focus section is free of asserted numbers: every value is read under a confirmed
  `a.matches(':focus-visible') === true`, with `outline-width`/`outline-offset` from
  `getComputedStyle` rather than assumed. The one arithmetic passage (3 + 4 = 7 = `.gh`'s
  padding-bottom) explains an already-measured number rather than producing a new one, and the
  measured values carry realistic sub-pixel precision rather than round figures.
- Checked `clearanceAbove` measures the right reference: `.sechead`'s rule line is a flex-child
  `::after` INSIDE its box (SectionHead.astro:11-14, system.css:62), so a bounding-box read already
  encloses it — no closer collision the measurement's reference point could miss.
- Verified the asymmetric padding (system.css:508-511) grows the border-box 9px above the text with
  no visual shift, giving the uniform 13px clearance measured on all three groups — a constant
  offset from the text, not a coincidence.
- Confirmed 0.7px below is an intentional derived value (the ring lands on the divider's inner
  edge), not an unnoticed defect, with the coupling to `.gh`'s padding-bottom flagged in the CSS
  for future maintenance.
- Re-cleared the binding rule: `competition_name`/`slug` on the new page and
  `competition_slug`/`league_name` on the heading trace to real `mart_competition_index` columns
  via `shape_competition_index`; no fabricated field.
- Re-confirmed `.fxrow` is still a single anchor with 0 nested `<a>`, the new CSS introduces no
  `--accent`, and no metric, percentage or KPI is rendered anywhere in this diff.

## escalations
(none)

⭐ **What the reviewers caught that I did not — recorded because it is the point of the cycle.**
Every FAIL on this branch was found by a reviewer and none by me, and two were defects in the
PRODUCT, not the paperwork: a 21px tap target on mobile (under the 24px minimum, invisible at
desktop width) and a keyboard focus ring cutting through the group divider. Both sat behind a green
build. A third was a build gate failing OPEN on an ambiguity its own comment called a bug. The
remaining FAILs were mine writing derived numbers as measured — twice on this branch, including
inside the artifact written to correct the first instance.
