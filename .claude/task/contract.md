# Task contract — memory cut to behaviour rules, with size budgets a hook enforces

objective: >
  The agent's memory folder (`~/.claude/projects/D--Projects-football-data-pipeline/memory/`,
  outside the repo) holds 108 files + the index — 477,078 chars; the index `MEMORY.md`, loaded into
  every session, 17,152 chars over 103 lines. 34 files are dead weight (13 handovers superseded by
  `.claude/active_work.md`; 21 repeating a repo fact or describing a state that changed), the rest
  say the same rules several times in files of 8–20 KB. This branch cuts the folder to behaviour
  rules and pointers, then adds the guard: an edit-time hook that refuses a write into the folder
  when it would push the index, a note or the file count past a budget — the three budgets pinned
  to what the cut measured, ratcheting down only. #115 step 9, the last.

refs: >
  GitLab #125 (this task, `Task` template; the What/Why/How below are copied from it). #115 step 9
  ("memory cut to behaviour-changing rules, and size budgets per surface … Mechanism owed: a
  budget, so adding requires removing"). The rule the cut applies: `CLAUDE.md` "Which source
  answers which question" — memory answers none of the four. The pattern the hook copies:
  `.claude/hooks/comment_history_gate.py` (`!177`) and the pinned-count ratchet of
  `tests/test_no_decision_history_in_code.py`.

protected_override: >
  `.claude/hooks/memory_budget_gate.py` (new) and `.claude/settings.json` (one hook registration).
  The product owner's go to this step's plan is recorded verbatim in `decisions_taken` below, in
  the commit message and in the MR head; under working_agreement §11 the durable approval is his
  merge of this MR.

scope_paths:
  - .claude/hooks/memory_budget_gate.py
  - .claude/settings.json
  - tests/test_memory_budget_gate.py
  - docs/agent_guardrails.md
  - docs/operations_guide.md
  - CLAUDE.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: one new hook, one registration entry, one test file, one guardrails row, one
    operations-guide section (the CI-runner facts moving in from memory), the `CLAUDE.md` memory
    section, the handover. Outside the repo: the memory folder — deletions, merges, rewrites and a
    rebuilt index, none of which the patch shows; the evidence carries them.

  downstream (a guard's blast radius is every future memory write): the hook fires on every
    `Edit`, `Write`, `MultiEdit` and `NotebookEdit`. It acts ONLY when the target path matches
    `…/.claude/projects/<slug>/memory/<name>.md`; every other path returns 0 with no output, so no
    repo edit, task artifact, plan file or scratchpad file is touched by it. On a memory path it
    computes the RESULTING file (Write: `content`; Edit: the file on disk with `old_string` →
    `new_string` applied, `replace_all` honoured; MultiEdit: the edits in order) and denies when
    (a) the file is `MEMORY.md` and the result exceeds `INDEX_MAX_CHARS`, (b) any other note and
    the result exceeds `FILE_MAX_CHARS`, or (c) the path does not exist yet and the folder already
    holds `MAX_FILES` notes. A result no larger than the file on disk always passes, so an
    over-budget file can always be cut. `NotebookEdit` writes `new_source`, which the hook does
    not read, so it passes. Any exception → return 0, no output: fails OPEN like every hook here.
    The test drives the hook as a subprocess on a temp folder of the same shape; the real folder
    is measured by `--report` in the evidence. `task_contract_gate.py` keeps ignoring paths outside
    the repo — this hook is the only one that looks there. Every other hook, the review hash,
    routing and CI: untouched.

  what stops being enforced if it is wrong: nothing enforced today — the folder had no gate. If
    the hook mis-denies, the message names the surface, the measured size and the budget, and the
    way out is to cut the note or delete one first.

  layer_rules: n/a.

  deploy_order: none.

  blast_radius: a NEW DENY on memory writes only. Bounded by the path test. The one edit it can
    make harder is a large memory write in a hurry — by design; the budget is the mechanism.

acceptance_criteria:
  - The memory folder is cut to behaviour rules and pointers: the 13 `session_handoff_*` and every
    `project_*` that repeats a repo fact (named per file) or describes a changed state are deleted;
    the nine same-rule clusters are merged; every surviving note is the rule, why, and how to
    apply, without dates or PR narrative. Reported two-sided: files before/after by class, chars
    before/after, the merge map.
  - The three memory-only facts have a home or are gone: `ci-runner-01` → `docs/operations_guide.md`;
    the guardrails plugin → a `reference_` note; the semantic-layer intention dropped.
  - `.claude/hooks/memory_budget_gate.py` is wired and its three budgets equal the measured
    landing (`--report`): file count, index chars, largest note chars. On the real folder, one
    char over any budget is denied with the hook's own text; a shrinking edit of an over-budget
    file passes.
  - `tests/test_memory_budget_gate.py` covers each deny and each pass on a temp folder, plus
    non-memory path ignored and malformed stdin fails open; `pytest tests/` green with `main`'s
    count plus the new tests; ruff clean on the hook and the test.
  - `docs/agent_guardrails.md` has the row; `CLAUDE.md` "Memory files" names the budgets and the
    hook and its key-files lines point at files that exist; `MEMORY.md` links all resolve; the
    handover states #115 done and product work next.

decisions_taken: >
  CPO, 2026-09-12, in chat: "go" — to the plan as revised after his objection that the budgets
  "seem quite arbitrary": the budgets are MEASURED, NOT CHOSEN. The cut happens first; the hook's
  three constants are then pinned to what the cut landed on (file count, index size, largest
  note) and ratchet down only — the same pattern as the comment guard's pin. Nothing else in the
  step is a choice: the cut applies `CLAUDE.md`'s rule (memory holds behaviour feedback and
  pointers, never a product fact), and the rewrite applies the sweeps' rule (keep the why, drop
  the who and when).

  THE THREE MEMORY-ONLY FACTS: the builder's disposition, stated in the plan he approved —
  `ci-runner-01` facts move to `docs/operations_guide.md` (the doc that owns operations); the
  guardrails-plugin pointer becomes `reference_guardrails_plugin.md`; the semantic-layer
  intention is dropped (an issue if it is ever wanted).

  THRESHOLD — NEW MECHANISM: yes — a new deny on memory writes, approved above; the numbers are
  measurements. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - A SessionStart report line; closing the shell-write bypass; any widening of the hook's
    path test beyond the memory folder.

