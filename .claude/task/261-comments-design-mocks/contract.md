# Task contract — design-mocks and deploy: comments state only why

objective: >
  Issue #261, the design-mocks and deploy folders. Bring every comment and docstring in
  design-mocks/*.py, deploy/nightly/profiles.yml and deploy/nightly/entrypoint.sh up to
  dbt_project/docs/engineering_standards.md section 1.2: a one-line why where the reason is not
  obvious, nothing else. No code changes.

refs: >
  #261. Standard: engineering_standards.md section 1.2. Gate:
  .claude/hooks/comment_history_gate.py.

scope_paths:
  - design-mocks/*.py
  - deploy/nightly/profiles.yml
  - deploy/nightly/entrypoint.sh
  - tests/test_no_decision_history_in_code.py
  - .claude/task/261-comments-design-mocks/

decisions_taken: >
  The standard already rules every case, so the sweep is agent-executable under working_agreement
  section 10. A string the code compares, prints, writes or parses is code, not a comment, and
  stays, so a flagged line inside a string stays too; ten flagged lines in design-mocks are HTML
  or CSS the mocks render and stay. A bare string statement that is neither a docstring nor
  assigned is a no-op that only reads as a comment, so the two in gen_top_players.py and
  gen_top_teams.py are swept like comments. Tool directives (noqa, type, pragma) stay.
  Only the pins in tests/test_no_decision_history_in_code.py change besides comments. No new
  mechanism, no new dependency, no recurring cost.

decisions_reserved:
  - A length limit on comments in the gate would be a new rule; it is not added here.

done_when:
  - The AST of every changed design-mocks file, with docstrings and bare string statements removed, equals the AST on the base branch.
  - Every gen_*.py that renders on the base branch writes byte-identical files; the five that fail on the base fail the same way.
  - The mock_css counts of scripts/check_page_css.py are unchanged for every generator.
  - entrypoint.sh and profiles.yml differ from the base only in `#` lines; profiles.yml loads to the same YAML.
  - The only non-comment change is PINNED_LINES and PINNED_FILES in tests/test_no_decision_history_in_code.py.
  - python -m pytest tests passes.
  - The offline gates pass.

amendments: (none)
