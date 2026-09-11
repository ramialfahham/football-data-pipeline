# Task contract — sweep 1 of 4: decision history out of dbt comments

objective: >
  137 comment lines in `dbt_project/` (65 files) carry a date, "CPO", "reviewer", "round N" or an
  MR number — builder-written claims about decisions, in files nobody reads for them. The guard
  (`!177`) stops new ones and pins the count; this sweep rewrites each such line as the why alone
  (or removes it when it was only history) and lowers the pin by exactly what it removed. No SQL
  or YAML behaviour changes.

refs: >
  GitLab #121 (this task, `Task` template; the What/Why/How below are copied from it). #115 step 8,
  the first of the four sweeps the CPO said "do it" to on 2026-09-11 ("four sweeps, one per
  reviewer territory, each lowering the pin … Each line keeps the why and drops the who/when").
  The rule: `engineering_standards.md` §1.2 (`!176`). The guard: `!177`.

scope_paths:
  - dbt_project/models/**
  - dbt_project/macros/**
  - dbt_project/tests/**
  - dbt_project/seeds/**
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: comment lines only, in 65 dbt files. No model logic, no column, no test predicate, no
    seed row changes. The pin constant in one test file.

  downstream: none that a comment can reach. dbt compiles `--` and `/* */` comments into the
    compiled SQL and BigQuery ignores them; YAML comments are dropped by the parser before dbt
    sees them; Jinja `{# #}` comments are dropped at render. EVIDENCE, not assertion: for every
    touched `.sql` file, the text with comments stripped is byte-identical before and after; for
    every touched `.yml` file, the parsed YAML document is identical before and after — a script
    run over the diff and its output pasted in the evidence. `dbt parse` green;
    `scripts/check_layer_contract.py` green.

  layer_rules: unchanged — no file moves between layers, no per-competition file appears.

  deploy_order: none — nothing changes in the warehouse.

  blast_radius: none in data. In prose: a why that was carried by an attribution alone could be
    lost — the rule applied is to KEEP the deviation, its cost, the design analogy, the downstream
    contract and any pointer to a design doc, and drop only who decided and when. Where a comment
    was only history it is removed. The analytics-engineer reviewer judges that per file.

acceptance_criteria:
  - Every comment line in `dbt_project/` (models, macros, tests, seeds) that carries a date, "CPO",
    "reviewer", "round N" or `!N` is rewritten as the why alone, or removed when it was only
    history — 137 lines in 65 files today.
  - No SQL or YAML behaviour changes: for every touched `.sql` file the text with comments stripped
    is byte-identical before and after; for every touched `.yml` file the parsed YAML is identical
    before and after.
  - The pin in `tests/test_no_decision_history_in_code.py` is lowered by exactly the lines removed
    (850 → 713, 174 → 109 files), and the guard's test suite is green.
  - Nothing load-bearing is lost: for a model header that explains a deviation (e.g.
    `stg_apif__coaches.sql` reads all snapshots), the deviation, its cost and the design pointer
    stay; only the attribution goes.

decisions_taken: >
  THE REWRITE RULE, applied line by line: keep the why (the deviation, its cost, the analogy, the
  downstream contract, a pointer to a design DOC); drop who decided and when (a name, a title, a
  date, a log pointer, a ruling label such as "Option A" when the definition it labels is stated,
  a reviewer credit, an MR number). A comment that was ONLY history is removed. A date that is
  DATA (a boundary the code depends on) would be moved into code, not prose — none of the 137
  is one on inspection; each is judged as met.

  THE PIN MOVES BY EXACTLY THE LINES REMOVED, checked by running `count_tree` before and after,
  not by arithmetic on the sample.

  THRESHOLD — NEW MECHANISM: none. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - The other three sweeps and their order; widening the pattern to `#N`.

done_when:
  - The four criteria proven; `pytest tests/test_no_decision_history_in_code.py` green at the new
    pin; `python scripts/check_layer_contract.py` green; `dbt parse` green; the comment-stripping
    and YAML-parse comparison over every touched file → identical.

amendments:
  - none yet
