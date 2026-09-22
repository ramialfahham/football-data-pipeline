# Task contract — #152: metric groups defined in one place

objective: >
  A metric group is defined once: its key and its order in `metric_catalogue.csv` (`duels` becomes
  `one_on_one`; a `metric_group_order` column, the same value on every row of a group), its names
  as site copy keyed by the group key (`metricGroups.<key>.label`, EN/DE/FI), and tests binding the
  three. The export publishes the groups (key, order) as a data file the site build reads; the
  hard-coded `MetricGroup` type and `GROUP_ORDER` in `metricRows.ts` go; the two components that
  print a group heading resolve it per locale from the copy, in the catalogue's order. #98 closes
  with it. No metric moves group; no metric value, format or direction changes.

refs: >
  #152 (the CPO's ruling on #129, 2026-09-16: no second seed; the names table, quoted in
  `decisions_taken` by reference); the order ruling in chat 2026-09-21 (quoted in
  `decisions_taken`). `docs/metric_layer.md` (the catalogue is the single source);
  `docs/wireframes/metrics_display.md` (LOCKED; owns row order within a group, and until now
  group order); `docs/wireframes/99_gaps_register.md` GAP-09. Measured on `main` at `f1931742`:
  87 catalogue rows, 10 distinct groups, `duels` on 10 rows (2 team, 8 player); the site's
  `MetricGroup` union has 7 English words; `TeamPerformance.astro:89,110` and
  `MetricComparison.astro:40` print the raw group string on every locale.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_metric_group_order_is_one_per_group.sql
  - scripts/export_site_data.py
  - site_v2/src/data/metric_groups.json
  - site_v2/src/data/README.md
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/components/team/TeamPerformance.astro
  - site_v2/src/components/fixture/MetricComparison.astro
  - site_v2/scripts/check-metric-labels.test.mjs
  - tests/test_metric_groups.py
  - design-mocks/gen_competition_teams.py
  - docs/metric_layer.md
  - docs/wireframes/metrics_display.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md
  - docs/tracker/gitlab_snapshot.md

impact_map: >
  writers: `dbt_project/seeds/metric_catalogue.csv` is a seed — its only writer is this repo. The
  rename touches the `metric_group` value on 10 rows and adds one column; no `metric_id`,
  expression, format or direction changes, so every model that reads the catalogue computes the
  same numbers.
  downstream, measured on this branch with the scratchpad profile:
  `dbt ls --select metric_catalogue+ --resource-type model` → no output (no model reads the
  seed); `dbt ls --select metric_catalogue+ --resource-type test` → the seed's own schema tests
  (7 `accepted_values_metric_catalogue_*`, `not_null_*`, `metric_catalogue_label_en_unique_within_entity`)
  and the singular tests `assert_form_window_rates_inputs_covered`,
  `assert_metric_catalogue_expr_resolvable`, `assert_metric_catalogue_unique_by_entity`,
  `assert_metric_direction_lower_is_better_agree`, `assert_metric_group_order_is_one_per_group`
  (new), `assert_metric_meaning_complete`, `assert_no_uncatalogued_season_metric`,
  `assert_season_rates_inputs_covered`. Of those only
  `accepted_values_metric_catalogue_metric_group__…` reads `metric_group` (updated in the same
  MR) and the new test reads `metric_group_order`; the rest read expressions, ids and meaning
  columns. `grep -rn "metric_group" dbt_project/models dbt_project/macros` → 0 hits;
  `sync_metric_docs_blocks.py` reads `description` only. Under `persist_docs` the seed rebuilds in
  `ci_mr<IID>_*` once per pipeline — cents.
  consumption: `scripts/export_site_data.py` gains a `metric_groups` entity (seed → JSON, no
  BigQuery, the `fetch_glossary` precedent); the glossary entity (`metrics.json`, not a committed
  build input) carries the renamed key and the new column through unchanged code. The site reads
  `site_v2/src/data/metric_groups.json` (a committed root file, not gitignored) for keys and
  order, and `strings.ts` for names. The fixture comparison and the team page reorder their
  groups to the catalogue's order — the CPO's choice, quoted below.
  layer_rules: none touched; no model, no schema, `check_layer_contract.py` unaffected.
  deploy_order: nothing until `deploy:export` (manual, `teams,fixtures`) or #156; the committed
  sample carries the new file so the build is self-contained on the merge.
  blast_radius: no number on the site moves. The group heading text on DE/FI pages changes from
  English to the locale's name (#98), and group order on two pages changes as ruled.

