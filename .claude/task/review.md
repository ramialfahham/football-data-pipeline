# Review — fix/238-red-star-own-id

diff_sha256: 8522a29667dee2c56cc33a012870bc5c63dbee444e8e9d78e05f025e6e00f3ba

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- All 14 changed paths are in scope_paths: three seeds, seeds/schema.yml, six base models, base.yml, two tests and contract.md.
- The -1 id, its name and country, the reattribute_in_fixture mode and the new test are declared in decisions_taken; the new mechanism is declared; no metric, URL, label, cadence or recurring cost changes.
- decisions_reserved is honest: only fixtures 1239850 and 1239851 are keyed, and the three other shared-id clubs are untouched.
- impact_map carries the dbt ls lineage (79 models, 29 marts), deploy order and blast radius; approved_design none holds, as no page surface is touched.
- Doc sync: the two yml files that describe the overrides are updated; no secrets, dates, decision history or bare issue numbers added.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every team-id reader of the fixture list, the four match feeds and the team keys takes the correction; no other base model reads a fixture team id from staging.
- The new joins are unique on (wrong id, fixture_id) by the seed test; null fixture_id never joins, so the older rows are untouched; the new mode outranks the other two and the player's-team resolution stays ahead of it, built from corrected events.
- A negative id passes dim_team, the seed relationship tests and the still-needed tests; no sentinel or positive-id filter exists.
- The new test fails on uncorrected data and passes on corrected data, as the prod reads show.
- Round 2: the slug concern is cleared by the prod read; -1 takes red-star, 104 keeps red-star-fc-93, and no other team's slug changes.

## escalations
(none)
