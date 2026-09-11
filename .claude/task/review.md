# Review — feat/115-step8-history-out-of-code-guard — 2026-09-11

diff_sha256: 1475a9dfeca684abd7973741a0ef0464c6b1990a8411960ffc862c77f0a0aa64

rebound: the four PASS verdicts below were given on
`cc102ceea2b2886062bcd66b2ef3b6402e235439b35a6987c3fcc6a0c6fa6b79`. `!176` merged first and the
branch was rebased onto it; every code, test, settings and doc file is byte-identical to the
reviewed commit (the rebase conflicted only in the four per-task artifacts, resolved by keeping
this branch's), and the hash moved solely because the base side of `contract.md` moved. Rebound
without a new round, as `!172`'s rebinding was.

rounds: 4

cto-reviewer: PASS at round 1, PASS at round 2 (delta), PASS at round 3 (delta), PASS at round 4 (delta).
platform-reviewer: FAIL ×3 (rounds 1-3), PASS at round 4.
scope-auditor: PASS at round 1, PASS at round 2 (delta), PASS at round 3 (delta), PASS at round 4 (delta).

Hashes: round 1 `5cd9000c5909b0fbcd4276bbd4e5221e697d022368864b15e393f277df90a4b9`; round 2
`394d49c06fa253082438e9f06185fbe57d172ec98cc33a09265e021440bab32b`; round 3
`f08116480d52f9af592acc4f3ecce1517deca255f6ca058232eef31338cdf1fb`; round 4 above.

WHAT THE ROUNDS WERE ABOUT — the parser, every time, and every FAIL was right. Round 1: a per-line
marker check cannot see the continuation lines of a wrapped `/* … */` block (`system.css:623`,
"!151 shipped exactly this", was invisible) — fixed as a class, with Python docstrings included,
and the pin moved 481 → 849. Round 2: a line that closes one block and opens another dropped the
state — fixed with an in-order opener/closer walk, pin 849 → 850. Round 3: no test put two comment
syntaxes on one line, so a "last pair wins" regression would have passed — a test and a mutation
added, no hook change. The authority, the trees, the markers and the deny were accepted from round
1 by cto-reviewer and scope-auditor; the platform-reviewer's three FAILs each made the guard see
something real it did not see before.

rounds_cap_override: The CPO directed that the context cleanup finish before product work resumes
(his words on 2026-09-10, quoted in the frozen log's entry `2026-09-10 chore/dead-issue-references`),
and the commit gate refuses a standing FAIL. Round 4 clears round 3's FAIL BY REVIEW rather than
shipping past it, as `!172`, `!173` and `!174` recorded the same override. ⚠ RECORDED PRECISELY:
he did not rule on the cap itself, and this override does not claim he did.

## cto-reviewer
VERDICT: PASS (round 4)
risks_checked:
- Round 4 PASS (delta): the `rounds_cap_override` quote checked verbatim against the frozen log's
  2026-09-10 entry and worded precisely — it authorises the cleanup ordering, not a cap; the new
  test read end to end, no literal marker outside the runtime-assembled samples; the hook re-read
  in full, fail-open intact, stdlib-only, no new deny path; scope and override unchanged; five
  files in the cumulative diff; no cost, dependency or credential surface.
- Round 1 PASS: authority — `protected_override` quotes the "do it" with date and place and the
  routing (`.claude/hooks/**` → cto + platform; `settings.json` → cto) checked from the file, not
  memory; fail-open traced through `main()`; the two-sided pin precedented by the dead-reference
  guard; the `round \d` marker checked against every football-domain "round" in the tree — none
  collides; the string-literal false positive disclosed and bounded; ratchet-by-touch judged
  disclosed friction, not a trap; cost trivial; no dependency or credential.
- Round 2 PASS (delta): widening "comment line" to block-comment and docstring lines is the same
  approved pattern applied to a corrected definition, not a new decision; the pin jump is declared
  with its breakdown; the docstring/date trap (a date that IS the why) is disclosed friction under
  an approval that carved out nothing.
- Round 3 PASS (delta): the in-order walk is a correction to the approved mechanism; fail-open
  untouched; the two files still hold no flagged line; the guardrails row still accurate.

## platform-reviewer
VERDICT: PASS (round 4)
risks_checked:
- Round 4 PASS: hand-traced the four sub-cases of the new test against the current algorithm and
  the weakened comparison — the `sql3` sub-case (an unterminated C block whose text contains the
  Jinja opener and, two lines on, a Jinja closer) is the one that discriminates: correct keeps
  `/*` open until `*/` and flags lines 2 and 4; the mutant closes on the embedded `#}` and misses
  line 4 — red exactly there. 15 collected tests match "15 passed"; the new test's docstring and
  samples hold no marker; the pin unchanged, correctly, for a test-only diff.
- Round 1 FAIL: the per-line `_COMMENT` regex was blind to the marker-less continuation lines of
  a wrapped `/* … */` block — `site_v2/src/styles/system.css:623` narrates what `!151` shipped and
  was neither counted nor deniable; no test covered the class. Secondary: case-sensitive
  extension match; `_SKIP_DIRS` substring match. All taken; the class widened to docstrings too.
- Round 2 FAIL: `if closer in line: closer = None` dropped a block reopened on the same line; the
  same root in two more shapes (only the first opener found; an opener glued to code never
  entered block state). Taken with `_open_at_end` and a four-shape test.
- Round 3 FAIL: coverage — no test exercised the leftmost-opener comparison with two competing
  syntaxes on one line; a "last pair wins" regression would pass. Taken: a test for `.sql` (both
  orders, an unterminated block containing the other syntax's opener) and `.astro`; the mutation
  named turns exactly that test red.
- Held across rounds: `_docstring_ranges` via `ast.walk` reaches nested docstrings and falls back
  to the heuristic only when the text does not parse; the one-line docstring does not open a
  block; `{#` cannot hit CSS `#fff`; `_open_at_end` terminates (`pos` strictly increases); the
  hook is stateless and re-run safe; the deny fails open, the pin fails closed.

## scope-auditor
VERDICT: PASS (round 4)
risks_checked:
- Round 4 PASS (delta): the amendment matches the diff (one test, no hook change, pin 850/174 in
  all three artifacts); the override paragraph cites an existing frozen entry, and the log's last
  entry is still the freeze — nothing smuggled in; five evidence bullets for five criteria; five
  files in scope; no credential-shaped content.
- Round 1 PASS: scope exact; the five markers match the quoted "do it" with no sixth; the
  two-sided pin declared and justified in `decisions_taken`; `#N` reserved with its number;
  doc-sync — `agent_guardrails.md` row added, `working_agreement.md` defers to it, `CLAUDE.md`'s
  "five offline gates" is the Stop hook's count; thresholds declared; no credential; five
  evidence bullets for five criteria, the governance suite honestly marked pending at freeze.
- Round 2 PASS (delta): 481 → 849 documented as a corrected definition, not a new pattern; the
  lone "481" sits in the amendment's before/after sentence; `settings.json` unchanged since round 1.
- Round 3 PASS (delta): the state-machine fix and its test match the amendment; 850/174
  consistent across contract, evidence and test; `decisions_reserved` untouched.

## escalations
- None. The one reserved question — widening the pattern to `#N` issue refs — stays reserved with
  its number; the four sweeps and their order are the next MRs.

## Found and NOT fixed, all disclosed in the contract
- The 850 lines themselves — the four sweep MRs, each lowering the pin.
- A marker inside a string literal on a line that also holds whitespace + a marker character
  reads as a comment line (stated in the hook); a docstring continuation edited without its
  opener is seen by the CI pin, not by the hook (stated in the evidence).
- A date that IS the why (a season boundary) in a docstring is denied like any other — write the
  fact without the literal date, or put the date in code.
