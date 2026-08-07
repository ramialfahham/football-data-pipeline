# Task contract — connect the guards that were built and never wired

> Branch `chore/wire-the-unwired-guards` from `main` (`cbd81aa`). Six PROTECTED paths, so
> `protected_override` and `impact_map` are both declared. No `site_v2/src/` path is in scope,
> so no `acceptance_criteria`.

objective: >
  Wire the guards this repo already owns and does not run, and make the two that fail silently
  say so.

  THE PATTERN, from the collaboration audit. Every item here is the same defect wearing
  different clothes: the guard was BUILT, is CORRECT, and is invoked by NOTHING. The audit found
  three separately-built working guards connected to nothing; `inventory.py` reproduces the list
  mechanically. This is the cheapest class of fix in the repo — the engineering is already done.

  SIX ITEMS:
  1. `check_copy_gate.py` runs in no CI job and no skill. Wire it into `.gitlab-ci.yml`
     `validate:governance` and into the `validate-local` skill. Its 16 findings on `main` were
     cleared in PR !7, so this cannot redden the default branch — verified: the gate exits 0 on
     `cbd81aa`.
  2. The same gate ADVERTISES an exemption it never implemented: its message offers "the value
     needs a comment saying so", but check 4 parses no comment. Found in PR !7 when a CPO ruling
     that relied on it proved impossible to satisfy. A gate that promises an escape hatch it
     does not have will be worked around by changing the copy instead — which is how a
     legitimate identical string gets mistranslated to please a checker.
  3. `stop_gate.py` asks only "is the tree in scope?" — a governance question. Nothing verifies
     CORRECTNESS at turn end. Add the fast offline gates. Measured at 2.9s for all five, against
     5m07s for `tests/test_governance_hooks.py`, which is why the full suite is NOT used.
  4. Reviewers are handed a patch that is ~89% generated JSON. `review_exclude_paths` already
     exists and simply does not cover `site_v2/src/data/**`.
  5. `scope-auditor` runs `haiku`/`medium` while reviewing every diff and holding the sole
     enforcement for undeclared thresholds and secrets. Move to `sonnet`.
  6. The commit gate fails open SILENTLY. Keep the house rule, add a canary so a dead gate is
     visible instead of indistinguishable from a satisfied one.

refs: >
  GitLab issues #5 (Confirm step), #7 (copy gate — CLOSED by PR !7, this wires it), #8 (turn-end
  correctness), #9 (review payload), #10 (scope-auditor model), #11 (fail-open canary).
  PR !7 (`4844c32`) cleared the copy gate's findings and is the precondition for item 1.
  Item 2 was recorded as a follow-up in PR !7's `review.md` under "builder findings, not fixed
  here", and in that contract's `amendments:`.

scope_paths:
  - .gitlab-ci.yml
  - scripts/check_copy_gate.py
  - .claude/hooks/stop_gate.py
  - .claude/hooks/git_discipline.py
  - .claude/review_routing.json
  - .claude/agents/scope-auditor.md
  - .claude/skills/validate-local/SKILL.md
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - .claude/agents/cto-reviewer.md
  - tests/test_governance_hooks.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

protected_override: >
  CPO approval of 2026-08-06, in this session, for the plan titled "Apply the collaboration-audit
  fixes, on GitLab" — approved via plan mode after a written plan-back that named every item
  below and stated outright that the work touches protected paths and would need
  `protected_override`, an `impact_map`, and cto+platform review at the opus floor.

  THE AUTHORITY IS FOR THIS SET, NOT A STANDING ONE. It covers exactly the six items in
  `objective:` and the paths in `scope_paths:`. It does not authorise any further guard change.

  THE SCOPE NARROWED SINCE APPROVAL, and narrowing is reported rather than assumed: the approved
  plan's item 1 was a NEW push-to-main hook in `.claude/hooks/`. That is no longer needed and is
  NOT in this contract — `~/.claude/hooks/branch_discipline.py` already implements it, verified
  by execution (denies `git push gitlab main` and `HEAD:main`, allows a feature-branch push), and
  it was registered in the user-level settings instead. A protected-path edit was avoided
  entirely.

  The CPO separately chose, in the same session, to keep the GitHub repo and leave its dormant
  workflows untouched. `.github/workflows/**` is therefore NOT in scope here.

