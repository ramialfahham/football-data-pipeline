{#
  The sheets of each team in each match that carry the newest ingest time of the team's sheets.
  The team is the team after fixture_team_id_overrides, so two provider ids of one team count as one.
  Each group is counted, with whether its sheets differ. A team with a differing tie has no sheet.
  base_apif__lineup_sheets and base_apif__fixture_players leave it out. The research list names the
  match. Grain: (league_code, fixture_id, team_id).
#}
select
    league_code,
    fixture_id,
    team_id,
    raw_ingested_at,
    tied_rows,
    rows_differ
from (
    {{ newest_fetch_ties(
        ref('base_apif__lineup_fetches'),
        ['league_code', 'fixture_id', 'team_id'],
        ['raw_ingested_at', 'provider_team_id']
    ) }}
)
