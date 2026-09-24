# Task contract — No decision history in documents (#163)

objective: >
  CLAUDE.md keeps every rule and loses its history (dates, issue and MR numbers, commit ids,
  incident stories, who decided). A guard refuses, at write time, any Markdown line that ADDS
  history, and a CI test pins each document's count so it can only go down.
refs: >
  GitLab #163 (requirement, checklist and plan; approved in plan mode 2026-09-24). Extends the
  code guard of closed #115 (`comment_history_gate.py`, `tests/test_no_decision_history_in_code.py`)
  to documents.

scope_paths:
  - CLAUDE.md
  - .claude/hooks/comment_history_gate.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - dbt_project/docs/engineering_standards.md
  - docs/agent_guardrails.md
  - .claude/task/**
  - docs/tracker/**

protected_override: >
  `.claude/hooks/comment_history_gate.py` is a protected path. Authority: the plan for GitLab #163,
  approved in plan mode on 2026-09-24, whose How names the file ("`.claude/hooks/comment_history_gate.py`:
  also check Markdown files; ... refuse only lines the edit adds that carry a marker") and whose
  header says the contract quotes that approval for the protected hook file. The commit message and
  the MR head repeat this under `Locked files`; his merge is the approval (working_agreement §11).

impact_map: >
  writers: none. No raw writer, model, seed, export or site file.
  what fires it: the PreToolUse hook `comment_history_gate.py` on every `Edit`, `Write` and
  `MultiEdit` (registered in `.claude/settings.json`, unchanged). Today it checks code files in
  `TREES` only and returns early for everything else; after, it also checks tracked-style Markdown
  paths (`*.md` outside `.claude/task/`, `docs/tracker/`, `site/`), where it refuses only marker
  lines the edit ADDS (a marker line already present in the replaced text or on disk is allowed).
  Code-file behaviour is unchanged.
  what imports it: `tests/test_no_decision_history_in_code.py` (imports `marker_kind`, `TREES`,
  `EXTS`, `is_code_path`, `comment_lines`; all kept with the same behaviour) and the new
  `tests/test_no_decision_history_in_docs.py`, which imports the doc definitions and pins per-file
  counts.
  what stops being enforced if it is wrong: a broken doc check that raised would fail open (the
  hook's `except` returns 0), so docs would be unguarded, as today; the code check is a separate
  branch and keeps its own tests. A too-broad doc check would refuse legitimate edits; the tests
  pin that an unchanged existing marker line and a clean line pass.
  failure behaviour: unchanged; deny is a PreToolUse refusal the agent sees; any error fails open.
  layer_rules: none. deploy_order: none; the hook is local to agent sessions, CI runs the test.
  blast_radius: none on data. The CLAUDE.md rewrite changes what every session reads: every rule
  line is kept (the MR head lists each before and after); the `1_staging: +materialized: table`
  and `2_base: +materialized: table` tokens pinned by `tests/test_materialisation_policy.py` stay.

decisions_taken: >
  Every item is a line of GitLab #163, approved in plan mode 2026-09-24.

  Document markers: date, reviewer credit, review round, MR number (the code guard's own
  definitions, imported); plus an issue number in CLAUDE.md only. The product owner's title is NOT
  a document marker: the decision-rights rules name that role; a dated ruling is caught by the date.

  Documents: only ADDED marker lines are refused, so existing history never blocks an edit;
  the per-file CI pin makes the count go down only. The other documents are not swept here.

  CLAUDE.md names the handover issue by role and points to `HANDOVER_ISSUE` in
  `.claude/hooks/handover_in.py` for its number, which every session also sees in the injected
  handover header.

  `docs/agent_guardrails.md` lists every hook; its `comment_history_gate.py` row gains that it also
  covers documents.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none new in kind; the existing write-time guard and its
  pinned-count test are extended from code to documents. RECURRING COST: none.

decisions_reserved:
  - none open: #163's plan was approved as written; a new CPO-class question found while building
    is brought to him, not decided.

done_when:
  - CLAUDE.md: zero marker lines and zero issue numbers; every former rule line present as a rule
  - hook: refuses an added dated line in a doc, allows an edit that keeps an existing dated line,
    allows a clean line; code-file tests unchanged and green
  - `tests/test_no_decision_history_in_docs.py` pins per-file counts and fails if one rises
  - full `tests/` green; blinded review PASS; MR open; CI green

amendments: (none)