impact_map: >
  This is a GUARD change, so the trace is what depends on the guards rather than table lineage,
  per TEMPLATE.md. Evidence gathered by running the commands, not from memory.

  which events fire them:
    `.claude/settings.json` — `git_discipline.py` on PreToolUse(Bash); `stop_gate.py` on Stop
    with no matcher (so it fires on every turn end, including after `/compact`).
    `.gitlab-ci.yml` — `validate:governance` runs on every pipeline except schedules.

  what imports from them (`grep -rn "from .* import" .claude/hooks/`):
    `stop_gate.py` imports `_dirty_outside_task_dir`, `_is_protected`, `_matches_scope`,
      `_read_contract`, `_repo_root` FROM `task_contract_gate.py`, plus `read_event` from
      `_command_utils`. So a change to stop_gate cannot break task_contract_gate, but the
      reverse is true — and task_contract_gate is NOT in scope here.
    `git_discipline.py`, `git_workflow.py`, `dbt_layer_gate.py`, `task_contract_gate.py` all
      import from `_command_utils.py`, which is NOT in scope here.
    Nothing imports from `stop_gate.py`.

  what stops being enforced if each is wrong:
    `git_discipline.py` — the commit gate. If broken, commits proceed with no review
      verification. This is the single most load-bearing guard in the repo, which is why the
      change to it is additive only: the canary adds output on the EXISTING exception path and
      alters no decision. `git_discipline` carries 53 test references today.
    `stop_gate.py` — the turn-end net. If broken, an out-of-scope tree survives a turn. Only 5
      test references today, the weakest coverage of any gate being touched; new tests are in
      scope for that reason.
    `review_routing.json` — if unparseable, `_load_routing` returns None and the review
      requirement is disabled ENTIRELY (fail open). A JSON syntax error here silently switches
      off the blinded review cycle, so the edit is one array entry and is validated by
      `json.load` before commit.
    `scope-auditor.md` — frontmatter only. A malformed `model:` value would fail the spawn.
    `check_copy_gate.py` — currently enforces nothing anywhere; after this it gates CI.

  what happens on failure:
    Every hook here fails OPEN by house rule (`_command_utils.py`). That is the defect item 6
    addresses for the commit gate, not one it introduces.
    `validate:governance` is a blocking CI job, so a copy-gate false positive blocks every MR.
    Mitigated by the gate having run clean on `main` at `cbd81aa` (`exit=0`, 354 strings) before
    being wired.

  CI-side recheck: `scripts/check_task_artifacts.py` recomputes the review hash on every MR
    (`.gitlab-ci.yml:272`), so a locally-bypassed commit gate is still caught there.

  blast_radius: no warehouse object, no dbt model, no mart, no user-visible string, no URL.
    `python scripts/check_layer_contract.py` -> "Layer contract checks passed." No number a
    reader sees changes. The reach is entirely over future TASKS in this repo, which is wider
    than most model changes and is why these paths are protected.

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field and `scope-auditor` FAILs an
  undeclared crossing.

  NEW MECHANISM — YES, ONE. The first version declared TWO; the second was WITHDRAWN in review,
  not approved (see (B)).

  (A) A SECOND ROUTING KEY, `review_summarise_paths`, for item 4. CPO-APPROVED 2026-08-06, in
  this session, AFTER `cto-reviewer` at opus correctly refused to rule on it — §10 reserves new
  mechanisms to the CPO, and §2 step 3 says a reviewer never approves a §10 decision, so asking
  the reviewer to bless it (as the first version of this contract did) was asking the wrong party.
  The ruling is recorded durably in `.claude/task/escalations.log`; this is a pointer, not the
  record.

  WHAT THE CPO WAS TOLD, in plain terms, before ruling: reviewers are handed a file of which ~9
  lines in 10 are machine-generated sample data nobody reads; the approved plan said DELETE those
  lines; deleting them outright would also stop `bi-analyst-reviewer` knowing the data changed,
  which silently breaks its check that a displayed field exists in the exported sample; so the
  built version deletes them AND leaves a manifest naming the changed files. He approved the
  manifest version, on the stated reasoning that the alternative is "cheaper to approve and
  strictly worse".

  The obvious implementation —
  adding `site_v2/src/data/**` to the existing `review_exclude_paths` — is WRONG, and the reason
  matters. That list means "the review's own paperwork, which reviewers must never judge". Sample
  data is not paperwork: it is reviewed CONTENT that merely should not be PASTED. Hiding it
  outright would silently remove `bi-analyst-reviewer`'s core hunt item, which is whether a
  displayed field actually exists in the exported sample — trading a payload saving for a real
  loss of coverage, which is the "never loosen a guard" failure.

  So the new key excludes those paths from the patch BODY and substitutes a MANIFEST — the file
  list with +/- line counts — telling reviewers exactly what changed and to grep it directly.
  Reviewers have `Read` and `Grep`, so the check survives; only the paste goes away. Two keys
  with two meanings, rather than one key doing two jobs badly.

  (B) WITHDRAWN, NOT APPROVED — an `i18n:same-as-en` exemption marker for `check_copy_gate.py`.
  It was built, then REMOVED after `cto-reviewer` at opus argued it down. Recorded because a
  withdrawn mechanism is as much part of the audit trail as an approved one, and because the
  argument is the reusable part:

    · The case it existed for is ALREADY exempt. Check 4 skips any value with no `[a-z]{3,}` word
      (numbers, symbols, abbreviations) and any single capitalised token (brand names). The
      residual case is a multi-word English string deliberately kept in de/fi — of which this
      repo has ZERO; the gate exits 0 on `cbd81aa`.
    · The one historical instance, `fi.footerDataSource`, was ruled on by the CPO by TRANSLATING
      it, in a decision taken with no exemption available.
    · Translation is §10. A self-serve comment would let any future agent whose change reddens
      check 4 go green on its own authority — a guard bypass added ahead of demonstrated need, in
      the direction the last real ruling went against.

  Item 2 is therefore delivered as the builder's own stated FALLBACK, which needs no new
  authority because it removes a capability rather than adding one: check 4's message no longer
  advertises an exemption that does not exist, and points at the CPO instead. The dead helper and
  its parser were deleted with it, rather than left orphaned.

  RECURRING COST — YES, ONE. The first version of this contract declared "NO". That was FALSE and
  `cto-reviewer` at opus caught it.

  ITEM 5 IS A RECURRING COST. `scope-auditor` is in `always`, so moving it haiku -> sonnet is a
  permanent per-review spend increase on every substantive commit in every future task. The
  precedent is quoted verbatim inside the very file item 4 edits (`review_routing.json`): "two
  opus specialists where one ran before is a RECURRING COST, and cost is CPO-class ... Do not
  widen them without a cost approval quoted in `decisions_taken`."

  THE APPROVAL EXISTS — the 2026-08-06 plan named the model change explicitly and was approved in
  plan mode. What was wrong was the DECLARATION, and this field is the only place a cost crossing
  is visible because no gate parses it.

  Partly offset, but NOT claimed as netting to zero (the two are not measured on the same axis):
  item 4 removes ~89% of the review payload — measured at 30,480 of 34,074 lines — which lowers
  per-review tokens for every reviewer, including this one.

  No other item adds recurring cost. Item 1 adds one offline Python invocation to an existing CI
  job: no BigQuery read, no API call, no new job. Item 3 adds ~2.9s at turn end, locally, and only
  on a dirty in-scope tree. Neither is warehouse or provider spend.

  NEW EXTERNAL SURFACE — NO. Nothing is published, exposed or deployed.

  GUARD INVARIANT WEAKENED — NO, and this is the claim most worth checking. Item 6 changes no
  decision: the exception path still returns 0, exactly as the house rule requires, and only
  gains output. Item 4 removes files from what reviewers are HANDED, never from what the commit
  hash COVERS — `hash_exclude_paths` and `review_exclude_paths` are separate lists for precisely
  this reason, and NEITHER changes; a third key is added instead. Item 5 raises a model tier and
  lowers nothing.

  AMENDMENT 2026-08-06 — `docs/working_agreement.md` ADDED to `scope_paths`, on a clean tree,
  under the same CPO plan approval. It is not a new decision; it is the doc-sync obligation
  below applied to a second file that the original list missed.

  WHY: §2 states the model pinning in prose — "`scope-auditor` runs on **haiku**" (line 137) and
  "`scope-auditor` is exempt and stays on haiku" (line 144). Item 5 moves it to sonnet. Landing
  the code change without the doc would leave the working agreement asserting a model the repo
  no longer uses, which is the same "hand-copied prose disagrees with the source of truth"
  defect already filed as GitLab #1 — where one routing-row change cost eleven prose edits and
  three review rounds.

  ⚠ THAT SENTENCE ORIGINALLY CLAIMED the sites were "found by grepping for `haiku` repo-wide".
  THAT WAS FALSE. The grep covered three named files, not the repo. `platform-reviewer` at opus
  found `docs/agent_guardrails.md:93,99` still asserting haiku — the other authoritative guardrail
  doc, named in CLAUDE.md's own table. A real `git grep -i haiku` then surfaced a fourth site the
  reviewer had not flagged: `.claude/agents/cto-reviewer.md:81` ("those files hunted only at
  haiku"). Both are now in `scope_paths` and corrected.

  This is the contract-claims-are-unverified failure the handover already records as #904 —
  a claim written BEFORE the work, never re-checked against the finished tree. The correction is
  recorded rather than the sentence quietly rewritten, because a contract that silently repairs
  its own false claims is worth less than one that shows them.

  DOC-SYNC OBLIGATION, recorded because this task would otherwise commit the exact defect it
  exists to fix. `scripts/check_copy_gate.py`'s module docstring currently states, in bold,
  "DELIBERATELY NOT WIRED INTO CI YET, and that is a decision, not an oversight", and lists the
  16 findings as still live. Wiring the gate without rewriting that paragraph would leave a file
  whose header contradicts its own behaviour — "add and never retire" in a third medium. The
  docstring is updated in the same commit.

decisions_reserved:
  - CLOSED — the exemption-marker SHAPE for item 2 (`i18n:same-as-en`). This bullet used to read
    that the marker was "implemented ... so `cto-reviewer` rules on it", which `decisions_taken`
    (B) has contradicted since the marker was withdrawn. `cto-reviewer` at opus spotted the
    contradiction in round 2 and deliberately did NOT spend a round on it — it changes no
    authority conclusion, the durable record in `escalations.log` is correct, and a contract edit
    voids every verdict — advising instead that it be corrected if the contract were touched for
    any other reason. It was (the round-3 test fix voided the hash anyway), so it is corrected
    here. RESOLUTION: the marker was withdrawn; the fallback named in the old text — delete the
    promise from the gate's message — is what shipped.
  - Whether `stop_gate.py` should run the copy gate at all, or only the four structural gates.
    The copy gate is the slowest of the five and the only one whose failure is a §10 wording
    question the agent cannot fix alone. Implemented as INCLUDED, because a turn that leaves
    shipped copy defective should not end silently; open to a reviewer arguing it belongs only
    in CI.
  - `.claude/skills/` is not a protected path, but a skill folder can carry executable scripts,
    while `.claude/commands/` IS protected precisely because a command can embed shell. Same
    class, different treatment. Noted, NOT changed here — amending the protected-path list is a
    separate governance event and is not covered by this contract's authority.
