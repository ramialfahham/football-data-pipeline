# Review — refactor/metric-rename-player-passing — 2026-08-31

> **STEP 4 of the metric catalogue naming programme, MR 4 of seven.** The five player `passing`
> metrics: `passes_total` → `passes_player`, `passes_accurate` → `passes_accurate_player`,
> `passes_key` → `passes_key_player`, `pass_accuracy_pct` → `passes_accuracy_player_pct`,
> `key_passes_per90` → `passes_key_per90`, plus four derived yoy forms under a new CPO ruling.
> PLAYER entity only. Branched from main `1cf0d40`.

diff_sha256: 23d4a5368a076558102b668c501023f752fe09039a93645323cff23399d4170d

rounds: 3

⛔⛔ **ROUNDS 1 AND 2 BOTH FAILED, ON FOUR SITES OF ONE DEFECT CLASS — MODELS THAT COULD NOT HAVE
COMPILED.** Round 3 is the cap and all five reviewers PASS with no open findings.

- **Round 1, 4–1** (`analytics-engineer-reviewer`): three models shipped
  `sum(round(passes_player * passes_accuracy_percent / 100))` — a nested aggregate over a SIBLING
  ALIAS, against CTEs carrying only `passes_total`.
- **Round 2, 3–2** (`analytics-engineer-reviewer` and `bi-analyst-reviewer`, independently): a
  fourth site, `mart_player_season_record.sql`, where the `matched` CTE was updated but the model's
  own FINAL SELECT still projected the old names — while its own `shared.yml` entry already
  declared the new ones.

⭐⭐ **ONE CAUSE, THREE ROOTS, AND THE PROGRAMME HAD ALREADY LOGGED IT ONCE.** Every miss came from
my own source-resolution logic asking a proxy question instead of the real one. `!125`'s round-2
entry says, verbatim, that for bare reads I asked "does the alias happen to match the inner name"
rather than "did the source relation rename this column". Round 1 was that heuristic again in a new
shape; round 2 was the same rule failing because **neither the classifier nor the resolver followed
`JOIN`, only `FROM`**. Counts across the rounds: **275/151 → 267/159 → 272/154.**

⭐⭐ **WHAT CHANGED BEFORE THE LAST ROUND WAS SPENT.** Four failures from one kind of logic is a
signal about the method, not the instance — so instead of fixing it a third time and hoping, I built
a check that cannot fail the same way: **for every model, do the columns its yml declares actually
appear in its FINAL SELECT projection?** It needs no notion of CTEs, joins or aliases. Against the
still-broken state it found exactly one mismatch — the site already known, **and no fifth** — which
is what justified using round 3. Against the submitted state, zero.
⭐ Run as an audit of shipped work, the same check on the merged `!125` / `!127` / `!128` names
found **zero mismatches across 9 models**. The three merged batches are sound.

⛔ **AND IT SETTLES THE CPO'S OPEN CI-GATE QUESTION, against the resolver.** Across this MR the
column-reference resolver was found to have **four** blind spots — CTE-bodies-only scanning, window
clauses parsed as CTEs, single-branch join resolution, and a *silent skip* that contradicts the
"reported, never skipped silently" property I had claimed for it. Two batches of green results had
concealed all four. It is not committable. The simpler yml-vs-projection check is the better
candidate if a gate is ever wanted; neither is proposed here.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round-1 defect class: read `int_player_club_season__metrics.sql`, `int_player_season_position__metrics.sql`
  and `int_player_season_record.sql` **in full** — all three now read the provider columns
  `passes_total` / `passes_accuracy_percent` inside the `ROUND` expression, not the renamed sibling
  alias. No recurrence.
- Round-2 defect class: read `mart_player_season_record.sql` end to end (`sides`, `season_final`,
  both `matched` branches, `chosen`, final SELECT) — the renamed names are consistent from the join
  through to the final `safe_divide`; no stale bare name remains.
- **Full-chain trace of all nine touched intermediate/mart models, reading each file in full rather
  than the diff hunk** — every CTE, join, window clause and final projection resolves to the correct
  name, with **no fifth compile-breaking site**.
- Macro-driven consumers (`int_player_competition_benchmarks`, `mart_player_competition_benchmarks`)
  reference metrics only through `player_benchmark_metrics()`; the macro's `col` / `num` / `den`
  were updated, so those models correctly needed and received no edit.
- Team/provider surfaces sharing the same stems (`int_legs__team_from_players.sql:28`,
  `int_legs__team_match.sql:120-121`, the team momentum models, the two provider marts) read
  TEAM-level or provider columns and remain correctly untouched.
- All six `accepted_values` lists and the four singular range tests, by eye against their intended
  rename/protect status.
- The seed, macro, every touched yml, the regenerated doc blocks, the export literals and
  `types.ts` — no orphaned old-name row, no stale `doc()` pointer.
- `mart_player_career.sql` carries none of the five names, matching the impact map's own
  over-count caveat.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- My round-2 finding is fixed: `mart_player_season_record.sql`'s `matched` / `chosen` / final SELECT
  now project `passes_key_player`, `passes_accurate_player`, `passes_player`, and
  `safe_divide(passes_accurate_player, passes_player)` — matching `shared.yml:1034-1039,1070-1071`
  exactly. No residual mismatch.
