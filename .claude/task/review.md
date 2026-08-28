# Review — refactor/metric-rename-team-shooting-shares — 2026-08-28

> Step 3 of the metric catalogue naming programme, MR **C of six**:
> `shot_accuracy` → `shots_on_goal_pct`, `danger_zone_ratio` → `shots_inside_box_pct`,
> `shot_share` → `shots_share_pct`. Branched from main `9e2aaf9`, the main carrying `!118`.

diff_sha256: 40fc20bea9616b824ea968c82bc04242a9c906f713fdb622d918d1cf0c5e3744

rounds: 2

> **Round 1: four PASS, one FAIL.** `bi-analyst-reviewer` FAILed on two findings, both correct and
> both in hash-excluded evidence artifacts — so the code diff never changed, the hash is identical
> across both rounds, and the four round-1 PASSes bind to the same hash and stand.
>   1. `.claude/task/rendered_page_evidence.md` was STALE — it still held the "export sample refresh
>      after #90" MR's content from two tasks earlier and documented nothing about batch C.
>      `!116` had already noticed it was stale and merely NAMED it; that deferral is what let it
>      mislead a second reviewer. REPLACED with batch C's actual rendered evidence.
>   2. The occurrence-reconciliation table in `acceptance_evidence.md` counted 6 hits in
>      `metric_columns.md` and 2 in `metric_definitions.json` as "stays", totalling 17. Regeneration
>      had cleared both to zero. CORRECTED to 128 replaced + 8 cleared by regeneration + 9 remaining
>      = 145, with the cause named rather than quietly patched.
>
> **Round 2: `bi-analyst-reviewer` PASS.** Only that reviewer was re-run, because the hash did not
> move.
>
> ⚠ ROUTING DEVIATION, DECLARED. `acceptance_evidence.md` and `rendered_page_evidence.md` are both
> in `review_exclude_paths` — reviewers are not normally shown them. All five were pointed at them
> directly. That is what surfaced both round-1 findings, neither of which was visible in the diff.

