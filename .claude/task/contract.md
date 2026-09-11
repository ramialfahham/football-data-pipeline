# Task contract — a stash left behind blocks the turn

objective: >
  Ten pieces of parked work sat in `git stash` — a store nothing lists, no gate sees, and one
  keystroke empties — including the whole player Overview tab, which memory had already written
  off as lost. All ten are now pushed `parked/*` branches and the stack is empty. This branch adds
  the mechanism that keeps it empty: the stop gate blocks a turn that ends with parked work in the
  stash.

refs: >
  `.claude/task/escalations.log` `2026-09-11 feat/stash-check-in-stop-gate` — the CPO's "yes" to
  editing the protected stop gate, after the plain-language explanation he asked for.
  Step 4 of the context cleanup as GitLab #115 numbers it ("4 — where parked work lives"; "5 —
  split `escalations.log`"). ⚠ The 2026-09-10 log entry that first listed the nine steps had those
  two the other way round; #115 is the tracker and supersedes it. Steps 1-3 merged as `!169`-`!172`.
  Precedent for a protected-path edit to this file: `check_description_hygiene.py` was added to
  `FAST_GATES` on 2026-08-20 "with CPO approval for the protected-path edit".

protected_override: CPO approved editing `.claude/hooks/stop_gate.py` on 2026-09-11 — asked
  directly, in plain language, and answered "yes". Recorded in `escalations.log` under
  `2026-09-11 feat/stash-check-in-stop-gate`.

scope_paths:
  - .claude/hooks/stop_gate.py
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log

impact_map: >
  writers: one hook (`.claude/hooks/stop_gate.py`), one test file. No model, mart, export, site
    source or CI config.

  downstream: the Stop hook fires at the end of every agent turn. It does NOT run in CI. Nothing
    else reads it.

  blast_radius: a NEW BLOCKING CONDITION on ending a turn. Today the gate blocks on out-of-scope
    dirty files and on failing offline checks; after this it also blocks when the stash holds
    ANYTHING — the rule exactly as the CPO was told it: "if you end your turn with something still
    in the pocket, you get stopped". No label is exempt. The contract stash-dance is not affected:
    it stashes, edits and pops inside ONE turn, and the gate fires at turn END — so the only
    stash-dance the gate can see is a forgotten one, which is the #41 case it should catch. Like
    the two existing conditions it blocks ONCE (`stop_hook_active`), so a stash this session cannot
    pop — another worktree's, since the stack is repo-wide — costs one nag, not a wall. The check
    runs BEFORE the dirty-tree short-circuit, because a forgotten stash leaves the tree clean —
    that is the exact case it exists for.

  deploy_order: none.

acceptance_criteria:
  - Any stash blocks the turn, with a message that names the stash and says to put it on a
    `parked/` branch. Proven by creating one and running the gate.
  - A `TEMP-` stash blocks too — there is no label exemption. Proven by a test, so the exemption
    the first draft carried cannot come back silently.
  - An empty stash list passes with no output. Proven.
  - The check runs even when the tree is clean — a mutation that moves it below the dirty-tree
    short-circuit turns a test RED.
  - The gate's existing behaviour is unchanged for the cases it already handled; the existing
    governance-hook tests stay green.

