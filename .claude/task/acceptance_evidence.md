# Acceptance evidence — decision history out of code: the guard

Every claim below was produced by RUNNING the hook or its tests, on the round-2 code. Mutations
ran on a scratch copy of the guarded trees plus `.claude/hooks/` (the classifier refuses a
deliberate weakening of the real hook, correctly); the count on the copy equals the real tree's.

criteria_demonstrated:
  - THE HOOK DENIES, LIVE, ON THE REAL FILE. While building this branch I attempted an `Edit` on
    `tests/test_no_decision_history_in_code.py` adding `HASH = chr(35)  # the CPO ruled this on
    2026-09-11` → the harness returned the hook's deny: "COMMENT HISTORY GATE: this edit adds a
    comment carrying decision history to a code file — line 1 (date): … A comment says WHY in one
    line; who decided, when, which reviewer, which round, which MR — never in code. That lives in
    the commit message, the MR and the issue … (engineering_standards.md section 1.2)". In the
    tests: `test_hook_denies_a_history_comment_in_a_code_file` (deny on `scripts/…`),
    `test_hook_allows_the_same_text_in_markdown_and_in_task_artifacts` (same text to
    `docs/working_agreement.md` and `.claude/task/contract.md` → no output),
    `test_hook_allows_a_why_only_comment`, `test_hook_checks_write_content_and_multiedit_edits`.
    Registered in `.claude/settings.json` on the `Edit|Write|MultiEdit|NotebookEdit` matcher
    (`NotebookEdit` carries `notebook_path`/`new_source`, neither read → passes at the missing
    `file_path` check).
  - THE PIN, BOTH DIRECTIONS. `PINNED_LINES = 850`, `PINNED_FILES = 174`; `count_tree(REPO)` on
    the frozen tree → `(850, 174)`. Mutation "one flagged line added" to
    `scripts/export_site_data.py` on the copy → `(851, 174)` →
    `test_the_tree_matches_the_pin_in_both_directions` RED with the "new comment line(s) … were
    added" message. Mutation "one flagged line removed, pin not lowered" (from
    `ingestion/api_football/bigquery.py` on the copy) → `(849, 174)` → the same test RED with
    "lower PINNED_LINES / PINNED_FILES … the number moves only in the open". Baseline on the copy:
    14 passed. WHY THE PIN IS 850 AND NOT 481: round 1 found the per-line check blind to wrapped
    `/* … */` continuation lines (`system.css:623`, "!151 shipped exactly this"); fixing the class
    added block-comment lines (+41: dbt models 29, macros 3, dbt tests 5, `site_v2` 4) and Python
    docstring lines (+329: tests 182, scripts 62, hooks 44, ingestion 26, design-mocks 15) —
    `stop_gate.py`'s docstring alone carries three; the hook's own docstring then lost one line to
    its own rule (850 → 849); round 2's corrected block walk (a line that closes one block and
    opens another) found one more (849 → 850).
  - ONE DEFINITION. The test does `import comment_history_gate as gate` and uses `gate.MARKERS`,
    `gate.TREES`, `gate.EXTS`, `gate.is_history_comment`, `gate.flagged_lines`, `gate.count_tree`;
    `test_definition_is_imported_not_copied` asserts the test's own source holds no `re.compile(`
    call and no `TREES = (` / `EXTS = ` definition, and that the hook exports all six names.
    `test_count_tree_counts_what_the_hook_flags` builds a scratch tree and shows the count moves
    by exactly the lines the hook flags, and that markdown is not counted.
    `test_block_comment_continuation_lines_are_comment_lines` pins the round-1 class for `.css`
    (`/* */`), `.sql` (`{# #}`) and `.astro` (`<!-- -->`), and that a slash-star block is NOT a
    comment in `.py`; `test_a_line_that_closes_one_block_and_opens_another_keeps_the_state` pins
    round 2's class with the reviewer's own repro (`*/ .b{} /* reopens` → the next line flagged),
    a line with two pairs where the second is left open, an opener glued to code with no
    whitespace, and a block closed on its own line that must NOT leak into the next;
    `test_two_comment_syntaxes_on_one_line_pick_the_leftmost_open_block` pins round 3's hole —
    `.sql` with `/* */` and `{# #}` on one line in both orders, an unterminated C block whose text
    merely contains the Jinja opener, and `.astro` with `<!-- -->` and `/* */`;
    `test_python_docstrings_are_comment_lines_but_string_literals_are_not`
    pins module and function docstrings (via `ast`), a `FIXTURE = """…"""` literal NOT counted,
    and an unparseable edit fragment's docstring caught by the triple-quote heuristic.
  - THE GUARD PROVES ITSELF. The two pin mutations above; plus mutation "hook deny disabled"
    (`if not hits: return 0` → unconditional `return 0` on the copy) → 2 RED:
    `test_hook_denies_a_history_comment_in_a_code_file`,
    `test_hook_checks_write_content_and_multiedit_edits`. The live deny on the real file is the
    non-scratch proof. `test_hook_ignores_paths_outside_the_repo_and_fails_open_on_garbage`: a
    path outside the repo → no output; stdin "not json" → exit 0, no output. `system.css:623` is
    now flagged by `flagged_lines(css, ".css")` — checked directly.
  - THE GUARD OBEYS ITS OWN RULE. `test_the_guard_files_hold_no_flagged_line` runs
    `flagged_lines(…, ".py")` over the hook and the test → `[]` for both — and that now includes
    their docstrings. The hook's first docstring described a marker with the word for a review
    role and was flagged by its own rule the moment docstrings counted; reworded. The samples in
    the test are assembled at runtime (`chr(35)`, `chr(47)`, split strings) so the file holds no
    literal flagged line.

## Runs, verbatim

```
pytest tests/test_no_decision_history_in_code.py            15 passed
ruff check --config .ruff-ci.toml  (hook, test)             All checks passed!
settings.json                                               json.load OK
[baseline (copy)]                                   15 passed
[mutation: one flagged line added]                   1 failed, 14 passed  (the pin, 851)
[mutation: one flagged line removed, pin not lowered] 1 failed, 14 passed  (the pin, 849)
[mutation: hook deny disabled]                       2 failed, 13 passed  (both real-event tests)
[mutation: leftmost comparison weakened]             1 failed, 14 passed  (the two-syntax test)
tests/test_governance_hooks.py (round-1 code)       exit 0 — no existing gate changed
tests/test_governance_hooks.py (round-2 code)       302 passed in 372.06s
tests/test_governance_hooks.py (round-3 hook)       see review.md; round 4 changes the test file only
```

## What is NOT demonstrated

- That the count reaches zero. That is the four sweep MRs; this branch pins the number so each
  sweep must state its own.
- Issue refs (`#N`) in comments: not in the pattern — a widening reserved for after the first
  sweep (contract `decisions_reserved`); its size is re-measured then, since the definition of a
  comment line changed in round 1.
- A marker inside a string literal on a line that also holds whitespace + a marker character
  (`x = """select 1 -- CPO"""`) reads as a comment line: a known, stated false positive. A plain
  string literal with no marker character on its line is NOT flagged (pinned in the docstring test).
- For an edit FRAGMENT that does not parse as Python, a docstring is recognised only when a line
  opens with a triple quote; a docstring continuation edited without its opener is seen by the CI
  pin (whole file, `ast`), not by the hook. Stated in the hook's docstring.
