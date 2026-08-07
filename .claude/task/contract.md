# Task contract — mark the GitHub tree dormant, without touching it

> Branch `chore/mark-github-dormant` from `main` (`b5ba63a`). One PROTECTED path
> (`.github/workflows/`), so `protected_override` and `impact_map` are both declared. No
> `site_v2/src/` path is in scope, so no `acceptance_criteria`.

objective: >
  Make it impossible for a session to mistake the dormant GitHub Actions tree for the live
  pipeline, WITHOUT deleting, moving or re-pointing anything in it.

  THE PROBLEM. Eleven workflow files sit at `.github/workflows/*.yml` looking exactly as they did
  when they ran. GitHub Actions execute none of them — the account is suspended and CI moved to
  `.gitlab-ci.yml` in the 2026-08 migration. Nothing in the tree says so. The repo already has the
  convention for a retired workflow (`_paused/`, holding three), so the ABSENCE of a marker on
  these eleven positively reads as "current".

  `CLAUDE.md` makes it worse, because it is loaded into every session before anything else and
  still says "GitHub Actions for CI (`ci-validate.yml`, `ci-data-build.yml`, `ci-ui.yml`) and
  scheduled runs (`dbt-scheduled.yml`)" and "GitHub Pages for the match preview UI". Both name a
  pipeline that does not run, and neither names the one that does.

  WHY NOT DELETE OR MOVE. The CPO ruled on 2026-08-06 that the GitHub repo is KEPT and how it gets
  used is decided once account access returns. So the defect to fix is that a dormant thing is
  indistinguishable from a live one — NOT that the dormant thing exists. Nothing here edits,
  moves or deletes a single workflow file; re-activating stays a decision rather than a
  reconstruction.

  This is the last item of the collaboration-audit work. It is the "add and never retire" pattern
  in its third medium: the audit found it in rules (MR !8), in knowledge (`MEMORY.md`, Phase 2),
  and here in machinery.

amendments: >
  ONE amendment, 2026-08-06, on a clean tree, with the CPO ruling in the same conversation.

  SCOPE WIDENED to move the `## Operational notes` section (~2,300 chars) OUT of
  `.claude/active_work.md` and into `CLAUDE.md`. Both files were already in `scope_paths` for the
  original objective, so no path is added — what widens is the OBJECTIVE, from "mark the GitHub
  tree dormant" to "…and stop the handover overflowing".

  WHY IT CAME UP MID-TASK. Recording today's guard changes pushed `active_work.md` to 16,304
  characters against a hard cap of 16,000 (`handover_in.py:46`). I trimmed three times and was
  still 304 over, at which point the problem was clearly structural rather than a wording issue.

  THE ACTUAL DEFECT, which is the collaboration audit's S1-F7: the handover's own header says
  "CURRENT STATE ONLY — history belongs in git", yet its largest section is the most DURABLE
  content in the repo — the dbt CLI path, commit mechanics, the SQLFluff invocation, the
  heredoc/CWD/fnmatch traps. None of that is current state. All of it is permanent, hard-won, and
  sitting in the one file whose job is to be rewritten and which DELETES ITS TAIL when it
  overflows. So every session that learns something must delete something, and the section most
  likely to be cut is the one worth keeping.

  CPO RULING: move them. Put to him with the alternatives (keep trimming; trim now and file an
  issue) and the recommendation that trimming leaves the next session at the same wall.

  BOUNDED: this moves EXISTING text between two in-scope files and adds a pointer. It writes no
  new operational rule, and it deletes none — every note that leaves the handover arrives in
  `CLAUDE.md`, which is always loaded and never truncated.

refs: >
  GitLab issue #12 ("Post-migration residue: dormant GitHub workflows read as live, CLAUDE.md
  names the wrong CI"). Its third instance — `validate-local` still validating the retired MVP and
  mapping to GitHub job names — was already fixed in MR !8 (`b1cd6fe`), so this task covers the
  remaining two. CPO ruling of 2026-08-06 that the GitHub repo is kept and its future use
  undecided, quoted under `protected_override`.

scope_paths:
  - .github/workflows/README.md
  - CLAUDE.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

