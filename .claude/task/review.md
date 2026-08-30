# Review — refactor/metric-rename-player-discipline — 2026-08-30

> **STEP 4 of the metric catalogue naming programme, MR 2 of seven.** The five player `discipline`
> metrics: `cards_yellow` → `cards_yellow_player`, `cards_red` → `cards_red_player`, `cards_total`
> → `cards_player`, `offsides` → `offsides_player`, `penalty_committed` →
> `penalty_committed_player`, PLAYER entity only. Branched from main `3e5b25b`.

diff_sha256: 4e3b49b0a03dc2b0e1e03c0d8d8c2113e8dcd247dae4589d39b634131d122d53

rounds: 1

⭐ **ALL FIVE REVIEWERS PASS AT ROUND 1, and the thing they were pointed at is the thing they
checked.** `!125` lost two rounds to one mistake — for dotted reads it asked "did the source
relation rename this column?" and for bare reads it asked a different question. This batch is the
first where that rule is tested against itself: **three `sum(X) … as X` sites with identical shape
and two opposite correct answers.** Four of the five reviewers traced all three by hand, from the
source relation up, rather than accepting the contract's narration of them.

⚠ **NO FINDING WAS RAISED THAT REQUIRED A CODE CHANGE, so nothing in the tree moved after the
reviewers were spawned.** The tree they read is the tree being committed.

## scope-auditor
VERDICT: PASS
risks_checked:
- Verified all five renamed names against `escalations.log`'s "⛔ PLAYER, 35 REMAINING" table
  verbatim, cited by content — matches the contract's `refs` claim exactly. Both governing rulings
  ("re-point them", "yes") are present in the log saying what the contract attributes to them.
- Verified the `escalations.log` diff hunk is a pure APPEND — every added line is `+`, nothing
  edited or removed from prior entries.
- Reconciled `scope_paths` against every `diff --git` header in both directions — nothing extra,
  nothing missing; the four unedited entries are task-artifact files.
- Traced the "reference follows source" classification against the actual SQL diffs in
  `int_player_club_season__metrics.sql`, `int_player_momentum__metrics.sql`,
  `int_player_season_record.sql` and `int_player_season__metrics.sql` — the two-opposite-answers
  bare-read case resolves exactly as the contract and log describe.
- Read `core.yml` and `shared.yml` post-branch to confirm the borrowed doc-block re-pointing for the
  TEAM columns (`fct_fixture_team_stats.offsides`, `mart_team_fixture_stats.offsides`) landed as
  `doc('offsides_player')` with no column rename on those provider surfaces.
- Checked for credentials, new mechanisms, recurring-cost or cadence changes anywhere in the diff —
  none found; `decisions_reserved` carries the open items forward without deciding any of them.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Traced all three `sum(X) … as X` self-aliasing sites: `int_player_club_season__metrics.sql:135-139`
  (source `fct_fixture_player_stats` via `per_fixture`, provider — inner reads correctly kept, only
  the alias moves), `int_player_season_record.sql:60-67` (source `int_legs__player_match` via
  `player_legs`, provider — inner reads correctly kept), `int_player_season__metrics.sql:58-62`
  (source `int_player_club_season__metrics` via `club_season`, a metric relation this MR renames —
  both inner read and alias correctly moved). No defect.
- Followed every dotted/bare read of the renamed names through `int_player_momentum__metrics.sql`,
  `mart_player_momentum.sql`, `mart_player_season_record.sql`, `mart_player_profile.sql` and
  `mart_leaderboards.sql` — every read resolves against a relation that actually emits the
  referenced column after the change.
- Checked the seed: the five `metric_id` values move; `base_relation` / `numerator_expr` stay
  pointed at `int_legs__player_match` and reference the provider's unrenamed columns, which that
  model still emits. `lower_is_better` / `direction` still agree, so
  `assert_metric_direction_lower_is_better_agree.sql` still passes.
- Grepped for the five old `doc()` names across `dbt_project/models` — zero hits. 48 `doc()`
  occurrences of the new names across the 7 touched ymls, matching the contract's count;
  `metric_columns.md` blocks verified by direct read, no content swapped between blocks.
- Read all six `accepted_values` lists directly: `shared.yml:1756` correctly moved
  `cards_total` → `cards_player`; the other five contain none of the names and are untouched.
- Checked layer boundaries: no column name changed on any staging/base/core model or on
  `int_legs__player_match`, `mart_player_fixture_stats`, `mart_player_match_log`,
  `mart_team_fixture_stats` — every bare `- name:` hit mapped by hand to its owning provider model.
- Checked the export against the consumption-layer contract: only the two leaderboard literal
  tuples change; `shape_top_players` uses a DROP list and derives nothing.
- Checked the over-counted lineage files (`int_player_profile__yoy`, `mart_player_career`,
  `int_player_competition_benchmarks`, `int_player_season_position__metrics`, the benchmark macro)
  for any of the five names — none found, consistent with the contract's impact map.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Cross-checked all five renames against the "⛔ PLAYER, 35 REMAINING" table — all verbatim; RULING
  5's shape confirmed present. No fabricated authority.
- Read the seed rows in full and diffed against the patch: **only `metric_id` changed on each of the
  five rows.** `label_i18n_key`, `label_en`, `description`, `base_relation`, `numerator_expr`,
  `denominator_expr`, `computation_kind`, `lower_is_better`, `format`, `metric_group`,
  `importance_tier`, `direction` and `interpretation` are byte-identical before and after.
