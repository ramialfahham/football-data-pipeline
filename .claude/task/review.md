# Review — refactor/metric-rename-player-duels — 2026-08-31

> **STEP 4 of the metric catalogue naming programme, MR 5 of seven.** The six player `duels`
> metrics: `duels_total` → `duels_player`, `duels_won` → `duels_won_player`, `duels_won_pct` →
> `duels_won_player_pct`, `dribbles_attempts` → `dribbles_attempts_player`, `dribbles_success` →
> `dribbles_success_player`, `dribbles_success_pct` → `dribbles_success_player_pct`.
> PLAYER entity only. Branched from main `9ea88b5`.

diff_sha256: 68a0aa111fd8cbfc97ea1a7c525ea332c35ce7d75b64d251d4c1e1df4c49ca86

rounds: 1

⭐ **ALL FIVE REVIEWERS PASS AT ROUND 1** — the first batch of step 4 to do so since `!127`.
537 tokens across 46 files, 348 renamed / 189 protected. No new CPO ruling was needed: every target
name is in the record verbatim.

⭐⭐ **THE BATCH WHERE THE SAME TOKEN MOVES ON ONE ENTITY AND STAYS ON THE OTHER.** `duels_won_pct`
is a `metric_id` on BOTH entities; `duels_total` and `duels_won` name TEAM columns on the
`int_legs__team_from_players` chain and PLAYER metric columns on the `int_legs__player_match` chain.
Measured split: `duels_won_pct` 48 renamed / 46 protected, `duels_total` 61/30, `duels_won` 60/27.
⚠ The planning note claimed a token→decision map could not express this and that the classifier
needed re-keying by entity. **Tested rather than believed, and it was wrong** — `decide()` already
resolves entity on every path; the change made was to PRINT the entity in every reason so the
discrimination is checkable rather than trusted.

⭐⭐ **A RENAME CAN COLLAPSE A DISAMBIGUATION, AND THAT EDITS THE OTHER ENTITY.** `_blocks()` splits
a metric into `__team`/`__player` only where its rows disagree, so renaming the player row makes
`duels_won_pct` unambiguous and the pair collapses: `doc('duels_won_pct__team')` →
`doc('duels_won_pct')` on **5 TEAM-side references caused by a player rename**, which no token sweep
finds from the player side. Blocks 175 → 172; 77 `doc()` references re-point in all.

⭐ **THREE PREDICTIONS WRITTEN INTO THE CONTRACT BEFORE THE CODE, THEN MEASURED** — after `!129` had
three of mine disproved after the fact. The block count and its exact removed/added sets were
predicted by running the real generator against the renamed seed in memory during planning, and
measured identical term for term; the description count held at **1604**; the hygiene gate's
ambiguous-name list dropped **5 → 4**. All three CONFIRMED.

⛔ **TWO SELF-CORRECTIONS, BOTH MADE BEFORE THE REVIEW ROUND.** (1) The contract first claimed the
rendered-page comparison would discriminate a mis-scope; performing the mis-scope shows **the build
never completes**, so it is a confirmation, not a discriminating check — and the failed build left a
stale dist that was nearly reported as a fresh measurement. (2) The contract speculated
`check_description_hygiene` has no dangling-reference check and one might need writing; **it has
one**, found by mutation. No new guard was needed and none is proposed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- All nine changed intermediate/mart models traced **in full rather than by diff hunk** — every CTE,
  join and final SELECT projects the new names consistently; no stale name survives in any final
  projection, checked specifically against the `!129` round-2 failure mode.
- The self-aliasing aggregate pattern in each model: inner reads of provider/leg columns stay
  unrenamed while outer aliases move, matching "a reference follows its source".
- `int_legs__team_from_players.sql:32-35`, the junction, is untouched — both the leg-column read and
  the team-column alias remain — and its two consumers still read those team names unrenamed.
- The whole team chain is unmodified SQL and still resolves `duels_total` / `duels_won` /
  `duels_won_pct` at the team grain.
- The macro moved all four fields on both rate rows, while the seed's `numerator_expr` /
  `denominator_expr` stayed as leg-column names on team AND player rows — the two opposite rules.
- The block collapse verified in the tree: both suffixed blocks gone, exactly 5 `doc('duels_won_pct')`
  references now exist (3 `shared.yml`, 2 `int_team_season.yml`), matching the predicted count.
- All six `accepted_values` lists and all nine singular range tests, by eye.
- The export's literal changes are select/filter/sort only — consumption-layer contract intact.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- All six renamed fields traced from the wireframes through the four player marts back to the
  renamed catalogue rows — **every field a wireframe now names is actually produced by the export
  chain**; no fabrication.
- `03_player_profile.md`'s two surfaces checked independently: the season-stats bundle renamed, the
  wrapped "full per-match line" provider row correctly protected, and those provider names confirmed
  to still exist on `mart_player_match_log`. The zero-denominator example correctly renamed.
- **Both dual-entity wireframes checked at EVERY occurrence, not just the three cited anchors** —
  including `metrics_display.md:221-222`, where the overriding sentence wraps onto the next line.
