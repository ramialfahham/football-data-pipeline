{#
  Every upcoming fixture side's windows hold the matches docs/metrics_context_model.md section 4
  names, recomputed here from int_legs__team_match:

  - the form window (int_team_momentum_window): in a world or continental championship, every
    finished match of this edition before kickoff (tournament_to_date), or before the team's first
    one, every match of its qualifiers (qualifiers); elsewhere the team's last 5 finished matches of
    its kind (club or national), a club's from this season only, a national team's with no season
    cap (last_5). Left out: a qualifying campaign under way, which section 4 gives the whole campaign
    and the model does not yet build ("Form-window code diverges from metrics_context_model.md
    section 4 in two places").
  - the season record (mart_team_season_record): the team's record in the fixture's competition this
    season, or the previous season's before its first match (prev_season), with the number of
    matches it holds.

  One row per side whose window differs: the window, the model's matches and the expected ones.
#}
{{ config(store_failures = true, severity = 'error') }}

with upcoming as (
    select
        f.fixture_sk,
        f.home_team_sk,
        f.away_team_sk,
        f.league_code,
        f.season_api_year,
        f.kickoff_datetime,
        reg.competition_type,
        typ.entity_type
    from {{ ref('fct_fixture') }} as f
    left join {{ ref('competition_registry') }} as reg
        on f.league_code = reg.league_code
    left join {{ ref('competition_types') }} as typ
        on reg.competition_type = typ.competition_type
    where
        f.status_short in ('NS', 'TBD')
        and f.fixture_date >= current_date()
),

sides as (
    select
        fixture_sk as upcoming_fixture_sk,
        home_team_sk as team_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        competition_type,
        entity_type
    from upcoming
    union all
    select
        fixture_sk,
        away_team_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        competition_type,
        entity_type
    from upcoming
),

earlier_legs as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        s.league_code as upcoming_league_code,
        s.season_api_year as upcoming_season_api_year,
        s.competition_type,
        s.entity_type,
        l.fixture_sk as leg_fixture_sk,
        l.league_code,
        l.season_api_year,
        l.kickoff_datetime,
        reg.parent_competition
    from sides as s
    inner join {{ ref('int_legs__team_match') }} as l
        on
            s.team_sk = l.team_sk
            and s.entity_type = l.entity_type
            and l.kickoff_datetime < s.kickoff_datetime
    left join {{ ref('competition_registry') }} as reg
        on l.league_code = reg.league_code
),

side_kinds as (
    select
        upcoming_fixture_sk,
        team_sk,
        any_value(competition_type) as competition_type,
        countif(league_code = upcoming_league_code and season_api_year = upcoming_season_api_year)
            as legs_in_this_edition
    from earlier_legs
    group by upcoming_fixture_sk, team_sk
),

expected_form as (
    select
        e.upcoming_fixture_sk,
        e.team_sk,
        e.leg_fixture_sk,
        case
            when k.competition_type in ('world_championship', 'continental_championship') and k.legs_in_this_edition > 0
                then 'tournament_to_date'
            when k.competition_type in ('world_championship', 'continental_championship') then 'qualifiers'
            else 'last_5'
        end as window_type,
        case
            when k.competition_type in ('world_championship', 'continental_championship') and k.legs_in_this_edition > 0
                then e.league_code = e.upcoming_league_code and e.season_api_year = e.upcoming_season_api_year
            when k.competition_type in ('world_championship', 'continental_championship')
                then e.parent_competition is not distinct from e.upcoming_league_code
            else
                (e.entity_type = 'national' or e.season_api_year = e.upcoming_season_api_year)
                and 5 >= row_number() over (
                    partition by
                        e.upcoming_fixture_sk, e.team_sk,
                        e.entity_type = 'national' or e.season_api_year = e.upcoming_season_api_year
                    order by e.kickoff_datetime desc
                )
        end as in_window
    from earlier_legs as e
    inner join side_kinds as k
        on e.upcoming_fixture_sk = k.upcoming_fixture_sk and e.team_sk = k.team_sk
    where not (k.competition_type = 'qualifying' and k.legs_in_this_edition > 0)
),

form_compared as (
    select
        coalesce(e.upcoming_fixture_sk, m.upcoming_fixture_sk) as upcoming_fixture_sk,
        coalesce(e.team_sk, m.team_sk) as team_sk,
        array_agg(distinct format('%d %s', m.leg_fixture_sk, m.window_type) ignore nulls) as model_matches,
        array_agg(distinct format('%d %s', e.leg_fixture_sk, e.window_type) ignore nulls) as expected_matches,
        countif(e.leg_fixture_sk is null or m.leg_fixture_sk is null or e.window_type != m.window_type)
            as differing
    from (select * from expected_form where in_window) as e
    full outer join (
        select w.*
        from {{ ref('int_team_momentum_window') }} as w
        inner join side_kinds as k
            on w.upcoming_fixture_sk = k.upcoming_fixture_sk and w.team_sk = k.team_sk
        where not (k.competition_type = 'qualifying' and k.legs_in_this_edition > 0)
    ) as m
        on
            e.upcoming_fixture_sk = m.upcoming_fixture_sk
            and e.team_sk = m.team_sk
            and e.leg_fixture_sk = m.leg_fixture_sk
    group by 1, 2
),

season_legs as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        countif(l.season_api_year = s.season_api_year) as legs_this_season,
        countif(l.season_api_year = s.season_api_year - 1) as legs_previous_season
    from sides as s
    inner join {{ ref('int_legs__team_match') }} as l
        on
            s.team_sk = l.team_sk
            and s.league_code = l.league_code
            and l.season_api_year in (s.season_api_year, s.season_api_year - 1)
    group by s.upcoming_fixture_sk, s.team_sk
),

expected_record as (
    select
        upcoming_fixture_sk,
        team_sk,
        if(legs_this_season > 0, 'season_to_date', 'prev_season') as window_type,
        if(legs_this_season > 0, legs_this_season, legs_previous_season) as games_played
    from season_legs
),

record_compared as (
    select
        coalesce(e.upcoming_fixture_sk, m.upcoming_fixture_sk) as upcoming_fixture_sk,
        coalesce(e.team_sk, m.team_sk) as team_sk,
        [format('%s %d', m.window_type, m.games_played)] as model_matches,
        [format('%s %d', e.window_type, e.games_played)] as expected_matches
    from expected_record as e
    full outer join {{ ref('mart_team_season_record') }} as m
        on e.upcoming_fixture_sk = m.upcoming_fixture_sk and e.team_sk = m.team_sk
    where
        e.window_type is distinct from m.window_type
        or e.games_played is distinct from m.games_played
)

select
    'form window' as window_checked,
    upcoming_fixture_sk,
    team_sk,
    model_matches,
    expected_matches
from form_compared
where differing > 0

union all

select
    'season record',
    upcoming_fixture_sk,
    team_sk,
    model_matches,
    expected_matches
from record_compared
