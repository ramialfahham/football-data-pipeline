# Review — claude/170-team-link-built-only — 2026-11-21

diff_sha256: e9a49f9a7f002cdaf72c6b8817b209686330d8d74deae7fc96602a9f63c0ce2a

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3, whole branch: every route that renders TableRow with a team prop (Home through TopTeams, competition through StandingsTable and DeservedTable, Statistics through RankingsBlock and RankingBoard) is named in approved_design with its issue in approved_designs.yml; the earlier findings (rounds 1 and 2) were pages missing from that list and are closed.
- Scope: only builtTeams.mjs, its test, TableRow.astro, the Teams page and the task folder are touched; no amendment is needed.
- Decision classes: no new URL, wording, metric, dependency, recurring cost or mechanism; the lookup mirrors builtPlayers and the plain-text rule is named as approved in chat, 21 Nov 2026.
- decisions_reserved: whether a team with no match gets a page stays with #170.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1, code unchanged since (only contract.md changed in rounds 2 and 3): a div row lays out as an a row, because the layout rules sit on .ctab-row; hover and the 44px minimum height are a-only, correct for a row that leads nowhere; player rows already render as div.
- Rows of teams with a page build the same href as before; the built set equals the pages the team route emits; the Teams page's linking is unchanged.
- The lookup is read once per build process; the Teams page used to parse every team file once per locale.

## escalations
(none)
