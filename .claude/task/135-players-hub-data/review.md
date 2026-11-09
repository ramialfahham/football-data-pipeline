# Review — claude/feat-135-players-hub-data-c6087e — 2026-11-09

diff_sha256: d58136ad4a6034cf25ff296f7eb74b7eadc5f5bf6ac4ba51f6fdbad86ec89b25

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is inside scope_paths; .gitlab-ci.yml is untouched, so the deploy job's entity list does not gain players_index.
- decisions_taken matches the code: the latest edition per award, the Goalkeepers list as the Yashin Trophy nominees, 90 or 120 match minutes since 1 July 2025, the one-third regular threshold, club minutes over the this_season window.
- The docs/site_architecture.md §5 table is keyed by page template; the contract records that the Players template brings its row in the page MR, which closes the round-1 doc-sync finding.
- decisions_reserved keeps the page-size question open; no page code is touched.
- No new mechanism or recurring cost beyond two tables; impact_map carries the pasted lineage; approved_design names players: #135.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Grain of mart_player_index against each join: one featured row per page player, one order per nation, national minutes per (player, team), club minutes summed once per player, one award per player.
- club_order, nation_order, order_in_nation and worlds_best_order end in a unique tie-break and are deterministic; one_value replaces any_value; no approx_quantiles.
- The [worlds_best_list, worlds_best_order] uniqueness test is limited to rows in a list, so the round-1 failure on the non-nominees' NULL group is gone.
- The goalkeeper expression test fails on a Yashin nominee with no list; the World's best singular test fails on a page-holding Ballon d'Or nominee with no position.
- Intermediate reads no mart; the marts read marts in their own layer, as layering.md allows; descriptions agree with the SQL and stay under the length limits.

## platform-reviewer
VERDICT: PASS
risks_checked:
- teams_index.json is unchanged: club_order is not in _TEAM_INDEX_KEEP; players_index writes its own file and manifest entry.
- The deploy job passes an explicit entity list without players_index, so nothing deployed changes.
- The export output order is total (nation_order, order_in_nation; worlds_best_list, worlds_best_order).
- The two new tests fail on a changed shape, order clause, mart or select list.
- No dependency, workflow, hook or permission change.

## escalations
(none)
