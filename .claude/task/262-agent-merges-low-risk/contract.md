# Task contract — the agent merges low-risk merge requests itself

objective: >
  Issue #262: the agent merges a merge request itself when its pipeline is green,
  `scripts/merge_ready.py` says ready, every required reviewer passed and the diff touches no CPO
  path (fan-visible text, the metric catalogue, a core document, a guard hook or gate, a cost
  setting). Every other merge request waits for the CPO's merge. Parts: the working_agreement §3
  rule and §10 standing rules; the merge hook allowing `glab mr merge` for such an MR, with the
  allowlist of paths read from `gitlab/main`; a CI step that proves a research-fix branch changes only
  correction-seed rows; the research skill landing its rows through this route.

refs: >
  #262.

scope_paths:
  - .claude/task/262-agent-merges-low-risk/
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - .claude/hooks/git_discipline.py
  - .claude/review_routing.json
  - tests/test_research_fix_merge_hook.py
  - tests/test_governance_hooks.py
  - scripts/check_research_fix_mr.py
  - tests/test_check_research_fix_mr.py
  - .gitlab-ci.yml
  - .claude/skills/research-provider-errors/SKILL.md
  - CLAUDE.md
  - .claude/agents/
  - .claude/hooks/dbt_layer_gate.py

protected_override: >
  The merge allowance in the hook, the allowlist of paths in the routing file, the one validate:governance
  step in .gitlab-ci.yml, and the working_agreement §3 and §10 text and the two docs/agent_guardrails.md
  rows: approved in chat, 2026-11-20. The pointer changes (§3 lines "wait for CI", CLAUDE.md line 19
  and "(§10 meta-rule)" to "(§10 Unclear cases)" in the eight .claude/agents files) only restate the
  approved §3 merge rule and §10 Unclear-cases rule, under the §10 restated-rule paragraph. The
  eight agent files and the message of .claude/hooks/dbt_layer_gate.py lose the clause that sent an
  unclear classification to the CPO and keep "ESCALATE": a cut, no new rule.

impact_map: >
  writers: none; no table, model or page output changes.
  guard: `.claude/hooks/git_discipline.py` (PreToolUse Bash) blocks every `glab mr merge`/`accept`.
  It now lets one form through: `glab mr merge <literal number> --sha <head>` with only --yes or
  --remove-source-branch, as the sole command, when the MR is open into main, its head pipeline is
  success, the MR diff (read with -z, so a non-ASCII path is not quoted) touches only paths in
  `agent_merge_paths` and none in `agent_merge_except`, and `scripts/merge_ready.py <number>`, run from a detached checkout of `gitlab/main`,
  exits 0. The list and the judge both come from `gitlab/main`, so an MR cannot change what judges
  it. A list that is missing or empty on `gitlab/main` blocks. An MR that changes a correction seed
  (`dbt_project/seeds/*_corrections.csv`) is cleared only from a `research-fix/*` branch, the one
  branch whose pipeline runs the seed-only and source check; any other branch waits for the CPO. Every error, timeout or missing value blocks, a
  watchdog prints the deny and exits at 500 s if a child process hangs, and `--auto-merge`, `--squash`,
  other flags, a non-literal number, a chained command and an env prefix stay blocked.
  readers: `agent_merge_paths` and `agent_merge_except` are new keys in the routing file; `_load_routing`
  and every other reader take the keys they know. Tests pin that no guard path of task_contract_gate,
  no core document named in working_agreement §10 and no CI, security, cost or config path is
  agent-mergeable, and that the allowlist holds no test and no directory wildcard. scripts/merge_ready.py runs from a checkout of
  `gitlab/main`, so no file of the MR can shadow what it imports. "Every required reviewer passed" is held by
  the green pipeline: validate:governance runs scripts/check_task_artifacts.py.
  failure: if the list or the hook is wrong, an MR that should wait for the CPO is merged by the
  agent; the list is deny by default (a path that is not listed waits for the CPO), a post-merge
  watch of main's pipeline and a revert on red are the §3 rule, and the hook denies on every doubt.
  ci: one step in validate:governance runs scripts/check_research_fix_mr.py from the target branch's
  copy on `research-fix/*` source branches only (a failed copy stops the job). No data job, rule or
  schedule changes; a research-fix MR takes the normal data build.
  blast_radius: merge permission for MRs that touch only listed paths; nothing else.

approved_design:
  - none: no page output changes

depends_on:
  - none: works on main alone

shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  The agent merges low-risk merge requests itself, the §10 standing budget, wording and review-cap
  rules, and the unclear-cases rule: approved in chat, 2026-11-20. The working_agreement text is the
  approved text. The list of paths the agent may merge is an allowlist, decided in chat, 2026-11-20:
  `agent_merge_paths` holds the three correction seeds the research routine writes (card, goal,
  result) and the files inside a task folder. It holds no model, test, macro, yml, other seed or
  directory wildcard: each of those can hold or weaken a gate, decide a withholding rule or metric
  window, carry fan-visible text or change a cost. Adding one is a one-line change to the list on
  main, made by the CPO's merge. `agent_merge_except` is empty and kept for later exceptions. Every
  path not listed, a new file included, is the CPO's by default. Tests pin the list.
  A new dependency is decided at plan time, not at merge. The stopped-site test of the research check reads the skill's own
  site table: a source host outside it is refused. No new dependency.
  RECURRING COST, measured 18-19 Nov: a merged seed MR runs data:build:mr (17 to 85 GiB billed) and
  then data:build:main on main (85.5 GiB, about $0.52), about $1 per merge. The research routine lands
  one MR per batch of research. The coordinating agent reports each month's spend against the standing
  budget of EUR 25 a month on top of the nightly, and takes anything above it to the CPO first. A
  merge also rebuilds and redeploys the nightly image through the existing main-push rules.

decisions_reserved:
  - none: the rule, the hook allowance and the path list are the approved text.

done_when:
  - python -m pytest tests/test_research_fix_merge_hook.py tests/test_check_research_fix_mr.py tests/test_governance_hooks.py -q passes.
  - python scripts/ci_local.py --job test:python and --job lint:python are green.
  - the MR pipeline is green and python scripts/merge_ready.py <iid> says ready.

amendments: (none)