decisions_taken: >
  A STASH IS NOT A STORE, AND THE RULE IS ENFORCED, NOT WRITTEN. `working_agreement.md` could say
  "park work on a branch"; the point of this cleanup is that written rules have not held. The stop
  gate already holds the line on dirty trees and failing checks; this is the same instrument.

  NO EXEMPTION. The first draft exempted `TEMP-` stashes for 24 hours, on the premise that the
  contract stash-dance would otherwise be blocked. The premise was false — the dance is intra-turn
  and the gate is turn-end — and the CPO was never shown the exemption: the explanation he said
  "yes" to states the rule unconditionally (cto-reviewer, round 1). Removed. The rule shipped is
  the rule approved, and it is stricter: `TEMP-40-mrB` sat under that label for days "until the
  mart column is in prod", which the 24h window would have tolerated for a day.

  IT RUNS FIRST, BEFORE THE DIRTY CHECK. `FAST_GATES` is skipped on a clean tree to save 2.9s per
  conversational turn. A forgotten stash leaves the tree CLEAN — so a check placed with
  `FAST_GATES` would never see the case it exists for. `git stash list` costs ~10ms and runs
  unconditionally.

  THE TEN EXISTING STASHES WERE CONVERTED, NOT DELETED. Each is a pushed `parked/<original
  branch>` branch pointing at the stash commit, so all three parents — base, index, untracked —
  are reachable and `git stash apply parked/<x>` restores it exactly. Verified before dropping:
  every stash commit's SHA is a remote branch tip. Five of the ten are dead or superseded and are
  branches the CPO can delete at leisure; the dispositions are in `escalations.log`.
  THE SEQUENCE, plainly — AND NOT DRESSED AS APPROVED: the CPO approved the PLAN on 2026-09-10
  ("do as recommended", log entry `2026-09-10 chore/dead-issue-references`), which listed "where
  parked work lives — the 10 stashes ... [NEW]" as a step. That entry says nothing about the
  steps' content. The EARLIER entry that day, `2026-09-10 chore/authority-map-in-claude-md`,
  recording his "go" on the original six-step plan — before the stash step existed — says: "NOT
  A RULING ON ANY OF THE SIX STEPS' CONTENT. He approved the plan and told me to start; each
  step's own decisions are still his." I read that limit as carrying to the revised plan (a
  re-ordered checklist approved with "do as recommended" is no more a content ruling than the
  original approved with "go"), but that is MY reading; no entry disclaims content-approval for
  the revised plan in so many words. Either way: he did not approve the step's CONTENT.
  Converting each stash to a pushed `parked/*` branch and dropping it was MY choice,
  taken on my own initiative under the autonomy rule for a non-destructive, reversible action
  (each stash commit verified a pushed branch tip before its drop; all ten branches exist), and
  told to him afterwards in the same message as the ask for this gate. He answered the ask; he
  did not rule on the conversion, and this contract does not claim he did. Merging this MR is
  where he can. The live/dead split is a LABEL on a decision reserved to him, not an action taken.

  THRESHOLD — NEW MECHANISM: yes, one new blocking condition in an existing protected gate.
  Approved by the CPO, recorded. Routed to cto-reviewer and platform-reviewer by
  `review_routing.json`.
  THRESHOLD — RECURRING COST: ~10ms per turn end.

decisions_reserved:
  - Deleting the five dead/superseded `parked/*` branches. They are the CPO's to delete; the
    dispositions are recorded so he can.
  - Steps 5-9 of the cleanup (GitLab #115).

done_when:
  - All five criteria proven by running the gate against real stashes and by the tests.
  - `pytest tests/test_governance_hooks.py` green, ruff green.

amendments:
  - Round 1 (cto-reviewer FAIL, scope-auditor FAIL, platform-reviewer PASS). Three changes, none
    widening scope: (1) the `TEMP-`/24h exemption is REMOVED — the CPO was not shown it and its
    premise was false (above); the two acceptance criteria that described it are replaced by one
    that pins its absence. (2) "six" dead/superseded branches corrected to FIVE, in all three
    places the miscount appeared — the log's own enumerated list has five (scope-auditor). (3) the
    step number is disambiguated against #115, whose numbering supersedes the log's.
    Two findings answered with evidence rather than a change: this IS step 4 per #115 (the
    reviewer read the superseded numbering in the previous branch's contract text); and the
    conversion was not destructive — sequence recorded above. The self-attestation of
    `escalations.log` stands as recorded: it is what #115 step 5 exists to fix, and until then
    the CPO's merge of an MR that carries the entry is the verification.
  - Round 2 (cto-reviewer FAIL, platform-reviewer PASS, scope-auditor PASS). The round-1 answer
    on the conversion had put "a stash is not a store" in quotation marks as the recommendation
    the CPO said "do as recommended" to. The phrase IS in that recommendation — in the transcript
    — but the 2026-09-10 log entry does not carry it, so to a reviewer it read as a quote the
    source does not contain; and the deeper point holds regardless: "do as recommended" approved
    the plan, not the step's content, as that entry says itself. Rewritten (above) to state that
    the conversion was my own initiative under the autonomy rule, told afterwards, not approved;
    the recommendation text is now logged verbatim and attributed as MINE, not his. Also: the
    evidence file's `criteria_demonstrated` carried six bullets against five criteria (the ruff
    line belongs to `done_when`) — moved, since the artifact gate counts them.
  - Round 3 (cto-reviewer FAIL, scope-auditor FAIL, same finding). The round-2 rewrite cited
    "each step's own decisions are still his" as said by the entry that records "do as
    recommended". It is said by the EARLIER entry that day, about the original six-step plan,
    before the stash step existed. The seventh instance this session of citing a real sentence
    to the wrong place — inside the paragraph written to cure the sixth. Fixed above: each quote
    now names its entry, and the carry-forward to the revised plan is stated as my reading, not
    as something the record says. Every quote in this contract was then grepped against the log
    for the entry it names. Round 4 runs under a `rounds_cap_override` in `review.md`, recorded
    the way `!172` recorded it: to clear a standing FAIL by review, not to ship past one.
