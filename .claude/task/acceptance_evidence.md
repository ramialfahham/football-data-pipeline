# Acceptance evidence — sweep 4 of 4: decision history out of site_v2, ingestion and design-mocks

criteria_demonstrated:
  - EVERY FLAGGED LINE IN THE FOUR TREES IS GONE, AND THE WHOLE TREE IS AT ZERO. Before: `count_tree`
    → 250 lines in 56 files (`site_v2/src` 99 / 18, `ingestion` 62 / 18, `design-mocks` 72 / 15,
    `site_v2/scripts` 17 / 5; by marker: date 172, product owner 56, review credit 13, MR 7,
    round 2). After: **(0, 0)** for the whole repository. Every line was rewritten by hand, every
    edit passing the edit-time hook. The rule applied: keep the why, drop who decided and when.
    Examples: `strings.ts` keeps "a suffix is EARNED by equity, not a way to build it" and every
    quoted ruling as the rule ("more precise than just Vorlagen", "they all stack together or
    not"), and loses "CPO reversed his earlier ruling on <date> after seo-expert-reviewer argued
    it"; the loaders keep "raw appends and never deletes … Base decides" and the measured damage
    ("UCL 340 went 25 players to 0") and lose "(CPO ruling <date>)" and "on <date>";
    `design-mocks/rows.py` keeps every design quote ("this shouldn't be much different from next
    match design") and loses "CPO, <date>:". Provenance of user-visible copy is kept as the RULE
    (§10: "Supplied copy", "approved copy", "the product owner's call") without the title and
    date. Two stale facts corrected because the why was false as written: `index.astro` and
    `types.ts` said Top teams was "specified and NOT built" — it is built (#41, wired at
    `index.astro:77`); the header now says all three modules are built.
  - NO BEHAVIOUR CHANGE, PROVEN PER LANGUAGE. Non-Python (`prove_noncomment_lines.py`: the
    sequence of non-comment lines by the guard's own `comment_lines`, per language): **23
    identical, 0 differ, of 23** `.ts`/`.mjs`/`.astro`/`.css` files. Python
    (`prove_py_comments_only.py`, `ast` + `tokenize`): **27 identical, 7 differ, of 34** — the
    pin file, and six `design-mocks` generators whose changed lines are comments the stripper
    cannot see: nine CSS `/* … */` comment lines INSIDE the Python string each generator emits as
    the mock's stylesheet (`gen_competitions.py` 1, `gen_competition_hub.py` 1, `gen_matches.py` 1,
    `gen_top_players.py` 2, `gen_top_teams.py` 2, `rows.py` 2), and four lines in two module-level
    bare triple-quoted strings used as block comments (`gen_top_players.py:84-106`,
    `gen_top_teams.py:79-99`). The guard counts the CSS lines as comment lines (they are, in the
    emitted CSS) but cannot see their CONTINUATION lines (a `.py` file has no block-comment pairs)
    nor a bare string that is not a docstring — the platform-reviewer's grep found eight such
    lines after the guard reported zero, all swept by hand. Proof the nine change nothing rendered:
    `render_mocks.py` ran every generator on the working tree and on HEAD's generators
    (stash-dance, in-turn), captured the seven emitted `.html` files with CSS comments stripped,
    and `diff -r` → **identical** (re-run after the eight extra lines: identical). Proof the four
    change nothing at all: `ast.parse` shows both strings as bare `Expr(Constant)` statements
    after the module docstring, referenced by nothing. The generators that do not run (`gen_competitions.py`
    "undeclared type change — missing intercontinental_super_cup"; `gen_block_standard.py` "no
    entry for BPL, EKS, TSL") fail identically on HEAD and on the branch — pre-existing drift
    between the mocks and the registry, out of scope. `pytest tests/` → **1,057 passed, 1 skipped, 14 subtests
    passed** (9:08; the same count as `main`); `npm test` in `site_v2` → **83 pass, 0 fail**
    (the same as `main`); `ruff check --config .ruff-ci.toml ingestion/ design-mocks/` → "All
    checks passed!".
  - THE PIN IS ZERO. Whole-tree `count_tree` before: (250, 56); after: **(0, 0)** — measured, and
    equal to 250 − 250, 56 − 56. `PINNED_LINES = 0`, `PINNED_FILES = 0`; from here any new line
    carrying history is a CI failure and an edit-time deny.
  - NOTHING LOAD-BEARING LOST. `strings.ts` still says which strings are locked/approved/supplied
    copy and why each wording was chosen (the Finnish `kunto`/`muoto`, the masculine `Der
    Top-Spieler` warning, the four-string trap on the deserved block); every loader's docstring
    still names the incident class it guards against (the rate-limited HTTP 200 that looked like
    an empty squad; the delete whose trigger cannot tell "no players" from "we lost the players")
    and the numbers (26 dropped calls, ~23 of 1,265 teams, 27 → 17 events); every mock header
    still names its wireframe, its issue and the rules it renders; `registry.py`'s two cost fields
    still say they are cost decisions (§10).
  - THE HANDOVER STATES STEP 8 DONE: guard merged, four sweeps, pin 850 → 0, step 9 next.

## What is NOT demonstrated
- The guard is blind to two comment shapes in Python: a CSS block comment's continuation lines
  inside a string, and a bare triple-quoted string used as a block comment. Both were swept by
  eye here and are at zero; a future line of either shape will not be counted or denied. Widening
  the definition is reserved; the shapes are named so the next builder knows the grep to run.
- Comment lines with no marker were not shortened — out of scope, and a separate question for
  the CPO (the sweep removes who/when; it does not edit for length).
- `gen_competitions.py` and `gen_block_standard.py` do not render on `main` either; their drift
  from the registry (three new competitions, one renamed type) is a design-mocks maintenance item,
  not this sweep's.
- STRING LITERALS THAT ARE PROGRAM OUTPUT are outside the comment/docstring definition and
  deliberately untouched — changing them changes what a mock renders or a check prints, which
  criterion 2 forbids. The complete list in `design-mocks/` (grep `CPO|20\d\d-\d\d-\d\d` over
  `*.py`, minus comments): rendered mock text in `gen_competition_hub.py:232` (a `<p>` in the
  emitted page), `gen_competitions.py:700` (a `<p>`), `gen_navmap.py:67,257,351` and
  `gen_sitemap.py:51,62,81` (the sitemap/navmap pages' own labels); printed check labels in
  `check_home.py:40`, `check_teams.py:100,111`, `check_players.py:97,111`; a fixture URL in
  `gen_navmap.py:171`. The guard's `count_tree` classes none of them as a comment line (verified
  per line with `comment_lines`), so the (0, 0) claim is exact. Message strings and assertion
  messages in `tests/` are the same class. Whether the definition should widen to output strings
  is reserved.
