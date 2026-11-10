# Review — claude/feat-135-players-page — 2026-11-10

diff_sha256: 03990c538d1e016b6a5d03e70ce9e362c0618f7537542399eab54e8085a041f7

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is inside scope_paths; the page paths match `site_v2/src/pages/*players*.astro`; the three amendments name their authority and match the diff.
- The protected edits are only what protected_override names: players_index in the deploy export list, the fold link part and the used-on entries in components.yml.
- decisions_taken matches the code: the warehouse serves the four flags and the slug, the no-nation group shows its first 10 with no page, the slug clash is stopped in dbt, in the route and in the SEO audit.
- Doc sync: site_architecture.md lists both Players addresses as built and has the two §5 rows; block_standard.md carries the generated fold-link row.
- The rebase onto main after the term list follow-up leaves the branch's own change in menu.ts and site_architecture.md as reviewed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every new window ends in a unique key; club_place follows order_in_nation, so the flags are deterministic.
- is_hub_shown is regulars plus the first 10 others, the position flag the same inside a position and false without one; has_nation_page holds one value per nation and is false without a nationality.
- The flag test recounts through a self-join, not the model's window, and catches an off-by-one or a missing position partition; the flags are not_null.
- All 229 country keys match the nation slug pattern; the descriptions agree with the SQL.
- The export only selects and renames the four columns.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every field the pages read is emitted by shape_player_index from mart_player_index; the sample carries no hand-written key.
- Nothing in the frontend ranks: lib/playerIndex.mjs sorts by served orders and cuts by served flags.
- Every visible word is a strings.ts key in EN, DE and FI.
- rendered_page_evidence.md shows no sideways scroll or cut text at 280 to 1010px in three languages, every Show all link spanning its grid row, one count per nation under a position, and the group heads on one line at 280px.
- The hub's ItemList count is the players the page lists.

## platform-reviewer
VERDICT: PASS
risks_checked:
- players_index in the deploy export matches the entity in export_site_data.py; a missing file fails the build closed.
- The SEO audit's player shape covers both slugs the exporter emits, name-id and the bare id, and stays disjoint from the nation shape; the new tests fail on a revert.
- check-page-specs.mjs and the schema enum hold the same entity set, pinned by a test.
- The nation route throws on a slug clash inside getStaticPaths; the build stays deterministic.
- No dependency, credential or permission change.

## cto-reviewer
VERDICT: PASS
risks_checked:
- protected_override names both guard paths, what changes in each and the approval, approved in chat, 2026-11-10; the deploy job's trigger, permissions and credentials are untouched.
- PARAM_SHAPES, the two page entities and the position words on FilterRows are extensions of existing mechanisms, declared in the amendments.
- The SEO audit again checks every player page's structured-data type, the bare-id slug included.
- No new dependency or recurring cost: about 303 static pages in the manual deploy build, one SELECT in the export, four columns and a small test in the nightly.

## escalations
(none)
