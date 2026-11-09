-- Every player with a Player page has his row in mart_player_index, and none else, with the values
-- of their sources: his featured row of mart_player_profile, his nation's confederation in
-- dim_country, his club's club_order in mart_team_index and his minutes for his nation's team in
-- int_player__national_team_minutes. Returns every player that is missing, extra or differs.

with pages as (
    select
        player_sk,
        league_code,
        player_name,
        player_photo_url,
        position_group,
        player_nationality,
        nationality_team_sk,
        current_club_team_sk,
        current_club_name
    from {{ ref('mart_player_profile') }}
    where has_player_page and is_featured_season
),

expected as (
    select
        p.*,
        c.confederation as region_key,
        t.club_order,
        m.national_team_minutes,
        m.national_team_match_minutes
    from pages as p
    left join {{ ref('dim_country') }} as c
        on p.player_nationality = c.country_name
    left join {{ ref('mart_team_index') }} as t
        on p.current_club_team_sk = t.team_sk
    left join {{ ref('int_player__national_team_minutes') }} as m
        on p.player_sk = m.player_sk and p.nationality_team_sk = m.team_sk
),

served as (
    select * from {{ ref('mart_player_index') }}
)

select coalesce(e.player_sk, s.player_sk) as player_sk
from expected as e
full outer join served as s
    on e.player_sk = s.player_sk
where
    e.player_sk is null
    or s.player_sk is null
    or e.league_code != s.league_code
    or e.player_name is distinct from s.player_name
    or e.player_photo_url is distinct from s.player_photo_url
    or e.position_group is distinct from s.position_group
    or e.player_nationality is distinct from s.player_nationality
    or e.nationality_team_sk is distinct from s.nationality_team_sk
    or e.region_key is distinct from s.region_key
    or e.current_club_team_sk is distinct from s.current_club_team_sk
    or e.current_club_name is distinct from s.current_club_name
    or e.club_order is distinct from s.club_order
    or e.national_team_minutes is distinct from s.national_team_minutes
    or e.national_team_match_minutes is distinct from s.national_team_match_minutes