acceptance_criteria:
  - On the built DE team page (`site_v2/dist/de/teams/<slug of 33>/index.html`), the Performance tab's group headings read, in this order and only for groups that have rows: Tore · Schüsse · Pässe · Eins-gegen-eins · Defensive · Torwart · Standards — read as textContent from the built HTML.
  - On the built FI fixture page of a committed sample fixture with both windows populated, the comparison's group headings are the Finnish names from the #152 table (Maalit · Laukaukset · Syötöt · Yksi vastaan yksi · Puolustus · Maalivahti · Erikoistilanteet, only groups with rows), in that order.
  - No built page under `site_v2/dist` carries "Duels", "Goals", "Shooting", "Defending", "Passing", "Set pieces" or "Goalkeeping" as a group heading on a DE or FI page (the group-heading elements only; metric row labels keep their own words).

decisions_taken: >
  The CPO's rulings this contract rests on. (1) #129 review, 2026-09-16, written to #152: no
  second seed — the catalogue keeps the assignment, the group's names are site copy keyed by the
  group key, the order is a catalogue column, tests bind the three; the ten names EN/DE/FI as the
  issue's table. (2) Chat 2026-09-21, to the blinded question "which single order goes into the
  catalogue" with the 2×2 (the issue's table order vs the locked contract's order): "A" — the
  issue's table as it reads — "We will look into the fixture and team pages again anyway." So
  `metric_group_order` is goals 1, shooting 2, passing 3, one_on_one 4, defending 5,
  discipline 6, goalkeeping 7, set_pieces 8, outcomes 9, playing_time 10, and every surface
  renders groups in it; the locked display contract gets a one-line note that group order now
  comes from the catalogue, row order within a group stays there.

  Taken as implementation: the site reads the groups from an exported data file
  (`metric_groups.json`, `[{key, order}]`), not from the seed directly — the consumption-layer
  rule: the export is the site's source, the same path `competition_index.json` takes; the
  entity needs no BigQuery, as the glossary does not. The names live inside the existing
  `METRIC_LABELS_EN/DE/FI` maps as `metricGroups.<key>.label` — the issue's "the way
  `label_i18n_key` works for a metric" — so `check_copy_gate.py` and
  `check-metric-labels.test.mjs` govern them with no change to either gate, and `metricLabel()`
  resolves them. The column is named `metric_group_order` as the issue says, not GAP-09's
  `group_display_order` (the issue is newer and the CPO's); the register row is corrected. The
  mock generator's Finnish group names (Laukominen, Syöttäminen, Puolustaminen, Maalivahtipeli)
  give way to the issue's table (Laukaukset, Syötöt, Puolustus, Maalivahti); the approved renders
  are not regenerated. The singular test carries `store_failures` (§3.4) at `error`: a group with
  two orders, an order shared by two groups, or an order outside 1..N is a wrong page. No new
  mechanism: one export entity, one seed column, one singular test, one pytest, three assertions
  in an existing build test. No recurring cost. The seed's `column_types` pins
  `metric_group_order: int64` beside the existing `importance_tier: int64`, so the type is
  declared, not inferred.

decisions_reserved:
  - none: the names and the order are ruled; the per-row group assignment is unchanged (the issue's How: "the only wrong bucket was dribbles under duels, resolved by the group's new name").

done_when:
  - `python scripts/export_site_data.py --entities metric_groups --out <scratch>` writes a `metric_groups.json` byte-identical to the committed one.
  - `python -m pytest tests/test_metric_groups.py tests/test_export_site_data.py tests/test_metric_bindings.py -q` green; the regen pin seen red against a scratch CSV with one order duplicated.
  - `cd site_v2 && npm test` green; the group assertions seen red with one FI label removed.
  - `python scripts/check_copy_gate.py` exits 0; seen red with one DE group label removed.
  - `.venv/Scripts/dbt.exe parse` green with the scratchpad profile; the singular test lints clean from the repo root.
  - `npm run build` on the committed sample; `python scripts/check_design_inventory.py --dist site_v2/dist` exits 0; the three acceptance criteria demonstrated from `dist` in `acceptance_evidence.md`.
  - `data:build:mr` green.

amendments:
  - 2026-09-21: the first two acceptance criteria corrected — authority: the order ruling quoted in `decisions_taken` (goalkeeping 7, set_pieces 8); content: as first written they listed Standards/Erikoistilanteet before Torwart/Maalivahti, transposing positions 7 and 8 of the ruled order. The built page showed the ruled order; the criterion was the error. No path added, no criterion softened.
  - 2026-09-21: + `.claude/task/rendered_page_evidence.md` — authority: repo practice, `.claude/agents/bi-analyst-reviewer.md` item 4 (the artifact is required for a rendering-affecting `site_v2/src/**` change, produced before that reviewer runs); content: the group headings measured in headless Chromium at 375 and 700 px on the DE and FI team and fixture pages — text, box, overflow, page width — with screenshots in the session scratchpad. The reviewer's round-1 finding: the file on disk was #150's.
