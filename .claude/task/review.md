# Review — fix/german-coverage — 2026-09-23

diff_sha256: b5b5aa3e8bcb5d2c350be20461e40bb29055cf4087cccf93e164fcfdb2e460fb

rounds: 3

Three rounds, all three required reviewers PASS at the end. The platform reviewer FAILed twice, and
both findings were in the code this branch adds rather than around it: first the new coverage
caveat computed from configuration instead of from what rendered, then the caveat having no test
at all. The second is the sharper of the two — the whole branch exists because a gate was not
measuring what it claimed, and the fix for it initially shipped unpinned.

## scope-auditor
VERDICT: PASS
risks_checked:
- Two unrelated items on one branch: stated in `decisions_taken` rather than hidden, and tied to the CPO's own pushback quoted and dated in `refs`. Neither item is a naming, product or metric decision on its own. Disclosed, not smuggled — defensible, not drift.
- The German word: checked against the handover's record that Mannschaft(en) was ruled sitewide on !216, which predates this task, then grepped the whole German block for remaining "Team" — none outside the `{team}` interpolation placeholder. Applying a settled ruling, not a new naming call.
- `scope_paths` against the staged diff: every file matches an entry; nothing outside it.
- `.gitlab-ci.yml`'s stale "EN and FI" comment: the file is absent from the diff, no `protected_override` was taken, and the staleness is disclosed in three places rather than forced through or silently left. Correct handling of a protected governance path.
- The rule-extension question: read `block_standard.md` and confirmed it already rules the tab bar to fit "in EN, DE and FI" while the guard enforced two. Tuning a guard to an existing written rule is the builder's, not a §10 extension.
- Attribution: the CPO quote is dated, no entry was added to the frozen escalations log, and `decisions_reserved` keeps the address-vocabulary question off this branch.
- No new mechanism, no credential-shaped content; the +14 renders are disclosed in the impact map.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the new coverage caveat was computed from the CONFIGURED page list, so `--page` ad-hoc targets — hard-coded to render English only — were counted in the page total and implied covered in every requested language; with no inventory page selected the caveat was suppressed entirely. The same class of overstatement the branch exists to fix, reproduced in miniature. Fixed by reading the tally from the renders as they happen and counting every language ASKED FOR, so one that reached nothing shows as 0. Re-traced in round 2 against the original repro: closed.
- Every `continue` above the counter — mock generator failure, the `fi == "none"` skip, a language outside the mock set, no built file, a missing or unresponsive FI toggle — sits before the increment, so nothing that failed to render is counted as covered, and nothing increments without having been measured.
- Round 2 FAIL: the caveat had no test. Every existing subprocess test hardcodes `--langs en`, so the branch was unreachable and a regression would have turned nothing red; the only evidence was hand-run transcripts, which CI never re-runs. Closed by a `@needs_browser` subprocess test asserting the exact tally on a three-language ad-hoc run and asserting silence on a one-language run. Checked that it is an exact-substring assertion, so a caveat firing with wrong numbers still fails; that the "last line containing renders" selection cannot pick up a spurious line; and that the RED mutation targets the same lines the round-1 defect lived in.
- `MOCK_LANGS` faithfully replaces the literal it came from, and the neighbouring `p.fi == "none"` guard still runs first and behaves identically. A `fi = "none"` row, if one is ever added, falls through correctly with no new code.
- The new locale pin parses `href.ts` with a regex but asserts the match before using it, so a format drift fails CLOSED. `check_design_inventory` imports Playwright inside `main()` under a guard, so importing it at test time needs no browser and the suite still runs where Chromium is absent.
- Test idiom matches its neighbours — `@needs_browser`, subprocess, `PYTHONIOENCODING`, `encoding="utf-8"`, the shared fixture constants — and the `--page NAME=PATH` argument is a list element, so Windows paths are not a parsing hazard. It cannot reuse `_run_check`, which hardcodes one language.
- Cost: +14 renders per run, plus two browser launches in the new test. Stated in the impact map and the evidence; acceptable for `validate:ui`.
- The prose edits in this territory now describe built pages and mocks separately and carry no stale claim. `.gitlab-ci.yml` still says "EN and FI" and is confirmed knowingly left, not forgotten.
- Stated limitation: this reviewer had no execution tool, so the pass/fail counts and the RED transcript were checked for logical consistency against the source rather than re-run.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Swept the whole German dictionary for remaining "Team" after the change: every German value now reads Mannschaft(en), and the only surviving occurrences in the file are English code comments. "Mannschaften, Spieler suchen…" is a correct plural and mirrors the English and Finnish constructions rather than being newly invented wording.
- Verified against the built output, not the source: the German pages carry the new text and a grep for the old string under `dist/de` returns zero files.
- Read the BUNDLED CSS rather than `system.css`: `.searchbox{display:none; … min-width:180px}` with `@media (min-width:1010px){.searchbox{display:flex}}`. So the control is structurally hidden below 1010px — covering both viewports the check measures — and where it is visible it has no fixed or maximum width, which means a longer word cannot clip by construction. That is a stronger confirmation than the measurement it was checking.
- Traced the built-page branch of the check to confirm the block standard's corrected `FI` line is true of the code: a built page loops over every requested language and never reads `p.fi`; only the mock branch consults it. The correction is accurate, not a new inaccuracy.
- Counted the Pages table against the reported coverage: 7 built rows and 13 mock rows, consistent with `en 20, de 7, fi 20`.
- The header paragraph names today's three locales as well as the general clause, so a fourth locale would need a follow-up edit. Judged consistent with the document's existing convention — the tab-bar rule names the three the same way — rather than a defect this diff introduces.
- Checked the patch hunks for both files against the working tree: no edits beyond the one German value and the two disclosed prose corrections.

## Noted, not fixed here
- `.searchbox` is hidden at both viewports the check measures, so a search-box defect in any language would still pass the gate. A different gap from the one closed here; named on the MR head rather than folded in.
- `covered` counts distinct page NAMES per language, accumulated across both viewports, so a page rendering at 375 but failing to render at 700 in one language would still read as covered on the summary line. Not silent: each skip appends a failure carrying its viewport. Raised by the reviewer as narrow and not failed on.
