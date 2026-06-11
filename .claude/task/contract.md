# Task contract — G2: task-contract gate + shell coverage + stop gate

objective: >
  Governance PR G2 (approved plan, CPO 2026-06-11): build and register the
  enforcement machinery — task_contract_gate.py (edit + shell gates),
  stop_gate.py (turn-end reversion), git_discipline.py flag denies,
  the contract template, working_agreement §2 upgrade, hook docs, tests.
refs: governance plan (fuzzy-launching-meadow), PR sequence G2

scope_paths:
  - .claude/hooks/task_contract_gate.py
  - .claude/hooks/stop_gate.py
  - .claude/hooks/git_discipline.py
  - .claude/hooks/_command_utils.py        # shared quote/heredoc stripper used by both gates
  - .claude/settings.json                  # hook registration — LAST edit (bootstrap rule)
  - .claude/task/TEMPLATE.md
  - .claude/task/contract.md
  - docs/working_agreement.md              # §2 upgrade to the machine-gated contract
  - docs/agent_guardrails.md               # hook documentation rows
  - tests/test_governance_hooks.py         # offline subprocess matrix (python-ci)
  - .claude/active_work.md                 # handover (standing rule)

protected_override: >
  .claude/hooks/ and .claude/settings.json are protected paths; this task edits
  them under the explicit CPO approval of governance plan G2 ("changes to the
  guards are their own CPO-approved task with the gate consciously lifted").

decisions_taken: >
  All mechanics specified in the approved plan: hard-block scope gate;
  clean-tree-only contract amendments; protected paths; shell-mutation coverage
  (write-operator denies + post-Bash status check with stop-gate latency
  fallback); --amend/--no-verify/-n/core.hooksPath denies; escalations.log
  convention; fail-open on hook errors (existing house rule).

decisions_reserved:
  - Any NEW deny class not named in the plan (would be a rule extension — CPO).

done_when:
  - all hooks pass the offline subprocess test matrix (committed as pytest)
  - live-fire after registration: out-of-scope Edit denied; contract amendment
    on dirty tree denied; shell redirect to repo file denied; quoted ">" in a
    bq query NOT denied (false-positive guard)
  - validate-local tier-1 green; PR open with this contract committed

amendments: (none)
