{#
  The Players page: one row per player with a Player page, with the orders its two blocks show.

  World's best: the latest edition of each award in player_award_results. The Goalkeepers list
  holds the Yashin Trophy nominees, the other lists the Ballon d'Or nominees by their page
  position. Inside a list, the current club in club_order, then the published placing, then the
  name.

  Players by nation: one group per nationality. Nations by the national team's
  national_team_rank, then the nations it does not hold A to Z, then the players with no
  nationality. Inside a nation, the regulars of its national team by their minutes for it, then
  the others by club_order, players with no club last, and their club minutes this season.

  A player's region is the confederation of the country of his nationality.

  Reads mart_player_profile and mart_team_index in its own layer.
  Grain: (player_sk).
#}

with profile as (
    select
        player_sk,
        season_sk,
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

countries as (
    select
        country_name,
        confederation
    from {{ ref('dim_country') }}
),

team_index as (
    select
        team_sk,
        club_order,
        national_team_rank
    from {{ ref('mart_team_index') }}
),

national_minutes as (
    select * from {{ ref('int_player__national_team_minutes') }}
),

club_minutes as (
    select
        p.player_sk,
        sum(l.minutes) as club_minutes_this_season
    from profile as p
    inner join {{ ref('int_competition_season__club_windows') }} as w
        on
            p.season_sk = w.anchor_season_sk
            and w.window_type = 'this_season'
    inner join {{ ref('int_legs__player_match') }} as l
        on
            p.player_sk = l.player_sk
            and w.season_sk = l.season_sk
    group by p.player_sk
),

latest_nominees as (
    select
        award,
        edition_year,
        placing,
        player_api_id as player_sk
    from {{ ref('player_award_results') }}
    qualify edition_year = max(edition_year) over (partition by award)
),

nominees as (
    select
        player_sk,
        award,
        edition_year,
        placing
    from latest_nominees
    qualify row_number() over (
        partition by player_sk
        order by award = 'yashin_trophy' desc, award asc
    ) = 1
),

nations as (
    select
        p.player_nationality,
        {{ one_value('t.national_team_rank') }} as national_team_rank
    from profile as p
    left join team_index as t
        on p.nationality_team_sk = t.team_sk
    group by p.player_nationality
),

nation_orders as (
    select
        player_nationality,
        national_team_rank,
        row_number() over (
            order by
                player_nationality is null asc,
                national_team_rank is null asc,
                national_team_rank asc,
                player_nationality asc
        ) as nation_order
    from nations
),

players as (
    select
        p.player_sk,
        p.league_code,
        p.player_name,
        p.player_photo_url,
        p.position_group,
        p.player_nationality,
        p.nationality_team_sk,
        c.confederation as region_key,
        n.national_team_rank,
        n.nation_order,
        nm.national_team_minutes,
        nm.national_team_match_minutes,
        p.current_club_team_sk,
        p.current_club_name,
        ci.club_order,
        a.award,
        a.edition_year as award_edition_year,
        a.placing as award_placing,
        coalesce(nm.is_regular, false) as is_national_team_regular,
        coalesce(cm.club_minutes_this_season, 0) as club_minutes_this_season,
        case
            when a.award = 'yashin_trophy' then 'GK'
            when a.award = 'ballon_dor' and p.position_group != 'GK' then p.position_group
        end as worlds_best_list
    from profile as p
    left join countries as c
        on p.player_nationality = c.country_name
    left join nation_orders as n
        on p.player_nationality is not distinct from n.player_nationality
    left join national_minutes as nm
        on
            p.player_sk = nm.player_sk
            and p.nationality_team_sk = nm.team_sk
    left join team_index as ci
        on p.current_club_team_sk = ci.team_sk
    left join club_minutes as cm
        on p.player_sk = cm.player_sk
    left join nominees as a
        on p.player_sk = a.player_sk
)

select
    *,
    row_number() over (
        partition by player_nationality
        order by
            is_national_team_regular desc,
            if(is_national_team_regular, national_team_minutes, null) desc,
            club_order is null asc,
            club_order asc,
            club_minutes_this_season desc,
            player_name asc,
            player_sk asc
    ) as order_in_nation,
    if(
        worlds_best_list is null,
        null,
        row_number() over (
            partition by worlds_best_list
            order by
                club_order is null asc,
                club_order asc,
                award_placing is null asc,
                award_placing asc,
                player_name asc,
                player_sk asc
        )
    ) as worlds_best_order
from players
