# Review — feat/152-metric-groups — 2026-09-21

diff_sha256: eb000c4d1b49b8f18946df906bc9f5795387e0532d6c8fd0221b00a471471bba

rounds: 2

Round 2 (delta): two FAILs in round 1. Scope-auditor — the contract's impact map cited a `dbt ls`
output that was not pasted (now pasted, with the models/macros grep at 0), and the locked display
contract kept its old block-order sentences under an appended note (now replaced in place: the
"Tier never orders" rule, the team table's block-order sentence, the GAP-09 bullet). Bi-analyst —
`rendered_page_evidence.md` on disk was #150's (now this branch's: Playwright at 375/700 on the
DE/FI team and fixture pages; no overflow, page width 375 at 375; the 700px sideways scroll is the
site header's search button on every page, pre-existing, flagged as its own task), and the player
rows table's two Group cells said "Duels" (now One-on-one). Also since round 1: the seed
description's order sentence narrowed and `column_types` pins `metric_group_order: int64` (the
platform reviewer's observation). After round 2 the scope-auditor's residual — the team table's
two Group cells (rows 8, 9) still "Duels" — was applied the same way; that two-cell rename is the
only change since the five round-2 verdicts.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: the impact map's lineage is now the measured `dbt ls` model (empty) and test lists and
  the models/macros grep at 0, consistent with the reviewer's own round-1 greps; the three stale
  passages in `metrics_display.md` are replaced, not annotated (§11); `schema.yml`'s description
  replaces the old sentence and the `column_types` pin is a declared type recorded in
  `decisions_taken`; the second amendment's authority is a written repo rule
  (`.claude/agents/bi-analyst-reviewer.md` item 4) and the added path is a task note outside the
  reviewable patch. Residual noted, applied after the round: the team table's two Group cells.
- Round 1: every touched path in `scope_paths`; `metric_groups.json` is a root file the
  `.gitignore` allowlist does not ignore; the 30 strings match the #152 table key for key and
  language for language; `metric_group_order` in the seed, the JSON and the mock generator equal
  the ruled order, quoted with its date; exactly 10 rows moved `duels` → `one_on_one` and no other
  assignment, expression, format or direction changed; no model refs the seed, so no number
  moves; the mock's `True → False` flip is the Finnish-probe flag, correct now the names are the
  CPO's; the first amendment corrects a transposed criterion toward the quoted ruling; no new
  mechanism, cost, hook, CI line or credential; no other component prints a group heading, so the
  third criterion's reach is honest.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the seed description now splits row order (the display doc) from groups and their
  order (the two columns); `metric_group_order: int64` declared beside `importance_tier: int64`;
  the display doc and the register state the catalogue's ownership in place; the singular test's
  CTE is `per_group` (not the reserved word), sqlfluff exit 0.
- Round 1: all 87 rows diffed old vs new — only `metric_group` on the 10 `duels` rows and the new
  column change; `metric_group_order` consistent with the ruled mapping on every row; the new
  column's description under 1,024 chars and for a stranger; the singular test has a FROM and each
  of its three defects returns rows (reasoned through the predicate); `fetch_metric_groups()` is a
  select-distinct-and-sort over seed values, no computation; no `ref('metric_catalogue')` in any
  model, no model file in the patch, layer rules untouched; no stale `duels` group key in scripts
  or tests (only `duels_*` metric ids, unrenamed).

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the seed is byte-identical to round 1; `schema.yml`'s delta is a type pin and a
  description sentence, neither touches a formula, direction, group key or name.
- Round 1: every one of the 87 rows compared old vs new — expressions, base relation, kind,
  direction, format, interpretation and description byte-identical; the 10 moved rows are exactly
  the duel and dribble metrics (2 team, 8 player), football-correct as one-on-one;
  `dribbles_past_player` correctly stays in `defending`; all 10 moved rows `higher_better`; the
  order values match the ruling on every row; no stale `duels` group key anywhere live; the
  One-on-one names in EN/DE/FI are accurate football terms.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 2: blob SHAs of every file traced in round 1 unchanged; the `int64` pin makes the singular
  test's comparisons int-to-int by declaration and closes a future blank-cell STRING flip; the
  column is in the CSV header so the #109 projection check is unaffected; the regen pin and red
  tests read the CSV, untouched; the evidence file is a task artifact no gate reads.
- Round 1: the regen pin is correct on Linux (LF blob vs LF fresh bytes) and Windows (`read_text`
  folds CRLF), and red on a stale JSON, a removed column or an added trailing newline; the two red
  pytests go red for the reason asserted; the mjs `group:` regex yields 16 tokens now and 0 on the
  reverted file, the floor catches that; `labelBlock` accepts the dotted group keys; the stray
  check catches a leftover `metricGroups.duels.label`; the copy gate's block regex tolerates the
  added comment lines; the JSON import resolves under Astro's strict tsconfig and nothing in Node
  imports the TS file; `deploy:export` neither deletes nor rewrites the root JSON; zero stale
  `GROUP_ORDER`/`MetricGroup`/`grp*` references outside the patch; the mock generator's `loc()` is
  a plain dict lookup and every key it needs is in `COPY`; the singular test's shape has
  precedents; no guard, dependency, CI, credential or hosting change. Observation applied: the
  seed description's stale order sentence.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the rendered evidence is this branch's — Playwright at 375/700 on four pages; at 375
  every page is 375 wide and the longest headings (113–126 px) fit a 343 px parent, font 11px/700
  unchanged; at 700 the headings fit and the 728/707 page width is the header's search button on
  untouched pages too, pre-existing and correctly not folded in; the player-rows table's two Group
  cells read One-on-one; the team table's block-order text is corrected in place; the "Tier never
  orders" rule states the mechanism; the GAP-09 bullet and register row agree; dated rulings-log
  entries that say "Duels" are history and correctly left.
- Round 1: `METRIC_ROWS` diffed — same 16 entries, same array order, same field/labelKey/tier/
  format/direction/denom/sublabel, only the `group:` literals changed; zero leftover
  `GROUP_ORDER`/`MetricGroup`; all 30 labels verbatim against the CPO's table; the committed JSON's
  10 pairs match the catalogue and the ruled order; both components render each heading once
  through `metricLabel`, iteration by `GROUP_KEYS_IN_ORDER`; the acceptance evidence demonstrates
  text and order from `dist` (0 English headings on 796 DE/FI pages).

## escalations
(none)
