# Task contract — sweep 3 of 4: decision history out of the tests

objective: >
  245 comment and docstring lines in `tests/` (28 files; `test_governance_hooks.py` alone 103)
  carry a date, "CPO", a review credit, "round N" or an MR number. This sweep rewrites each such
  line as the why alone, or removes it when it was only history, lowers the guard's pin to the
  measured count, and brings the handover to the current state of #115. No behaviour change: no
  test predicate, fixture, or assertion changes.

refs: >
  GitLab #123 (this task, `Task` template; the What/Why/How below are copied from it). #115 step 8,
  the third of the four sweeps the CPO said "do it" to on 2026-09-11 ("four sweeps, one per
  reviewer territory, each lowering the pin … Each line keeps the why and drops the who/when").
  The rule: `engineering_standards.md` §1.2 (`!176`). The guard: `!177`, refined in `!179`.
  Sweeps 1–2: `!178`, `!179`.

protected_override: none — no protected path is touched.

scope_paths:
  - tests/**
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: comment and docstring lines only, in up to 28 test files; the pin constants in
    `tests/test_no_decision_history_in_code.py`; the handover.

  downstream: the tests are CI's `test:python` job and the `validate-local` skill; a comment
    cannot change a test's outcome — EVIDENCE: for every touched file, the source with comments
    and docstrings removed (`ast` + `tokenize`) is byte-identical before and after, output pasted
    in the evidence; `pytest tests/` green with the same pass count as `main`; ruff green.

  what stops being enforced if it is wrong: nothing — no assertion line changes. The one thing a
    docstring sweep can break is a test that reads ANOTHER test's docstring text: `grep` for
    `__doc__` and `inspect.getdoc` in `tests/` before the sweep; the suite run is the check.

  layer_rules: n/a. deploy_order: none.

  blast_radius: none in behaviour. In prose: a test's docstring must still say what it pins and
    why the case exists — "the case every other test misses" stays; "platform-reviewer found it
    by reading round 2" goes.

acceptance_criteria:
  - Every comment or docstring line in `tests/` that carries a date, "CPO", a review credit,
    "round N" or `!N` is rewritten as the why alone, or removed when it was only history — 245
    lines in 28 files today, plus the two split-line credits and the plural "rounds 6-12" the
    guard cannot see, swept by eye. `count_tree` over `tests/` → 0.
  - No behaviour change: for every touched test file the text with comments and docstrings
    stripped is byte-identical before and after, except the pin constants and ONE fixture string
    (`GOOD_BODY` in `test_governance_hooks.py`, re-joined so its `## <role>` header no longer
    starts a source line — the guard read it as a comment line; its value byte-identical to
    HEAD's, proven by `ast.literal_eval` of both); `pytest tests/` is green with the same pass
    count as `main`; ruff green.
  - The pin in `tests/test_no_decision_history_in_code.py` is lowered to what `count_tree`
    measures: 495 → 250 lines, 84 → 56 files (measured; 495 − 245 and 84 − 28).
  - Nothing load-bearing is lost: a test's docstring still says what it pins and why — without
    who found it or in which round.
  - The handover states sweep 3 done, sweep 4 remaining, step 9 after.

decisions_taken: >
  THE REWRITE RULE, as in sweeps 1–2: keep the why (what the test pins, the defect class it
  exists for, the number, the mechanism, a pointer to the rule or doc); drop who decided and when
  (a title, a name, a date, a log pointer, a reviewer credit, a round, an MR). A comment that was
  ONLY history is removed.

  THE GUARD'S DEFINITION IS NOT TOUCHED. Sweep 2 tuned it; this sweep only lowers the pin.
  Lines the definition cannot see (a credit split across a line break, "rounds 6-12") are swept
  by eye and named in the evidence, so the two-sided count stays honest.

  THRESHOLD — NEW MECHANISM: none. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - Sweep 4; widening the pattern to `#N`; any change to the guard's definition.

done_when:
  - The five criteria proven; `pytest tests/` green at the new pin with the same pass count as
    `main`; `ruff check --config .ruff-ci.toml tests/` clean; the stripping comparison over every
    touched file → identical except the pin.

amendments:
  - Criterion 2 names the one non-comment change: the `GOOD_BODY` fixture string in
    `test_governance_hooks.py` re-joined (value identical) so a `## analytics-engineer-reviewer`
    header — a routing key the fixture must carry literally — no longer starts a source line and
    is no longer counted as a comment. Found when the file reached 1 flagged line that was not a
    comment; the alternative (a permanent line in the pin that every future edit of the fixture
    would be denied for) is worse. Criterion 3 carries the measured figures.
