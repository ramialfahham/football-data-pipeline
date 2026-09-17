# Review — feat/153-design-inventory — 2026-09-17

diff_sha256: ff88a5fef87b4a46a215b0096289bd78267a8e8a5723981f9bdc1ceb57edade3

rounds: 2

Round 1: bi-analyst-reviewer PASS, cto-reviewer PASS; scope-auditor's verdict then was a fail
(resolved at round 2): the breadcrumb inventory row was `ruled` while its note said "put to the
CPO"; platform-reviewer's verdict then was a fail (resolved at round 2): the `visible` and
`min-box` assertion kinds (the picker rows) were exercised by no test, and `requirements-ui.txt`
left two packages unpinned. Round 2: the row is `proposed` and in `decisions_reserved`, the
fixtures carry the picker and the RED proof covers both kinds, every package is pinned; both
reviewers PASS. The cumulative diff includes the stacked base branch (!195); its files are
outside this contract's scope by design and reviewed there. Rebased onto !195 after its round 4
(two `sorted()` calls in its test, a CI-found Linux ordering trap): the hash above is the
rebased branch's; nothing of this branch's own changed.

## scope-auditor
VERDICT: PASS
risks_checked:
- The round-1 finding: "Breadcrumb current page" is `status=proposed`, its Rule cell states both versions (the shipped site's `ink-2` current page with muted links; #52's mock CSS inverted), its "Ruled on" reads "put to the CPO on the #153 MR; measured, never fails, until ruled"; `decisions_reserved` carries the question with both versions and the resolution path — no product decision asserted as settled.
- A second silent `proposed` row: `tests/test_design_inventory.py` pins `proposed == ["Breadcrumb current page"]`; the table holds only the one.
- `requirements-ui.txt` completeness: `decisions_taken` names `playwright`, `pytest` and `tzdata` together, with "no recurring cost until the CI MR".
- The `visible`/`min-box` kinds: `red.html` and the RED test exercise "Matchday picker" and "Picker arrow".
- Credentials: the whole cumulative patch grepped for key/secret/token/password patterns — only CSS "design token" vocabulary.
- Scope: the file list diffed against `scope_paths`; the only files outside it (`render.py`, the five `bl1_*.json`, `gen_diagnostic.py`, `tests/test_design_mock_renders.py`) belong to the stacked base branch the contract names.
- Round 1, still holding: the `!important` on the 14px gap rule, the `.md` picker nesting and the masthead margin are implementation of already-authorised changes; rulings (a) and (b) recorded as given, not decided; the three-tab bar, the `compTabRankings` copy and the page-spec key list named with authority; the `impact_map` evidenced (the `Layout.astro:7` import chain, a consumption-only surface).

## platform-reviewer
VERDICT: PASS
risks_checked:
- The picker fixture renders through the real `system.css` cascade: `red.html`'s `.md > .mdnav { display: block }` ties `system.css`'s `.md > .mdnav, .md > section { display: none }` and loads later, so every step lays out (visible 1 → 3); `.mdstep .step { width: 20px; height: 20px }` beats the 34px at equal specificity (34 → 20). `compare()` and `measure_page()` wire both kinds to real DOM measurements and the test's strings match `compare()`'s output.
- `requirements-ui.txt`: three exact pins, the convention `requirements.txt` uses; the repo has no lockfile, so none is missing.
- The breadcrumb `proposed` status is pinned as the sole proposed row and does not weaken "a proposed row is measured but never fails".
- Round 1, still holding: the browser tests skip cleanly in `test:python` (no playwright installed there, `ImportError` before any launch); the check decodes generator output from bytes with utf-8 and a replacement, the tests pass `encoding="utf-8"` and `PYTHONIOENCODING`; the http servers use ephemeral ports and daemon threads and shut down in a `finally` that covers the early return; the `.sechead + *` rule's mutation is what `red.html` reconstructs (34px, 49px) and the RED proof fails on it; the lint's `class:list` computed-expression blind spot has no instance in the tree; `check_row_consistency.py`'s two CSS assertions moved to the lint by design.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every row of `block_standard.md`'s Elements table traced against `system.css`: selector, rule text and `Measured as` match the shipped declarations (13px block heading; the 14px gap zeroed with `!important`; the competition group head's 2px line excluding `.rkgroup`; the metric group heading's 0px; the table head's 1px as the only line; the row's 0px with the stripe verified against `StandingsTable.astro`'s DOM order, so "first plain, from row 2" is the pseudo-class's real effect; the ordered-by number on `DeservedPoints.astro`'s Diff column; board name, sub-line, spacing; tag; picker; hover and press tints; chevron; the prose-link underline exception; the breadcrumb).
- The two rulings of 2026-09-17 implemented: `.fxgroup:not(.rkgroup) > .gh` keeps its 2px line, `.rkgroup > .gh` has none; the row's `border-bottom` removed, the head's kept.
- The three-tab bar: `compTabTeams`/`compTabPlayers` removed and `compTabRankings` added in EN/FI/DE (DE left as the untranslated placeholder, an open item, not invented copy) and in `index.spec.json`; no leftover references in the tree.
- `Masthead.astro`'s inline style deleted and the equivalent `.mast .eyebrow` rule added — no behaviour lost, no duplicate.
- `docs/wireframes/metrics_display.md` (LOCKED) untouched; only `00_overview.md`'s owner row and the new `block_standard.md` under `docs/wireframes/`.
- `rendered_page_evidence.md` names the tool, the pages, the before/after counts and a DE run for the tab bar; the RED proof asserts an exact failing set through a real subprocess run.
- No metric creep, no naked percentage, no new displayed number; the parser and the lint fail closed as documented.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Playwright: the CPO's blinded answer of 2026-09-16 quoted in `decisions_taken`; not wired into CI here (`validate:ui` at `.gitlab-ci.yml:438` unrelated and untouched).
- Renders in git: the CPO's answer quoted; scope confined to `design-mocks/renders/*_2026-09-17_*.html`.
- `pytest` already a dependency; `tzdata` needed by `zoneinfo` on Windows and, since round 1, named in `decisions_taken` and pinned.
- `BORROWED` in `check_row_consistency.py` grew by the row classes that moved into the stylesheet; the collision guard still fires on any unlisted class — the rule keeping up, not a loosening.
- `!important` on the 14px gap rule: an existing #129 invariant enforced with ordinary CSS, as the file already does elsewhere — not a new mechanism.
- `gen_diagnostic.py` deleted with authority and reason in `amendments`.
- No recurring cost: no CI job, `.gitlab-ci.yml` untouched and out of scope; the check runs locally and in tests that skip without a browser. No guard path touched. No credential-shaped string.

## escalations
(none)
