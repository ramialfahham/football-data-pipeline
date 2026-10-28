-- A decided knockout tie has exactly one winner: of its two team rows one won and one lost, and
-- both read the same decision. Returns each tie whose two rows disagree.

{{ config(store_failures = true) }}

with ties as (
    select
        league_code,
        season_api_year,
        round_name,
        won,
        decided_by,
        least(team_sk, opponent_team_sk) as team_a,
        greatest(team_sk, opponent_team_sk) as team_b
    from {{ ref('int_knockout_ties') }}
)

select
    league_code,
    season_api_year,
    round_name,
    team_a,
    team_b,
    count(*) as team_rows,
    countif(won) as winners,
    countif(not won) as losers,
    count(distinct coalesce(decided_by, 'undecided')) as decisions
from ties
group by league_code, season_api_year, round_name, team_a, team_b
having
    count(*) != 2
    or count(distinct coalesce(decided_by, 'undecided')) != 1
    or (countif(won is not null) > 0 and (countif(won) != 1 or countif(not won) != 1))
