# Task contract — the dead-reference guard used a boundary that was wrong within the hour

objective: >
  `tests/test_no_dead_issue_refs.py` shipped in `!171` with `FIRST_DEAD = 115`: any issue reference
  at or above 115 is dead. GitLab issued **#115** the same day — the context-cleanup issue the CPO
  asked for as his reference — so the guard would flag a live reference, and the constant would need
  chasing GitLab's counter forever. Replace the moving boundary with a CLOSED SET, which needs no
  periodic re-tuning — see `decisions_taken` for what it does still cost.

refs: >
  `!171` shipped the guard. GitLab **#115** is "Context engineering cleanup", filed 2026-09-10 and
  live — the collision.
  `.claude/task/escalations.log` `2026-09-10 chore/dead-issue-references` — the CPO's direction that
  the cleanup finishes before product work resumes, and the revised nine-step plan.
  ⭐ THE JUSTIFICATION FOR REWRITING RATHER THAN BUMPING THE CONSTANT IS TECHNICAL AND STANDS ON ITS
  OWN, without reference to anything the CPO said: **there is no value of `FIRST_DEAD` that is both
  correct and stable.** Correct means just above GitLab's maximum, which moves. Stable means high,
  which stops flagging everything below it — that is, all of them. A one-character bump to 116 buys
  one issue of life. That argument is checkable by anyone and is what this branch rests on.

  ⚠ THE CPO'S STANDARD IS CONTEXT, NOT AUTHORITY, AND `scope-auditor` WAS RIGHT TWICE ABOUT IT.
  Round 1: I quoted him without logging it, and it FAILed as fabricated — correctly, because an
  unlogged quote is indistinguishable from an invented one. Round 2, after I logged it: it FAILed
  again on the deeper point, that a log entry I wrote, in the branch under review, after being
  caught, corroborates nothing but my own assertion.
  ⛔ THAT SECOND OBJECTION IS UNANSWERABLE AND IT IS NOT SPECIFIC TO THIS BRANCH. Every entry in
  `escalations.log` is authored by the party it constrains, in the branch it justifies. The file the
  working agreement designates as the durable record of the CPO's rulings is self-attested. No care
  taken while writing an entry fixes that. Recorded as a finding against step 4 of the context plan
  (GitLab #115), which is where `escalations.log` is restructured — this branch does not pretend to
  solve it, and deliberately no longer leans on it.

scope_paths:
  - tests/test_no_dead_issue_refs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log

impact_map: >
  writers: one test file. No model, mart, export, site source, doc or CI config.

  downstream: the test runs in CI's `test:python`. Nothing else reads it.

  blast_radius: the guard's COVERAGE changes shape. Before: everything `>=115`, which over-covers
    (future live issues) and under-covers nothing. After: exactly the 256 GitHub-era numbers this
    repo actually references. That UNDER-COVERS a GitHub number nothing has ever cited, and that
    gap is real, silent and unguarded — see `decisions_taken`, which states it the same way. It has
    not occurred historically (every dead reference that got in was copied from elsewhere in the
    repo, which the set covers), but "has not happened" is not "cannot happen".
    ⚠ THIS SENTENCE READ "harmless" UNTIL ROUND 4, while `decisions_taken` called the same gap "the
    worse property, and it is not guarded". `scope-auditor` FAILed it as the same defect class as
    rounds 2 and 3 — an absolute claim sitting apart from its own rebuttal — surviving a third time
    because the sweep grepped for the WORDS I had used ("correct forever", "cannot rot") and this
    instance said "harmless".

  deploy_order: none.

acceptance_criteria:
  - A live GitLab reference is NOT flagged. Pinned for `#115` specifically, the number that broke
    the boundary version.
  - A dead reference IS flagged. Pinned for `#753` (the player page's phantom design authority) and
    `#153`/`#156` (the "Next" line).
  - The CSS colour `#475569` in `docs/roles/ui_expert.md` is not read as an issue number.
  - Removing ANY number from the set turns a test RED — pinned by a digest over all 256 members,
    not by asserting a handful. ⚠ The first version pinned `min(...)`, two literal strings and
    nothing else: 4 of 256 members, so deleting any of the other 252 stayed green. Worse, the
    mutation offered as proof deleted `151`, which is the member `min(...)` pins — a cherry-picked
    mutation presented as a general property. `platform-reviewer` caught both.
  - A previously-uncited dead number entering these files is NOT caught, and no test claims it is.
  - A three-digit all-decimal CSS colour (`#217`) in either guarded file IS misread as an issue.
    Accepted, not fixed — pinned by `test_a_short_all_digit_hex_colour_is_a_KNOWN_false_positive`,
    which asserts the wrong behaviour so it is a documented limitation rather than an unknown gap.
  - A dead reference abutting a hex letter (`#217e`) is NOT caught — a silent false negative.
    Accepted, not fixed, for the mirror reason: `#217e` is itself a valid `#RGBA` colour. Pinned by
    `test_a_reference_abutting_a_hex_letter_is_a_KNOWN_false_negative`; no such form exists in
    either guarded file today.
  - `pytest tests/` and `ruff check .` green.

decisions_taken: >
  THE SET IS CLOSED, AND THAT IS THE WHOLE POINT. GitHub's tracker is gone, so no NEW dead number
  can ever come into existence. A frozen list therefore needs no periodic re-tuning, where a
  boundary is wrong the moment GitLab's counter moves.
  ⚠ NOT "correct forever", and the decay is not a single event either. As GitLab's counter climbs
  from #115 into this range, more members become live numbers, so the collision SURFACE grows — and
  unevenly, because the set has dense runs (`range(276, 297)` is 21 consecutive, `range(407, 429)`
  is 22). `scope-auditor` FAILed the earlier "a named event with a one-line fix" wording for
  exactly that, and it was right that the wording understated it.
  ⚠ WHAT IT GOT WRONG, and it changes the size of the problem: it concluded the guard would then
  fail "on every single issue GitLab files for weeks, each one requiring its own commit". It does
  not. The guard fires on CITATION, not existence — `_dead_refs` only returns numbers the text
  actually contains — so entering a dense run costs nothing by itself. Verified by running it: with
  280 in the set, prose that does not cite it returns `[]`. The cost is one deletion at the moment
  someone writes that live issue into one of the two guarded files, and those files cite ~15 issues
  between them across the project's entire life.
  Contents: every `#115`-`#9999` referenced across
  `CLAUDE.md`, `docs/`, `.claude/active_work.md` and the memory store on 2026-09-10 — 256 numbers.
  The derivation is sound because GitLab had only reached #115 that day, so anything at or above it
  in an older document is necessarily GitHub-era.

  ⛔ A CSS COLOUR WAS BEING READ AS AN ISSUE NUMBER. `docs/roles/ui_expert.md` carries `#475569`
  (slate-600), and the shipped regex `#(\d+)` matched it as issue 475569. `platform-reviewer` raised
  this class on `!171` as hypothetical — "would false-positive on a pure-digit hex colour if one
  were ever added" — having grepped only the two guarded files. One already existed elsewhere in the
  repo. The pattern is now `#(\d{1,4})(?![0-9a-fA-F])`.
  ⚠ FOUND BY REGENERATING THE SET, not by review: the derived range ran to 475569, which is not a
  plausible issue id. The number was the tell.

  THE ONE REMAINING FAILURE MODE IS DISCLOSED AND MADE LOUD, not hidden. If GitLab ever issues a
  number inside the set, a legitimate reference is flagged. The fix is deleting one entry —
  deliberate and visible. `test_the_headroom_before_a_collision_is_stated` pins the
  lowest member (#151), so the headroom is stated and a silencing edit cannot pass quietly.

  THRESHOLD — NEW MECHANISM: none. The same test file, in the same suite.

  THRESHOLD — RECURRING COST: **NOT "strictly less". It is a TRADE, and the earlier version of this
  line was self-contradictory** — it claimed "no regeneration at all" three lines above conceding
  that a previously-uncited dead number would slip through, which is precisely a case where the set
  would need regenerating. `scope-auditor` caught the contradiction. Stated honestly:

    | | boundary (`>=115`) | closed set |
    |---|---|---|
    | maintenance | re-tune whenever GitLab's counter passes it — perpetual, and triggered by the counter alone | one deletion per collision, and only when a colliding issue is actually CITED in one of the two files (~15 citations in the project's life so far) |
    | covers a dead number NEVER cited before | **yes** | **no** |
    | covers live GitLab issues correctly | no — flags them | yes |
    | silencing it | move one constant, invisible | RED, digest-pinned |

  ⛔ A FOURTH FALSE-POSITIVE CLASS IS ACCEPTED, NOT FIXED, AND THAT IS A DECISION — recorded here
  because `scope-auditor` FAILed round 6 for it living only in a test docstring while the other two
  known gaps were disclosed in this contract. Selectively surfacing some limitations to the
  authoritative record and leaving one in code comments is the "documented to get past review"
  pattern, whatever the intent.
  THE CLASS: a three-digit all-decimal CSS shorthand colour is TEXTUALLY IDENTICAL to a dead-set
  member — `#217` the colour and #217 the issue cannot be told apart. Verified by running it:
  `_dead_refs("accent colour #217 was chosen")` returns `[217]`. The six-digit form is only caught
  because a trailing hex digit gives the lookahead something to trip on.
  NOT FIXED BECAUSE EVERY FIX IS WORSE. A context rule — ignore it after "colour", ignore it inside
  backticks — buys this at the price of FALSE NEGATIVES, and a guard that lets through the thing it
  exists to catch has failed at its job, where one that occasionally complains has not.
  PINNED INSTEAD by `test_a_short_all_digit_hex_colour_is_a_KNOWN_false_positive`, which asserts the
  current WRONG behaviour, so anyone later "fixing" it must deliberately decide whether they have
  introduced a false negative. The failure is loud — a red test naming the number — never silent.
  ⚠ Found by `platform-reviewer` at its third round, after it had already found the six-digit colour
  and two depths of HTML entity in the same pattern.

  ⛔ A FIFTH CLASS, AND IT RUNS THE DANGEROUS WAY: A SILENT FALSE NEGATIVE, ACCEPTED. The trailing
  `(?![0-9a-fA-F])` that stops `#475569` reading as an issue excludes ANY digit run abutting a hex
  letter — so `#217e` and `#908d` match nothing, and a dead reference written that way is MISSED.
  That is the guard letting through what it exists to catch.
  ACCEPTED because the ambiguity is genuine in both directions: CSS colours are 3, 4, 6 or 8
  characters, so `#217e` is itself a valid `#RGBA` colour, and there is no reading of it that is
  unambiguously a citation. What decides it is which side has occurred — `#475569` was real, in
  `docs/roles/ui_expert.md`, while a citation with no space or punctuation after the number is not
  a form anyone uses: `grep -P "#\d{1,4}[a-fA-F]"` over both guarded files matches nothing.
  PINNED by `test_a_reference_abutting_a_hex_letter_is_a_KNOWN_false_negative`, which asserts the
  wrong behaviour deliberately and shows every ordinary citation form still matches.
  ⚠ Found by `platform-reviewer` at round 4 — the mirror of the class above, undisclosed while the
  false-positive side was pinned. And then `scope-auditor` FAILed round 7 because I had pinned it
  in the test and NOT written it here: the identical defect it had FAILed in round 6 for the class
  above, repeated one round later on the next class. Recorded because that repetition is the
  finding.

  SO THE SET IS NARROWER IN ONE DIMENSION AND THE OLD GUARD WAS BROADER THERE. What decides it is
  which failure has actually occurred: the boundary flagged a live issue within hours of shipping
  (#115, his own reference issue). Nobody has ever pasted a never-before-cited GitHub number into
  these two files — the dead references got in by being COPIED FROM elsewhere in the repo, and the
  set covers everything the repo cites.
  ⚠ THE GAP IS SILENT, WHICH IS THE WORSE PROPERTY, and it is not guarded. Recorded rather than
  papered over: no test can catch it offline, because the only complete check is asking the tracker.

decisions_reserved:
  - The 292 dead references under `docs/` and 470 in memory, unchanged from `!171`.
  - Steps 4-9 of the revised plan, tracked on GitLab **#115**.

done_when:
  - Mutation-proven in both directions: a dead ref returning goes RED, and removing a set member to
    silence the guard goes RED.
  - `pytest tests/` and `ruff check .` green.

amendments:
  - none yet
