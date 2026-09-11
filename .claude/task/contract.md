# Task contract — decision history out of code: an edit-time hook and a pinned count

objective: >
  The code holds 850 comment lines carrying a date, "CPO", "reviewer", "round N" or an MR number —
  builder-written claims about what the CPO decided, in files he never reads. `engineering_standards.md`
  §1.2 has forbidden it for as long as it has existed and it is ignored. This branch adds the
  guard: an edit-time hook that refuses adding such a line to a code file, and a CI test that pins
  the count so it can only move in the open. The sweeps that take the count to zero are four
  later MRs, one per reviewer territory.

refs: >
  GitLab #120 (this task, `Task` template; the What/Why/How below are copied from it). #115 step 8,
  which depends on step 7 (`!176`, the rule and the recipe). The CPO's "do it" in chat on
  2026-09-11 to the five-MR shape — the guard first (a pinned count and an edit-time hook on a
  date / CPO / reviewer / round N / !N in a comment), then four sweeps by reviewer territory.

protected_override: >
  `.claude/hooks/comment_history_gate.py` (new) and `.claude/settings.json` (one hook
  registration). The CPO approved this in chat on 2026-09-11 ("do it", to the plan "a hook that
  refuses an edit adding a date / CPO / reviewer / round N / !N to a comment … Protected path →
  cto + platform review"). Under working_agreement §11 the durable approval is his merge of this
  MR, whose head repeats this quote under Locked files.

scope_paths:
  - .claude/hooks/comment_history_gate.py
  - .claude/settings.json
  - tests/test_no_decision_history_in_code.py
  - docs/agent_guardrails.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: one new hook, one registration line, one test file. No model, script, export, site
    source or CI-config change.

  downstream (a guard's blast radius is every future edit): the hook fires on every `Edit`,
    `Write` and `MultiEdit` in the repo. It reads `tool_input` — `new_string`, `content`, or
    `edits[].new_string` — and denies ONLY when (a) the target path is under one of the code trees
    it lists with a code extension it lists, and (b) a line of the written text is a comment line
    carrying one of the five markers. Everything else — markdown, docs, `.claude/task/**`,
    non-listed trees, a marker outside a comment — passes without output. `NotebookEdit` shares
    the matcher but writes `new_source`, which the hook does not read, so it passes. On any
    exception it returns 0 with no output: fails OPEN, like every hook here. The
    test imports the hook's pattern and trees, so the CI count and the edit-time deny cannot
    diverge; `test_governance_hooks.py` is untouched (no existing gate changes behaviour).
    `check_task_artifacts.py`, the review hash and routing: untouched.

  what stops being enforced if it is wrong: nothing that is enforced today — the rule had no
    enforcement. If the hook mis-denies, the message names the line and the rule, and the fix is
    to write the why without the marker.

  layer_rules: n/a.

  deploy_order: none.

  blast_radius: a NEW DENY on edits. Bounded by (a) and (b) above. Measured false-positive risk:
    a code line where a marker appears after a `#` inside a STRING (`"… # CPO …"`) reads as a
    comment line to the pattern — accepted, stated in the hook, and rare.

acceptance_criteria:
  - An edit-time hook refuses an `Edit`/`Write`/`MultiEdit` that adds a comment line carrying a
    date, "CPO", "reviewer", "round N" or an MR number (`!N`) to a code file, and says where that
    belongs (the commit message, the MR, the issue — `engineering_standards.md` §1.2). Docs,
    markdown and `.claude/task/` are not code and are untouched by it.
  - A test pins the count of such lines already in the code (850 across 174 files today) and
    fails if the count RISES — or if it falls without the pin being lowered, so every sweep moves
    the number in the open.
  - The hook and the test share one definition of "a comment line carrying history" and one list
    of code trees, and a test pins them against each other so they cannot drift.
  - The guard proves itself: deleting one flagged line without lowering the pin turns the test
    red; adding one turns it red; the hook denies a real `Edit` that adds one and allows the same
    text in a markdown file.
  - The hook itself and the test contain zero flagged lines — they obey the rule they enforce.

decisions_taken: >
  THE PATTERN IS THE ONE HE SAID "DO IT" TO: date, CPO, reviewer, round N, !N. Issue refs (`#N`)
  would add 535 lines (962 total, 208 files), mostly dead GitHub-era pointers — a widening for
  after the first sweep, recorded in #120's Not-in-scope, not taken here.

  THE PIN FAILS IN BOTH DIRECTIONS. A one-sided "must not rise" pin lets sweeps go unrecorded and
  the number drift; a two-sided pin makes every sweep MR state its new count. Same design as the
  dead-reference guard's digest.

  THE HOOK CHECKS THE WRITTEN TEXT, NOT THE FILE. An Edit that re-includes an existing flagged
  line is denied until the marker goes — ratchet-by-touch. A Write of a file that still holds one
  is denied until cleaned. Deliberate: the sweeps get help from every ordinary edit.

  ONE DEFINITION, IMPORTED. The test imports `MARKERS`, `TREES`, `EXTS` and `is_history_comment`
  from the hook; a pin test asserts the test module holds no copy. The stop-gate/validate-local
  parity test is the precedent.

  THRESHOLD — NEW MECHANISM: yes, one new hook and one CI test, approved above. THRESHOLD —
  RECURRING COST: one regex pass over the written text per Edit/Write — microseconds; one file
  walk per CI run (~1 s).

decisions_reserved:
  - Widening the pattern to `#N` issue refs — after the first sweep, with its number (535).
  - The four sweeps and their order.

done_when:
  - The five criteria proven; `pytest tests/test_no_decision_history_in_code.py
    tests/test_governance_hooks.py` green; `ruff check --config .ruff-ci.toml` clean on both new
    files.
  - Mutations run on a scratch copy (the classifier refuses weakening the real hook): count pin
    both directions; hook deny/allow on a real event.

amendments:
  - Scope +`docs/agent_guardrails.md`: its hook table inventories every hook in
    `.claude/settings.json`; a new hook without a row is the doc-sync defect the scope-auditor
    hunts. Bookkeeping inside the approved task, not a decision. Also corrected the impact_map's
    `NotebookEdit` sentence: it shares the matcher and passes because the hook does not read
    `new_source` — not "not matched".
  - Round 1 (platform-reviewer FAIL; cto-reviewer PASS; scope-auditor PASS). The finding: a
    per-line marker check is blind to the continuation lines of a wrapped `/* … */` block —
    `site_v2/src/styles/system.css:623` narrates what `!151` shipped on such a line and was neither
    counted nor deniable. Fixed as a CLASS, not a line: `comment_lines()` now treats every line
    inside a block comment of the file's language (`/* … */`, `<!-- … -->`, `{# … #}`) and every
    line of a Python docstring (`ast` when the text parses; a line opening with a triple quote when
    it is an edit fragment) as a comment line. Measured before fixing: block continuation lines
    +41, docstring lines +329 — `stop_gate.py`'s own docstring carries three. The pin moves from
    481/140 to **849/174**; the criteria and #120 are updated to say so. Also taken from the same
    review: extension matching is case-insensitive; skip-directories match as path segments.
    The hook's first docstring described the markers with the word for a review role and flagged
    ITSELF once the docstring rule existed — reworded, which is the rule reading source, not intent.
  - Round 2 (platform-reviewer FAIL; cto-reviewer PASS; scope-auditor PASS). The finding, with a
    repro: a line that CLOSES one block and OPENS another (`*/ .b{} /* reopens`) cleared the block
    state and hid the reopened block's continuation lines from the deny and the pin; the same root
    (`line.find(opener)` sees only the first opener; an opener glued to code without whitespace
    never entered block state) had two more shapes. Fixed as the class: `_open_at_end()` walks the
    line matching every opener to its closer in order, from the start of a fresh line or from just
    after the closer that ended a block; a line with any opener is a comment line whether or not
    whitespace precedes it. Pinned by `test_a_line_that_closes_one_block_and_opens_another_keeps_the_state`
    with the reviewer's repro plus the two sibling shapes and a same-line-closed block that must
    NOT leak. The corrected walk finds one more line in the tree: pin 849 → **850**/174. Round 3
    is the cap; it re-runs all three reviewers on the fixed hook.
  - Round 3 (platform-reviewer FAIL; cto-reviewer PASS; scope-auditor PASS). Not a bypass this
    time — a coverage hole: no test put two comment syntaxes on one line (`.sql` has `/* */` and
    `{# #}`; `.astro` has `/* */` and `<!-- -->`), so the leftmost-opener comparison in
    `_open_at_end` was exercised only with one pair and a "last pair wins" regression would pass.
    Taken: `test_two_comment_syntaxes_on_one_line_pick_the_leftmost_open_block` — both orders, an
    unterminated C block whose text merely contains the Jinja opener, and the Astro pair;
    mutation "leftmost comparison weakened" on the scratch copy turns exactly that test red. No
    hook change; the pin stays 850/174. Round 4 runs under a `rounds_cap_override` in `review.md`,
    recorded as on `!173` and `!174`: to clear a standing FAIL by review, not to ship past one.
