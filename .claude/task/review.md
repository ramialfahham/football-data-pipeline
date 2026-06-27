# Review — refactor/500-pr-d-step6-teardown — dead-seed trigger ref + stale doc model-name globs

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set: always → scope-auditor; `.github/workflows/**` → cto-reviewer; `docs/wireframes/**` → bi-analyst-reviewer.
> #500 PR-d step 6 (teardown), candidates 1 + 4 only. PROTECTED path (`.github/workflows/pages-match-preview.yml`)
> edited under the contract's protected_override (CPO-approved 2026-06-27).

diff_sha256: b73a5055b2e47548c5e8852ca7432ada0d32d75114c2861b24f206dce7de0028

## scope-auditor
VERDICT: PASS
risks_checked:
- Trigger-path deadness recovery: the diff replaces the deleted `dbt_project/seeds/metric_definitions.csv`
  trigger with `dbt_project/seeds/metric_catalogue.csv` in `pages-match-preview.yml`. Verified metric_definitions.csv
  is gone, metric_catalogue.csv exists in dbt_project/seeds/, and only that ONE trigger path changes in the
  on.push.paths block — no other path added or removed. Workflow now fires correctly on the active metric seed.
- Doc/model-name consistency: both docs/content_architecture.md and docs/wireframes/99_gaps_register.md are
  updated from the pre-#500 shorthand `mart_fixture_stats__{team,player}` / `mart_fixture_stats__*` to the
  canonical `mart_team_fixture_stats` / `mart_player_fixture_stats`. Verified both marts exist on main at
  dbt_project/models/5_marts/shared/; docs are consistent with each other and the live model names.
- Scope boundary: all changed files are within scope_paths; the three reserved decisions (candidates 3 + 5,
  trigger-block rot) appear nowhere in the diff. No §10/CPO-class decision embedded — the doc rename points at
  names that already exist on main; the trigger change is a faithful migration of existing intent.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Trigger correctness — deleted seed + replacement existence: `metric_definitions.csv` confirmed absent (no glob
  match); `metric_catalogue.csv` confirmed present. The replacement points at a real file that is the post-migration
  SSoT. No phantom trigger.
- Trigger correctness — run step actually consumes the catalogue: `scripts/export_metric_definitions_json.py`
  (workflow line 129) reads `dbt_project/seeds/metric_catalogue.csv` directly, so triggering the Pages deploy on
  catalogue changes is semantically meaningful, not decorative.
- Redundancy/coverage — bindings already triggered: `site/match-preview/metric_bindings.csv` is covered by the
  `site/**` glob (line 17), so the contract's claim that only the catalogue needs adding is correct; no missing
  trigger. The new catalogue path is NOT subsumed by any existing glob (no wildcard under dbt_project/seeds/) — it
  is the minimum necessary addition.
- YAML validity/style: exactly one line changes; six-space indentation, double-quote style, and list position are
  preserved. No structural YAML defect.
- Protected-override completeness: the contract carries `protected_override:` naming the CPO (Rami), the approval
  date, the path, and the reviewing role (cto-reviewer). Guard-integrity satisfied.
- Remaining stale trigger paths (dead build_metric_glossary_json.py path; flat mart paths lines 18-23) are
  explicitly flagged out-of-scope and deferred — not silently left. Defensible boundary: pre-existing rot from a
  different refactor; the workflow still runs correctly on every trigger that fires today.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Renamed mart references resolve to real models: both `mart_team_fixture_stats.sql` and
  `mart_player_fixture_stats.sql` exist at dbt_project/models/5_marts/shared/. Post-patch text in both docs
  resolves to existing models — no dangling reference.
- Naming-convention consistency: docs/site_architecture.md line 121 already uses the entity-first
  `mart_team_fixture_stats`/`mart_player_fixture_stats` form; after the patch the two edited docs match it, and a
  grep across docs/ for the old shorthand `mart_fixture_stats` returns zero matches — no orphaned old form remains.
- No silent display/scope-claim change: GAP-07's disposition keeps the same scope (header, final score, the two
  fixture-stats marts); only the shorthand is made explicit/canonical. Gap type, ruling, and issue columns untouched.
- Markdown table structure preserved: both edited rows retain their pipe-delimited cell count (content_architecture
  row = 5 cells; gaps_register row = 7 cells). No column collapse or ghost cell.

## escalations
(none)
