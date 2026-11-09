{#
  Each squad a player's page compares against, and every player of it with their metrics for that
  team. A squad is a team over a window: a club over the club competitions of a featured season, a
  nation over its current competitions. Every metric is its catalogue formula over the window's leg
  rows, written by scripts/generate_metric_sql.py by the rules in models/docs/metric_rules.md.
  team_matches is what the team played in the window; the floor on it is
  mart_player_squad_benchmarks'.

  Grain: (squad_sk, player_sk).
#}

with profile as (
    select * from {{ ref('int_player__page_profile') }}
),

squad_keys as (
    select distinct
        'club' as page_tab,
        featured_team_sk as team_sk,
        featured_season_sk as anchor_season_sk
    from profile
    where featured_team_sk is not null and featured_entity_type = 'club'
    union distinct
    select distinct
        'national_team' as page_tab,
        national_team_sk as team_sk,
        cast(null as string) as anchor_season_sk
    from profile
    where has_national_team_tab
),

squads as (
    select
        page_tab,
        team_sk,
        anchor_season_sk,
        concat(page_tab, '|', cast(team_sk as string), '|', coalesce(anchor_season_sk, 'current')) as squad_sk
    from squad_keys
),

squad_seasons as (
    select
        s.squad_sk,
        s.team_sk,
        w.season_sk
    from squads as s
    inner join {{ ref('int_competition_season__club_windows') }} as w
        on s.anchor_season_sk = w.anchor_season_sk
    where w.window_type = 'this_season'
    union all
    select
        s.squad_sk,
        s.team_sk,
        c.season_sk
    from squads as s
    inner join {{ ref('int_team__current_national_competitions') }} as c
        on s.team_sk = c.team_sk
    where s.page_tab = 'national_team'
),

without_player_data as (
    {{ team_seasons_without_player_data() }}
),

squad_totals as (
    select
        s.squad_sk,
        count(distinct if(not tm.is_awarded_result, tm.fixture_sk, null)) as team_matches,
        logical_and(u.team_sk is null) as window_is_complete
    from squad_seasons as s
    left join {{ ref('int_legs__team_match') }} as tm
        on s.team_sk = tm.team_sk and s.season_sk = tm.season_sk
    left join without_player_data as u
        on s.team_sk = u.team_sk and s.season_sk = u.season_sk
    group by s.squad_sk
),

window_rows as (
    select
        legs.*,
        s.squad_sk,
        t.team_matches,
        t.window_is_complete
    from squad_seasons as s
    inner join {{ ref('int_legs__player_match') }} as legs
        on s.team_sk = legs.team_sk and s.season_sk = legs.season_sk
    inner join squad_totals as t
        on s.squad_sk = t.squad_sk
),

metrics as (
    select
        squad_sk,
        player_sk,
        {{ one_value('team_matches') }} as team_matches,
        if(logical_and(window_is_complete and minutes is not null), sum(minutes), null) as minutes,
        -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
        if(logical_and(window_is_complete and (minutes > 0) is not null), countif(minutes > 0), null) as appearances,
        if(logical_and(window_is_complete and goals is not null), sum(goals), null) as goals_player,
        if(
            logical_and(window_is_complete and goals_penalty is not null),
            sum(goals_penalty),
            null
        ) as goals_penalty_player,
        if(logical_and(window_is_complete and assists is not null), sum(assists), null) as assists_player,
        if(logical_and(window_is_complete and shots is not null), sum(shots), null) as shots_player,
        if(
            logical_and(window_is_complete and shots_on_target is not null),
            sum(shots_on_target),
            null
        ) as shots_on_goal_player,
        if(logical_and(window_is_complete and passes is not null), sum(passes), null) as passes_player,
        if(
            logical_and(window_is_complete and passes_accurate is not null),
            sum(passes_accurate),
            null
        ) as passes_accurate_player,
        if(logical_and(window_is_complete and passes_key is not null), sum(passes_key), null) as passes_key_player,
        if(logical_and(window_is_complete and tackles is not null), sum(tackles), null) as tackles_player,
        if(
            logical_and(window_is_complete and interceptions is not null),
            sum(interceptions),
            null
        ) as interceptions_player,
        if(logical_and(window_is_complete and blocks is not null), sum(blocks), null) as blocks_player,
        if(logical_and(window_is_complete and duels is not null), sum(duels), null) as duels_player,
        if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null) as duels_won_player,
        if(logical_and(window_is_complete and dribbles is not null), sum(dribbles), null) as dribbles_attempts_player,
        if(
            logical_and(window_is_complete and dribbles_success is not null),
            sum(dribbles_success),
            null
        ) as dribbles_success_player,
        if(logical_and(window_is_complete and saves is not null), sum(saves), null) as saves_player,
        if(
            logical_and(window_is_complete and goals_against is not null),
            sum(goals_against),
            null
        ) as goals_against_player,
        if(
            logical_and(window_is_complete and cards_yellow is not null),
            sum(cards_yellow),
            null
        ) as cards_yellow_player,
        if(logical_and(window_is_complete and cards_red is not null), sum(cards_red), null) as cards_red_player,
        safe_divide(
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null),
            if(logical_and(window_is_complete and (minutes > 0) is not null), countif(minutes > 0), null)
        ) as minutes_per_appearance,
        safe_divide(
            if(logical_and(window_is_complete and passes_accurate is not null), sum(passes_accurate), null),
            if(logical_and(window_is_complete and passes is not null), sum(passes), null)
        ) as passes_accuracy_player_pct,
        safe_divide(
            if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null),
            if(logical_and(window_is_complete and duels is not null), sum(duels), null)
        ) as duels_won_player_pct,
        safe_divide(
            if(logical_and(window_is_complete and dribbles_success is not null), sum(dribbles_success), null),
            if(logical_and(window_is_complete and dribbles is not null), sum(dribbles), null)
        ) as dribbles_success_player_pct,
        safe_divide(
            if(
                logical_and(window_is_complete and saves is not null),
                sum(saves),
                null
            ),
            if(
                logical_and(window_is_complete and (saves + goals_against) is not null),
                sum(saves + goals_against),
                null
            )
        ) as saves_player_pct,
        safe_divide(
            if(
                logical_and(window_is_complete and (goals - goals_penalty) is not null),
                sum(goals - goals_penalty),
                null
            ),
            if(
                logical_and(window_is_complete and shots_on_target is not null),
                sum(shots_on_target),
                null
            )
        ) as finishing_efficiency_player_pct,
        safe_divide(
            if(logical_and(window_is_complete and shots_on_target is not null), sum(shots_on_target), null),
            if(logical_and(window_is_complete and shots is not null), sum(shots), null)
        ) as shots_on_goal_player_pct,
        safe_divide(
            if(logical_and(window_is_complete and goals is not null), sum(goals), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as goals_per90,
        safe_divide(
            if(logical_and(window_is_complete and assists is not null), sum(assists), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as assists_per90,
        safe_divide(
            if(logical_and(window_is_complete and (goals + assists) is not null), sum(goals + assists), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as scorer_points_per90,
        safe_divide(
            if(logical_and(window_is_complete and shots_on_target is not null), sum(shots_on_target), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as shots_on_goal_per90,
        safe_divide(
            if(logical_and(window_is_complete and passes_key is not null), sum(passes_key), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as passes_key_per90,
        safe_divide(
            if(logical_and(window_is_complete and dribbles_success is not null), sum(dribbles_success), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as dribbles_success_per90,
        safe_divide(
            if(logical_and(window_is_complete and passes is not null), sum(passes), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as passes_per90,
        safe_divide(
            if(logical_and(window_is_complete and tackles is not null), sum(tackles), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as tackles_per90,
        safe_divide(
            if(logical_and(window_is_complete and interceptions is not null), sum(interceptions), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as interceptions_per90,
        safe_divide(
            if(logical_and(window_is_complete and blocks is not null), sum(blocks), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as blocks_per90,
        safe_divide(
            if(
                logical_and(window_is_complete and (tackles + interceptions + blocks) is not null),
                sum(tackles + interceptions + blocks),
                null
            ) * 90,
            if(
                logical_and(window_is_complete and minutes is not null),
                sum(minutes),
                null
            )
        ) as defensive_actions_per90,
        safe_divide(
            if(logical_and(window_is_complete and duels_won is not null), sum(duels_won), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as duels_won_per90,
        safe_divide(
            if(logical_and(window_is_complete and saves is not null), sum(saves), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as saves_per90,
        safe_divide(
            if(
                logical_and(
                    window_is_complete
                    and (passes + shots + dribbles + tackles + interceptions + blocks + saves) is not null
                ),
                sum(passes + shots + dribbles + tackles + interceptions + blocks + saves),
                null
            ) * 90,
            if(
                logical_and(
                    window_is_complete
                    and minutes is not null
                ),
                sum(minutes),
                null
            )
        ) as ball_actions_per90,
        safe_divide(
            if(logical_and(window_is_complete and shots is not null), sum(shots), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as shots_per90,
        safe_divide(
            if(logical_and(window_is_complete and fouls is not null), sum(fouls), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as fouls_per90,
        safe_divide(
            if(logical_and(window_is_complete and offsides is not null), sum(offsides), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as offsides_per90,
        safe_divide(
            if(logical_and(window_is_complete and goals_against is not null), sum(goals_against), null) * 90,
            if(logical_and(window_is_complete and minutes is not null), sum(minutes), null)
        ) as goals_against_per90
        -- end of generated metric sql
    from window_rows
    group by squad_sk, player_sk
)

select
    m.*,
    s.page_tab,
    s.team_sk,
    s.anchor_season_sk
from metrics as m
inner join squads as s
    on m.squad_sk = s.squad_sk
