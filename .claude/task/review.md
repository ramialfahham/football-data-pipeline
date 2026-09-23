# Review — chore/wide-design-check-and-handover-home — 2026-09-23

diff_sha256: 0bf679c1b8da735a58aaa61c83523aa2596f1ea81a15de896a34dc06c0c3b65f

rounds: 2

Round 1: scope-auditor FAIL, platform-reviewer FAIL (opus), cto-reviewer FAIL (opus),
bi-analyst-reviewer PASS. Every finding was real. The scope auditor found the impact map claiming a
complete sweep of the old handover file's readers and missing `.gitlab-ci.yml:1123`; the re-sweep
found two more (`design-mocks/section_sizes.py`, a comment in `scripts/sync_metric_docs_blocks.py`).
The platform reviewer found a search field REMOVED from the page, rather than hidden, still passed;
the hook's timeout untested; one old test calling the real GitLab; and a cache that could be left
half written. The CTO found that moving the handover to a public issue drops the host-address
check that guarded it as a tracked file, undeclared. Round 2 amended the contract on a clean tree
and fixed all of it; every new test was seen RED against the mutation it guards. All four PASS.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL closed: the impact map lists every mention of the old file with its disposition, including `.gitlab-ci.yml:1123` and `:455-456` as protected and knowingly left, and the owed resource-group follow-up carried into issue #157.
- The amendment is dated, made on a clean tree, names its authority as the approved move (not a new decision) and credits the round-1 reviewers; the two added paths are readers of the deleted file.
- Each amendment claim checked against the diff: `section_sizes.py` reads an argument or the cache; the `sync_metric_docs_blocks.py` comment states the finding instead of citing the dead file; the hook's atomic write and empty-cache rule; `check_handover.py`'s address and size refusal; `CLAUDE.md`'s chained session-end command.
- Protected-path override quoted in `decisions_taken`; new mechanism and the render growth declared; no credential-shaped text; every file inside `scope_paths`.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Finding 1 closed: Expect entries take the width condition (`_split_when`, `Page.expected_at`), the check loops over `page.expected_at(viewport)`, every built row expects the search field at >=1010px and the button below; `test_a_search_field_removed_from_the_page_fails` proves both directions and went RED with the Expect loop mutated away.
- Finding 2 closed: `test_a_hanging_gitlab_read_times_out` loads the hook in-process with a 1s timeout and a sleeping fake `glab`; RED with `timeout=` removed. On Windows the fake's child process makes it take ~5s; the real `glab.exe` has no child.
- Finding 3 closed: the fail-open parametrize hands `handover_in.py` a failing fake `glab`, so it never reaches the network and runs the same path everywhere.
- Finding 4 closed: temp file plus `os.replace`; a whitespace-only cache counts as none (RED with the check removed); `.gitignore` covers `.claude/handover.cache.md*`.
- The hook still fails open; `check_handover.py` only reads and stops the `&&` chain on any failure; the two docstring-level files change no machinery.
- Round 1, unchanged since: the width-condition parser fails closed with boundary tests at 1009/1010; the text-line counter change is pinned by the green fixture at 1010px; the 1010 width is tied to `system.css` by a test; no dependency, credential, hosting or build change; +50% renders as declared.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL closed: `check_handover.py` imports the gate's own `flagged_lines`, exits 1 on an address or an oversize draft, and its failure modes stop the publish; tested with the address assembled at run time.
- The loss is declared: the impact map names the lost coverage, its replacement, that it is a step in a command and not a hook, and that CI still catches a leak afterwards through the tracker backup.
- No new mechanism in round 2: an existing script and the existing gate's patterns; the atomic write, empty-cache rule and Expect width condition are implementation of what was approved.
- The hook fails open (exception, hang, missing `glab`); the 15s timeout is pinned by a test.
- `protected_override` and its quote unchanged; no new protected path opened; the two stale `.gitlab-ci.yml` comments disclosed, not edited; no dependency change; no new recurring cost beyond round 1. Advisory carried to the MR head: state the measured change in CI minutes.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1: the three element rows traced against `SiteHeader.astro`, `system.css` (hidden below 1010px, shown from it; the button the reverse, 36px against a 34px floor) and `09_chrome.md`; nothing invented, no existing rule changed.
- Round 2 delta: the three rows are byte-identical; all seven built rows gained `Search field [>=1010px], Search button [<1010px]`, no mock row touched; the new Expect prose traced into `Page.expected_at` and the check's loop, and it closes the removed-element gap independently of `inDom`.

## escalations
(none)