- Frontend containment verified independently rather than trusted: zero `site_v2` files in the
  patch, all four swept files byte-identical and still carrying only the TEAM label keys, no player
  stem anywhere under `site_v2/src/`.
- `rendered_page_evidence.md` judged as evidence: the self-correction is honest, the stale-dist
  near-miss is disclosed, and the two guards that do discriminate are named with real output.
- The seed's formula atoms still point at the provider chain while the macro's `num`/`den` use the
  renamed atoms — confirmed as two different, correct rules.
- `mart_player_season_record.sql` read end to end — the exact shape of the `!129` round-2 defect —
  both `matched` branches and the final SELECT project the new names.
- No naked percentage, no metric added or removed, no display wording invented.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- The seed diffed row by row: on all six renamed rows **only `metric_id` changed**; every other
  field is byte-identical to base.
- **The dual-entity row**: the TEAM `duels_won_pct` row is untouched context in the hunk with no
  `+`/`-` at all; only the PLAYER row moved. No entity mix-up.
- All 13 seed formula occurrences unchanged on both entities, per the "yes" ruling.
- The macro traced term-for-term against the catalogue: still duels won over duels contested, and
  dribbles completed over dribbles attempted.
- `duels_won_per90` / `dribbles_success_per90` confirmed unrenamed in the macro, both 18-name lists
  and every model — each reads the renamed atom while keeping its unrenamed output name.
- Full trace of both new ratios from the mart's `safe_divide` back through the intermediates to the
  catalogue's own numerator/denominator.
- **Doc-block prose compared byte-for-byte on every renamed block** — all identical to what they
  replaced; the three deleted `__player` yoy blocks confirmed as orphans with zero references.
- Team-side protection verified live in the repo, not from the contract's prose.
- CPO authority checked verbatim against the log, including that no new ruling was needed.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `_LEADERBOARD_METRICS` (9) and `_LB_KEEP` (25) diffed against `mart_leaderboards.sql` and the
  14-name list — matching SETS post-rename. Confirmed **no test exercises either constant** (the
  leaderboard test fabricates its own metrics), so the gap is real but carried unchanged in kind
  from `!127`/`!128`/`!129`, not newly introduced or widened.
- `tests/test_export_site_data.py` grepped for every other step-4 renamed name: **zero hits**,
  substantiating the "no precedent in this file" claim; the changed literals match a real
  `metric_id` and a real `position_group`.
- The three prose-only edits confirmed to sit entirely inside comments / `description:` blocks, with
  the executable `DERIVED_AFFIXES` tuple and the singular test's SQL body byte-identical around them.
- **The 175→172 arithmetic reconciled term by term against the real `metric_columns.md` diff** —
  10 removed, 7 added, exact match, no slippage. The 5 and 6 re-point counts verified by grep.
- The contract's self-correction substantiated at source: the literal string
  `"unresolved docs block: {name!r}"` found in `check_description_hygiene.py` — not a fabricated claim.
- **The disclosed yml-vs-projection blind spot independently re-derived rather than taken on trust**:
  every renamed atom used inside a `safe_divide(...)` is ALSO separately projected as its own output
  column, so **the bound has no live instance in this MR's delivered tree**.
- Materialisation swept across every model: the only `incremental` model is `fct_fixture_player_stats`,
  whose diff touches only `doc()` pointers — no renamed column lands on an incremental fact, so
  `protected_override`'s claim holds and no `--full-refresh` is implied.
- Whole-patch grep: nothing under `.claude/hooks/`, `.github/workflows/`, `.gitlab-ci.yml` or any
  dependency manifest; no gate committed.
- The three 22-name TEAM lists confirmed absent from the diff and byte-identical in the tree.

## scope-auditor
VERDICT: PASS
risks_checked:
- `scope_paths` reconciles exactly against the 34 changed entries in both directions; the four
  absent entries are the review paperwork and active-work exclusions, by design.
- All six renames checked verbatim against the record's "PLAYER, 35 REMAINING" table — no name in
  the diff was invented.
- **The §3 FORM decision judged as a classification, not just an edit**: only illustrative comment
  and description text changed; no formula, label, mechanism or name moved, and `_blocks()` /
  `_derived()` are untouched code — so FORM rather than a silent §10 decision holds.
- The carried observation about the block split losing its last live instance: confirmed nothing was
  removed or weakened on its strength.
- **Honesty of the record**: the contract's self-correction and `rendered_page_evidence.md` say the
  same thing — the mis-scope was actually performed and the build never completes, not "might" — and
  both flag the stale-dist near-miss. The yml-vs-projection bound is stated plainly as a weakness
  rather than glossed. **No over-claiming found.**
- `escalations.log` is a pure APPEND — single hunk, three lines of unchanged context, then addition.
- Credential sweep across the full patch: every "token" hit is the classifier's word-token
  terminology.
- Threshold declarations: no CI gate, schedule or cost change; the renamed singular tests track
  their column rather than being deleted or loosened.

## escalations
(none)
