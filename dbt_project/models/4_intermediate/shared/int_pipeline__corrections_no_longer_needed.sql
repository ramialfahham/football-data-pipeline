{#
  Every hand correction of a result, a goal list, a round, a standings row or a match's cards that
  the provider no longer needs, because its own data now carries the corrected values. One row per
  correction, to be removed from its seed:
  - fixture_result_corrections: the provider carries the official score and any shoot-out. An
    award is always needed: the provider never says how it came about.
  - fixture_goal_corrections: the provider's goal events add up to the score, and carry every
    corrected goal with the same team, player id and minute. A goal without a player id, or whose
    scorer or assister fails the line-up check, never matches.
  - fixture_round_corrections: the provider files the fixture under the same round.
  - standings_corrections: the provider's table row carries every corrected figure and team.
  - fixture_card_corrections: the provider's card events equal the seed's cards one for one
    (provider_cards_match_research), its stat lines carry the same cards (no cards_from_research),
    and every player with a corrected card has a stat line.

  correction names the seed row as assert_result_corrections_applied names it. Grain: (seed,
  correction).
#}

with fixtures as (
    select * from {{ ref('base_apif__fixtures_next') }}
),

fixture_corrections as (
    select * from {{ ref('fixture_result_corrections') }}
),

goal_corrections as (
    select * from {{ ref('fixture_goal_corrections') }}
),

round_corrections as (
    select * from {{ ref('fixture_round_corrections') }}
),

table_corrections as (
    select * from {{ ref('standings_corrections') }}
),

card_corrections as (
    select * from {{ ref('fixture_card_corrections') }}
),

standings as (
    select * from {{ ref('base_apif__standings') }}
),

events as (
    select * from {{ ref('base_apif__fixture_events_checked') }}
),

goal_counts as (
    select
        c.fixture_id,
        countif(c.goal_order > 0) as seed_goals,
        min(if(f.award_kind in ('played', 'abandoned'), f.on_pitch_home, f.goals_home)) as score_home,
        min(if(f.award_kind in ('played', 'abandoned'), f.on_pitch_away, f.goals_away)) as score_away
    from goal_corrections as c
    left join fixtures as f
        on c.fixture_id = f.fixture_id
    group by c.fixture_id
),

provider_goals as (
    select
        e.fixture_id,
        countif(e.is_provider_goal and e.team_id = f.home_team_id) as provider_home,
        countif(e.is_provider_goal and e.team_id = f.away_team_id) as provider_away
    from events as e
    inner join goal_counts as g
        on e.fixture_id = g.fixture_id
    inner join fixtures as f
        on e.fixture_id = f.fixture_id
    group by e.fixture_id
),

seed_goal_keys as (
    select
        fixture_id,
        team_id,
        player_id,
        minute_elapsed,
        coalesce(minute_extra, 0) as minute_extra,
        count(*) as goals
    from goal_corrections
    where goal_order > 0 and player_id is not null
    group by fixture_id, team_id, player_id, minute_elapsed, coalesce(minute_extra, 0)
),

provider_goal_keys as (
    select
        e.fixture_id,
        e.team_id,
        e.player_id,
        e.minute_elapsed,
        coalesce(e.minute_extra, 0) as minute_extra,
        count(*) as goals
    from events as e
    inner join goal_counts as g
        on e.fixture_id = g.fixture_id
    where e.is_provider_goal and not e.scorer_needs_research and not e.assist_needs_research
    group by e.fixture_id, e.team_id, e.player_id, e.minute_elapsed, coalesce(e.minute_extra, 0)
),

goal_matches as (
    select
        s.fixture_id,
        sum(least(s.goals, p.goals)) as matched_goals
    from seed_goal_keys as s
    inner join provider_goal_keys as p
        on
            s.fixture_id = p.fixture_id
            and s.team_id = p.team_id
            and s.player_id = p.player_id
            and s.minute_elapsed = p.minute_elapsed
            and s.minute_extra = p.minute_extra
    group by s.fixture_id
),

card_matches as (
    select distinct fixture_id
    from card_corrections
),

card_events_agree as (
    select fixture_id
    from {{ ref('base_apif__fixture_events') }}
    group by fixture_id
    having logical_and(coalesce(provider_cards_match_research, false))
),

stat_lines_differ as (
    select distinct p.fixture_id
    from {{ ref('base_apif__fixture_players') }} as p
    cross join unnest(p.stat_corrections) as c
    where c.rule = 'cards_from_research'
),

carded_players_without_line as (
    select distinct c.fixture_id
    from card_corrections as c
    left join {{ ref('base_apif__fixture_players') }} as p
        on c.fixture_id = p.fixture_id and c.player_id = p.player_id
    where c.card_order > 0 and p.player_id is null
)

select
    'fixture_result_corrections' as seed,
    cast(c.fixture_id as string) as correction,
    c.fixture_id,
    f.league_code,
    f.season as season_api_year
from fixture_corrections as c
inner join fixtures as f
    on c.fixture_id = f.fixture_id
where
    f.provider_goals_home = c.goals_home
    and f.provider_goals_away = c.goals_away
    and not c.awarded
    and (
        c.shootout_home is null
        or (f.provider_shootout_home = c.shootout_home and f.provider_shootout_away = c.shootout_away)
    )
union all
select
    'fixture_goal_corrections' as seed,
    cast(g.fixture_id as string) as correction,
    g.fixture_id,
    f.league_code,
    f.season as season_api_year
from goal_counts as g
inner join provider_goals as e
    on g.fixture_id = e.fixture_id
inner join fixtures as f
    on g.fixture_id = f.fixture_id
left join goal_matches as m
    on g.fixture_id = m.fixture_id
where
    e.provider_home = g.score_home
    and e.provider_away = g.score_away
    and coalesce(m.matched_goals, 0) = g.seed_goals
union all
select
    'fixture_round_corrections' as seed,
    cast(c.fixture_id as string) as correction,
    c.fixture_id,
    f.league_code,
    f.season as season_api_year
from round_corrections as c
inner join fixtures as f
    on c.fixture_id = f.fixture_id
where f.provider_round_name = c.round_name
union all
select
    'standings_corrections' as seed,
    concat(c.league_code, ' ', cast(c.season as string), ' ', cast(c.team_id as string), ' ', c.group_name)
        as correction,
    cast(null as int64) as fixture_id,
    c.league_code,
    c.season as season_api_year
from table_corrections as c
inner join standings as s
    on
        c.league_code = s.league_code
        and c.season = s.season
        and c.team_id = s.provider_team_id
        and c.group_name = s.group_name
where
    s.provider_standing_rank = c.standing_rank
    and s.provider_points = c.points
    and s.provider_played_all = c.played
    and s.provider_wins_all = c.wins
    and s.provider_draws_all = c.draws
    and s.provider_losses_all = c.losses
    and s.provider_goals_for_all = c.goals_for
    and s.provider_goals_against_all = c.goals_against
    and s.team_id = s.provider_team_id
union all
select
    'fixture_card_corrections' as seed,
    cast(m.fixture_id as string) as correction,
    m.fixture_id,
    f.league_code,
    f.season as season_api_year
from card_matches as m
inner join fixtures as f
    on m.fixture_id = f.fixture_id
inner join card_events_agree as a
    on m.fixture_id = a.fixture_id
left join stat_lines_differ as d
    on m.fixture_id = d.fixture_id
left join carded_players_without_line as w
    on m.fixture_id = w.fixture_id
where d.fixture_id is null and w.fixture_id is null
