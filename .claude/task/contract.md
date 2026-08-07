# Task contract — #22 + #23 + #24: three facts the August migration broke

> Branch `fix/22-23-24-migration-residue` from `main` (`930fe26`). TWO protected paths
> (`.claude/agents/platform-reviewer.md`, `.gitlab-ci.yml`), so `protected_override` AND a
> non-placeholder `impact_map` are both required and both present. Both are GUARD paths, so
> `cto-reviewer` and `platform-reviewer` are required at the **opus** floor. No `site_v2/src/`
> path, so no `acceptance_criteria`.

objective: >
  Correct three statements that stopped being true at the 2026-08 GitHub-to-GitLab migration and
  that nothing reconciles against reality.

  #22 — `.claude/agents/platform-reviewer.md` states that reviewer's territory and omits
  `.gitlab-ci.yml`. Routing DOES give platform that file, and line 31 of the same brief lists it.
  The migration updated the model-tier blockquote and missed the sentence six lines above. The
  brief is the prompt that reviewer reads, so a CI-config diff can reach a reviewer whose own
  remit statement excludes it.

  #23 — `.gitlab-ci.yml` says above `build:site-v2` that the live Pages URL keeps serving the MVP
  "until the parity cutover (#377)". That product was RETIRED 2026-07-21; there is no cutover; and
  #377 points at the GitHub tracker, which is unreachable. COMMENT LINES ONLY.

  #24 — the governance base is spelled `origin/main` in six places. `origin` is the GitHub remote,
  which is DORMANT, and `gitlab` is live. Running `check_task_artifacts.py` locally with no
  `--base` therefore diffs against a stale tree and FALSE-FAILS, naming reviewers that are not
  required. Reproduced on this branch before any edit, with zero commits on it:
    check_task_artifacts: FAIL
      - review.md diff_sha256 does not match this PR's code+contract diff ...
      - required reviewer `bi-analyst-reviewer` has no verdict section
      - required reviewer `cto-reviewer` has no verdict section
      - required reviewer `data-engineer-reviewer` has no verdict section
      - required reviewer `platform-reviewer` has no verdict section
  None of those four is required for an empty diff.

  MEASURED, because two earlier characterisations of this were wrong and the CPO corrected them:
  `origin/main` is `1f459a3` (2026-08-03), `gitlab/main` is `930fe26` (2026-08-07), and the gap is
  **27 commits spanning 2026-08-06 to 08-07**. Four days and this week's work, NOT months, and NOT
  a pre-migration snapshot. GitLab issue #24's own text carried the wrong claim and has been
  corrected on the issue.

  ⚠ GITHUB IS DORMANT, NOT RETIRED, and this contract is written to keep it that way. The CPO's
  standing position is that the repo is KEPT and how it is used is decided when account access
  returns. So: nothing here is worded as retirement; `.github/workflows/` is NOT touched (its
  `origin/main` is CORRECT inside GitHub Actions, and !9 ruled the tree stays unedited so
  re-activating is a decision rather than a reconstruction); and the fix is a reversible RUNTIME
  PREFERENCE, overridable by the `GOVERNANCE_BASE` environment variable that already exists.

refs: >
  GitLab issues #22, #23, #24. Plan approved in plan mode 2026-08-07
  (`~/.claude/plans/splendid-tickling-bumblebee.md`), then WIDENED with CPO approval (see
  `amendments`). Filed from this task and deliberately not fixed in it: #27 (`.claude/skills/**`
  carries shell but is neither protected nor routed, unlike `.claude/commands/**`).

scope_paths:
  - .claude/agents/platform-reviewer.md
  - .gitlab-ci.yml
  - CLAUDE.md
  - scripts/check_task_artifacts.py
  - .claude/skills/validate-local/SKILL.md
  - .claude/skills/onboard-competition/SKILL.md
  - tests/test_governance_hooks.py
  - tests/test_governance_doc_parity.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