done_when:
  - The five criteria proven; the hook's `--report` on the real folder equals its three constants;
    the four mutations shown; `pytest tests/` and ruff green; the MR head lists the deletions by
    class and the merge map.

amendments:
  - After round 1 (cto-reviewer): the "CI runner" section written into `docs/operations_guide.md`
    carried the runner's public IPv4, host size and city, and its exact firewall rule — a live
    host's fingerprint moved from a private note into a public repo, beside the description of the
    prod credential's WIF binding. Never in the tracked tree before this branch, and not a
    disclosure his "go" covered (the plan said "the facts move into the operations guide", not
    which facts). Removed: the address, the specs, the city, the firewall rule. Kept: that one
    small Hetzner VM is the only runner, its registration, why no group, no GCP credentials on the
    host, the IPv6 clone failure and its fix, the console keyboard trap, SSH by key only. The
    address lives in the Hetzner account, which the section now says.
  - After round 1 (platform-reviewer): three defects in the machinery, all fixed and each proven
    by mutation. (1) `test_budgets_only_ever_move_down` compared the three budgets as ONE tuple,
    which Python compares lexicographically — a lowered first budget would have hidden a raised
    third; now three assertions, and the mutation (`MAX_FILES` 49, `FILE_MAX_CHARS` 999999) goes
    red. (2) The universal-newline read the hook relies on had no test that could fail on the
    Linux runner (every fixture wrote LF); a new test writes a CRLF note as BYTES at exactly the
    budget after normalisation and over it raw, and the mutation (`newline=""`) goes red. (3)
    `--report` on a missing folder crashed with a traceback; it now prints "no memory folder at …"
    and exits 1, pinned by a test. Criterion 4's test count is 29, not 27.
