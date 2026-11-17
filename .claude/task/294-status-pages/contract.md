# Task contract — every Matchdays match has a page, each status its word

objective: >
  Issue #294. Every match a competition's Matchdays tab lists gets a match page in EN, DE and FI,
  whatever its status and date: the export writes a preview payload for every fixture of
  mart_competition_fixtures that is not played, so the match pages are the same set as the
  Matchdays rows (one-source rule of #173). A match that was postponed, abandoned or cancelled, or
  whose kick-off passed with no result yet, shows its status word in the tag form where the score
  or kick-off would stand, on the match row and in the match page head. check-built-pages fails a
  full-export build when a Matchdays row has no match payload.

refs: >
  #294; its note 4255394677 holds the approved words and placement (approved in chat, 17 Nov 2026);
  #173 (one source for every list of matches); #243 parts library (the row components, !473, !475).
  Visual details are the coordinating agent's under docs/design/design_standard.md (approved in
  chat, 16 Nov 2026).

scope_paths:
  - .claude/task/294-status-pages/
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/src/components/ui/MatchRow.astro
  - site_v2/src/components/ui/StatusTag.astro
  - site_v2/src/components/fixture/Masthead.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/[[]fixture].astro
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/styles/system.css
  - site_v2/src/lib/fitBlocks.mjs
  - site_v2/src/data/README.md
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

protected_override: >
  docs/design/components.yml: the status tag joins the registry as the component that draws it
  (site_v2/src/components/ui/StatusTag.astro), placed by the match row and the match header, and the Tag rule's
  selector takes its class, so the status tag carries the Tag rule's one form (11px bold capitals
  on the accent mark, 4px corners), and the Fitted block rule's selector takes a match row with a
  status tag, so it gets the row tag's ruled narrow form. No other part, text style, value or measurement changes. The
  status display of #294 note 4255394677 (approved in chat, 17 Nov 2026: the word in the existing
  tag form, where the score or kick-off would stand, on the row and the match page head); placement
  and form are a visual detail under docs/design/design_standard.md, approved in chat, 16 Nov 2026.

impact_map: >
  writers: mart_competition_fixtures is written only by its own model
  (dbt_project/models/5_marts/shared/mart_competition_fixtures.sql); this adds one column,
  unplayed_state, computed from columns the model already reads (status_short, kickoff_datetime and
  the played join). The fixture payloads are written only by scripts/export_site_data.py
  fetch_fixture_payloads; its filter changes from `status_short in ('NS','TBD') and fixture_date >=
  current_date()` to `not is_played`.
  downstream: `dbt ls --select mart_competition_fixtures+ --resource-type model` (main 6b80c12e) =
  mart_competition_fixtures, mart_match_days, mart_player_index, mart_team_competitions,
  mart_team_index. Each downstream model selects named columns in its final select
  (mart_team_competitions reads `select *` only into a CTE whose final select lists its columns), so
  the new column reaches none of them. Consumers: scripts/export_site_data.py
  (_COMPETITION_FIXTURE_COLUMNS feeds the competition payloads' Matchdays rows, the Matches day
  payloads, Home's Next matches and each match page's next-match rows; fetch_fixture_payloads), then
  site_v2 (MatchRow, the match page head).
  layer_rules: the classification is computed in the mart (layering.md, Consumption layer: the
  frontend never derives a value a DQ test would cover); the export selects and filters only; the
  site maps the served key to its word. check_layer_contract.py applies unchanged (no new model,
  no partition_by/cluster_by).
  deploy_order: additive column. The export selects it, so an export against a mart built before
  the merge fails on the missing column instead of serving rows without it; deploy:site-v2 is
  manual and runs after the merge's data:build:main has rebuilt the mart, the order every mart
  change already takes. The 04:00 nightly rebuilds the mart from main and is unaffected.
  blast_radius: the fixture payload count grows by the not-played fixtures that are not future
  NS/TBD; measured on prod marts on 17 Nov 2026: 182 fixtures (CANC 161, PST 10, PEN with no result
  8, ABD 2, WO with no result 1; 3,442 future NS), 546 more match pages. Every row of
  mart_competition_fixtures keeps its values; one column is added. The committed sample carries no
  unplayed_state, so its rows and pages render as before.

acceptance_criteria:
  - Every match a competition's Matchdays tab lists has a match page in EN, DE and FI, whatever its status (not started, postponed, abandoned, cancelled, awaiting result) and whatever its date.
  - Each of those statuses has an approved display on the match page and on the match row, approved before the build (fan-visible).
  - A full build from live data passes `check-built-pages` with no "an unplayed row is not a link" finding.
  - A test fails the build when a row on a built Matchdays page has no match payload.

approved_design:
  - competition: #129
  - matches: #130
  - match: #132
  - home: #127

depends_on:
  - none: the work is on main alone; the #243 row components it builds on merged (!473, !475)

shared_files:
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

decisions_taken: >
  The approved words of #294 note 4255394677 map to the served unplayed_state: postponed (PST),
  abandoned (ABD), cancelled (CANC), and awaiting_result for every other fixture that is not played
  and whose kick-off is at or before the mart's build time. That last class is the note's own
  condition, "kick-off passed, no result yet", applied as written: it covers a stale NS or TBD, an
  in-play or suspended status, and a finished status with no result in int_legs__team_match. A
  played match and a match still to kick off carry NULL. The kick-off comparison is the mart's, at
  its build, the way the next-round flag already is; a site build never reads its own clock, so a
  committed sample renders the same on every build.
  On the row the tag takes the kick-off column, zone label included, and no Next or Top match tag
  stands beside it. Where the names would lose their space beside it, the tag takes the row tag's
  ruled narrow form, its own line above the home team, measured by fitBlocks.mjs the way it measures
  the Top match row (the "Fitted block" rule); at 280px the German "Ergebnis ausstehend" is 151px
  wide. In the match page head it takes the kick-off time's unit in the kick-off line,
  which shows at every width (the head's centre score slot is hidden below 700px). A status match's
  page has the form a match further out already has (head, head-to-head, each team's next match):
  its pre-match form rows leave the marts once it is due, so the preview blocks would stand empty.
  The status tag is one component, site_v2/src/components/ui/StatusTag.astro, placed by MatchRow
  and the match page head. The payload-per-row check runs when the export's manifest is present (a
  full export), the way the match-page count's manifest half does: the committed sample carries
  payloads for 11 played matches only, by design (site_v2/src/data/README.md).
  Decided by the builder under docs/design/design_standard.md and the layer contract. No new
  mechanism, dependency or recurring cost: one column on a mart the nightly already rebuilds.

decisions_reserved:
  - none: the words and the placement are approved in #294 note 4255394677; any further question goes to the coordinating session.

done_when:
  - dbt parse passes; sqlfluff lint of the mart reports no new finding against main.
  - python -m pytest tests/test_export_site_data.py passes.
  - node --test site_v2/scripts/check-built-pages.test.mjs passes, including a case that fails on a Matchdays row with no payload and passes once the payload is there.
  - A local build shows each status word on a row and on a match page in EN, DE and FI, swept at 280 to 768px.
  - python scripts/ci_local.py --mr --full-scope is green.

amendments: (none)
