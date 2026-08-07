# Task contract — #29: the post-commit hook must check whether the MR is OPEN, not whether one exists

> Branch `fix/29-post-commit-mr-state` from `main` (`c5d6088`). Neither scope path is PROTECTED
> (`.githooks/` is absent from `PROTECTED_PREFIXES`, `task_contract_gate.py:66`) and neither is on
> the structural surface, so no `protected_override` and no `impact_map`. No `site_v2/src/` path,
> so no `acceptance_criteria`. A commit touching `contract.md` is NEVER artifact-exempt, so this
> still takes a scope audit.

objective: >
  Make `.githooks/post-commit` open a merge request when the branch has no OPEN one, instead of
  reporting success because some MR exists.

  THE DEFECT. The hook resolves an MR for the branch and prints "MR already open" whenever it
  finds one, never checking its state. On 2026-08-07 it printed `MR already open: !16` while !16
  was `state: merged`. Two commits carrying three CPO rulings then sat on the branch with no MR,
  and `main` kept a handover the CPO had already corrected. It was caught by a CI timestamp
  reading as older than the commits, which is luck, not a check.

  WHY IT IS WORSE THAN "NO MR OPENS". The hook exists so that working agreement §3 ("the task is
  not done until you open the MR") cannot be forgotten. A hook that reports a URL when nothing is
  open makes the builder believe step 4 is done and stop looking. That is the fail-open class the
  collaboration audit collected, not a missing feature.

  WHY THE MECHANISM DIFFERS FROM THE ONE #29 PROPOSED. #29 suggested checking `.state` on
  `glab mr view`. Measured against the live project first: `glab mr view <branch>` cannot answer
  at all when a branch carries more than one MR (exit 1, and a JSON error object written to
  STDOUT, not stderr, so `2>/dev/null` does not suppress it and a `-n` test passes on a failure).
  That is not hypothetical — `chore/handover-after-22-23-24` is in that state right now.
  `glab mr list --source-branch` DEFAULTS to open MRs, returns `[]` with exit 0 when there are
  none, and is unaffected by how many merged MRs the branch carries. It answers the question
  directly rather than inferring it. The CPO approved the deviation at plan time.

refs: >
  GitLab #29. First item of the AI-collaboration audit stream (handover `NEXT` step 1, CPO ruling
  2026-08-07). Order confirmed by the CPO this session: #29, then #25, then #21 brought as a
  recipe. Cost is a SEPARATE stream and is explicitly out of this session.

scope_paths:
  - .githooks/post-commit
  - tests/test_post_commit_hook.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO, with one thing named rather than left implicit. The hook already existed and
  already decided whether to open an MR; this corrects the predicate it decides on. What IS new is
  that `tests/test_post_commit_hook.py` is the FIRST test in this suite to shell out to `bash`.
  That is coverage for existing machinery, not a new guard, and it was declared in the plan and
  approved by the CPO before any file was touched. Naming it here so `cto-reviewer` rules on the
  classification rather than discovering it.

  RECURRING COST — NO. The hook makes one `glab` API call per commit before and after. The test
  adds four `bash` subprocess spawns per CI test run, no network (both `git` and `glab` are
  stubbed), sub-second. No new service, no new infrastructure, no schedule.

  NEW EXTERNAL SURFACE — NO. Same CLI, same project, same single call.

  GUARD INVARIANT — STRENGTHENED, never loosened. The hook's old predicate returns a confident
  wrong answer ("already open") on a merged MR. The new one can only be wrong in the direction of
  attempting `glab mr create` when an MR is in fact open, which fails loudly and visibly. Every
  failure path — list call errors, empty result, unparseable output — now falls to CREATE. There is
  no input for which the new code claims an MR is open and none is.

  WHY A BEHAVIOURAL TEST AND NOT A TEXT ASSERTION. `tests/test_materialisation_policy.py` records
  the lesson directly: a guard that names its targets in prose is nearly inert, because a reword
  silently defeats it. This test runs the hook and asserts whether `glab mr create` was reached.

decisions_reserved:
  - "`.githooks/**` is neither a PROTECTED path nor routed to any reviewer, while
    `.claude/commands/**` is PROTECTED + routed on the CPO's reasoning (2026-06-14) that anything
    auto-launching a command is command-class. A git hook auto-launches a command on EVERY commit
    and pushes to the remote. Whether the protected set should cover it is §10 (the protected set
    is a guard invariant and a recurring review cost). This is the same finding as GitLab #27
    (`.claude/skills/**`), so it is going there as a comment rather than being built here or filed
    twice. NOT decided in this task and NOT in scope."
  - "Whether pushing new commits to a branch whose MR already MERGED should warn at all. #29 calls
    this a separate call. It costs an extra API call per commit, which is a cost question. Not
    done here."

done_when:
  - "`tests/test_post_commit_hook.py` FAILS against the unfixed `.githooks/post-commit` and PASSES
    against the fixed one. BOTH runs pasted — a test that was never seen red is decoration
    (`feedback_verify_the_test_fails.md`)."
  - "The test covers four cases driven by payloads measured from the live API, not invented: an
    OPEN MR (create must NOT run), a branch whose only MR is merged (create MUST run), a branch
    with no MR at all (create MUST run), and the list call failing (create MUST run)."
  - "`python -m pytest tests/ -q` is clean and the collected count is MEASURED with
    `pytest --collect-only -q`, never predicted (#904; three contracts in one day shipped a wrong
    predicted count)."
  - "The five offline gates pass, and `check_task_artifacts.py` is run BARE (it resolves the live
    remote itself since !15; passing `--base` by hand is the retired workaround)."
  - "LIVE, on this branch's own commits: commit 1 fires the hook with no MR on the branch and must
    OPEN one; commit 2 fires it with that MR now open and must print `MR already open` with the
    real URL. Both hook outputs pasted. The merged-MR path stays covered by the TEST, not live,
    because reproducing it live means pushing to a merged branch — stated rather than claimed as
    end-to-end."

amendments: (none)
