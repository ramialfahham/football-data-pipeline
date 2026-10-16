# Review — feat/175-played-match-page

diff_sha256: 7eb0a7cd795be57a1a0a37d6fb4aff0e761a2e6195504ac885777a77e930f1e3

rounds: 5

rounds_cap_override: approved in chat, 2026-10-16, for rounds 4 and 5, limited to criterion 16 moving to right after the merge and the two impact_map lines that state its reach.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The substitutes order sits in base_apif__lineups: starters in the sheet's order, then substitutes who came on by minute, added minute and event, then the bench by shirt; lineup_order stays unique and the reworked test pins it.
- The export copies served columns only; the played payloads build no player slug (CPO ruling), and the tests assert none is emitted.
- recent_meetings.fixture_api_id follows the nested provider-id pattern; assert_mart_head_to_head_meetings_are_fixtures joins every meeting to fct_fixture.
- awarded_to_team_sk passes through mart_competition_fixtures with its relationships test; no other payload gains a key.
- The streamed walk reads each mart once, ordered by fixture_sk; no seed or config changes; no league identifier in the new logic.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every field the new components read exists in the played payload's shaping functions.
- Match stats shows rows only when a served row outside the Goals group has a value; otherwise its one not-recorded line.
- A missing scorer, player or replaced player shows "–"; the score is reachable by screen readers at every width.
- Played rows link exactly when their page is built, proven by check-built-pages' data-fixture check; player rows stay unlinked by CPO ruling.
- The Substitutes head keeps its 14px in both columns; rendered_page_evidence.md reads 375 and 1010px and the design check passes.
- Round 3: the eleven samples re-exported from the MR build carry no player slug, carry awarded_to_team_id (Bastia–Lyon names Lyon), list substitutes in coming-on order, and cover goals without minutes, goals not recorded and one side without player stats.

## platform-reviewer
VERDICT: PASS
risks_checked:
- checkMatchRowLinks runs on every built page against the payload ids and fails both directions; its unit test pins them.
- The check's header comment and summary line state the current rules; the --played-ids help is accurate.
- builtFixtures.mjs reads each payload once; no client script imports node:fs; no dependency, workflow or hook change.
- Not blocking, noted for later: the row check has no floor on rows checked, so a component that drops data-fixture goes unchecked.
- Criterion 16 stays open by agreement; the measurement includes the export artifact's size.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; each amendment names its authority.
- decisions_taken records the CPO's approvals of 2026-10-16: the wording, the composed description, the permanent URL, no player slug, the fixture_api_id name.
- Core-document edits (ui_design_brief.md, site_architecture.md) carry their approved texts.
- No new mechanism; the recurring cost is declared and its measurement is owed (criterion 16).
- No secrets; doc-sync complete.
- Round 3: the delta is the eleven sample payloads only, in scope; no secret, no player slug; the export query bytes were put to the CPO first.
- Rounds 4 and 5: criterion 16 moves to right after the merge with its authority recorded; deploy_order and blast_radius now say the measuring deploy from main runs after the merge and publishes the site.

## escalations
(none)
