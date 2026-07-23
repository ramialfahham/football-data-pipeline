# Task contract — trim the guardrail machinery to what earns its place

> Written on a CLEAN tree (branch `chore/trim-guardrails` off main @ e7e516f).

protected_override: >
  `.claude/hooks/**`, `.claude/settings.json` and `.claude/task/TEMPLATE.md` are PROTECTED: removing
  a hook, unwiring it, and dropping a machine-gated contract field are governance events. CPO-
  directed 2026-07-22 after a staff-level AI-engineering review of the `.claude/` machinery, chosen
  discretely (AskUserQuestion): **"Trim the weak parts, then reframe"**, whose option text named
  exactly what to cut. Routes to cto-reviewer; the opus-on-guards rule applies.

objective: >
  A staff-level AI-tooling review found the core of the guardrails genuinely strong (the hash-bound
  blinded review and the self-gating hooks) but three mechanisms over-scoped: "the machinery
  defending itself against itself." This removes exactly those, so the system passes its own
  proportionality test before the README reframes it as the portfolio artifact. Four cuts:

  (1) DELETE `plain_language_gate.py` and its wiring. A 232-line Stop hook that blocks the agent's
  final chat message on an em dash, a section sign, a repo path in prose, or 2,500 characters. Its
  own docstring calls it provisional and admits it fires after the message renders, so it does not
  even prevent a wall of text. It governs chat-prose preference, not code or data integrity, and it
  is the single mechanism most likely to read as over-engineered. The CPO's no-em-dash preference
  SURVIVES as a stated norm in the handover; only the machine enforcement goes.

  (2) DEMOTE the `consulted:` field (shipped one day ago in #807). Remove its machine enforcement
  from the contract gate (Edit and shell paths) and the CI backstop; keep the intent as a reviewer
  norm and a template comment. It was hardened into two enforcement paths before it earned it. This
  PARTIALLY REVERSES #807, knowingly and on the review's recommendation, not as thrash.

  (3) COMPRESS the multi-round "forgery archaeology" comments in `task_contract_gate.py` (the
  `_NULLISH`/block-scalar/placeholder essays that narrate four rounds of the same finding). Keep the
  `_BLOCK_HEADER_RE` pattern and a one-line why; the incident history belongs in git, not the body.

  (4) SPEED the test suite. The `repo` fixture is function-scoped and rebuilds a git repo via six
  subprocesses per test, which is why the suite takes ~11 minutes. Build the template once and copy
  it per test, cutting it toward ~2 minutes so it can run in the loop, which is the point of a gate.

refs: >
  Verified this session, not recalled:
  - `plain_language_gate` is wired ONLY at `.claude/settings.json:101` (Stop hook, second of two;
    `stop_gate.py` at :95 stays) and referenced in `docs/agent_guardrails.md` and the tests.
  - `consulted` enforcement lives in `task_contract_gate.py` (parse + Edit path + shell path),
    `scripts/check_task_artifacts.py` (import-delegated), `TEMPLATE.md`, `working_agreement.md`,
    `agent_guardrails.md`, and the tests. `.venv/**` and `dbt_packages/**` matches are unrelated.
  - The `repo` fixture is `tests/test_governance_hooks.py:106-116`: git init + 2 configs + mkdirs +
    add + commit, per test.

scope_paths:
  - .claude/hooks/plain_language_gate.py
  - .claude/hooks/task_contract_gate.py
  - .claude/settings.json
  - scripts/check_task_artifacts.py
  - .claude/task/TEMPLATE.md
  - docs/agent_guardrails.md
  - docs/working_agreement.md
  - tests/test_governance_hooks.py
  - .claude/active_work.md
  - .claude/task/escalations.log

consulted: >
  The staff-level AI-tooling review (a general-purpose agent briefed as a 12-year engineer half in
  LLM-agent systems), run BEFORE this build. Its verdict IS the spec: keep the hash-bound review and
  self-gating hooks, cut the plain-language gate, demote the day-old consulted field, compress the
  archaeology, and fix the fixture. Nothing here is my own taste; it is that review carried out.

impact_map: >
  writers: none. No data, no model, no table, no warehouse object.
  downstream: the blast radius is EVERY FUTURE TASK, which is why a protected path demands this
    trace. Enumerated by grep, not memory:
      `.claude/hooks/plain_language_gate.py` deleted -> the Stop event runs only `stop_gate.py`
        afterwards; verified `stop_gate.py` does not import or depend on it.
      `.claude/settings.json` loses one Stop-hook entry; the SessionStart and PreToolUse blocks are
        untouched.
      `.claude/hooks/task_contract_gate.py` loses the `consulted_present` parse and the two deny
        sites; a future structural contract is NO LONGER denied for a missing `consulted:`. The
        `impact_map` gate and every other check are untouched.
      `scripts/check_task_artifacts.py` loses its `consulted` branch; it still imports the hooks for
        the round-cap and structural checks, so the CI/local parity that #807 established holds.
      `tests/test_governance_hooks.py` loses the plain-language and consulted tests and gains a
        faster fixture; the count drops but coverage of the KEPT mechanisms is unchanged.
  layer_rules: none apply. No dbt model, no SQL, no seed.
  deploy_order: none. Takes effect on the next session (settings) and the next commit (gates).
  blast_radius: bounded and REDUCTIVE. This removes enforcement rather than adding it, so the risk is
    the opposite of the usual one: not that it breaks a build, but that a norm now rests on judgement
    instead of a gate. Accepted deliberately for the plain-language preference (a chat-prose taste,
    not integrity) and the consulted habit (one day old, unproven). The hash-bound review, the
    contract/scope gate, the impact_map gate, the layer gate, the round cap and the blinded reviewer
    cast are ALL kept. The suite still runs on every PR via `python-ci.yml`, faster.

decisions_taken: >
  (1) TRIM, then reframe. CPO 2026-07-22 (AskUserQuestion) after the staff review: "Trim the weak
      parts, then reframe", the option whose text named cutting the plain-language gate, demoting the
      consulted field, deleting the archaeology comments, and fixing the fixture.
  (2) The no-em-dash / plain-language PREFERENCE is retained as a norm in the handover; only its
      machine enforcement is removed. It is not being decided away.
  (3) Demoting `consulted` partially reverses #807. This is a considered reversal on the review's
      recommendation, recorded in `escalations.log`, not a flip-flop.

decisions_reserved:
  - The README reframe and dead-link/screenshot polish is the SEPARATE next PR (`chore/repo-polish`,
    contract saved), out of scope here.
  - Whether to trim anything FURTHER in the machinery is not decided; this does exactly the four cuts
    the review named and the CPO approved, no more.

done_when:
  - `plain_language_gate.py` is deleted, its `settings.json` Stop entry removed, and its tests and
    doc references gone; `stop_gate.py` still fires on Stop and still passes its tests.
  - A structural-path edit whose contract has no `consulted:` is NO LONGER denied (the demotion),
    verified by a test; the `impact_map` gate still denies as before.
  - `check_task_artifacts.py` no longer references `consulted`; CI/local round-cap parity still holds
    (its parity test still passes).
  - The `repo` fixture builds the template once and copies per test; the full suite passes and runs
    materially faster (target: well under half the prior wall-clock).
  - `working_agreement.md`, `agent_guardrails.md` and `TEMPLATE.md` no longer describe the removed
    enforcement; no doc describes a gate that no longer exists.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments: (none)
