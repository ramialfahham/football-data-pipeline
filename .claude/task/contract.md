# Task contract — make the new org operational (#868)

> Written on a CLEAN tree, before any file was touched. Branch `feat/868-org-operational` from
> `main`; no open PRs. Governance task: it edits the guards themselves, so it carries
> `protected_override` + `impact_map`. See docs/working_agreement.md §2, §10, §11, Appendix A.

objective: >
  Put the CPO's 2026-07-31 org design into force. Four rulings become running mechanisms: the CTO
  splits so it stops reviewing markup and starts ruling on thresholds; a new Platform and
  Reliability reviewer inherits the territory and the line review; acceptance criteria are drafted,
  approved and locked before code; a Quality Assurance evidence artifact becomes gate-required; and
  user-visible strings hit a mechanical localisation gate. The session's rulings are also written to
  the decisions log so they survive the chat.

refs: >
  #868 (Operationalise the agent org). CPO session 2026-07-31: four in-conversation rulings, plus an
  implementation plan for the split that two independent reviewers challenged (nine defects, all
  fixed) and the CPO approved. Plan saved at
  `C:\Users\Rami\.claude\plans\ethereal-beaming-charm.md`.

scope_paths:
  - .claude/review_routing.json
  - .claude/agents/*.md
  - .claude/hooks/git_discipline.py
  - .claude/task/*.md
  - .claude/task/escalations.log
  - .claude/active_work.md
  - docs/roles/*.md
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - docs/north_star.md
  - scripts/check_copy_gate.py
  - scripts/report_process_health.py
  - tests/test_governance_hooks.py

protected_override: >
  CPO approval, 2026-07-31, this conversation. Three authorities, in his words:
  (1) the split and threshold plan was presented in plan mode and APPROVED via ExitPlanMode;
  (2) asked whether to proceed on the split he answered **"do it"**, and on the threshold mechanism
  **"go"**;
  (3) on the exercise as a whole: **"I want the new org to be operational"** and **"do we have a
  concept for the company that we will put in action"** — an instruction to implement, not to plan
  further.
  Each of the four rulings is recorded verbatim in `.claude/task/escalations.log` under 2026-07-31.

impact_map: >
  writers: `.claude/review_routing.json` has exactly two consumers, verified by grepping every key
    name across all non-markdown files. `.claude/hooks/git_discipline.py:123` (`_load_routing`)
    fails OPEN — it swallows every exception and returns None, so a malformed file silently disables
    the local gate. `scripts/check_task_artifacts.py:93` (bare `open`) fails CLOSED — traceback and
    non-zero exit in CI. No workflow other than `ci-validate.yml` reaches it.

  downstream: the required-reviewer set is computed by a matching loop HAND-COPIED into both
    consumers (`git_discipline.py:132-139`, `check_task_artifacts.py:156-160`) with NO parity test —
    `tests/test_governance_hooks.py:491` pins only `_rounds_gate` and `_NULLISH`. Every row added
    here must be correct in both, and only the local copy is exercised in-process (the helper at
    `:418` calls the hook's matcher alone). A follow-up issue is filed, not fixed here.

  layer_rules: not a warehouse change, so `check_layer_contract.py` is unaffected. The machine rules
    that DO apply: `tests/test_governance_hooks.py:456` — every `.claude/agents/*.md` must carry a
    byte-identical `## Delta re-review` with nothing after it, globbed with no opt-out; `:606` and
    `:613` — every routing pattern must be pinned in `PINNED_CASES`; `:541` and `:557` — the two
    frontend routing invariants.

  deploy_order: no warehouse or deploy sequencing, but this branch is routed BY ITS OWN new table,
    because both consumers read the file from the working tree and not from HEAD. The commit that
    changes routing must therefore also contain `platform-reviewer.md`, or the gate demands a
    verdict from a reviewer whose brief does not exist. Commit order is fixed for that reason.

  blast_radius: every future commit in this repo. What stops being enforced if it is wrong — a moved
    row with no matching brief means the gate demands a `## <name>` section forever and nothing can
    commit; a duplicate JSON key silently drops a reviewer requirement with no signal, because
    `json.load` keeps only the last occurrence of a key; a typo in a reviewer name fails nothing at
    all, because no allowlist of reviewer names exists anywhere in the repo. Measured effect on
    review volume over the last 150 commits: `cto-reviewer` 28% -> 12%, `platform-reviewer` 24%,
    10% requiring both. Verified that zero tracked `site_v2/src/**` files will require either.

decisions_taken: >
  **The CPO's four rulings, 2026-07-31, now in force.** (1) Quality Assurance exists as a required
  evidence artifact with a gate, NOT as a reviewer agent — the builder demonstrates each acceptance
  criterion against BUILT output. (2) Acceptance criteria: the builder drafts, the CPO approves
  before any code, locked after; the lock is the mechanism, not the authorship. (3) Editorial and
  Localisation is a mechanical gate, not a copy approver — wording stays the CPO's, and Growth owns
  a title's shape while Editorial owns its words. (4) Split the CTO: Platform and Reliability
  inherits the territory and the line review, the CTO keeps the authority and loses the globs, and
  thresholds no glob can express are declared here with the always-on scope-auditor as tripwire.

  **Builder judgement inside those rulings, recorded so it is visible rather than silent.** The slug
  `platform-reviewer`, which must be whitespace-free because the gate parses `## <name>` with
  `(\S+)`. The hunt-item allocation between CTO and Platform, with item 4 (fail-open vs fail-closed)
  STAYING with the CTO because the challenge showed moving it would cost the opus depth that caught
  the G3 commit-gate bypasses. `*requirements*.txt` replaces `requirements*.txt`, a deliberate
  correction: the old pattern anchors at the start of the path, so
  `ingestion/api_football/requirements.txt` never reached the dependency threshold at all, and the
  new one matches exactly two tracked files, verified. Patterns shared by two roles are ONE JSON key
  carrying both names in its array.

  **The threshold mechanism is judgement, not machinery, and this contract says so plainly.** No gate
  parses `decisions_taken` — `task_contract_gate._read_contract` returns only `scope`,
  `protected_override`, `impact_map_present` and `decisions_reserved_present`. Enforcement is one
  always-on reviewer, pinned to haiku, reading prose. That is a real downgrade from every other
  threshold in this system, and it is accepted deliberately as the cheapest thing better than
  nothing.

  **Added after review round 3, on the CPO's rulings of 2026-07-31.** Three things the reviewers were
  right to demand be recorded here rather than left to the diff:

  (a) **The credentials hunt item is on THREE reviewers, not moved.** The approved plan moved it off
  `cto-reviewer`; `cto-reviewer` at opus then found that this left nothing hunting secrets in
  `site_v2/src/**`, `dbt_project/**` or `ingestion/**`, and `scope-auditor` escalated that on the six
  guard paths platform is not routed to — `.mcp.json` and `.claude/settings.json` above all, the file
  class that carries tokens — a secret would be hunted only at haiku. Put to the CPO as a plain
  question; he answered **"yes"** to putting it back on the CTO as well. So it now sits on
  `cto-reviewer` (its former home, still spawned at opus on all eight guard paths),
  `platform-reviewer` (its own territory) and `scope-auditor` (every diff, because a secret can land
  anywhere). Strictly wider than before the split, at no extra cost, since the CTO is already spawned
  on those paths.

  (b) **`scripts/report_process_health.py` ships BUILDER-INITIATED and UNRULED.** It was proposed to
  the CPO as one of six gap fixes and he did not rule on it. It reads artifacts and prints them; it
  carries no authority and sets no target. An earlier draft invented a threshold AND a rule for
  withdrawing CPO-ruled process, which both guard reviewers failed as builder-authored governance.
  Whether any number it prints should carry a threshold is reserved below.

  (c) **Review round 4 is authorised.** `ROUND_CAP = 3`. Asked whether to go past it to write the two
  missing tests `platform-reviewer` demanded, the CPO answered **"yes"**. `review.md` carries the
  matching `rounds_cap_override:`.

decisions_reserved:
  - The priority mechanism. The CPO confirmed the milestone order, but 116 issues have been closed in
    this repo and NOT ONE was in a milestone, while 86 open issues have none — including every issue
    we call next (#845, #846, #838, #861, #843, #852, #868). The confirmed order has no throughput to
    order, and Phase 0 was written for a site retired on 2026-07-21. This contract records the
    finding and does NOT invent a replacement; the mechanism is the CPO's.
  - Routing `seo-expert-reviewer`. Approved in principle this session, not commissioned. It fires on
    nothing today and stays that way until its own governance event.
  - Which of the twelve stashes are dropped. Two are empty (`stash@{9}`, `stash@{12}`), eight are ten
    weeks to three months old, two are live. Dropping is destructive and needs the CPO's yes.
  - Whether cost is its own function (`docs/roles/cfo.md` exists and was excluded from the org) and
    whether narrative becomes one (`docs/roles/data_journalist.md`, same). Both unruled.
  - The remaining process moments: the discovery-spike gate, the design-review moment, and the
    release-readiness checklist. Designed and presented, NOT ruled on. Nothing here implements them.
  - **Wiring `scripts/check_copy_gate.py` into CI.** It exits 1 on `main` with 16 findings and every
    fix is copy, which is §10. Wiring it today makes CI red on strings only the CPO may rewrite, so it
    ships runnable and unwired, with the reason in its own docstring. Filed as #872. (Reserved here
    because `cto-reviewer` round 3 caught the docstring claiming this was already reserved when it was
    not — the sentence is now true.)
  - **Whether any number in `report_process_health.py` carries a threshold, and what follows from
    crossing one.** The script deliberately sets none. Setting one is a rule extension.
  - ~~The mechanical half of the credentials guard is unenforced in CI.~~ **WITHDRAWN in round 5: the
    premise was FALSE and I should never have put it to the CPO.** `.github/workflows/security-secrets.yml`
    runs `gitleaks-action@v2` on every `pull_request` and on push to `main`, with a terminal gate that
    exits 1 — CI secret scanning exists and fails CLOSED. `check_no_secrets.py` and
    `detect-private-key` are a LOCAL-ONLY second layer. `cto-reviewer` caught this by grepping all 11
    workflows; I had inferred the coverage. Kept here struck through rather than deleted, because a
    cost question asked on bad data is a defect worth leaving visible. The residual question, much
    smaller and probably not the CPO's, is whether the two local hooks catch patterns gitleaks misses.

done_when:
  - `python -m pytest tests/test_governance_hooks.py -q` passes in full, not a subset.
  - `.claude/review_routing.json` parses, AND the count of `paths` keys equals the count of distinct
    pattern strings in the raw file text, proving no duplicate key was silently collapsed.
  - The activation measurement reproduces: `cto-reviewer` at 12% over the last 150 commits, and zero
    tracked `site_v2/src/**` files requiring `cto-reviewer` or `platform-reviewer`.
  - `git diff` shows no change to the bytes after `## Delta re-review` in any pre-existing brief.
  - `python scripts/check_task_artifacts.py` agrees with the local hook on the new table.
  - `python scripts/report_process_health.py` prints the four baseline numbers (rounds, reviewer
    FAILs, CPO rulings, gate denials), so the org design has a measurable before.
  - The four rulings and the milestone finding are recorded in `.claude/task/escalations.log`.

amendments:
  - 2026-07-31: + `docs/north_star.md` — authority: CPO, asked directly whether the roles roster there
    should be updated now or filed as a to-do, answered **"yes, update"**. Raised by `scope-auditor`
    as an ESCALATE in review round 3: `CLAUDE.md` cites that roster as the definition of the roles,
    this branch adds `docs/roles/platform_reliability.md` and narrows `docs/roles/cto.md`, and the
    roster was neither updated nor in scope. **Content: itemised in full in `escalations.log`'s E5
    answer** — that is the authoritative description, and this clause is a pointer to it, not a
    summary of it. In outline: add the Platform and Reliability row; narrow the CTO's to
    authority-only; add the three rows that were missing (`seo_expert`, `data_journalist`, and the
    Scope Auditor, never listed despite firing on every commit); replace the empty `Brief` column with
    a **Wakes on** column naming what actually routes each role; and append a paragraph on the three
    functions ruled to be mechanisms rather than reviewer roles. Round 4 correctly failed a narrower
    description than the diff, and round 5 established that a contract under-describing its own
    amendment is the surface a §10 item gets smuggled through. Written on a tree made clean outside
    `.claude/task/` by stashing the branch's other 13 paths, then popped back — the stash-dance the
    clean-tree rule forces. Done twice; the 13 older stashes verified untouched each time.
