# Review — fix/build-checks-after-astro

diff_sha256: e9d1402469269ef369971a1538ef294f4568de3aedb5f8781919fb16d75fc44b

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every touched path is in scope_paths; the test pin and the wiring test each joined by an amendment that names its approval, trigger and content; nothing reserved (runner size, the nightly site build, the played match payload) is decided.
- Build wiring only: both checks and their verdicts are unchanged, no page, metric, URL or wording changes; the lost page-count log line is disclosed and has no reader.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed because no test pinned the build script; round 2: build-wiring.test.mjs asserts the exact `&&` steps and that astro.config.mjs imports nothing from ./integrations/, it fails on main's wiring and runs in prebuild on every build.
- The `&&` chain fails closed: both scripts exit with their code, both default to site_v2/dist, the sitemap is written before Astro exits; the decision-history pin moves 749/189 to 748/188 for the one flagged line in the deleted integration.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The site_v2/src edits are a code comment and two schema description strings that no page renders; the byte compare of the committed sample (2,543 files, 0 differ) and the design check (165 renders, 0 failures, main's 27 warnings) show no rendered change.
- No dangling reference to the integrations or astro:build:done remains under site_v2; the page_count_driver description no longer claims what the removed hook did.

## cto-reviewer
VERDICT: PASS
risks_checked:
- No new mechanism: two existing scripts move from Astro integration hooks to `&&` steps of the build script, which drops a hook layer and two child-process wrappers; no dependency or lockfile change.
- The guard invariant holds: both CI jobs run `npm run build`, a failing check stops the build and the deploy; no cost, cadence or credential change.

## escalations
- question: Nothing pins the new build line, so reverting it would drop both checks silently — add a wiring test to this MR?
  CPO ANSWER: add it; approved in chat, 2026-10-11.
