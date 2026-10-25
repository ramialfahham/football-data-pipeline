# Review — feat/229-season-label — 2026-10-25

diff_sha256: ffe5c0702503335818417d86207d27e2149539a1f60be8383795feb9ef7cb5f2

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; the header text matches the approved wording and the Season/Saison/Kausi copy is unchanged; approved_design names the competition page.
- The committed BL1 sample gains only season_label 2026/27, the export's key with the value the MR's own warehouse build serves.
- The impact_map lists the lineage of dim_competition_season with its leaves, and the two direct SQL readers select named columns, so the new column reaches no model.
- The label is built only in dim_competition_season; the export reads it and the pages pass it through; no new mechanism, no credential, a 48-row seed join as the only recurring cost.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The registry seed is unique and not null on league_code, so the left join cannot fan out; season_sk and the grain test are unchanged.
- A league missing from the seed or an unknown season_type gives a null label, caught by not_null and by the named shape test that the label starts with its year and reads YYYY or YYYY/YY.
- The descriptions are well under BigQuery's limits and name the seed as the label's source; the export selects the served column and computes nothing.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The export keys the label on (league_code, int(season_api_year)), the same key as the payload combos, and passes it through; a missing key gives None.
- season_label is a trailing keyword argument defaulting to None, so every existing caller of shape_competition_payload is unaffected.
- The tests pin the pass-through for a split-year and a calendar-year label, None when not served, and that a fetched payload takes its own season's label.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The header reads only payload.season_label, a field the export serves from dim_competition_season; the three specs name that source.
- No page in the competition header path formats a year; the header interpolates the served string through compSeason.
- compSeason reads Season/Saison/Kausi {season} in EN, DE and FI, the approved text; the meta line stays one plain-text line.
- The committed sample carries only season_label, a served field with the warehouse's value; its build renders Season 2026/27 on the three Bundesliga tabs in EN, DE and FI, and the inventory passes 174 renders.

## escalations
(none)