protected_override: >
  AUTHORITY: `.claude/task/escalations.log`, the `2026-08-07 fix/22-23-24-migration-residue` entry,
  block `⭐ CPO RULING: PROTECTED_OVERRIDE for #22 and #23`. It records the CPO instruction verbatim
  — *"merged, now do #22, #23 and #24 together"* — and cites the two earlier rulings it builds on,
  at `escalations.log:1186` (#22 ruled into its own task) and `:1203` (#23 likewise).

  ⚠ THIS BLOCK CITED NOTHING AT FIRST, and BOTH `cto-reviewer` and `scope-auditor` FAILed round 1
  for it. It is the FOURTH instance of that defect in one session (:1156, :1238, :1287 are the
  others). Each earlier one was fixed by adding an entry, and none changed the habit. The class fix
  is recorded in the log entry itself: the log entry and the `protected_override` are written in
  the SAME action, never one after the other.

  THE AUTHORITY IS NARROW AND THIS CONTRACT CLAIMS NO MORE. On `.claude/agents/platform-reviewer.md`
  it covers ADDING `.gitlab-ci.yml` to one sentence — no hunt item, no model pin, no verdict rule.
  On `.gitlab-ci.yml` it covers REWRITING ONE COMMENT BLOCK — no job, rule, anchor, script or
  variable. `git diff .gitlab-ci.yml` showing only `#` lines is an acceptance check in `done_when`,
  not an intention.

  IT DOES NOT AUTHORISE: any edit to `.github/workflows/` (dormant, and correct as written); any
  change to the protected list or the routing table (that is #27, filed not fixed); or the
  `.claude/hooks/stop_gate.py:53` comment, which repeats the same stale spelling on a PROTECTED
  path and is left alone precisely because this override does not reach it.

impact_map: >
  Two protected paths, traced as guards rather than as table lineage.

  === .claude/agents/platform-reviewer.md ===
  fired_by: the orchestrator at review time, for any staged diff matching `platform-reviewer`'s
    routing rows. Verified against the live table: `scripts/**`, `scripts/export_*.py`, `tests/**`,
    `*requirements*.txt`, `.claude/hooks/**`, `.github/workflows/**`, `.gitlab-ci.yml`,
    `site_v2/package.json`, `site_v2/package-lock.json`, `site_v2/astro.config.mjs`,
    `site_v2/tsconfig.json`, `site_v2/firebase.json`, `site_v2/.gitignore`,
    `site_v2/integrations/**`, `site_v2/scripts/**`.
  imports: the brief names `docs/roles/platform_reliability.md`, `docs/agent_guardrails.md` and
    `docs/working_agreement.md` as its Inputs. None is edited here.
  what_stops_being_enforced_if_wrong: nothing mechanically — a brief is a prompt, it executes
    nothing. The failure is judgement: a reviewer handed a `.gitlab-ci.yml` diff while its own
    territory sentence omits that file can treat it as out of remit and pass without working its
    hunt list. `.gitlab-ci.yml` is the file that decides what CI enforces, so that is the expensive
    place for a shallow review.
  downstream_in_code: `tests/test_governance_doc_parity.py` keys a `KNOWN_INCOMPLETE` entry on the
    EXACT path set in that sentence, paired with `test_known_incomplete_lists_have_not_been_fixed`,
    which goes RED the moment the prose is corrected. So this edit FORCES that entry's deletion.
    That is the self-retiring guard from #1 working, and it is why `tests/` is in scope.
  on_failure: no runtime failure mode. A malformed brief degrades a review; it cannot break a build.

  === .gitlab-ci.yml ===
  fired_by: every GitLab pipeline. It is the CI definition.
  what_is_changed: a `#` comment block above `build:site-v2`. Comments are inert to the YAML parser.
  what_stops_being_enforced_if_wrong: nothing, PROVIDED only comment lines change. The real risk is
    an accidental edit to an adjacent job, rule, anchor or `id_tokens` block, which is why
    `done_when` asserts the diff is `#` lines only rather than trusting care.
  on_failure: a YAML syntax error would fail every job at parse time. Mitigated by the comment-only
    constraint and by the pipeline itself, which runs on the MR.

  === scripts/check_task_artifacts.py (not protected; traced because it is a GUARD) ===
  callers, enumerated with `grep -rn` rather than recalled:
    - `.gitlab-ci.yml:279` — `validate:governance`, passes `--base` EXPLICITLY. UNAFFECTED by a
      default change, and `origin` is the GitLab project inside CI, so that line stays as it is.
    - `.claude/skills/validate-local/SKILL.md:71` — local, currently passes the stale base. IN SCOPE.
    - `.github/workflows/ci-validate.yml:38` — dormant tree. NOT TOUCHED; `origin` is correct there.
    - `.claude/hooks/stop_gate.py:53` — a comment stating this script is deliberately NOT in the
      stop gate. It is not a caller. Not touched (protected, and outside the override).
  blast_radius: the default is consulted ONLY when no `--base` argument and no `GOVERNANCE_BASE`
    are given, i.e. a bare local run. Every CI invocation passes `--base`, so CI behaviour is
    byte-for-byte unchanged. Reversible: `GOVERNANCE_BASE` overrides it, and the preference is one
    function.

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO. No new hook, job, stage, agent, routing row, skill or dependency. One
  existing script's DEFAULT becomes computed instead of hardcoded, using `subprocess`, which the
  file already imports (`:35`).

  RECURRING COST — NO. Nothing new executes. THREE added unit tests in the existing suite and job
  (`default_base` preference, the `GOVERNANCE_BASE` override, and the git-unavailable fallback).
  This said "one" until both reviewers counted; corrected against the diff, not from memory.

  NEW EXTERNAL SURFACE — NO.

  GUARD INVARIANT — CHANGED, DECLARED, AND NARROWED RATHER THAN LOOSENED. `check_task_artifacts.py`
  is a guard, and its default base changes. It is a NARROWING: today the bare command compares
  against a 27-commit-stale tree and returns a WRONG answer; after this it compares against the
  live one. No check is removed, no threshold relaxed, and a test pins the new resolution. The
  `GOVERNANCE_BASE` escape hatch is unchanged.

  THE GITHUB POSITION IS NOT CHANGED BY THIS TASK. GitHub stays dormant-not-retired. Nothing here
  decides its future, and `.github/` is untouched.

decisions_reserved:
  - Whether `.claude/skills/**` should be protected and/or routed, given that all four skills carry
    shell and `.claude/commands/**` is protected for exactly that reason. Filed as #27 and
    deliberately NOT decided here: it is a rule extension and a recurring cost, two of the CTO's
    four thresholds. This branch touches no routing row and no protected list.
  - Whether `.claude/hooks/stop_gate.py:53`'s stale `origin/main` mention should be corrected. It
    is prose on a PROTECTED path, outside this override's stated reach. Left alone rather than
    swept in, because widening an override by judgement is the defect #18 describes.

done_when:
  - "`git diff main -- .gitlab-ci.yml` shows ONLY comment lines. No job, rule, anchor, script or
    variable is altered."
  - "The bare `python scripts/check_task_artifacts.py`, with no `--base`, is run BEFORE and AFTER
    and both outputs pasted. Before: FAIL naming four reviewers that are not required. After: the
    correct result for the branch."
  - "The new default-resolution test is made to FAIL against the hardcoded default first, red
    output pasted, then passes. A passing test proves nothing."
  - "`test_known_incomplete_lists_have_not_been_fixed` is observed going RED after the #22 fix and
    BEFORE its entry is removed, pasted as evidence the paired guard fired."
  - "`git grep -n 'origin/main'` shows the remaining hits are only: `git_discipline.py` (its base
    fallback tries local `main` FIRST, so it is already correct), `stop_gate.py:53` (out of this
    override's reach, recorded under `decisions_reserved`), `check_task_artifacts.py` (the new
    resolver's own GitHub-primary fallback), and records describing the defect.
    ⚠ `.gitlab-ci.yml` and `.github/workflows/` do NOT appear in that grep, and an earlier draft of
    this line wrongly predicted they would. They interpolate the branch
    (`origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-main}`) rather than writing the literal string.
    Both are still correct as they stand and neither is touched; the expectation was wrong, not
    the tree. Corrected after running the sweep rather than before."
  - "Full suite green at 648 collected: 645 on `main`, plus THREE new tests, and the
    `KNOWN_INCOMPLETE` parametrisation goes from one case to a skip when the dict empties (net
    +3). MEASURED with `pytest --collect-only -q`, not predicted. This line said '645 plus the one
    new test' until the count was actually run — the same #904 class the previous task flagged
    against itself, repeated here."
  - "The five offline gates pass."

amendments: >
  ONE amendment, 2026-08-07, taken BEFORE any file was edited, so the tree was clean by
  construction. SCOPE WIDENED by three paths: `.claude/skills/validate-local/SKILL.md`,
  `.claude/skills/onboard-competition/SKILL.md`, and (already implied by #22) the two test files.

  WHY. The approved plan named three #24 sites, taken from the issue text. A `git grep` sweep of
  the whole tree found SIX. The three extra are in `.claude/skills/**`, which is NOT protected, so
  this widens the task by ordinary text files and adds no protected surface.

  THE WORST OF THEM WAS NOT IN THE ISSUE: `.claude/skills/onboard-competition/SKILL.md:137` runs
  `git checkout -B feat/onboard-{league} origin/main`, which starts a new competition on a tree 27
  commits behind. A different symptom of the same root cause, and more damaging than the false-FAIL
  the issue was filed about.

  AUTHORITY: `.claude/task/escalations.log`, same entry, block `⭐ CPO RULING: SCOPE WIDENED from
  three sites to six`. It records the finding, the recommendation as put, and the CPO's answer —
  *"fix all six, and file the skills gap"* — plus the measured 27-commit gap and the
  dormant-not-retired position. The skills gap is filed as #27. This block, like the override
  above, cited nothing until both reviewers failed it.
