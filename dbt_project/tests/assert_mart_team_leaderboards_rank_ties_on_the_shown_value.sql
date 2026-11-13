-- rank on mart_team_leaderboards is a RANK over the shown value: walking a board in its tie-broken
-- order, a row whose display_value equals the previous row's shares its rank, and any other row's
-- rank is its position. display_value follows the display rule, recomputed here: a percentage to
-- two decimals of the share, a count as it is, any other number whole from 10 up and to one
-- decimal below 10, half away from zero on the decimal value (0.575 shows as 58%).
{{ config(store_failures = true) }}

with boards as (
    select
        league_code,
        season_api_year,
        metric_key,
        team_sk,
        sort_value,
        display_value,
        rank,
        row_number() over w as position,
        lag(display_value) over w as previous_display,
        lag(rank) over w as previous_rank
    from {{ ref('mart_team_leaderboards') }}
    window w as (partition by league_code, season_api_year, metric_key order by league_leader_order)
),

catalogue as (
    select
        metric_id,
        format
    from {{ ref('metric_catalogue') }}
    where entity = 'team'
),

wrong_rank as (
    select
        league_code,
        season_api_year,
        metric_key,
        team_sk,
        'rank does not tie on the shown value' as failure
    from boards
    where
        rank != if(previous_display is not null and display_value = previous_display, previous_rank, position)
),

wrong_display as (
    select
        b.league_code,
        b.season_api_year,
        b.metric_key,
        b.team_sk,
        'display_value does not follow the display rule' as failure
    from boards as b
    inner join catalogue as c on b.metric_key = c.metric_id
    where
        abs(
            b.display_value
            - case
                when c.format = 'percent' then cast(round(cast(b.sort_value * 100 as numeric)) / 100 as float64)
                when c.format = 'integer' then b.sort_value
                when abs(round(cast(b.sort_value * 10 as numeric))) >= 100
                    then cast(round(cast(b.sort_value as numeric)) as float64)
                else cast(round(cast(b.sort_value * 10 as numeric)) / 10 as float64)
            end
        ) > 1e-9
)

select * from wrong_rank
union all
select * from wrong_display