- Confirmed `base_relation` and every formula field still name real columns of the relation they
  point at — the exact class the prior MR was FAILed for. No dangling formula reference.
- Read the three self-aliasing sites directly; all three answers match "a reference follows its
  source". Traced the four downstream marts' dotted reads to their renamed metric relations.
- Group-split completeness: scanned the full seed — exactly 5 rows with
  `entity=player, metric_group=discipline`, no more and no fewer; no team-side `discipline` group
  exists to be missed.
- Football validity, judged independently rather than diff-checked: `lower_better` on all five
  (cards, offsides, penalties conceded) is correct, and `cards_player`'s `sum(cards_yellow +
  cards_red)` is a transparent disclosed sum, not an opaque composite index.
- Read `assert_metric_direction_lower_is_better_agree.sql:9` directly and confirmed it is inert
  prose inside a `{# #}` comment recording a dated fact — leaving it unrenamed is the declared
  judgement call, not a half-rename defect.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Confirmed no file under `.claude/hooks/**`, `.github/workflows/**`, `.gitlab-ci.yml`,
  `*requirements*.txt`, `package*.json`, `astro.config.mjs`, `tsconfig.json`, `firebase.json`,
  `.gitignore` or `tests/` is touched — the diff is dbt models/ymls/seed/docs/wireframes plus one
  script, so most machinery hunt items have no changed surface.
- Traced the "reference follows source" rule through every changed SQL file **by hand rather than
  trusting the contract's narration**; all three self-aliasing sites resolve to the two opposite
  correct answers claimed, and `cards_yellow_player + cards_red_player as cards_player` is correct.
- Verified provider surfaces genuinely untouched by grepping `int_legs__player_match.sql` and
  `fct_fixture_player_stats.sql` — they still emit the unrenamed columns the seed's formulas and the
  protected inner reads read.
- Grepped the whole `dbt_project` tree for the five old `doc()` names — zero hits; spot-checked
  `metric_columns.md` content mapping, no content swapped between blocks during the rename.
- Verified `int_team_season.yml`'s renamed columns fall inside the `int_player_season__metrics`
  model block, not inside `int_team_season__metrics` — the file's dual naming is confusing but the
  renamed lines are on the correct model.
- Read all six `accepted_values` lists in full: `shared.yml:1756` is the only one that changes.
  Verified `mart_leaderboards.sql`'s `count_boards`, `_LEADERBOARD_METRICS` / `_LB_KEEP` and that
  `accepted_values` list all agree on `cards_player` with no `cards_total` retained anywhere.
- Checked `tests/test_export_site_data.py`: `shape_leaderboards` / `shape_top_players` are exercised
  with synthetic keys only, so no committed test would catch a stale literal in those tuples. **A
  real coverage gap — but explicitly disclosed in `decisions_reserved` as pre-existing across the
  whole programme (identical in `!125`), not introduced here; the values were independently
  verified correct.**
- Checked the wireframe judgement calls by direct read: `03_player_profile.md:100/106` renamed vs
  `:119` correctly left (the exact class that failed `!125` round 2), `metrics_display.md:264`
  renamed vs `:271` left, `docs/ui_design_brief.md` untouched.
- Noted that `rendered_page_evidence.md` names and disclaims its own zero-built-file grep as "not
  proof the rename happened" — the vacuous-check class this brief hunts for is disclosed by the
  author rather than hidden.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **Verified the provenance claim independently**, which was the central hunt item:
  `scripts/export_site_data.py:871` builds `top_players[]` from `mart_player_momentum`, not
  `mart_player_fixture_stats`, and `_TOPPLAYER_DROP` (`:66-67`) names none of the five — so the
  renamed mart columns flow straight through into the payload keys, exactly as the contract states.
- Grepped all five old names and `cards_player` across `site_v2/src`: only the 19 committed
  `src/data/fixtures/*.json` sample files match; no `.astro` / `.ts` matches. Checked
  `metricRows.ts` (team-only, correctly carries none), `PlayerRow.astro` and the `TopPlayer`
  interface in `types.ts` — none reads or declares any of the five, confirming they are genuinely
  unrendered.
- Wireframe-to-code binding: confirmed `03_player_profile.md:100` matches `mart_player_profile.sql`'s
  actual output columns and `:119` matches the untouched `mart_player_match_log.sql`; confirmed
  `10_home.md`'s board table and `metrics_display.md` row 8 match `mart_leaderboards.sql`'s output
  and the `shared.yml:1756` list.
- Doc re-pointing completeness: grepped for any leftover old-name `doc()` across `dbt_project` —
  zero, so nothing was left to break `check_description_hygiene.py`.
- Spot-checked the reference-follows-source classification repo-wide for three of the five names;
  the two opposite-answer self-aliasing sites are exactly as the contract claims.
- Read the three prose judgement calls directly (`ui_design_brief.md:98,166`,
  `metrics_display.md:271`, the dated test comment) and agreed each is plain English or inert
  historical prose, correctly left unrenamed.
- Confirmed `rendered_page_evidence.md` measures structurally (`div.mrow` / `div.mgroup` counts,
  whole-token grep over built HTML) across 19 fixture pages × 3 locales, from `dist/` rather than
  source or `outerHTML`, with both base and branch independently built.
- No metric creep, no naked percentage, no double-render: none of the five is new to any display
  surface, none takes a `_pct` form, and no component renders any of them today.

## escalations
(none)
