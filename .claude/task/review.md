# Review — feat/151-rankings-tab — 2026-09-22

diff_sha256: d6240a908c95f3cbf80916e847d691e79ac4409d7290e15e1fc80cf1312f417f

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: `docs/wireframes/99_gaps_register.md` GAP-11 still recorded `clean_sheets` as `x/y` while the branch ships `integer`; a design-chain document the diff contradicts must move in the same branch. Round 2: the row now reads approved as `x/y`, ruled a bare count on #129, shipped as `integer` by #151, with the issue in the last column — resolved.
- scope_paths coverage: every file in the cumulative patch matches an entry, including the fnmatch-corrected page globs and the amendments; no drift.
- §10 decisions: `/stats/`, the blank-card-as-zero reading, the catalogue-direction join with the ruled card override, inert headings and fact rows, the player stub's page set, the `count_fraction`/`.ctab.dp` removal, the six dropped player boards — each traced to a quoted #129/#151 ruling or a mechanical consequence of one.
- The audit-seo h1 exemption widening against "the header never changes with the tab" — the one-header-per-entity rule extended to a third tab, tested both directions; not a rule extension.
- No credential-shaped content, no new mechanism, no recurring cost; `decisions_reserved` empty and nothing decided silently against it.
- Round 3 (delta): the adjacency test's direction branch is a mechanical consequence of the ruled ascending boards, not a new ranking rule; the amendment quotes the issue line and the CI failure; no other path moved.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Blank-card-as-zero in `int_legs__team_match.sql` against the LEFT JOIN's null-ness and the measured provider behaviour; `games_with_card_stats` and the NULL-out in the cumulative model follow the same coverage idiom as every other team-feed metric.
- A mart reading `metric_catalogue` via `ref()` has precedent (`mart_standings` + `standings_table_kinds`); the inner join's silent-drop failure mode is caught by `assert_mart_team_leaderboards_all_boards_present` (count != 12).
- `rank_order` / `sort_key` / dense_rank consistency against the catalogue's directions for all 12 boards; the new singular test re-derives the extreme independently and checks the zero rule; the yml expression matches the model's row filter.
- The three-way board-set pin reads the real files and its mutation tests go red in each direction.
- `clean_sheets` format and the `count_fraction` removal swept across seed, schema, docs, `format.ts`, `MetricRow.astro` — no dangling reference.
- The export and the components select served columns only; no ranking or metric math client-side. Round 2: `layering.md` mart rows now match the models (no games floor, the served direction, 12/13 boards).
- Round 3 (delta): `data:build:mr` on !216 failed `assert_mart_team_leaderboards_one_leader_per_league` with 201 rows, all from the adjacency invariant assuming descending order; the fix branches on the served `rank_order` and mirrors the model's signed `sort_key` without re-running the window; the tie-break and the other three invariants unchanged; 0 rows against the inlined chain on prod.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- `cards_yellow` / `cards_red`: real per-match provider statistics summed over the season; `lower_better` matches the player rows and football sense; the descriptions state the blank-vs-zero reading and the withheld total honestly and match the SQL.
- The second-yellow quirk is stated only where cards are summed into one metric (`cards_player`); no team composite is introduced, so the omission on the separate boards is consistent.
- The most-first ruling on the card boards is a display order on the mart, not a catalogue misstatement.
- `clean_sheets` `count_fraction` → `integer` against the ruling; no other row or the schema enum still references the retired format.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every field on the Rankings tab traced from `RankingBoard.astro` / `RankingsBlock.astro` through `types.ts`, `shape_competition_boards`, `_board_catalogue` to the two marts and the seed — every rendered field a served column, none computed in the page.
- The committed sample carries the 12 team boards and 12 of 13 player boards (finishing legitimately empty after four matchdays, omitted by design); no hand-typed key.
- Group order from `metric_groups.json` via `boardGroups()`; no tier reorders boards.
- The zero rule and the fewest-first note enforced in SQL, by the new singular test, and re-checked on the built HTML by `check-built-pages.mjs`; `acceptance_evidence.md` shows the run against `dist`.
- `rendered_page_evidence.md` present and drawn from a real headless-Chromium pass at 375/700 px EN/DE/FI; the pre-existing 700px header overflow disclosed, not hidden.
- Every new string resolves in EN/DE/FI and is pinned by `check-metric-labels.test.mjs`; the removed strings have no call site.
- The Overview's Balance column traced to the quoted #129 ruling; `system.css` removes `.ctab.dp` and adds nothing. Round 2: the GAP-11 register row now agrees with the shipped code and the locked wireframe.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `shape_competition_payload` signature change: every caller (the fetcher, the tests) updated; no stale positional caller.
- `shape_competition_boards` unit-tested for the five-row cut, empty-board omission, the carried catalogue facts and the player shape.
- `tests/test_leaderboard_board_sets.py` reads the production files; the red tests exercise real mutated inputs; `_LEADERBOARD_METRICS` aliasing leaves no untested gap.
- `check-built-pages.mjs`'s `BOARD_RE` traced line by line against `RankingBoard.astro`'s emitted markup; the link check requires a real `href`.
- `sharesHeader` requires the parent page to carry the same h1; the test proves unrelated siblings still fail; `isTabOf` unchanged.
- Rerun safety: views rebuilt wholesale, deterministic export order; no dependency, credential or `.gitignore` change; the new checks are wired in CI through `test:python`, `prebuild` and the `astro:build:done` integrations.
- The player stub's page growth disclosed in the spec and the contract; scale is not this reviewer's to block on.
