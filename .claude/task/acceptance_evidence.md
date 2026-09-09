# Acceptance evidence — #40 MR B, the Top players block

Read from BUILT output (`site_v2/dist`, the dev server at 375px and 1280px, and the committed
`site_v2/src/data/landing.json`), not from source. Every number below was measured in this session.

criteria_demonstrated:
  - ONE ROW PER LEAGUE, ALL SEVEN, AND THE WAREHOUSE DECIDES IT. The committed `landing.json` carries
    4 boards x 7 rows = 28 rows, and every board lists BL1, ED, L1, LP, PD, PL, SA exactly once.
    That is now a filter on `league_leader_order = 1`, a column `mart_leaderboards` serves since MR
    A (`!164`, merged `943c9f2`); confirmed live in prod before re-exporting — 28 rows carry it
    across the four Home boards and seven elite leagues.
    ⚠ `rank = 1` alone is NOT one per league and never was: the mart ranks with DENSE_RANK, and
    measured the same week, assists returned 24 rank-1 rows whose top 7 covered 5 leagues with two
    of them twice; goals showed ED three times; key passes covered 4 of 7.
    ⚠ THE RULING CHANGED WHO IS SHOWN, VISIBLY. Under the old Python tie-break (lowest player id)
    the Goals board showed Haaland for PL and Daal for ED; under the ruled one (fewer minutes) it
    shows A. Isak and S. Tengstedt. Same data, different and better-justified rows.
  - THE INTRO SENTENCE IS TRUE AGAINST WHAT RENDERS. `dist/{de,en,fi}/index.html`, comments stripped
    and whitespace collapsed, gives one `.tt-intro` naming exactly seven leagues — La Liga, Serie A,
    Liga Portugal, Ligue 1, Eredivisie, Premier League, 1. Fussball-Bundesliga — which is exactly the
    set every board shows. It is read from the rendered rows, so it cannot drift from them.
  - THE EXPORT IS DETERMINISTIC AND COMPARES NOTHING AT ALL. `--entities landing` was run twice
    against live BigQuery after MR C landed and the two outputs compared with `cmp`: IDENTICAL.
    The query is now `order by l.board_leader_order` — ONE served column. `_board_order` is deleted,
    the shaper only groups, preserves and caps, and the three-key ORDER BY that replaced it is gone
    too. Mutation-tested from the other side: putting a value sort back into the shaper turns
    `test_top_players_does_not_reorder_what_it_is_given` RED (1 failed, 15 passed). That test hands
    the shaper rows in an order no sort would produce, so it cannot pass by luck.
  - ⭐ THE SERVED COLUMN REPRODUCES THE PREVIOUS PAYLOAD EXACTLY, which is the check that the column
    encodes the rule the export used to apply rather than some other order. The payload built by the
    three-key ORDER BY and the payload built by `order by l.board_leader_order` are IDENTICAL.
    ⚠ Stated precisely rather than rounded up: `cmp` on the raw files reported a difference at
    byte 2, and the cause was line endings, not content — the "before" copy came from the working
    tree, which git had converted to CRLF, while the export writes LF. With CRs stripped the two are
    byte-identical, and `python -m json.tool` diffs to nothing. Git's own view of the change is
    `334 insertions(+), 0 deletions(-)` against main, i.e. `upcoming` untouched and only
    `top_players` added — the same figure as before the switch.
    Board order after the switch, unchanged: goals PD,SA,LP,L1,ED,BL1,PL / assists PD,SA,ED,PL,LP,
    L1,BL1 / passes LP,ED,PL,PD,SA,L1,BL1 / key passes PD,ED,SA,LP,L1,PL,BL1.
  - EVERY BOARD TITLE IS LOCALISED AND NON-EMPTY IN ALL THREE LOCALES. From the built HTML:
    EN Goals / Assists / Passes / Key passes; DE Tore / Torvorlagen / Paesse / Schluesselpaesse;
    FI Maalit / Maalisyoetoet / Syoetoet / Avainsyoetoet. Blank-title count is 0 in each locale. The
    German assists label is the CPO's 2026-09-08 ruling; the draft carried "Vorlagen".
  - THE BUILD IS GREEN AND NO PLAYER LINK IS DEAD. `npm run build` completes: "audit-seo: 250 built
    page(s) checked. OK." Page-count driver reports `/[lang]/players/[player] -> 84`, i.e. the 28
    distinct players the 28 board rows link to x 3 locales. (It was 81 before MR A: the old
    tie-break happened to put Dybala on two boards, the ruled one does not — the page count follows
    the data, which is why it is read from the build rather than asserted.) Before the scaffold
    existed, check 8 would have failed on every one of those hrefs.
  - TAP TARGETS AND PER-BOARD STACKING HOLD AT 375px, RE-MEASURED AFTER THE DATA CHANGED. On the dev
    server at 375x812 with the post-MR-A payload: row heights 55.8-73px, minimum 55.8px, against the
    44px floor. Within every board `.ent` resolves to a SINGLE computed display value (`block` at
    375px, `flex` at 1280px), so a board stacks as a whole and never row-by-row. The value column's
    right edge is one value per board (359 at 375px, 945 at 1280px), so the numbers stay aligned
    down the board. No console errors on the home page or a player stub.
    ⚠ Re-measured rather than carried over: the ruling changed which players are shown, and name
    length is what drives row height and wrapping.
  - THE FOCUS RING NO LONGER CROSSES A DIVIDER. Measured with real keyboard focus at 375px, row 3 of
    the Goals board: BEFORE, `outline-offset: 2px` + `outline-width: 2px` put the ring at
    y=373.5..438.3 against dividers at 377.5 and 434.3 — 4px through the line at both ends, the
    defect !151 shipped. AFTER `a.brow:focus-visible { outline-offset: -2px }`: ring reach beyond the
    border box is 0, `crossesUpperDivider` and `crossesLowerDivider` both false.
  - A MISSING FINNISH BOARD LABEL NOW FAILS, WHERE IT PREVIOUSLY PASSED SILENTLY. Deleting
    `playerMetrics.keyPasses.label` from `METRIC_LABELS_FI`: `check_copy_gate.py` exits 1 with "key
    missing from fi", and `check-metric-labels.test.mjs` fails with "FI has no label for". Both were
    blind to the whole `playerMetrics.*` namespace before this branch widened their parsers, so a
    blank board title would have shipped with nothing red.
  - AND THE WIDENING ITSELF IS PINNED, which round 1 correctly found it was not. Narrowing
    `_METRIC_ENTRY_RE` back to the `metrics.*.label` anchor makes
    `test_copy_gate_sees_the_player_metric_namespace_too` RED, naming all four keys. The same
    mutation leaves the gate printing `COPY GATE ok: 453 strings across 3 locales (396 chrome + 57
    metric labels)` and exiting 0 — 57 against 69, i.e. the twelve board-label strings silently
    invisible again. That 69-vs-57 gap is the hole, measured from both sides.
  - THE WHOLE OFFLINE GATE SET IS GREEN. `pytest tests/` 1020 passed / 1 skipped; `npm test` 81
    passed; `check_layer_contract`, `check_registry_var_sync`, `check_competition_type_seed`,
    `check_copy_gate`, `check_description_hygiene` and `sync_metric_docs_blocks --check` all exit 0;
    `dbt parse` clean apart from the pre-existing unused-snapshots warning.
