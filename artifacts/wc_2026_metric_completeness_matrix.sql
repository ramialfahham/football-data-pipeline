-- Pivot: count of teams per metric by completeness tier (WC 2026, 48 teams)

with base as (
    select * from (
        -- reuse logic: import from a view would be nicer; inline subquery for one-shot
        select
            metric,
            metric_completeness,
            count(*) as team_count
        from (
            select
                team_sk,
                metric,
                case
                    when qualifier_legs = 0 then 'unavailable'
                    when legs_with_inputs = qualifier_legs then 'complete'
                    when legs_with_inputs = 0 then 'unavailable'
                    else 'partial'
                end as metric_completeness
            from (
                with supporting as (
                    select league_code from unnest(['WCQEU','WCQAF','WCQCA','WCQSA','WCQAS','WCQIP','WCQOC']) as league_code
                ),
                wc_2026_teams as (
                    select distinct team_sk from (
                        select home_team_sk as team_sk from `football-data-pipeline-gcp.core.fct_fixture`
                        where league_code = 'WC' and season_api_year = 2026
                        union distinct
                        select away_team_sk from `football-data-pipeline-gcp.core.fct_fixture`
                        where league_code = 'WC' and season_api_year = 2026
                    )
                ),
                legs as (
                    select leg.team_sk, leg.goals_for is not null as has_goals,
                        leg.shots_total is not null as has_shots_total,
                        leg.shots_on_goal is not null as has_shots_on_goal,
                        leg.shots_inside_box is not null as has_shots_inside_box,
                        leg.opponent_total_shots is not null as has_opponent_shots,
                        leg.passes_total is not null as has_passes_total,
                        leg.passes_accurate is not null as has_passes_accurate,
                        leg.corner_kicks is not null as has_corners,
                        leg.opponent_corner_kicks is not null as has_opp_corners,
                        leg.goalkeeper_saves is not null as has_saves
                    from `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg` leg
                    inner join supporting s on leg.league_code = s.league_code
                    inner join wc_2026_teams wt on leg.team_sk = wt.team_sk
                ),
                leg_counts as (
                    select team_sk, count(*) as qualifier_legs,
                        countif(has_goals) as legs_with_goals,
                        countif(has_shots_total) as legs_with_shots_total,
                        countif(has_shots_on_goal) as legs_with_shots_on_goal,
                        countif(has_shots_inside_box) as legs_with_shots_inside_box,
                        countif(has_opponent_shots) as legs_with_opponent_shots,
                        countif(has_passes_total) as legs_with_passes_total,
                        countif(has_passes_accurate) as legs_with_passes_accurate,
                        countif(has_corners) as legs_with_corners,
                        countif(has_opp_corners) as legs_with_opp_corners,
                        countif(has_saves) as legs_with_saves
                    from legs group by team_sk
                ),
                metric_reqs as (
                    select * from unnest([
                        struct('points_capture' as metric, 'goals' as input_family),
                        struct('goals_per_match' as metric, 'goals' as input_family),
                        struct('goals_against_per_match' as metric, 'goals' as input_family),
                        struct('shots_per_match' as metric, 'shots_total' as input_family),
                        struct('shot_share' as metric, 'shots_total_opponent' as input_family),
                        struct('danger_zone_ratio' as metric, 'shots_inside_box' as input_family),
                        struct('shot_accuracy' as metric, 'shots_on_goal' as input_family),
                        struct('finishing_efficiency' as metric, 'shots_on_goal' as input_family),
                        struct('pass_accuracy' as metric, 'passes' as input_family),
                        struct('passes_per_match' as metric, 'passes_total' as input_family),
                        struct('corner_kicks_per_match' as metric, 'corners' as input_family),
                        struct('corners_conceded_per_match' as metric, 'opp_corners' as input_family),
                        struct('save_ratio' as metric, 'saves' as input_family)
                    ])
                ),
                coverage as (
                    select lc.team_sk, mr.metric, lc.qualifier_legs,
                        case mr.input_family
                            when 'goals' then lc.legs_with_goals
                            when 'shots_total' then lc.legs_with_shots_total
                            when 'shots_total_opponent' then least(lc.legs_with_shots_total, lc.legs_with_opponent_shots)
                            when 'shots_inside_box' then least(lc.legs_with_shots_total, lc.legs_with_shots_inside_box)
                            when 'shots_on_goal' then least(lc.legs_with_shots_total, lc.legs_with_shots_on_goal)
                            when 'passes' then least(lc.legs_with_passes_total, lc.legs_with_passes_accurate)
                            when 'passes_total' then lc.legs_with_passes_total
                            when 'corners' then lc.legs_with_corners
                            when 'opp_corners' then lc.legs_with_opp_corners
                            when 'saves' then lc.legs_with_saves
                        end as legs_with_inputs
                    from leg_counts lc cross join metric_reqs mr
                )
                select team_sk, metric, qualifier_legs, legs_with_inputs from coverage
            )
        )
        group by metric, metric_completeness
    )
)
select * from base
order by metric, metric_completeness
