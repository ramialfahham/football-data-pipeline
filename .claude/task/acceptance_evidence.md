# Acceptance evidence — a stash left behind blocks the turn

Every claim below was produced by RUNNING the hook or its tests, not by reading them. Round 2:
the `TEMP-`/24h exemption is gone, so the evidence was re-run from scratch rather than patched.

criteria_demonstrated:
  - ANY STASH BLOCKS. Against the real repo: created `parked: some real work`, invoked
    `stop_gate.py` the way the harness does (`echo '{}' |`) → `decision: block`, reason
    `STOP GATE (parked work): the stash holds work that should not be there at turn end:
    stash@{0}: … parked: some real work`, and the message names `parked/<name>` as where it goes.
    Pinned by `test_stop_blocked_by_a_parked_stash_even_on_a_clean_tree`.
  - A `TEMP-` STASH BLOCKS TOO. `test_stop_blocks_a_temp_stash_too` parks `TEMP-contract-amend`
    and asserts the block names it. MUTATION, on a scratch copy of the hook (the classifier
    refuses a deliberate weakening of the real file, correctly): re-adding a `"TEMP-" not in
    line` filter → that test and only that test goes RED (11 passed, 1 new failure).
  - AN EMPTY STACK PASSES SILENTLY. Invoked the real hook with 0 stashes → empty output. Pinned by
    `test_stop_passes_on_an_empty_stash`, which asserts the empty stack as a precondition.
  - ⭐ THE CHECK RUNS ON A CLEAN TREE, PROVEN BY MUTATION. Moved the parked-stash block to AFTER
    the `_dirty_outside_task_dir` short-circuit in `main()` on the scratch copy → **3 new
    failures**: both behavioural tests (a clean tree with a stash no longer blocks) AND the
    structural test (`test_stop_stash_check_precedes_the_dirty_tree_short_circuit`, which asserts
    the call order by reading `main()`'s source). A second mutation, `parked = []` (check
    disabled), fails the same three. The structural test exists so the failure names its cause.
  - EXISTING BEHAVIOUR UNCHANGED. The three pre-existing stop-gate tests (out-of-scope blocks,
    clean passes, never loops) and the five `test_stop_gate_*` correctness tests still pass:
    `-k stop_` → 14 passed in the real tree. Full `tests/test_governance_hooks.py` on the round-2
    code: **302 passed in 358.64s**.

## done_when, beyond the criteria

- ruff clean on both changed files under CI's ruleset (`--config .ruff-ci.toml`): "All checks
  passed!". (Bare `ruff check` without that config reports 40 pre-existing findings across the
  two files under a broader ruleset; CI's is the binding one.)

## Mutation runs, verbatim

```
[baseline]        2 failed, 12 passed   (the 2 are test_ci_backstop_*, which read repo files the
                                         scratch copy does not carry; 14 passed in the real tree)
[exemption_back]  3 failed, 11 passed   +test_stop_blocks_a_temp_stash_too
[ordering]        5 failed,  9 passed   +blocked_by_a_parked_stash, +blocks_a_temp_stash_too,
                                        +stash_check_precedes_the_dirty_tree_short_circuit
[check_disabled]  5 failed,  9 passed   same three
```

## Why the ordering is the whole design

`FAST_GATES` is skipped on a clean tree to save ~2.9s per conversational turn. A forgotten stash
leaves the tree CLEAN. So a stash check placed with `FAST_GATES` — the obvious place, where the
other five checks live — would never fire on the one case it exists for. That is why it is a
separate call, first in `main()`, at ~10ms unconditionally.

## Why there is no exemption (removed in round 1)

The first draft let a `TEMP-` stash pass for 24h "or every contract amendment becomes impossible".
False: the stash-dance stashes, edits and pops inside ONE turn, and this gate fires at turn END —
it never sees a dance that completed. The only `TEMP-` stash it can see is a forgotten one, which
is the #41 case it should catch. And the CPO was never shown the exemption: the explanation he
said "yes" to reads "if you end your turn with something still in the pocket, you get stopped" —
unconditional. The rule shipped is the rule approved.

## The ten stashes, converted before this branch — verified, not assumed

Each became `parked/<original branch>` pointing at the stash COMMIT, so all three parents (base,
index, untracked) are reachable and `git stash apply parked/<x>` restores it exactly. Before
dropping: every one of the ten stash SHAs confirmed as a remote branch tip. After: `git stash list`
= 0, and `git branch -r --list 'gitlab/parked/*'` lists exactly ten. Dispositions (5 live, 5 dead
or superseded) are in `escalations.log` `2026-09-11 feat/stash-check-in-stop-gate`.

⚠ ONE CORRECTION MADE DURING THE WORK. I told the CPO `stash@{5}` held the built player Overview
tab, then briefly concluded it did not, because its CHANGED tracked files were only supporting edits.
The tab's eleven files are untracked and live in the stash's THIRD parent — `git stash -u` puts them
there. Checked, found, and the recovery command records where to look.

## What is NOT demonstrated

- That the hook fires in the live harness on the next real turn end. It fires in the test harness
  invoked identically; the live harness is the same script on the same stdin contract.
- That anyone follows the block message. The hook blocks ONCE (`stop_hook_active`) by design — a
  loud net, not an impassable one, like the two checks already there. That is also what makes a
  stash this session cannot pop (another worktree's — the stack is repo-wide) a one-time nag.
