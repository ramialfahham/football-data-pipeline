-- Fails when relegation mart rows exist but either side has no form window (BL1/BL2 mix).
select
    fixture_sk,
    home_team_name,
    away_team_name,
    home_form_matchdays_used,
    away_form_matchdays_used
from {{ ref('mart_matchday_insights_bl1_relegation') }}
where
    home_form_matchdays_used = 0
    or away_form_matchdays_used = 0
