# Review — feat/222-team-rankings — 2026-10-31

diff_sha256: f1c6480ec2da4269a29f5b67290f065a195410a17779587855862abc6e8fa0d7

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the layering.md row, the macro replaced by int_team_index__round_values, the nightly cost, the approved_design pages, the pasted dbt ls list with the 435-fixture measurement, and the AFC readings, each with its approval in the contract.
- No credential, workflow or permission change; layering.md inventories no intermediate models, so the new int_ model needs no row.
- Every round_names.csv row is scoped to one competition; strings.ts gains one key in EN, DE and FI; decisions_reserved is none.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The round values live in one intermediate model with unique, not_null and accepted_values tests, read by the mart and the round test; no intermediate model reads a mart.
- A national team counts only its own region's championship; the qualifier criterion uses the latest season with a finished table match, on matches with goals.
- The round test fails on an unnamed round and on a configured competition with no counted season; six consistency tests and a coverage test guard the mart.
- A ranked club's served region is its top club competition's, the key top_club_rank is partitioned by.
- No hard-coded competition identifier; the mart takes the layer's table materialisation.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- roundKnockoutPlayoffs matches its approved EN, DE and FI text, and every key the new round_names.csv rows use exists in all three languages.
- mart_team_index serves every order the Teams page needs, so the page applies none of its own.
- region_key and top_club_rank agree for every ranked club; national_teams_first follows the nightly build, as #133 says.
- Round 3: the competition header, Matchdays and the Team page Competitions block name rounds through roundName from the served key; no match-page file does, so the criterion names only those two pages.

## escalations
(none)
