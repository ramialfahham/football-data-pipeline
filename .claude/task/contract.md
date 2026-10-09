# Task contract — the checks before each commit start through Python

objective: >
  .pre-commit-config.yaml starts each pre-commit-hooks check as `python -m <module>`, so no separately
  built helper program runs and Smart App Control, kept on, no longer blocks commits on this machine.

refs: >
  Commits failed locally: the Windows code-integrity log shows Smart App Control blocking the
  check-added-large-files, end-of-file-fixer and trailing-whitespace-fixer launchers pre-commit built.
  Smart App Control stays on, and the hooks start through Python instead: approved in chat, 2026-10-09.

scope_paths:
  - .pre-commit-config.yaml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

acceptance_criteria:
  - Every check of the config passes on this machine on the staged change, and on --all-files with no file modified.
  - Only the seven entry lines and one comment change in .pre-commit-config.yaml.
  - pytest tests/ passes; CI's lint:python runs the same config.

decisions_taken: >
  Smart App Control stays on; the seven pre-commit-hooks checks start as `python -m`: approved in chat,
  2026-10-09.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - Smart App Control and every other machine setting: the CPO's.

done_when:
  - pre-commit run, pre-commit run --all-files and pytest tests/ pass; git commit passes every check.
  - The criteria are shown in .claude/task/acceptance_evidence.md.

amendments: (none)
