# Acceptance evidence — sweep 2 of 4: decision history out of the hooks and scripts

criteria_demonstrated:
  - EVERY FLAGGED LINE IN `.claude/hooks/` AND `scripts/` IS GONE. Before, under the `!178`
    definition: hooks 82 lines in 4 files, scripts 110 in 17 (192 in 21). Under the final
    definition, on the same HEAD tree: hooks 67 in 4, scripts 94 in 16 (one credit the old
    definition missed, "All three reviewers caught it", is now counted). After: **0 lines, 0
    files** in both trees under BOTH definitions (per-tree table in `matrix.py` output below).
    Every line was rewritten by hand, every edit passing the edit-time hook, which refuses a
    rewrite that still carries a marker. The rule applied: keep the why, drop who decided and
    when. Examples: `task_contract_gate.py`'s PROTECTED_PREFIXES comment keeps why
    `.claude/commands/` and `.mcp.json` are guard-class ("a command file is the same high-stakes
    class as a hook"; "auto-launches a command every session") and loses "per the CPO ruling
    <date> (this branch's escalations.log)"; `git_discipline.py`'s rounds-gate docstring keeps
    what the cap does and that the override records the product owner's go-ahead, loses the
    dated approval; `export_site_data.py` keeps every ruling as the rule ("the page renders the
    order it is served", "if a board is missing, the user may not even notice, so don't show")
    and loses "(CPO <date>, escalations.log)"; `sync_metric_docs_blocks.py` keeps "ANY
    occurrence is wrong and there is no phrasing to enumerate" and loses "Caught by
    football-analytics-expert-reviewer". A comment that was only history is removed
    (`export_site_data.py`: the list of merged MR numbers; a pointer to a per-task evidence file
    since overwritten by other tasks). One dbt line the refined marker newly catches,
    `mart_team_leaderboards.sql:148` "that reviewers failed twice", is swept in the same MR:
    the file is byte-identical with `--` comments stripped (`True`, scripted), `LT05` re-linted 0,
    `check_layer_contract.py` passed, and `dbt parse` (the pinned `.venv/Scripts/dbt.exe`, a
    scratchpad-only `dev_scratch` profile, no connection) → no errors, the one pre-existing
    unused-config warning only.
  - NO BEHAVIOUR CHANGE, PROVEN ON EVERY TOUCHED PYTHON FILE. `prove_py_comments_only.py`: for
    each modified `.py`, HEAD's text and the working text with docstrings removed (`ast`: module,
    class and function first-statement string constants) and comments removed (`tokenize`), blank
    lines dropped, compared. Output: **18 identical, 4 differ, of 22** — and the four are exactly
    the declared non-comment changes, each shown in full by the script: (1)
    `comment_history_gate.py`: `_ROLES`, `_FOUND`, the `reviewer` marker, `_TRIPLE`, `_LITERAL`,
    and `marker_kind` matching on the blanked line — nothing else; (2) `git_discipline.py`: one
    deny message string, "(CPO ruling <date>, #868). " removed, sentence re-joined; (3)
    `check_copy_gate.py`: the Finnish terminology row's explanation string loses "(CPO
    correction, #867)"; (4) the guard's test: pin, sample, one new test, assertions added to one.
    The dbt file: 2 comment lines changed, SQL untouched (`git diff --stat`: 2+/2−, both `--`
    lines). Suites: `pytest tests/test_no_decision_history_in_code.py` → 16 passed at the new pin;
    `pytest tests/test_governance_hooks.py` → **302 passed** with the final hooks;
    `pytest tests/test_export_landing.py tests/test_export_site_data.py
    tests/test_no_dead_issue_refs.py tests/test_governance_doc_parity.py
    tests/test_sync_metric_docs_blocks.py` → 165 passed, 1 skipped; `ruff check --config
    .ruff-ci.toml` on all 22 touched `.py` files → "All checks passed!". The CI scripts run as CI
    runs them: `check_copy_gate.py` → "COPY GATE ok: 474 strings"; `check_registry_var_sync.py`
    → OK; `check_layer_contract.py` → passed; `sync_metric_docs_blocks.py --check` → "OK: 163
    metric docs blocks match"; `report_process_health.py` prints the same figures as before.
  - THE PIN IS LOWERED TO THE MEASURED COUNT, AND THE TWO CAUSES ARE SEPARATED. `matrix.py`
    counts the HEAD tree (a `git archive HEAD` of the guarded trees) and the working tree under
    HEAD's hook and the working hook:

        |               |  HEAD tree  | working tree |
        | HEAD hook     | (713, 109)  |  (562, 96)   |
        | working hook  | (657, 105)  |  (495, 84)   |

    The definition refinements alone: 713 → 657 on the unchanged tree. `dropped_lines.py` lists
    every one of the 70 lines the old definition flags on the working tree and the new one does
    not; by eye: ~60 are the bare word "reviewer" used as the review gate's own concept ("what a
    reviewer reads", "a required reviewer", "a reviewer with no routing row"), 5 are quoted
    tokens or usage examples (`"CPO ANSWER:"`, `'CPO ANSWER'`, `'2026-05-07 17:55:00'` ×2, an ISO
    string example in `format.ts`), 3 are code string literals the old comment detector matched
    by accident (two `print("… -- …")` in `design-mocks`, one assertion message in
    `test_raw_merge_on_write.py`), 1 is a quoted phrase inside prose (`strings.ts:221` `"STILL
    AWAITING THE CPO"`) and 1 is a credit split over a line break
    (`test_nightly_entrypoint_parity.py:277-278` "found by a / reviewer rather than") — the last
    two are sweep-4 and sweep-3 lines and are named here so they are swept by eye. The sweep
    alone: 657 → 495 under the new definition (162 lines, 21 files: hooks 67 → 0, scripts 94 →
    0, dbt 1 → 0, every other tree unchanged), 713 → 562 under the old. `PINNED_LINES = 495`,
    `PINNED_FILES = 84`; the pin test passes in both directions.
  - THE GUARD'S REFINEMENTS ARE TESTED AND MUTATION-PROVEN. Round 1 found the first draft's
    reviewer marker (named role only) missed 10 anonymous credits in `tests/` ("a reviewer caught
    it", "a reviewer produced four rewrites"); the marker now also matches the reviewer word next
    to a finding verb. `credit_shape.py` measured that shape over the whole tree before it went
    in: 14 lines matched that the named-role marker missed, all credits — including 4 the `!178`
    definition itself missed (plurals) — and 0 concept lines. New test
    `test_a_quoted_span_is_a_literal_and_the_rest_of_the_line_is_prose`: a quoted token is not a
    marker; a quoted usage example is not; a marker outside the quotes still is; an apostrophe
    inside a word opens no span and a quote ending inside a word closes none; backticks are not
    literals; a one-line docstring is a comment line. `test_every_marker_kind_is_flagged_and_a_why_is_not`
    also asserts the bare word and "every reviewer required by" are not markers, and four
    anonymous-credit shapes and `scope-auditor` are. `mutate_history_guard2.py`, on a scratch
    COPY of the trees and the hook (the real hook is never edited): 10 mutations, **10 killed** —
    (1) one flagged line added → pin red; (2) one removed without lowering the pin → pin red;
    (3) deny disabled → 2 real-event tests red; (4) leftmost-opener comparison weakened → red;
    (5) backticks blanked as literals → pin AND the new test red; (6) triple quotes not stripped
    before blanking → both red; (7) apostrophes open spans → red (its first sample SURVIVED —
    the date sat after the apostrophe pair, not between; fixed); (8) reviewer marker widened
    back to the bare word → 3 red; (9) anonymous credit shape dropped → pin and marker-kind test
    red; (10) closing-quote lookahead dropped → red (added after round 1 showed it unpinned).
  - NOTHING LOAD-BEARING LOST. Each hook docstring still states what it enforces, what it denies,
    what fails open and why: `stop_gate.py` keeps "blocks the stop ONCE … `stop_hook_active`
    prevents loops" and the stash rule; `handover_in.py` keeps the 16,000-character cap and why
    it announces truncation; `task_contract_gate.py` keeps every protected-path justification,
    the structural-surface rule, and that the override quotes the product owner's approval;
    `git_discipline.py` keeps the hash-identity explanation, the exclusion-vs-hash-exclusion
    distinction, and the rounds cap with whose go-ahead the override records. Scripts:
    `report_process_health.py` keeps that the reference point is computed, never typed, and that
    no threshold is set; `drop_injuries_raw_tables.py` keeps "has outlived one removal already …
    name its consumer first"; `export_site_data.py` keeps every consumption-layer reason (the
    analytics-engineer's round-1 check, docstring by docstring). One false sentence corrected on
    the way: `sync_metric_docs_blocks.py`'s "the property platform-reviewer required in MR3" now
    states the property itself (a fresh run reproduces the file byte for byte). The rule doc
    `engineering_standards.md` §1.2, which said the interim grep was the measure "until" the hook
    existed, now names the hook as the measure (§11: a rule's doc edited in the same MR).
  - THE HANDOVER STATES THE CURRENT STATE OF #115. `.claude/active_work.md` "WHERE WE ARE": steps
    1–7 merged, the step-8 guard merged, sweep 1 done, sweep 2 this branch, sweeps 3 and 4 with
    their measured sizes, step 9 remaining. 15,848 characters (`len()`), under the 16,000 cap.

## What is NOT demonstrated
- The remaining trees (`tests` 245 lines / 28 files, `site_v2` 116 / 23, `ingestion` 62 / 18,
  `design-mocks` 72 / 15) are untouched — sweeps 3 and 4. The 11 backticked routing-key mentions
  in the governance tests, flagged because backticks are not literals, are among sweep 3's lines.
- A credit written entirely inside a quoted span passes the guard by design (a quoted span is a
  literal); zero instances in the tree today (grep by platform-reviewer and by `literal_spans.py`).
- `report_process_health.py` still reads the frozen `escalations.log`; that it reads a frozen
  file is a separate question, not this sweep's.
- The hooks were not exercised on live events beyond their own suite (302 tests); the
  comment-only proof is the `ast`/`tokenize` comparison, not a runtime trace.
