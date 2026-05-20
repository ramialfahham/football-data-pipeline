-- WC upcoming fixtures before kickoff must expose qualifier form for both teams.
select
    m.fixture_sk,
    m.home_team_name,
    m.away_team_name
from {{ ref('mart_matchday_insights_wc') }} as m
where
    m.home_form_from_qualifiers
    and m.away_form_from_qualifiers
    and (
        m.home_form_games_played is null
        or m.home_form_games_played = 0
        or m.away_form_games_played is null
        or m.away_form_games_played = 0
    )
