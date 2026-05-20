-- WC fixtures must never mix qualifier/tournament phase inside the same match.
select
    m.fixture_sk,
    m.home_team_name,
    m.away_team_name,
    m.home_form_from_qualifiers,
    m.away_form_from_qualifiers
from {{ ref('mart_matchday_insights_wc') }} as m
where
    m.home_form_from_qualifiers != m.away_form_from_qualifiers
