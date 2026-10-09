# Acceptance evidence — the checks before each commit start through Python

criteria_demonstrated:
  - EVERY CHECK PASSES HERE. With the committed config, `pre-commit run` passes every check on the staged change.
    `pre-commit run --all-files` passes all nine (large files, merge conflicts, private key, yaml, json, end of
    files, trailing whitespace, ruff, secrets), and `git status` shows no file modified. With main's config the
    same run fails: Smart App Control blocks check-added-large-files.exe (WinError 4551; the Windows
    code-integrity log names the file).
  - ONLY THE ENTRIES. The diff of .pre-commit-config.yaml adds the seven `entry: python -m pre_commit_hooks.<module>`
    lines and one comment; no hook, version, arg or exclusion changes.
  - TESTS. pytest tests/: 1496 passed, 2 skipped; tests/test_lint_config.py reads only the ruff hook, unchanged. CI's
    lint:python runs `pre-commit run --all-files` on Linux, where `python -m` starts the same module.
