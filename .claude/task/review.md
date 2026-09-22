# Review — feat/151-rankings-tab — 2026-09-22

diff_sha256: f831c602e93e2703ebde0405c8730529c46a06030db437dae375cd3d97effe3e

rounds: 7
rounds_cap_override: every round past 3 is the CPO correcting the open MR, not the builder grinding. Round 4: "change it to /rankings/" (2026-09-22). Rounds 5 and 6: he challenged a Finnish label the bi-analyst had passed as language — *"Harhautusyritykset?? is not football language"* — which was correct, and the reviewer's FAIL on that round found the same gap in German. Round 7: shown where the "(fewest first)" note renders, he asked where it mattered and answered himself — *"it isn't. the user is not an idiot"* — reversing his own #129 board rule. Each round is reviewed as a delta by the territory it touches, and none clears a standing FAIL by fiat. He did not rule on the cap.

⚠ REBASED onto `main` after !217 (the menu rename) merged, which moved the base under this branch.
The hash above is the recomputed cumulative diff against the new base; the four round-by-round
verdicts below stand unchanged, because **none of this branch's own code moved**: the only
conflicts were the five task artifacts (all diff3, all four marker kinds), resolved to this
task's side; `strings.ts` and `docs/site_architecture.md` auto-merged, and `git diff <old tip>
<new tip>` outside the paperwork returns exactly !217's eight files — the changes this branch
inherited from the base, not changes to its own.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: `docs/wireframes/99_gaps_register.md` GAP-11 still recorded `clean_sheets` as `x/y` while the branch ships `integer`; a design-chain document the diff contradicts must move in the same branch. Round 2: the row now reads approved as `x/y`, ruled a bare count on #129, shipped as `integer` by #151, with the issue in the last column — resolved.
- scope_paths coverage: every file in the cumulative patch matches an entry, including the fnmatch-corrected page globs and the amendments; no drift.
- §10 decisions: `/stats/`, the blank-card-as-zero reading, the catalogue-direction join with the ruled card override, inert headings and fact rows, the player stub's page set, the `count_fraction`/`.ctab.dp` removal, the six dropped player boards — each traced to a quoted #129/#151 ruling or a mechanical consequence of one.
- The audit-seo h1 exemption widening against "the header never changes with the tab" — the one-header-per-entity rule extended to a third tab, tested both directions; not a rule extension.
- No credential-shaped content, no new mechanism, no recurring cost; `decisions_reserved` empty and nothing decided silently against it.
- Round 3 (delta): the adjacency test's direction branch is a mechanical consequence of the ruled ascending boards, not a new ranking rule; the amendment quotes the issue line and the CI failure; no other path moved.
- Round 4 (delta): the `/stats/` → `/rankings/` rename rests on the CPO's quoted, dated ruling on the MR; the cascade (page, spec, tab prop, three docs, two checks' identifiers) is complete with no stray old identifier in functional code; `scope_paths` respelled to the renamed files only.
- Round 7 (delta): the removal of the "(fewest first)" note reverses a rule the CPO set himself on #129, so the quote was tested as a ruling and not an aside — first person, dated, answering his own question about that exact rendered note. The reversal is written into everything that stated the old rule in the same branch (`block_standard.md`, `decisions_taken`, the acceptance criterion, an amendment) and into nothing that is frozen — `escalations.log` untouched. Every path in the round matches `scope_paths`. The built-page check's move from reading the direction off the page to reading it off the payload is a mechanical consequence of the note's removal, not a new mechanism: the invariant is unchanged and only its evidence source moved. Copy the CPO was reviewing, rather than copy he had approved, is stated plainly as withdrawn.

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
- Round 4 (delta): the address rename is complete and consistent in every file of the territory that names it (page, spec `page` and note, the tab's `hasRankingsPage` href at all three call sites, the Overview spec's note, the block standard's Pages row); no field, label or rendering change rides with it; the SEO copy keys' internal names are unchanged and were reviewed in round 1.
- Round 5 FAIL, after the CPO rejected the Finnish dribbles label this reviewer had passed in round 1: the same failure class was uncorrected in German. Established mechanically that seven of the nine player labels are byte-identical to an existing team row in the file once the "Ø " sigil is stripped, so they are borrowed and not coined; the two that are not — `dribbles.attempts` and `savePct.saves` — had no repo-recorded backing.
- Round 7 (delta): the note's removal is complete across the display territory — no key, spec entry, class or comment left claiming it, in any locale; checked against the built HTML in EN, DE and FI, where the two ascending boards now read "Goals against per match" at 0.5, "Gegentore pro Spiel" at 0,5 and "Maalilaukaukset vastaan ottelua kohden" at 2,0 and say nothing further. `rank_order` is not dead payload surface: it is what the mart ranks by and the only thing the zero rule can turn on, now read by the built-page check instead of drawn. The two evidence files' rewritten claims were re-checked against `dist` rather than taken from the round's narrative.
- Round 6 (delta): both unborrowed values now carry their source in the file (FotMob's German and Finnish localisations for dribbles; `site/i18n/de.json` for "Paraden", re-grepped independently — one occurrence, matching the claim). No value moved. On the words themselves: no basis to call either wrong; both rest on a live product's real per-language localisation, and the bare-plural-is-attempts pattern is consistent across DE, FI and the catalogue's own English pair.

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
- Round 7 (delta): the check can no longer read a board's direction off the page and now reads it off the payload by rendered position. `renderedBoards` composes `boardGroups` — the very function `RankingsBlock.astro` renders from — so the order matches by construction and not by a second implementation; traced against the component, including a board with no rows and a group key the catalogue does not list. The rework does not weaken the gate: the board-count mismatch still fails, the zero rule still runs per board, and its direction now comes from the payload rather than from a string the same generator wrote, which is strictly more independent. Mutations checked red: one global direction, an off-by-one index, a dropped length check, and a broken block or group order. Nothing dangles in the mock generator — `ranks_fewest_first` still drives its own sort. Noted, not blocking: `groupKeysInOrder` repeats the one-line `order` sort that `metricRows.ts` does, because a script cannot import the TypeScript constant; both read the same exported file.
- Round 4 (delta): `STATS_PAGE` → `RANKINGS_PAGE` and the function renames are mechanical, the parsing logic and the markup it is traced against unchanged; the URL-shape test exercises the same two false-positive shapes; `sharesHeader` untouched; the `parentOf` doc example corrected afterwards, comment only.
