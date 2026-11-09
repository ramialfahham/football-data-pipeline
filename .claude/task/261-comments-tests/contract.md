# Task contract — tests: comments state only why

objective: >
  Issue #261, the tests folder. Bring every comment and docstring in tests/*.py up to
  dbt_project/docs/engineering_standards.md section 1.2: a one-line why where the reason is not
  obvious, nothing else. No code changes. tests/test_design_inventory.py is a protected path and
  stays as it is.

refs: >
  #261. Standard: engineering_standards.md section 1.2. Gate: .claude/hooks/comment_history_gate.py.

scope_paths:
  - tests/test_*.py
  - .claude/task/261-comments-tests/

decisions_taken: >
  The standard already rules every case, so the sweep is agent-executable under working_agreement
  section 10. A string the code compares, prints or parses is code, not a comment, and stays, so a
  flagged line inside a string stays too. Tool directives (noqa, type, pragma) stay. Only the pins
  in tests/test_no_decision_history_in_code.py change besides comments. No new mechanism, no new
  dependency, no recurring cost.

decisions_reserved:
  - A length limit on comments in the gate would be a new rule; it is not added here.
  - tests/test_design_inventory.py needs the CPO's protected-path approval; it is left unchanged.

done_when:
  - The AST of every changed test file, with docstrings removed, equals the AST on the base branch.
  - The only non-comment change is PINNED_LINES and PINNED_FILES in tests/test_no_decision_history_in_code.py.
  - python -m pytest tests passes.
  - The offline gates pass.

amendments: (none)