protected_override: >
  CPO instruction of 2026-08-06, in this session, in his words: *"i willkeep my githup repo and
  we'll decide how we use it once i have access again. but to move forward we are on gitlab now"*.

  That is the ruling this task implements literally — KEEP the tree, make the state legible, decide
  its use later. The approved plan ("Apply the collaboration-audit fixes, on GitLab", approved in
  plan mode 2026-08-06) was amended on the strength of that instruction, from "delete or archive
  `.github/workflows/`" to "mark, don't remove", and the amended wording is explicit: *"Files stay
  exactly where they are, unedited, so re-activating is a decision and not a reconstruction."*

  THE AUTHORITY IS NARROW AND THIS CONTRACT CLAIMS NO MORE. It covers ADDING ONE NON-EXECUTING
  FILE to `.github/workflows/`. It does not authorise editing, moving, deleting or re-pointing any
  workflow, and none is touched — `git diff --stat .github/` must show only the new README, which
  is an acceptance check stated in `done_when`.

  ON WHY THIS NEEDS AN OVERRIDE AT ALL, stated rather than assumed: a `README.md` does not execute,
  and `.github/workflows/` is protected because the files there decide what CI enforces. It would
  be easy to argue the guard does not really apply. That argument is declined. `PROTECTED_PREFIXES`
  in `task_contract_gate.py:66` is a PATH prefix, not a judgement, and `cto-reviewer` has already
  failed one task for reasoning its way out of a path-based routing requirement ("routing is
  PATH-based, not judgement-based, and the builder's reasoning was the kind that sounds sensible
  and quietly drops a required reviewer"). Putting the file one directory up in `.github/` to dodge
  the prefix was also considered and rejected: it would be a workaround, and the file belongs next
  to what it describes.

impact_map: >
  writers: none. `.github/workflows/README.md` is a new, hand-authored, non-executing file. No
    loader, model, script or workflow writes it.

  downstream: NOTHING READS IT. Evidence, run rather than assumed:
    `grep -rn "workflows/.*\.md\|workflows/README" --include=*.py --include=*.yml --include=*.mjs .`
      -> no matches.
    GitHub Actions only parses `.yml`/`.yaml` in this directory, so a `.md` file is inert to the
      platform even if the account is reactivated.
    The only code that knows the path at all is `task_contract_gate.py:66`'s `PROTECTED_PREFIXES`,
      which treats it as a protected path — which is why this contract carries an override.

  layer_rules: none apply. `check_layer_contract.py` governs `dbt_project/models/**`; this diff
    touches no dbt model, seed or raw table. Verified: `python scripts/check_layer_contract.py` ->
    "Layer contract checks passed."

  deploy_order: none. No warehouse object, no CI job, no schedule. Nothing sequences around the
    nightly. The GitLab pipeline is unchanged — `.gitlab-ci.yml` is not in scope.

  blast_radius: documentation only. No workflow file is edited, so GitHub Actions behaviour is
    byte-for-byte unchanged if the account is ever reactivated. `CLAUDE.md` changes what a session
    READS at startup, which is the point — its reach is every future session, and that is why it
    is worth getting exactly right rather than approximately.

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO. A markdown file in a directory that already contains files. No hook, script,
  workflow, job, dependency or config surface is added. The `_paused/` convention it points at
  already exists.

  RECURRING COST — NO. Nothing executes. No CI job, no runner minute, no BigQuery byte, no API
  call. `CLAUDE.md` grows by a few hundred characters, which is startup context, not spend.

  NEW EXTERNAL SURFACE — NO. Nothing is published or deployed. The README is visible to anyone who
  can already read the repo.

  GUARD INVARIANT — UNCHANGED. No guard is edited. The one guard that touches this path
  (`task_contract_gate.py`'s protected-prefix check) is not modified; it is OBEYED, by carrying
  this override.

decisions_reserved:
  - What GitHub is actually FOR now. Explicitly NOT decided here and explicitly not implied by
    this task: the README says the tree is dormant and the decision is open, and says nothing
    about mirroring, archiving, re-activating or deleting. That is the CPO's call when access
    returns, and writing a recommendation into a file that will be read as current state is how a
    provisional note becomes a decision nobody made.
  - Whether the three workflows already in `_paused/` should be treated differently from the
    eleven dormant-by-platform ones. They are dormant for DIFFERENT reasons — one by decision, one
    by the account — and the README states both without proposing a merge of the two categories.

done_when:
  - "`git diff --stat .github/` shows exactly one file, the new README, and no workflow file."
  - "`CLAUDE.md` names `.gitlab-ci.yml` as the live pipeline AND records that GitHub is retained
    and dormant — both, so a session cannot infer either one wrongly."
  - "`python scripts/check_layer_contract.py` and the other four fast gates still pass."