- The three round-1 sites read directly: all now read the provider columns rather than a sibling
  alias, in both the plain sum and the `round(...)` expression.
- `site_v2` containment: exactly one file changes (`lib/types.ts`), exactly one token; verified
  `mart_player_momentum.sql` actually emits `passes_key_player`, so the type matches its data
  source. The other four swept frontend files still carry `passes_key_per_match` untouched.
- The wireframe surface split in `03_player_profile.md` — season-stats bundle renamed, match-log
  expanded row correctly retaining the provider names. That is the exact split whose omission
  FAILed a prior MR in this programme.
- Rendered-page evidence: both sides built, structural comparison, 12/12/12 rows and 7/7/7 headings
  across EN/DE/FI, zero old-name tokens in `dist`. It honestly states this is a confirmed prediction
  rather than a discriminating check, and names the guard that actually discriminates.
- Leaderboard board keys agree as a SET across `mart_leaderboards.sql`, `accepted_values` and the
  export; both 18-name player lists moved the two entries and left `passes_per90`.
- The four CPO-ruled derived yoy columns are consistent across the yoy model, its yml and the mart.
- The three provider-naming `description` fields in the seed still name the unrenamed columns.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- The five renamed rows diffed field by field: only `metric_id` changed; `label_i18n_key`,
  `numerator_expr` / `denominator_expr`, `direction`, `lower_is_better`, `format`, `metric_group`,
  `importance_tier` and `interpretation` are byte-identical to base.
- The three protected `description` fields still name the unrenamed provider column `passes_total`.
- `passes_per90` confirmed still reading `sum(passes_total) * 90` with its `metric_id` unmoved; the
  four unrenamed `_per90` rows resolve untouched.
- **The round-2 site traced term-for-term** from `safe_divide(passes_accurate_player, passes_player)`
  back through `int_player_season_record`'s window functions to the catalogue's own
  `numerator_expr` / `denominator_expr` — the join-follow bug is not reintroduced and the mart
  computes the metric the catalogue defines.
- **The four independent re-implementations of the pass-accuracy numerator** across the two
  per-fixture bases, the momentum model and the season record — no drift between them under the new
  alias names.
- Doc blocks: exactly −2 orphans and +4 new orphans, matching the 173 → 175 reconciliation, with
  byte-identical prose on every renamed block.
- Whole-tree grep for stale `pass_accuracy_pct` / `key_passes_per90` under `dbt_project/` — zero
  hits; the round-1/round-2 failure class does not recur anywhere in scope.
- CPO authority verified verbatim against the log, including the new ruling for the four yoy
  columns and what it was shown before answering.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round-2 fix verified real and round-1 fixes verified un-regressed, by reading all four sites in
  full rather than trusting the diff summary.
- **Full downstream reconciliation traced by hand** across every changed model, yml, the macro, the
  seed, the export, `types.ts` and all six wireframes: every reference to a renamed column resolves
  against a source that emits it, and every surviving old name is a genuine provider or TEAM read.
  No half-rename anywhere in the diff.
- No file under `scripts/`, `tests/`, `.claude/hooks/`, `.github/workflows/`, `.gitlab-ci.yml` or
  any dependency manifest is touched — consistent with the "no new mechanism / cost / dependency"
  declaration.
- **The resolver's self-assessment judged for honesty**: the fourth blind spot is disclosed plainly
  as contradicting the "reported, never skipped" property previously claimed, the conclusion "not
  committable" is stated outright, and the replacement check is named as a *candidate* without being
  claimed safe or ready. **No over-claim found.**
- ⚠ Raised, not a defect: the "10 models, one mismatch" sentence did not say which state it was run
  against. Resolved independently by reading the delivered SQL (zero mismatches), and recommended
  tightening. **Corrected in `acceptance_evidence.md` after this verdict — that file is
  hash-excluded, so no verdict is affected.**
- `_LEADERBOARD_METRICS` / `_LB_KEEP` updated and agreeing with the mart and `accepted_values`; the
  untested-literals gap correctly carried forward as pre-existing rather than newly introduced.
- Gate credibility assessed on methodology consistency with prior MRs; nothing in the diff
  contradicts the reported figures.

## scope-auditor
VERDICT: PASS
risks_checked:
- `scope_paths` reconciles exactly against the changed set in both directions; the four absent
  entries are review paperwork excluded by design.
- **All four defect sites read directly in this round's diff — the fixes are real, not merely
  claimed**, including the join-side fix.
- Counts 275/151 → 267/159 → 272/154 internally consistent between contract and log, with the fix
  mechanism recorded rather than asserted.
- The audit claim on the already-merged `!125` / `!127` / `!128` names is stated identically in both
  documents with its method disclosed, and presented as a check performed.
- `escalations.log` is a pure APPEND — single hunk, every added line new, nothing before it touched.
- The CPO ruling on the four yoy columns is quoted identically in both documents with what it
  answered, and the diff renames exactly those four columns, nothing more.
- The doc re-point pattern mirrors a pre-existing convention already in the base file — the
  mechanical "re-point them" ruling applied consistently, not a new decision.
- Credential sweep across the full patch: no matches beyond the word "token" in classifier prose.
- Threshold declarations checked against the diff: no CI gate committed, no schedule or volume
  change; the classifier and resolver remain unshipped scratchpad tools.

## escalations
(none)
