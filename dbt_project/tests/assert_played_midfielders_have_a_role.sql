{#
  Every midfielder who played carries DM, CM or AM where a fan meets him: in a comparison pool
  (player_min_minutes or more in a competition-season) or on a built Player page. A role comes from
  evidence only, so one this returns is filled through the researched sheet, never guessed.
  Returns the players without a role.
#}

with pool_members as (
    select
        player_sk,
        season_sk,
        'comparison pool' as where_shown
    from {{ ref('int_player_season_position__metrics') }}
    where position_group = 'MID' and minutes >= {{ var('player_min_minutes') }}
),

played_featured as (
    select distinct
        legs.player_sk,
        legs.season_sk
    from {{ ref('int_legs__player_match') }} as legs
    inner join {{ ref('int_player__page_profile') }} as page
        on legs.player_sk = page.player_sk and legs.season_sk = page.featured_season_sk
    where legs.position_code = 'M' and legs.minutes > 0
),

page_players as (
    select
        page.player_sk,
        page.featured_season_sk as season_sk,
        'player page' as where_shown
    from {{ ref('int_player__page_profile') }} as page
    inner join played_featured
        on page.player_sk = played_featured.player_sk and page.featured_season_sk = played_featured.season_sk
    where page.has_player_page and page.position_group = 'MID' and page.position_role is null
)

select * from pool_members
union all
select * from page_players
