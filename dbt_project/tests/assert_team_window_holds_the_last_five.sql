{#
  The team window (int_team_momentum_window rows with no upcoming fixture) holds every team's last
  5 finished matches, a club's within the season of its latest finished match, recomputed here from
  int_legs__team_match. One row per team whose window differs: the model's matches and the
  expected ones.
#}
{{ config(store_failures = true, severity = 'error') }}

with legs as (
    select
        team_sk,
        fixture_sk,
        season_api_year,
        entity_type,
        kickoff_datetime
    from {{ ref('int_legs__team_match') }}
),

latest as (
    select
        team_sk,
        season_api_year
    from legs
    qualify row_number() over (
        partition by team_sk
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
),

expected as (
    select
        l.team_sk,
        l.fixture_sk,
        row_number() over (partition by l.team_sk order by l.kickoff_datetime desc) as recency_rank
    from legs as l
    inner join latest as t
        on l.team_sk = t.team_sk
    where l.entity_type = 'national' or l.season_api_year = t.season_api_year
    qualify recency_rank <= 5
),

model as (
    select
        team_sk,
        leg_fixture_sk as fixture_sk,
        recency_rank,
        window_type
    from {{ ref('int_team_momentum_window') }}
    where upcoming_fixture_sk is null
)

select
    coalesce(e.team_sk, m.team_sk) as team_sk,
    array_agg(distinct format('%d %d %s', m.fixture_sk, m.recency_rank, m.window_type) ignore nulls)
        as model_matches,
    array_agg(distinct format('%d %d', e.fixture_sk, e.recency_rank) ignore nulls) as expected_matches
from expected as e
full outer join model as m
    on e.team_sk = m.team_sk and e.fixture_sk = m.fixture_sk
group by 1
having countif(
    e.fixture_sk is null or m.fixture_sk is null
    or e.recency_rank != m.recency_rank or m.window_type != 'last_5'
) > 0
