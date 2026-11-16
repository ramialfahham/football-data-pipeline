{#
  One failing row per set of player pages that share every part their title is made from: the full
  name, the team the title names (the current club, else the national team, else the nationality)
  and, when the shared-name flag is set, the position. Two such pages carry one title.
#}
{{ config(store_failures = true, severity = 'error') }}

with pages as (
    select
        profile.player_sk,
        profile.player_full_name,
        coalesce(club.team_name, nation.team_name, profile.player_nationality, '') as title_team,
        if(profile.shares_name_at_club, profile.position_group, '') as title_position
    from {{ ref('mart_player_profile') }} as profile
    left join {{ ref('dim_team') }} as club
        on profile.current_club_team_sk = club.team_sk
    left join {{ ref('dim_team') }} as nation
        on profile.national_team_sk = nation.team_sk
    where profile.has_player_page and profile.is_featured_season
)

select
    player_full_name,
    title_team,
    title_position,
    count(*) as pages,
    string_agg(cast(player_sk as string), ' ' order by player_sk) as player_sks
from pages
group by player_full_name, title_team, title_position
having count(*) > 1
