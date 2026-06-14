# Task contract — chore: settings deny-list + governed /status command (AI-collab tuning)

> CPO-directed tuning of the repo's AI-collaboration infrastructure, arising from assessing
> `.claude/` against a best-practice post. Two user-facing changes — (1) a deterministic
> `permissions.deny` backstop in `.claude/settings.json`; (2) the repo's first custom slash
> command, `/status` (read-only snapshot) — plus the governance lock-down the CPO ruled must
> precede shipping any command: make `.claude/commands/**` a PROTECTED + cto-routed + opus-
> guarded path, mirroring the `.claude/agents/**` precedent. Touches PROTECTED paths
> (settings.json, task_contract_gate.py, review_routing.json) → protected_override below.
> See docs/working_agreement.md §2, §10; .claude/task/escalations.log 2026-06-14 (this branch).

objective: >
  (1) Add a `permissions.deny` block to `.claude/settings.json` (filesystem / shared-prod /
  git-history / secrets backstops), leaving the `hooks` block byte-identical. (2) Govern the
  command surface BEFORE shipping a command: add `.claude/commands/` to the contract gate's
  PROTECTED_PREFIXES, route `.claude/commands/**` to cto-reviewer, add it to the opus-on-guards
  floor, and sync the protected/guard enumerations in working_agreement.md + agent_guardrails.md.
  (3) Add the read-only `.claude/commands/status.md` slash command.

refs: CPO in-conversation direction + two blinded rulings, 2026-06-14 (this branch's
  escalations.log entry): Issue 1 force-push = "block only reckless -f"; Issue 2 command
  surface = "lock down first, then add /status". Both rulings answer FAIL findings from the
  iteration-1 blinded review (scope-auditor + cto-reviewer opus).

scope_paths:
  - .claude/settings.json
  - .claude/hooks/task_contract_gate.py
  - .claude/review_routing.json
  - .claude/commands/status.md
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - tests/test_governance_hooks.py
  - .claude/task/contract.md

protected_override: >
  CPO (Rami) directed this work in-conversation (2026-06-14) and ruled both surfaced questions
  (Issue 1 = block -f only; Issue 2 = lock down the command surface first). That ruling is the
  authority to edit the protected guard machinery in this task: `.claude/settings.json`,
  `.claude/hooks/task_contract_gate.py`, and `.claude/review_routing.json`. Recorded in
  .claude/task/escalations.log (2026-06-14, this branch).

decisions_taken: >
  The deny-list is a defense-in-depth BACKSTOP (the active hooks remain the boundary). Issue 1
  ruling: block `git push -f` only — `--force-with-lease` (needed to update a rebased PR),
  long-form `--force`, and `git reset` stay allowed, because the glob matcher cannot carve
  `--force` out of `--force-with-lease`. Other denies: `rm -rf` variants, `git clean` (protects
  parked untracked work), `bq rm` + `gcloud projects delete` (shared prod; CPO ruled KEEP DENIED
  — friction on rare legit drops is intentional), `git commit --no-verify`/`-n` (defense-in-depth
  over the git-discipline hook), `.env`-family Read/Edit. Issue 2 ruling: `.claude/commands/**`
  is treated like the `.claude/agents/**` precedent — PROTECTED (gate), cto-routed
  (review_routing.json), and in the opus-on-guards floor — because command files can embed shell
  (the same high-stakes class as hooks). The doc enumerations are synced so the written rule and
  the code agree. `/status` is read-only (`allowed-tools` allowlists four read commands + reading
  the handover) and forbidden from acting.

decisions_reserved:
  - If a reviewer finds a denied pattern that breaks an established legitimate workflow (beyond
    the bq rm friction already CPO-accepted), STOP and surface it.
  - Tidying the accreted allow-list in settings.local.json, and any broader ceremony-threshold
    calibration, are explicitly OUT of scope (separate follow-ups).

done_when:
  - `.claude/settings.json` parses (`python -m json.tool`); `permissions.deny` present; the
    `hooks` block is unchanged vs main; the deny-list blocks `git push -f` but not
    `--force-with-lease`/`--force`.
  - `task_contract_gate.py` PROTECTED_PREFIXES includes `.claude/commands/`; `review_routing.json`
    routes `.claude/commands/**` → cto-reviewer; both parse.
  - working_agreement.md §2 + agent_guardrails.md list `.claude/commands/` among the protected /
    opus-guard paths.
  - tests/test_governance_hooks.py has `test_commands_dir_is_protected` (mirrors
    `test_agents_dir_is_protected`); `python -m pytest tests/test_governance_hooks.py -q` passes.
  - `.claude/commands/status.md` exists, read-only (no write/commit/push in allowed-tools).
  - reviewers: scope-auditor (always) + cto-reviewer (settings/hooks/routing routing; run on OPUS
    per opus-on-guards) — both PASS.

amendments:
  - 2026-06-14: + tests/test_governance_hooks.py to scope_paths. Authority: iteration-2
    cto-reviewer FAIL — the `.claude/agents/**` precedent shipped WITH a protection test
    (`test_agents_dir_is_protected`), so mirroring it "exactly" requires the same coverage for
    `.claude/commands/`. Clean-tree amendment (the six code files stashed). content: add
    `test_commands_dir_is_protected`; routing unchanged (tests/** already → cto-reviewer).
