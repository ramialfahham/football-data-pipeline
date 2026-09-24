# Task contract — The stop gate runs its checks in the repo's own Python environment (#162)

objective: >
  The turn-end stop gate runs its fast offline gates with the repo's `.venv` interpreter when
  `scripts/bootstrap.py` has created it, and with the hook's own interpreter otherwise. A fresh
  machine's system Python lacks the gates' packages (PyYAML), so today every turn with a dirty tree
  reports three false failures.
refs: >
  GitLab #162 (requirement, checklist and plan; approved in plan mode 2026-09-24). Follows #161
  (clone and continue), whose setup creates `.venv` with every requirement.

scope_paths:
  - .claude/hooks/stop_gate.py
  - tests/test_governance_hooks.py
  - .claude/task/**
  - docs/tracker/**

protected_override: >
  `.claude/hooks/stop_gate.py` is a protected path. Authority: the plan for GitLab #162, approved in
  plan mode on 2026-09-24, whose How names the file ("`.claude/hooks/stop_gate.py`,
  `_failing_gates`: run each check with the repo's `.venv` Python when it exists ..., otherwise with
  the Python that runs the hook, as today") and whose header says the contract quotes that approval
  for this protected file. His go in chat before it: "do it". The commit message and the MR head
  repeat this under `Locked files`; his merge is the approval (working_agreement §11).

impact_map: >
  writers: none. No raw writer, dbt model, seed, export script or site file.
  what fires it: the `Stop` hook in `.claude/settings.json` (line 119, `python
  "$CLAUDE_PROJECT_DIR/.claude/hooks/stop_gate.py"`, unchanged) at every agent turn end. The
  changed code runs only in the CORRECTNESS branch: after the stash check, after the scope check,
  and only when the tree is dirty outside `.claude/task/`.
  what imports it: `tests/test_governance_hooks.py` (runs the hook as a subprocess, and imports
  `stop_gate.FAST_GATES` for the validate-local agreement test; `FAST_GATES` is unchanged).
  Nothing else imports it.
  what stops being enforced if it is wrong: if the interpreter choice broke, every gate would fail
  to start; `subprocess.run` raising is caught and the gate skipped (fail open, the file's house
  rule), so a wrong path would silently skip gates rather than block. The new test pins both
  branches: with `.venv` the gate runs in it; without, it runs with the hook's interpreter and a
  failing gate is still reported. Scope and stash checks are untouched.
  failure behaviour: unchanged — block once, `stop_hook_active` prevents loops, any unexpected
  error returns 0.
  layer_rules: none touched.
  deploy_order: nothing reaches a host, a dataset or CI; the hook is local to agent sessions.
  blast_radius: none on data. Agent sessions on a machine with `.venv` stop seeing false
  PyYAML failures; sessions without `.venv` behave as today.

decisions_taken: >
  Every item is a line of GitLab #162, approved in plan mode 2026-09-24.

  Interpreter choice inside the hook, not in `.claude/settings.json`: launching the hook itself
  with `.venv` would fail to start it at all before setup has run. The hook stays standard-library
  only. Both venv layouts are checked (`.venv/Scripts/python.exe`, `.venv/bin/python`); the first
  that exists wins; otherwise `sys.executable`, as today.

  The failure message names the interpreter the gates ran with, so the suggested re-run command
  reproduces what the hook saw.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none; the existing gate runner chooses a different
  interpreter. RECURRING COST: none.

decisions_reserved:
  - none open: #162's plan was approved as written; a new CPO-class question found while building
    is brought to him, not decided.

done_when:
  - `.venv/Scripts/python.exe -m pytest tests/test_governance_hooks.py -k stop_gate` green,
    including the new interpreter test, and it turns red when `_gate_python` returns
    `sys.executable` unconditionally
  - on this machine, with a dirty in-scope tree, running the hook with the system `python` reports
    no correctness failure; with a deliberately failing gate it still blocks
  - blinded review cycle PASS; MR opened with the `Default` head; CI green

amendments: (none)
