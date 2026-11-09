{#
  One failing row per player whose shares_name_at_club disagrees with a count of the players with a
  page by full name and current club, or differs between the player's rows.
#}
{{ config(store_failures = true, severity = 'error') }}

with players as (
    select
        player_sk,
        min(player_full_name) as player_full_name,
        min(current_club_team_sk) as current_club_team_sk,
        logical_or(has_player_page) as has_player_page,
        count(distinct shares_name_at_club) as flag_values,
        logical_or(shares_name_at_club) as shares_name_at_club
    from {{ ref('mart_player_profile') }}
    group by player_sk
),

namesakes as (
    select
        player_full_name,
        current_club_team_sk,
        count(*) as players
    from players
    where has_player_page and player_full_name is not null and current_club_team_sk is not null
    group by player_full_name, current_club_team_sk
)

select
    p.player_sk,
    p.player_full_name,
    p.current_club_team_sk,
    p.shares_name_at_club,
    p.flag_values
from players as p
left join namesakes as n
    on
        p.player_full_name = n.player_full_name
        and p.current_club_team_sk = n.current_club_team_sk
where
    p.flag_values > 1
    or p.shares_name_at_club != (p.has_player_page and coalesce(n.players, 0) > 1)
