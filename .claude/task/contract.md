# Task contract — sweep 4 of 4: decision history out of site_v2, ingestion and design-mocks

objective: >
  250 comment and docstring lines in `site_v2/src/` (99), `ingestion/` (62), `design-mocks/` (72)
  and `site_v2/scripts/` (17) — 56 files, `strings.ts` alone 47 — carry a date, "CPO", a review
  credit, "round N" or an MR number. This sweep rewrites each such line as the why alone, or
  removes it when it was only history, lowers the guard's pin to zero, and brings the handover to
  the current state of #115. No behaviour change: no code line, string value, style rule or
  rendered output changes.

refs: >
  GitLab #124 (this task, `Task` template; the What/Why/How below are copied from it). #115 step 8,
  the last of the four sweeps the CPO said "do it" to on 2026-09-11 ("four sweeps, one per
  reviewer territory, each lowering the pin … Each line keeps the why and drops the who/when").
  The rule: `engineering_standards.md` §1.2 (`!176`). The guard: `!177`, refined in `!179`.
  Sweeps 1–3: `!178`, `!179`, `!180`.

protected_override: none — no protected path is touched.

scope_paths:
  - site_v2/src/**
  - site_v2/scripts/**
  - ingestion/**
  - design-mocks/**
  - tests/test_no_decision_history_in_code.py
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: comment and docstring lines only, in up to 56 files across four trees; the pin
    constants in one test file; the handover.

  downstream: `ingestion/` is the nightly (Cloud Run `fdp-nightly`) and the `test:python` suite;
    `site_v2/src` and `site_v2/scripts` are the Astro build, `validate:ui` and `npm test`;
    `design-mocks/` is the mock generator (`design-mocks/README.md`), run by hand. A comment cannot
    change any of their output — EVIDENCE: for every touched Python file, the source with comments
    and docstrings removed (`ast` + `tokenize`) is byte-identical before and after; for every
    touched `.ts`/`.mjs`/`.astro`/`.css` file, the sequence of NON-comment lines (by the guard's
    own `comment_lines`, per language) is identical before and after; `pytest tests/`, `npm test`
    in `site_v2`, ruff and `validate-local`'s UI gate green with the same counts as `main`.

  what stops being enforced if it is wrong: nothing — no enforcement line changes. The one
    class a comment sweep can break in these trees is a check that READS comment text:
    `site_v2/scripts/check-page-specs.mjs` and `check-metric-labels.test.mjs` parse `strings.ts`
    by its double-quoted entries, not its comments — verified by running `npm test`; the mock
    generators' `check_*.py` read the rendered mocks, not the generators' comments.

  layer_rules: n/a — no logic moves between layers; `scripts/export_*.py` is not touched.
  deploy_order: none.

  blast_radius: none in behaviour. In prose: `strings.ts`'s label comments must still say which
    labels are locked and why a wording was chosen ("football Finnish uses `kunto` for form");
    a loader's docstring must still say what incident class it guards against; a mock's header
    must still name the wireframe it renders.

acceptance_criteria:
  - Every comment or docstring line in the four trees that carries a date, "CPO", a review
    credit, "round N" or `!N` is rewritten as the why alone, or removed when it was only history
    — 250 lines in 56 files today. `count_tree` over the whole repo → (0, 0).
  - No behaviour change: for every touched Python file the text with comments and docstrings
    stripped is byte-identical before and after, EXCEPT the pin constants and thirteen lines in
    six `design-mocks` generators that are comments the `ast` stripper cannot see: nine CSS
    `/* … */` comment lines inside the Python STRING each generator emits as the mock's stylesheet
    (`gen_competitions.py` 1, `gen_competition_hub.py` 1, `gen_matches.py` 1, `gen_top_players.py`
    2, `gen_top_teams.py` 2, `rows.py` 2), and four lines in two module-level bare triple-quoted
    strings used as block comments (`gen_top_players.py:84-106`, `gen_top_teams.py:79-99` — no-op
    expression statements, never emitted). The proof for the nine is the rendered mocks, CSS
    comments stripped, byte-identical between HEAD's generators and the branch's; for the four,
    `ast` shows them as bare `Expr(Constant)` statements that nothing reads; for every touched
    `.ts`/`.mjs`/`.astro`/`.css`
    file the non-comment line sequence is identical; `pytest tests/` (same count as `main`),
    `npm test` in `site_v2` (same count), ruff and the UI gate are green.
  - The pin in `tests/test_no_decision_history_in_code.py` is lowered to what `count_tree`
    measures: 250 → 0 lines, 56 → 0 files.
  - Nothing load-bearing is lost: a locked display rule, a loader's safety reason, a mock's
    wireframe pointer still say what they enforce and why — without who ruled it or when.
  - The handover states step 8 done (guard merged, four sweeps merged, pin at zero) and step 9
    next.

decisions_taken: >
  THE REWRITE RULE, as in sweeps 1–3: keep the why (the rule, the deviation, its cost, the
  mechanism, the number, a pointer to the design doc or issue); drop who decided and when (a
  title, a name, a date, a log pointer, a reviewer credit, a round, an MR). A comment that was
  ONLY history is removed. A quoted ruling that IS the rule (`strings.ts`: "more precise than just
  Vorlagen") stays as the rule; the date and the title beside it go.

  A WHY THAT IS FALSE AS WRITTEN IS CORRECTED, NOT PRESERVED — the rule sweeps 1 and 3 applied and
  declared (`sources.yml`'s "nothing reads them"; `test_refetch_cadence.py`'s "unmerged branch").
  Two comments here said the Top teams block was "specified and NOT built" beside code that
  imports and renders it (`site_v2/src/pages/[lang]/index.astro` header, `site_v2/src/lib/types.ts`
  landing docblock); they now say all three home modules are built. Stripping only the date from
  a false sentence would leave a false sentence with no history to explain it. Comment text only;
  no string, markup or type changes.

  THE GUARD'S DEFINITION IS NOT TOUCHED. Lines the definition cannot see are swept by eye and
  named in the evidence, so the two-sided count stays honest.

  THRESHOLD — NEW MECHANISM: none. THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - Widening the pattern to `#N`; any change to the guard's definition; shortening comments that
    carry no marker; #115 step 9.

done_when:
  - The five criteria proven; `pytest tests/` green at the zero pin with the same count as
    `main`; `npm test` in `site_v2` green with the same count; `ruff check --config
    .ruff-ci.toml` on every touched `.py` clean; the two stripping comparisons over every touched
    file → identical except the pin.

amendments:
  - Criterion 2 names the five CSS-comment-in-string lines in four `design-mocks` generators and
    their proof (rendered mocks identical with CSS comments stripped). Found when the `ast`
    stripper reported them as string changes: the generators build the mock's `<style>` block
    from a Python string, so a CSS comment there is a comment to the guard and to the browser but
    a literal to Python. Leaving them would have left the pin at 5 with a permanently-denied
    edit path into those strings. Also recorded: `gen_competitions.py` and
    `gen_block_standard.py` do not run on `main` either (the mocks have drifted from the
    registry) — pre-existing, out of scope, named in the evidence.
  - After round 1 (scope-auditor): `decisions_taken` names the false-why correction rule and the
    two files it applied to (`index.astro`, `types.ts`) — the rule sweeps 1 and 3 used and
    declared, omitted here by oversight; the auditor found the change undeclared, not wrong.
  - After round 1 (platform-reviewer): eight more history lines the guard cannot see — CSS
    comment CONTINUATION lines inside emitted stylesheet strings (four files) and a bare
    triple-quoted block comment in two generators — found by a reviewer's grep and swept; the
    criterion-2 exception list grows from five lines in four files to thirteen in six, with the
    `ast` proof for the two bare strings added. The guard's blind spot for these shapes (a `.py`
    file has no block-comment pairs; a bare string is not a docstring) is named in the evidence;
    widening the definition stays reserved.
