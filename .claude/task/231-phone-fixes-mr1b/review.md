# Review — claude/231-phone-fixes-mr1b-a2bb82 — 2026-11-15

diff_sha256: 346922afc3ffbe75c0bf4f0d1ff1d91fd75e2d77c872d3270818111a8c6a88f6

rounds: 4
rounds_cap_override: round 4 holds the wrapper-test skip fix for the red test:python of !448 and gitlab/main merged in after !445; approved in chat, 2026-11-15

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths, including tests/test_check_chart_screenshots.py (added before round 2); no CI file, hook or workflow changes.
- The tap, picker, separator and explainer changes each apply a rule the contract ties to a dated #231 or #230 comment; square rows and the Goals space are defects against written rules; no §10 decision is taken and decisions_reserved stays none.
- The one new client script is named in decisions_taken; no service, library or recurring cost is added.
- Round 2 delta: the lowercase DE and FI strings remove the only wording difference between languages, adding no wording decision.
- Round 4 delta: gitlab/main merged in; the wrapper test skips when no built site exists; in scope, no decision, no CI file touched.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (DE and FI explainer capitalised after the colon, EN lowercase) is fixed: all three languages read lowercase and none names the team.
- No metric row, label, tier or percentage is added or reordered; the Goals and Points rows only gain the space between label and value.
- The picker carries both date forms with exactly one shown; the short form is the no-script form and fitBlocks leaves the competition-matchdays picker alone.
- The separator pass touches no bare dot that is not a separator; hidden dots are only those that start a line.
- The picker arrow row in the registry stays at its 34px probe, which the 44px page passes.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The built-page tests now run inside validate:ui through the existing pytest list (a subprocess test in tests/test_check_chart_screenshots.py); a missing sample page fails instead of skipping, so the wrapper cannot go green on a skipped module where dist and playwright exist.
- The page-css and component-registry pins do not rise: no new width query, no style write in a script, no unlisted class, every spacing value already in the registry set; requirements-ui.txt is unchanged.
- The day picker's short and long forms and the hidden-dot rule are pinned by built tests at 280 and 1010px in EN, DE and FI.
- Chart screenshot pins are the check's own output from the CI image; the check shows 0 differences over 18.
- Round 4 delta: the wrapper skip applies only where no dist exists (test:python); validate:ui gets the dist artifact and fails closed earlier without it, and the built-page module still fails on a missing page.

## escalations
(none)
