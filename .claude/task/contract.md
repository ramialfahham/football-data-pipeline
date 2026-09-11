# Task contract — sweep 2 of 4: decision history out of the hooks and scripts

objective: >
  192 comment and docstring lines in `.claude/hooks/` (82, four files) and `scripts/` (110,
  seventeen files) carry a date, "CPO", "reviewer", "round N" or an MR number. The hooks are the
  guards themselves, and their docstrings are the densest history in the repo. This sweep rewrites
  each such line as the why alone, or removes it when it was only history, lowers the guard's pin
  by exactly what it removed, and brings the handover to the current state of #115. No behaviour
  change anywhere.

refs: >
  GitLab #122 (this task, `Task` template; the What/Why/How below are copied from it). #115 step 8,
  the second of the four sweeps the CPO said "do it" to on 2026-09-11 ("four sweeps, one per
  reviewer territory, each lowering the pin … tests + hooks + scripts (193 → platform) … Each line
  keeps the why and drops the who/when"). The rule: `engineering_standards.md` §1.2 (`!176`). The
  guard: `!177`. Sweep 1: `!178`.

protected_override: >
  `.claude/hooks/git_discipline.py`, `task_contract_gate.py`, `handover_in.py`, `stop_gate.py` —
  comment and docstring lines only, plus ONE deny-message string in `git_discipline.py` (the
  acceptance-gate message loses its "(CPO ruling <date>, #868)" credit; no logic changes); the
  stripping proof shows every other hook line byte-identical. `comment_history_gate.py` — the two
  marker refinements recorded in `decisions_taken`, no other code change.
  The CPO approved this in chat on 2026-09-11 ("do it", to the plan "four sweeps, one per reviewer
  territory, each lowering the pin: … tests + hooks + scripts (193 → platform)"). Under
  working_agreement §11 the durable approval is his merge of this MR, whose head repeats this
  quote under Locked files.

scope_paths:
  - .claude/hooks/**
  - scripts/**
  - tests/test_no_decision_history_in_code.py
  - docs/agent_guardrails.md
  - dbt_project/docs/engineering_standards.md
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: comment and docstring lines only, in four hooks and seventeen scripts; the pin constant
    in one test file; the handover. One dbt model, `mart_team_leaderboards.sql`: two `--` lines
    (a credit the extended marker newly catches), no SQL — EVIDENCE: the file byte-identical
    with `--` comments stripped, `check_layer_contract.py` passed, `LT05` re-linted 0,
    `dbt parse` clean; lineage unaffected because no token the compiler reads changes.

  downstream (a guard's blast radius is every future edit): the four hooks fire on every Bash,
    Edit/Write, Stop and SessionStart event. Nothing in their control flow, patterns, messages or
    exit paths changes — EVIDENCE: for every touched `.py` file, the source with comments and
    docstrings removed (`ast`-based, so a docstring is recognised as such and a string literal is
    not) is byte-identical before and after, output pasted in the evidence; `tests/test_governance_hooks.py`
    (302 tests, the hooks' own suite) green; `ruff check --config .ruff-ci.toml` green. Scripts:
    same proof; the CI scripts among them (`check_*.py`, `export_site_data.py`) are exercised by
    `validate:governance` and `deploy:export` — a comment cannot change their output.

  what stops being enforced if it is wrong: nothing — no enforcement line changes. The one thing a
    docstring sweep can break is a TEST that pins docstring TEXT (`test_fast_gates_and_validate_local_agree`
    pins `FAST_GATES` against the skill's marker block, not prose); the suite run is the check.

  layer_rules: n/a.

  deploy_order: none.

  blast_radius: none in behaviour. In prose: a hook's docstring must still say what it enforces,
    what it denies, what fails open and why. The rewrite keeps every such sentence and drops the
    who/when — "Added 2026-08-20 with CPO approval for the protected-path edit (his 'do both')"
    becomes the reason the gate belongs at turn end as well as in CI.

acceptance_criteria:
  - Every comment or docstring line in `.claude/hooks/` and `scripts/` that carries a date, "CPO",
    "reviewer", "round N" or `!N` is rewritten as the why alone, or removed when it was only
    history — 192 lines in 21 files today under the `!178` definition (hooks 82 in 4 files,
    scripts 110 in 17); 162 in 21 under the final one (hooks 67 in 4, scripts 94 in 16, plus one
    dbt line the extended marker newly catches). All reach 0.
  - No behaviour change: for every touched Python file the text with comments and docstrings
    stripped is byte-identical before and after, except the declared non-comment changes — the
    guard's two marker refinements, one deny-message string in `git_discipline.py`, one
    explanation string in `check_copy_gate.py`'s terminology table (a credit dropped from the
    text the gate prints), and the pin and samples in the guard's test; the governance hook
    suite and CI's ruff are green.
  - The pin in `tests/test_no_decision_history_in_code.py` is lowered to what `count_tree`
    measures — 713 → 495 lines, 109 → 84 files — and the evidence separates the two causes: the
    definition refinements alone take the HEAD tree from 713 to 657 (56 lines, 4 files, each
    classified in the evidence); the sweep takes the refined count from 657 to 495 (162 lines,
    21 files: hooks 67, scripts 94, one dbt line the old definition missed).
  - Nothing load-bearing is lost: a hook's docstring still says what it enforces, what it denies,
    what fails open, and why — without who asked for it or when.
  - The handover (`.claude/active_work.md`) states the current state of #115: steps 1–7 merged,
    the step-8 guard merged, which sweeps are done and which remain.

decisions_taken: >
  THE REWRITE RULE, as in sweep 1: keep the why (what is enforced, what is denied, what fails open,
  the mechanism, the number, the cost of the alternative, a pointer to a design doc); drop who
  decided and when (a title, a name, a date, a log pointer, a reviewer credit, a round, an MR).
  A comment that was ONLY history is removed.

  TESTS ARE A SEPARATE SWEEP (267 lines, 29 files): combining them here would make the
  cto-reviewer read 460 hunks for the 82 that concern a locked file.

  THE HANDOVER RIDES IN THIS REVIEWED COMMIT, in scope from the start, so the "where are we" row
  is current without a post-review artifact commit (the lesson of `!178`).

  THE `reviewer` MARKER IS NARROWED TO A NAMED REVIEWER. The approved pattern says "reviewer"
  because the rule is "which reviewer" — a credit. In this repo the bare word is also the review
  machinery's own concept: `git_discipline.py` describes "what a reviewer reads" on 63 of the
  lines the guard flags across the remaining trees, and rewriting those sentences to avoid the
  word would make the guard's own code worse. So the marker becomes a REVIEW CREDIT: a named
  role (`<role>-reviewer` for the seven routed roles, `scope-auditor`) OR what an unnamed
  reviewer did — "a reviewer caught it", "two reviewers failed it", "found by a reviewer" (the
  reviewer word next to a finding verb). The first draft had the named role alone and claimed
  that was every credit's shape; the round-1 cto and platform reviews showed 10 anonymous
  credits in `tests/` that would have left the ratchet, and the credit shape was added. Measured
  over the whole tree: the final marker catches every credit the `!178` definition caught, plus
  4 it missed (plurals: "reviewers failed twice", "All three reviewers caught it"), and none of
  the ~60 concept lines. Known and accepted: a credit split over a line break ("found by a /
  reviewer rather than", one instance) and a credit written entirely inside a quoted span (zero
  instances) pass the guard; the pin is measured under BOTH definitions in the evidence so the
  effect of the sweep and of the refinement are separated. The refined marker was put to the
  CPO after the round-1 verdicts, with both paths (keep it, or reword the concept lines).
  CPO, 2026-09-11, in chat: "yes, both" — to "OK to keep my new rule?" and to "when I tune a
  guard's rule toward what the written rule means, and I show the before/after numbers in the
  MR — can I just do it, or do I ask you first each time?".

  RULE DOC EDITED IN THE SAME MR (§11): `engineering_standards.md` §1.2's measure paragraph named
  the interim grep "until then"; it now names the hook as the measure. `working_agreement.md`
  §10's agent-executable line is the CPO's to extend and is NOT edited here (see the note in
  the MR head).

  A QUOTED SPAN IS A LITERAL, NOT PROSE — the second refinement. `"CPO ANSWER:"` in
  `check_task_artifacts.py` is a token the code parses and `'2026-05-07 17:55:00'` in
  `restore_from_time_travel.py` is a CLI usage example: 4 lines in `scripts/` that cannot be
  reworded without making the docstring wrong. A double- or single-quoted span that starts a
  token is blanked before the markers are matched; an apostrophe inside a word opens no span; a
  triple quote is a docstring delimiter, not a span, or a one-line docstring would vanish whole.
  BACKTICKS ARE NOT LITERALS: a first draft blanked them too, and measured over the whole tree 23
  of the 34 backticked markers were credits ("caught by `platform-reviewer`", "`!27` fixed this")
  against 11 identifier mentions in the governance tests. The 11 are reworded in sweep 3; the 23
  would have been a permanent hole. Both refinements are form: they move the approved pattern
  toward the rule as written, and the 2×2 in the evidence (old/new definition × HEAD/working
  tree) shows exactly what each moved.

  THRESHOLD — NEW MECHANISM: none. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - The last two sweeps; widening the pattern to `#N`.

done_when:
  - The five criteria proven; `pytest tests/test_no_decision_history_in_code.py tests/test_governance_hooks.py`
    green at the new pin; `ruff check --config .ruff-ci.toml` on every touched `.py` clean; the
    `ast` stripping comparison over every touched file → identical.

amendments:
  - Scope +`docs/agent_guardrails.md` (the hook's row names the markers) and the `reviewer`
    marker narrowed in `comment_history_gate.py` — recorded in `decisions_taken` above. Found on
    the first hook edit: the guard denied "the reviewer definitions are governance artifacts"
    (the concept, not a credit). Authority: the same "do it" the override quotes; the pattern is
    the builder's form choice and the narrowing moves it toward the rule as written.
  - The literal-span rule in `comment_history_gate.py` (recorded in `decisions_taken`), the two
    non-comment message strings in `git_discipline.py` and `check_copy_gate.py` named in
    criterion 2 and the override, and criterion 3 re-measured — its first figures were written
    before either refinement existed. Authority: the same "do it"; form, not scope.
  - After round 1 (cto, platform, scope-auditor FAIL): the reviewer marker extended to the
    anonymous credit shape and the `decisions_taken` paragraph rewritten to the measured facts;
    scope +`dbt_project/models/5_marts/shared/mart_team_leaderboards.sql` (one comment line the
    extended marker newly catches, swept here so dbt stays at 0) and
    +`dbt_project/docs/engineering_standards.md` (§1.2's measure paragraph named an interim grep
    "until" the hook existed; it now names the hook — §11, the rule's doc in the same MR);
    criterion 3 re-measured again (713 → 495 / 109 → 84). The classification question the
    auditor raised was put to the CPO in chat; the two places §11 names as the record of his
    answer — the commit message's `Locked files` line and the MR head — carry his words.
  - After round 3 (scope-auditor): `impact_map` names the dbt model and its evidence; criterion 1's
    refined count corrected to the final definition (162 in 21, hooks 67 — the first figure was
    measured before the credit shape was added).
