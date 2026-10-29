# Review — feat/235-table-exact — 2026-10-29

diff_sha256: f58e1ab9bab6dced11cc99ca13026ab961b64c35626cd8e7b836c0bc47846e61

rounds: 5

rounds_cap_override: the first two MR data builds failed the published-table test on places; the fourth and fifth rounds review the fixes, approved in chat, 2026-10-29

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged path is in scope_paths; nothing credential-shaped.
- The Portugal in-season order, the column name provider_order_differs, the all_h2h_met condition and the skip carry their approval in the contract; the second-pass grouping is a technical reading of the head-to-head rule.
- The new column, condition and version test add no dependency, run or query volume; the skip covers only places of teams level on points in a flagged version.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The second pass now groups by every criterion from the first head-to-head one to the first h2h2 one; Spain's and Saudi Arabia's final-table versions are unchanged, versions without h2h2 never read it, and nothing fans out.
- all_h2h_met is read only where a version uses it; a one-team group counts as met.
- The test's exemption parses as intended, covers only ranks, and a version without rules falls back to compared.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The seed keeps CRLF, every row has eight fields and ends true or false, and only Portugal's 2023 in-season version is true.
- The new column is typed boolean and not null; both changed tests stay errors and nothing downgrades them.
- The exemption needs a flagged seed row; one value per version is enforced.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Portugal's in-season order matches Article 17 (head-to-head, goal difference, wins, goals; head-to-head goal difference only once both games are played) with the head-to-head again among the teams still level, as the league's tables show.
- Teams still level get no place, as Article 17.4 gives them the same place.
- Portugal's final-table rows are untouched; each rule row's condition and source hold only their own thing.

## escalations
(none)
