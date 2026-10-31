{#
  The Teams page: one row per team with a Team page, with the orders the page shows.

  Clubs: each continent's top club competition (confederations.top_club_competition) over its
  last five finished seasons, a season being finished once its final is played. A club scores
  its furthest round per season: 1 league or group phase, 2 round of 32, knockout play-off or
  round of 16, 3 quarter-final, 4 semi-final, 5 final, 6 winner; qualifying rounds score 0.
  top_club_rank orders a continent's clubs by the sum, then the most recent season, then wins,
  then goal difference in those matches; clubs still level share the place.

  Countries: the sum of their clubs' points, ordered by region_rank, then the sum, the most recent
  season, wins and goal difference; countries without points follow A to Z, teams without a
  country last.

  National teams: the furthest round at the latest finished World Cup, then at the region's
  latest finished championship (each round in order, the winner above the final), then points
  per match and goal difference per match in the team's World Cup qualifier table matches;
  teams still level share the place, teams with none of the three follow A to Z.

  Reads mart_team_competitions in its own layer, for each team's furthest round and final won.
  Grain: (team_sk).
#}

with shown_teams as (
    select distinct team_sk
    from {{ ref('mart_team_profile') }}
),

teams as (
    select
        team_sk,
        team_name,
        team_slug,
        team_logo_url,
        team_country
    from {{ ref('dim_team') }}
),

registry as (
    select
        league_code,
        competition_type,
        parent_competition,
        confederation,
        tier
    from {{ ref('competition_registry') }}
),

competition_types as (
    select
        competition_type,
        entity_type
    from {{ ref('competition_types') }}
),

regions as (
    select
        confederation,
        region_rank,
        top_club_competition,
        continental_championship
    from {{ ref('confederations') }}
),

team_competitions as (
    select * from {{ ref('mart_team_competitions') }}
),

round_names as (
    select
        league_code,
        season_api_year,
        round_name,
        round_label_i18n_key,
        round_stage_kind
    from {{ ref('int_round_names') }}
),

fixtures as (
    select
        league_code,
        season_api_year,
        round_name,
        home_team_sk,
        away_team_sk,
        goals_home,
        goals_away,
        date(fixture_date) as fixture_date,
        status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO') as is_finished
    from {{ ref('fct_fixture') }}
),

stage_values as (
    select * from {{ ref('int_team_index__round_values') }}
),

finished_seasons as (
    select
        f.league_code,
        f.season_api_year,
        row_number() over (
            partition by f.league_code order by f.season_api_year desc
        ) as recency
    from fixtures as f
    inner join round_names as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    where r.round_stage_kind = 'final'
    group by f.league_code, f.season_api_year
    having logical_and(f.is_finished)
),

club_cup_seasons as (
    select
        s.league_code,
        s.season_api_year,
        s.recency,
        g.confederation as cup_region_key
    from finished_seasons as s
    inner join regions as g
        on s.league_code = g.top_club_competition
    where s.recency <= 5
),

club_stages as (
    select
        tc.team_sk,
        cs.cup_region_key,
        cs.recency,
        if(tc.cup_status = 'winners', 6, v.club_points) as points
    from team_competitions as tc
    inner join club_cup_seasons as cs
        on
            tc.league_code = cs.league_code
            and tc.season_api_year = cs.season_api_year
    inner join shown_teams as st
        on tc.team_sk = st.team_sk
    left join stage_values as v
        on tc.reached_round_label_i18n_key = v.round_key
),

club_cup_matches as (
    select
        cs.cup_region_key,
        side.team_sk,
        side.goals_for,
        side.goals_against
    from fixtures as f
    inner join club_cup_seasons as cs
        on
            f.league_code = cs.league_code
            and f.season_api_year = cs.season_api_year
    inner join round_names as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    inner join stage_values as v
        on r.round_label_i18n_key = v.round_key
    cross join
        unnest([
            struct(f.home_team_sk as team_sk, f.goals_home as goals_for, f.goals_away as goals_against),
            struct(f.away_team_sk, f.goals_away, f.goals_home)
        ]) as side
    where f.is_finished and v.club_points > 0
),

club_cup_results as (
    select
        cup_region_key,
        team_sk,
        countif(goals_for > goals_against) as wins,
        sum(goals_for - goals_against) as goal_difference
    from club_cup_matches
    group by cup_region_key, team_sk
),

club_scores as (
    select
        s.team_sk,
        s.cup_region_key,
        sum(s.points) as cup_points,
        sum(if(s.recency = 1, s.points, 0)) as latest_season_points
    from club_stages as s
    group by s.team_sk, s.cup_region_key
    having sum(s.points) > 0
),

top_clubs as (
    select
        c.team_sk,
        c.cup_region_key,
        c.cup_points,
        c.latest_season_points,
        coalesce(m.wins, 0) as cup_wins,
        coalesce(m.goal_difference, 0) as cup_goal_difference,
        rank() over (
            partition by c.cup_region_key
            order by
                c.cup_points desc,
                c.latest_season_points desc,
                coalesce(m.wins, 0) desc,
                coalesce(m.goal_difference, 0) desc
        ) as top_club_rank
    from club_scores as c
    left join club_cup_results as m
        on
            c.team_sk = m.team_sk
            and c.cup_region_key = m.cup_region_key
),

team_kinds as (
    select
        tc.team_sk,
        logical_or(ct.entity_type = 'national') as is_national
    from team_competitions as tc
    inner join registry as reg
        on tc.league_code = reg.league_code
    inner join competition_types as ct
        on reg.competition_type = ct.competition_type
    group by tc.team_sk
),

-- a team's region: the confederation of the competitions it plays most, FIFA's left out
team_regions as (
    select
        tc.team_sk,
        reg.confederation as region_key
    from team_competitions as tc
    inner join registry as reg
        on tc.league_code = reg.league_code
    inner join regions as g
        on reg.confederation = g.confederation
    where reg.confederation != 'FIFA'
    group by tc.team_sk, reg.confederation, g.region_rank
    qualify row_number() over (
        partition by tc.team_sk order by count(*) desc, g.region_rank asc
    ) = 1
),

latest_league_seasons as (
    select
        league_code,
        max(season_api_year) as season_api_year
    from team_competitions
    where competition_type = 'domestic_league'
    group by league_code
),

covered_leagues as (
    select
        tc.team_sk,
        tc.league_code,
        reg.tier as league_tier,
        tc.standing_group_name,
        tc.standing_rank as league_position
    from team_competitions as tc
    inner join latest_league_seasons as ls
        on
            tc.league_code = ls.league_code
            and tc.season_api_year = ls.season_api_year
    inner join registry as reg
        on tc.league_code = reg.league_code
    qualify row_number() over (
        partition by tc.team_sk order by reg.tier asc, tc.league_code asc
    ) = 1
),

clubs as (
    select
        t.team_sk,
        t.team_name,
        t.team_country,
        coalesce(c.cup_region_key, r.region_key) as region_key,
        coalesce(c.cup_points, 0) as cup_points,
        coalesce(c.latest_season_points, 0) as latest_season_points,
        coalesce(c.cup_wins, 0) as cup_wins,
        coalesce(c.cup_goal_difference, 0) as cup_goal_difference
    from teams as t
    inner join shown_teams as st
        on t.team_sk = st.team_sk
    inner join team_kinds as k
        on t.team_sk = k.team_sk
    left join team_regions as r
        on t.team_sk = r.team_sk
    left join top_clubs as c
        on t.team_sk = c.team_sk
    where not k.is_national
),

countries as (
    select
        team_country,
        sum(cup_points) as country_points,
        sum(latest_season_points) as country_latest_season_points,
        sum(cup_wins) as country_wins,
        sum(cup_goal_difference) as country_goal_difference
    from clubs
    group by team_country
),

club_country_regions as (
    select
        c.team_country,
        c.region_key as country_region_key,
        g.region_rank as country_region_rank
    from clubs as c
    inner join regions as g
        on c.region_key = g.confederation
    where c.team_country is not null
    group by c.team_country, c.region_key, g.region_rank
    qualify row_number() over (
        partition by c.team_country order by count(*) desc, g.region_rank asc
    ) = 1
),

national_country_regions as (
    select
        t.team_country,
        r.region_key as country_region_key,
        g.region_rank as country_region_rank
    from teams as t
    inner join team_kinds as k
        on t.team_sk = k.team_sk
    inner join team_regions as r
        on t.team_sk = r.team_sk
    inner join regions as g
        on r.region_key = g.confederation
    where
        k.is_national
        and t.team_country is not null
    qualify row_number() over (
        partition by t.team_country order by g.region_rank asc
    ) = 1
),

-- a country none of whose clubs has a region takes its national team's
country_regions as (
    select
        coalesce(c.team_country, n.team_country) as team_country,
        if(c.team_country is not null, c.country_region_key, n.country_region_key)
            as country_region_key,
        if(c.team_country is not null, c.country_region_rank, n.country_region_rank)
            as country_region_rank
    from club_country_regions as c
    full outer join national_country_regions as n
        on c.team_country = n.team_country
),

country_orders as (
    select
        c.team_country,
        cr.country_region_key,
        rank() over (
            order by
                c.team_country is null asc,
                c.country_points = 0 asc,
                if(c.country_points > 0, cr.country_region_rank, null) asc,
                c.country_points desc,
                c.country_latest_season_points desc,
                c.country_wins desc,
                c.country_goal_difference desc,
                if(c.country_points = 0, c.team_country, null) asc
        ) as country_order
    from countries as c
    left join country_regions as cr
        on c.team_country = cr.team_country
),

club_orders as (
    select
        c.team_sk,
        row_number() over (
            partition by c.team_country
            order by
                l.league_code is null asc,
                l.league_tier asc,
                l.league_code asc,
                l.standing_group_name asc,
                l.league_position asc,
                c.team_name asc
        ) as team_order_in_country
    from clubs as c
    left join covered_leagues as l
        on c.team_sk = l.team_sk
),

world_cups as (
    select
        s.league_code,
        s.season_api_year
    from finished_seasons as s
    inner join registry as reg
        on s.league_code = reg.league_code
    where reg.competition_type = 'world_championship' and s.recency = 1
),

championships as (
    select
        s.league_code,
        s.season_api_year,
        g.confederation as region_key
    from finished_seasons as s
    inner join regions as g
        on s.league_code = g.continental_championship
    where s.recency = 1
),

national_stages as (
    select
        tc.team_sk,
        max(if(wc.league_code is null, null, if(tc.cup_status = 'winners', 7, v.national_stage)))
            as world_cup_stage,
        max(if(ch.league_code is null, null, if(tc.cup_status = 'winners', 7, v.national_stage)))
            as championship_stage
    from team_competitions as tc
    left join world_cups as wc
        on
            tc.league_code = wc.league_code
            and tc.season_api_year = wc.season_api_year
    left join team_regions as tr
        on tc.team_sk = tr.team_sk
    left join championships as ch
        on
            tc.league_code = ch.league_code
            and tc.season_api_year = ch.season_api_year
            and tr.region_key = ch.region_key
    left join stage_values as v
        on tc.reached_round_label_i18n_key = v.round_key
    where wc.league_code is not null or ch.league_code is not null
    group by tc.team_sk
),

qualifier_seasons as (
    select
        f.league_code,
        max(f.season_api_year) as season_api_year
    from fixtures as f
    inner join registry as reg
        on f.league_code = reg.league_code
    inner join registry as parent
        on reg.parent_competition = parent.league_code
    inner join round_names as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    where
        reg.competition_type = 'qualifying'
        and parent.competition_type = 'world_championship'
        and r.round_stage_kind = 'table'
        and f.is_finished
    group by f.league_code
),

qualifier_results as (
    select
        side.team_sk,
        avg(
            case
                when side.goals_for > side.goals_against then 3
                when side.goals_for = side.goals_against then 1
                else 0
            end
        ) as qualifier_points_per_match,
        avg(side.goals_for - side.goals_against) as qualifier_goal_difference_per_match
    from fixtures as f
    inner join qualifier_seasons as q
        on
            f.league_code = q.league_code
            and f.season_api_year = q.season_api_year
    inner join round_names as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    cross join
        unnest([
            struct(f.home_team_sk as team_sk, f.goals_home as goals_for, f.goals_away as goals_against),
            struct(f.away_team_sk, f.goals_away, f.goals_home)
        ]) as side
    where
        f.is_finished
        and r.round_stage_kind = 'table'
        and f.goals_home is not null
        and f.goals_away is not null
    group by side.team_sk
),

national_teams as (
    select
        t.team_sk,
        t.team_name,
        r.region_key,
        s.world_cup_stage,
        s.championship_stage,
        q.qualifier_points_per_match,
        q.qualifier_goal_difference_per_match,
        coalesce(
            s.world_cup_stage, s.championship_stage, q.qualifier_points_per_match
        ) is null as has_no_criterion
    from teams as t
    inner join shown_teams as st
        on t.team_sk = st.team_sk
    inner join team_kinds as k
        on t.team_sk = k.team_sk
    left join team_regions as r
        on t.team_sk = r.team_sk
    left join national_stages as s
        on t.team_sk = s.team_sk
    left join qualifier_results as q
        on t.team_sk = q.team_sk
    where k.is_national
),

national_orders as (
    select
        team_sk,
        world_cup_stage,
        championship_stage,
        rank() over (
            order by
                has_no_criterion asc,
                world_cup_stage desc,
                championship_stage desc,
                qualifier_points_per_match desc,
                qualifier_goal_difference_per_match desc,
                if(has_no_criterion, team_name, null) asc
        ) as national_team_rank,
        rank() over (
            partition by region_key
            order by
                has_no_criterion asc,
                world_cup_stage desc,
                championship_stage desc,
                qualifier_points_per_match desc,
                qualifier_goal_difference_per_match desc,
                if(has_no_criterion, team_name, null) asc
        ) as national_team_region_rank
    from national_teams
),

tournament_days as (
    select
        f.league_code,
        f.season_api_year,
        min(f.fixture_date) as first_day,
        max(f.fixture_date) as final_day
    from fixtures as f
    inner join registry as reg
        on f.league_code = reg.league_code
    left join regions as g
        on f.league_code = g.continental_championship
    where reg.competition_type = 'world_championship' or g.continental_championship is not null
    group by f.league_code, f.season_api_year
),

block_order as (
    select
        coalesce(
            logical_or(current_date() between first_day and date_add(final_day, interval 1 day)),
            false
        ) as national_teams_first
    from tournament_days
)

select
    t.team_sk,
    t.team_name,
    t.team_slug,
    t.team_logo_url,
    t.team_country,
    l.league_code,
    l.league_tier,
    l.standing_group_name,
    l.league_position,
    tc.cup_points,
    tc.top_club_rank,
    co.country_region_key,
    co.country_order,
    cl.team_order_in_country,
    n.national_team_rank,
    n.national_team_region_rank,
    n.world_cup_stage,
    n.championship_stage,
    b.national_teams_first,
    coalesce(tc.cup_region_key, r.region_key, co.country_region_key) as region_key,
    if(k.is_national, 'national', 'club') as entity_type
from teams as t
inner join shown_teams as st
    on t.team_sk = st.team_sk
inner join team_kinds as k
    on t.team_sk = k.team_sk
left join team_regions as r
    on t.team_sk = r.team_sk
left join covered_leagues as l
    on
        t.team_sk = l.team_sk
        and not k.is_national
left join top_clubs as tc
    on
        t.team_sk = tc.team_sk
        and not k.is_national
left join country_orders as co
    on
        t.team_country is not distinct from co.team_country
        and not k.is_national
left join club_orders as cl
    on t.team_sk = cl.team_sk
left join national_orders as n
    on t.team_sk = n.team_sk
cross join block_order as b
