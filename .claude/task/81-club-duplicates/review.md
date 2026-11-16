# Review — claude/81-club-duplicates-31d05c — 2026-11-16

diff_sha256: cf7979ac5078cef049ede22503aa739e0cdc77f9a1b855d82f68617868e108f4

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 failed on the fixture_team_id_overrides seed description, stale after alias was applied in seven more base models; round 2 updates it and its wrong_team_api_id column, and decisions_taken names the approval for the text and the extension.
- Every changed path is in scope_paths; the alias and Europa rows use existing seed modes, each with an external source; no naming, URL, metric or UX decision is made.
- team_id_override has the shape of player_id_override and adds no object class; no provider call or run-cadence change, so no recurring cost.
- No site_v2 or export file is touched, so approved_design none holds; the Bury merger in decisions_reserved is not touched.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed on the stale seed descriptions and on an impact map that named 47 of the downstream models; round 2 fixes both, and the pasted list counts 16 base, 44 intermediate, 12 core and 33 marts models, 105 in all.
- Layer placement: the id correction sits in base only, as player_id_override and the per-feed alias joins do; no core or mart logic, no per-competition file.
- Grain: squads, player-team-season, coach career, transfers and standings dedup after the alias, so two folded ids cannot break their grain tests; all staging team ids are int64.
- Seeds: no other seed names a retired id; no cohabiting or in-fixture row names a duplicate as its correct id, and the test guards alias chains.
- assert_team_id_aliases_merged covers left-behind ids, summed matches, both ids in one fixture or standings table, and chains; it sets store_failures as engineering_standards §3.4 asks.

## escalations
(none)