## scope-auditor
VERDICT: PASS
risks_checked:
- Naming authority for all three renames verified verbatim against `escalations.log`'s RULING 1, RULING 4, and item 2 of "THE SIX, ENUMERATED" — no reconstruction, and confirmed the superseded RULING-1 name `danger_zone_pct` does not leak into the diff anywhere (RULING 4's override was applied correctly).
- Scope: every file in `diff --git` output cross-checked against `scope_paths` in `contract.md` — no unlisted file touched; the six declared-excluded files (frozen `site/team-season/index.html`, `metric_manifest.json`, `docs/match_preview_pages_refinement.md`, `docs/working_agreement.md`, `mart_player_profile.sql`) confirmed absent from the diff.
- Formula integrity: read every SQL hunk in `int_team_season__metrics_cumulative.sql`, `mart_team_momentum.sql`, `mart_team_profile.sql`, `mart_team_season_record.sql`, `int_team_profile__yoy.sql` — only column aliases changed, no `case`/`safe_divide` logic altered.
- `accepted_values` lists (`int_competition_benchmarks.yml:27,66`, `shared.yml:2080`) recounted by hand — 22 values each, both new names present, `shot_share` correctly absent (not benchmarked).
- Secrets sweep across the entire patch (api key/token/password/private-key patterns) — no matches.
- `escalations.log` diff confirmed append-only (pure addition at end of file), consistent with the log's own discipline; no historical entry rewritten.
- Two illustrative-string renames in `check_description_hygiene.py`/`test_description_hygiene.py` — both files are in `scope_paths`, both changes are declared in `decisions_taken`, and both are cosmetic (comment/fixture text), not logic.
- `decisions_reserved` — the only forward-carried item (#98, DE/FI group-heading English wording) is untouched by this diff; no §10 item decided silently here.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Formula byte-identity across every renamed column in `int_team_season__metrics_cumulative.sql`, `mart_team_momentum.sql`, `mart_team_profile.sql`, `mart_team_season_record.sql`, `int_team_profile__yoy.sql` — only aliases changed, no layer-boundary move.
- Catalogue governance (A1): the three renamed seed rows change only `metric_id`+`label_i18n_key`; the fourth row's edit is a cross-reference text fix, not a redefinition; renames traced to RULING 4 and enumerated-six item 2 in `escalations.log`.
- Three 22-name `accepted_values` lists counted by hand post-change, all exactly 22, `shot_share`/`shots_share_pct` correctly absent.
- Derived-identifier sweep (yoy `_this_season`/`_prev_season`/`_delta_yoy` forms, `__team` doc blocks, nine named `*_in_range` tests) verified complete and correctly scoped. Confirmed via `int_team_profile.yml` that `shot_accuracy`/`shot_share` never had yoy forms, so their absence there is correct, not a miss.
- Protected `_recent` live_id in `metric_bindings.csv`/`metric_definitions.json` correctly left standing alone while catalogue-id plumbing around it was updated.
- Repo-wide grep for old names: every remaining hit is a declared exception (generated export sample, frozen `site/team-season/index.html`, `metric_manifest.json`, history docs, rejected player-metric comment) — no orphaned reference in `dbt_project/`.
- `mart_team_momentum` (#93 duplicate formula) renamed consistently with its own range tests; confirmed via `ref()` chain it sits outside the `int_team_season__metrics_cumulative` lineage, corroborating the contract's A6 disclosure about `mart_team_momentum`/`mart_matchday_insights` being edited despite absence from the pasted `dbt ls` output.
- Consumption-layer files (`export_site_data.py`, `metricRows.ts`, spec JSONs) checked for computation creep — only identifier renames, no new math/filter/derivation.
- No hardcoded league/competition identifier introduced.
- Same-window numerator/denominator coverage gating unchanged by the rename.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Pure-rename verification (all 3 rows): only `metric_id` and `label_i18n_key` changed; `label_en`, description, `base_relation`, `numerator_expr`, `denominator_expr`, `computation_kind`, `lower_is_better`, `format`, `metric_group`, `importance_tier`, `direction` and `interpretation` are byte-identical before/after.
- Direction correctness: all three keep `lower_is_better=false` / `direction=higher_better`, and that is football-correct — higher on-target share, higher box share and higher share of match shots are all genuinely better. No sign-flip introduced.
- Edge-case honesty survives verbatim: "Null when shots_total is zero" (×2) and "Null when no shots." unchanged word for word.
- The fourth changed line (`shots_inside_box`) is a mechanical cross-reference fix, not a redefinition: post-diff, zero stale references remain anywhere in the seed, and no formula, direction, tier or group field on that row changed.
- No id collisions / no composite smuggling: each new id appears exactly once; all three formulas are plain ratios of raw provider counts.
- The `shots_on_goal_pct` / `shots_on_goal_per_match` id-vs-label question, judged rather than deferred: `shot_accuracy` is on the CPO's own 9-row step-5 list moving English labels "on target" → "on goal" (RULING 2), so the id/label lag is a ruled, tracked, disclosed transient with a named fix already queued — not a gap invented here. It is also moot on the live surface today: the wireframes record `shots_on_goal_pct` as existing but unrendered, so the share and the rate are not shown side by side to a fan. The shared noun stem across a count/rate/pct family matches the catalogue's existing convention (`corners`/`corners_per_match`, `goals`/`goals_per_match`) — not a new confusion risk.
- `shots_inside_box_pct` beside `shots_inside_box`: the catalogue's standard count/percentage pairing; the count row's description now correctly names the share. No misleading pairing.
- CPO approval authenticity: quotes pulled from `escalations.log` and checked character for character against the contract's citations — RULING 4, RULING 1, enumerated item 2 and "apply the suggested changes to ensure consistency" all check out. No fabricated authority.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `scripts/check_description_hygiene.py:118` — the `shot_share`→`shots_share_pct` swap is inside a comment illustrating a generic snake_case regex, not a literal. Comment-only change, zero effect on gate behaviour.
- `tests/test_description_hygiene.py:287` (`OFFENDERS` fixture) — the fixture string still matches the same class regex identically, so `test_each_banned_class_turns_the_gate_red` still proves what it did before. Not weakened.
- `scripts/export_site_data.py:407` — only hit is a docstring; the export reads `row.get("metric_key")` generically, so no functional code references these names.
- Regenerated artifacts: `metric_columns.md`'s block reordering matches `sync_metric_docs_blocks.py`'s `sorted(blocks)` output shape, consistent with generation not hand-editing. `metric_definitions.json` is keyed by the unchanged `live_id` with `label`/`home_column`/`away_column` repointed — exactly the exporter's logic, and `test_regenerated_json_matches_committed` re-runs the exporter and byte-compares, so drift would be caught.
- Nine renamed dbt test names checked against the model each tests: `std_team_*` and `team_profile_shots_share_pct_in_range` bind to columns renamed in the same diff; `momentum_team_*` to `mart_team_momentum.sql`; `mmi_home_/away_*` to `mart_matchday_insights.sql`'s renamed aliases. No orphaned test, no duplicate old+new pair left behind.
- #96 verified directly rather than taken from the contract: the lists are correct, the gap is pre-existing and consistently disclosed, not introduced here.
- Mutation-2 characterisation traced through `check-metric-labels.test.mjs`: it asserts every `labelKey` used by `metricRows.ts`'s 16 rows is declared, so a non-displayed metric has nothing to check against — exactly as claimed; `shots_inside_box_pct` IS one of the 16 (confirmed at `metricRows.ts:86`), so the paired "goes RED" claim is architecturally sound.
- Residual old-name sweep over `dbt_project/`, `site_v2/src` (excl. `data/`), `site/`, `scripts/` — only the declared exemptions remain.
- No changes to `.claude/hooks/**`, `.github/workflows/**`, `.gitlab-ci.yml`, `*requirements*.txt`, `package*.json`, `site_v2/.gitignore`, `firebase.json` or `astro.config.mjs`.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Rendered-row and group-heading counts verified directly against the built tree, not from prose: `class="mrow"` (30), `class="mgroup"` (14), `class="cmp"` (2) in the built EN reference page → 15 rows / 7 headings per comparison block, matching both evidence files.
- Read the rendered `Shooting` group in that page's HTML directly: exactly 3 rows in both w1 and w2 blocks; `% Shots from box` is absent, never blank or zero — the row is honestly omitted, not fabricated.
- Checked the DE and FI builds for the box-specific words `Strafraum` and `boksista` — zero occurrences in either, while the generic shots labels that legitimately survive still render — confirming the removed row is gone in all three locales, not just EN.
- `grep -rl` over `site_v2/dist/` for all three old names → 0 files.
- Built team-page absent state present in all three locales.
- Diffed `strings.ts`, `site/i18n/{en,de,fi}.json` and `metric_catalogue.csv` line by line: only KEYS changed; every label VALUE is byte-identical. No display wording changed anywhere in this diff.
- Re-verified the CORRECTED reconciliation (128 + 8 + 9 = 145) against the actual tree file by file, including that `metric_definitions.json`'s 2 remaining hits are the protected `_recent` live_id keys — substrings, not whole-token catalogue references, correctly excluded from the "9 remain" bucket.
- The three 22-name `accepted_values` lists checked by eye — 22 entries each, new names at positions 5/6, `shot_share` correctly absent.
- Grepped `site_v2/src` for the new names outside the touched files: `shots_on_goal_pct` and `shots_share_pct` appear nowhere (consistent with not being among the 16 rendered rows); `shots_inside_box_pct` appears only in the 4 expected files.
- Both cited authorities verified verbatim in `escalations.log` — no invented naming.
- Both round-1 findings genuinely fixed rather than papered over; no new inconsistency introduced between the two evidence files and the tree, no wording drift, no field-binding fabrication.
