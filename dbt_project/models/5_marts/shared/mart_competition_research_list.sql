{#
  The list of provider errors to research, rebuilt each night: one row per match, or team in a
  match, where a check of the provider's data withholds a value on goals, scores, awards or cards,
  and one row per correction the provider no longer needs. A value the provider has corrected
  itself passes its check, and its row leaves the list. check_name says what failed:
  - result_withheld: the match's result fails a result check (result_needs_research);
  - goals_not_reconciled: the match's goal events add up neither alone nor with the players' goals,
    so it serves no goal (goal_data_state not_recorded);
  - scorer_withheld, assist_withheld: a goal's scorer or assister was not on the pitch at its minute;
  - cards_withheld: the match's stat lines and card events disagree, a card's player is not on
    the sheet, or a player's card events name two teams (cards_need_research);
  - lineup_goals_withheld: a line-up team's player goals do not add up to its score
    (goals_need_research);
  - misfiled_team_withheld: an event, a player line or a statistics line is filed under a team that
    did not play the match (team_needs_research). The line is left out of the facts; the repair is
    a row in fixture_team_id_overrides. provider_team_id is the team id the provider filed it
    under, and team_sk is that team only where it is in dim_team;
  - player_team_withheld: a player's stat line and his events name different teams of the match, and
    nothing decides which is right (player_team_needs_research). His line and his events are left
    out of the facts; the repair is a row in fixture_lineup_corrections;
  - lineup_duplicate_withheld: the provider stored a team's line-up twice at the newest ingest time
    with different content (base_apif__lineup_fetch_ties), so that team has no sheet and the match
    line-up is not_available. No seed fixes the row (seed none); a newer fetch without the tie
    removes it;
  - null_key_line_withheld: a statistics line or a line-up of the match came with no team id and
    base leaves it out, while a team of the match has no value base could otherwise have used
    (base_apif__fixture_lines_without_key). No seed fixes the row (seed none); a fetch that carries
    the team id removes it;
  - team_season_off_standings: a team-season's results disagree with the provider's standings
    (counts_withheld), so every value of the team-season is blank. One row per finished match of the
    team-season: the results or the standings are wrong and nothing says which, and no seed fixes it
    (seed none); a result in fixture_result_corrections or a points deduction in
    standings_points_adjustments can settle it. team_sk is the team of the team-season;
  - correction_no_longer_needed: the provider's own data now carries the row's corrected values
    (int_pipeline__corrections_no_longer_needed), and the row is to be removed.
  seed names the correction seed that fixes the row. research_tier is the research order of the
  match: 1 a domestic league of the registry, 2 a match of a national team, 3 a match of a club
  that plays a registry domestic league in its current season, NULL otherwise.

  It reads base for the flags that exist only there: the withheld cards and line-up goals, and
  the provider's own values a correction is compared with. Grain: item_key.
#}

with fixtures as (
    select
        fixture_sk,
        season_sk,
        league_code,
        season_api_year,
        fixture_date,
        home_team_sk,
        away_team_sk,
        result_needs_research
    from {{ ref('fct_fixture') }}
),

goal_event_matches as (
    select fixture_sk
    from {{ ref('fct_fixture_event') }}
    where is_goal
    group by fixture_sk
),

items as (
    select
        'result_withheld' as check_name,
        'fixture_result_corrections' as seed,
        fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from fixtures
    where result_needs_research
    union all
    select
        'goals_not_reconciled' as check_name,
        'fixture_goal_corrections' as seed,
        f.fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from {{ ref('mart_competition_fixtures') }} as f
    inner join goal_event_matches as e
        on f.fixture_sk = e.fixture_sk
    where f.goal_data_state = 'not_recorded'
    union all
    select distinct
        'scorer_withheld' as check_name,
        'fixture_goal_corrections' as seed,
        fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from {{ ref('fct_fixture_event') }}
    where scorer_needs_research
    union all
    select distinct
        'assist_withheld' as check_name,
        'fixture_goal_corrections' as seed,
        fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from {{ ref('fct_fixture_event') }}
    where assist_needs_research
    union all
    select distinct
        'cards_withheld' as check_name,
        'fixture_card_corrections' as seed,
        cast(card_matches.fixture_id as int64) as fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from (
        select p.fixture_id
        from {{ ref('base_apif__fixture_players') }} as p
        cross join unnest(p.stat_corrections) as c
        where c.rule = 'cards_need_research'
        union all
        select two_team_players.fixture_id
        from ({{ card_events_naming_two_teams(ref('base_apif__fixture_events_checked')) }}) as two_team_players
        left join {{ ref('fixture_card_corrections') }} as researched
            on two_team_players.fixture_id = researched.fixture_id
        where researched.fixture_id is null
    ) as card_matches
    union all
    select distinct
        'lineup_goals_withheld' as check_name,
        'fixture_goal_corrections' as seed,
        cast(fixture_id as int64) as fixture_sk,
        cast(team_id as int64) as team_sk,
        cast(null as string) as correction
    from {{ ref('base_apif__fixture_players_from_lineups') }}
    where goals_need_research and not team_needs_research
    union all
    select distinct
        'player_team_withheld' as check_name,
        'fixture_lineup_corrections' as seed,
        cast(fixture_id as int64) as fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from {{ ref('base_apif__fixture_events_checked') }}
    where player_team_needs_research
    union all
    select distinct
        'lineup_duplicate_withheld' as check_name,
        'none' as seed,
        fixture_id as fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from {{ ref('base_apif__lineup_fetch_ties') }}
    where rows_differ
    union all
    select distinct
        'null_key_line_withheld' as check_name,
        'none' as seed,
        fixture_id as fixture_sk,
        cast(null as int64) as team_sk,
        cast(null as string) as correction
    from {{ ref('base_apif__fixture_lines_without_key') }}
),

misfiled_lines as (
    select distinct
        cast(fixture_id as int64) as fixture_sk,
        cast(team_id as int64) as provider_team_id
    from (
        select
            fixture_id,
            team_id
        from {{ ref('base_apif__fixture_events_checked') }}
        where team_needs_research
        union all
        select
            fixture_id,
            team_id
        from {{ ref('base_apif__fixture_players_checked') }}
        where team_needs_research
        union all
        select
            fixture_id,
            team_id
        from {{ ref('base_apif__fixture_players_from_lineups') }}
        where team_needs_research
        union all
        select
            fixture_id,
            team_id
        from {{ ref('base_apif__fixture_statistics') }}
        where team_needs_research
    )
),

misfiled_items as (
    select
        'misfiled_team_withheld' as check_name,
        'fixture_team_id_overrides' as seed,
        m.fixture_sk,
        t.team_sk,
        cast(null as string) as correction,
        m.provider_team_id
    from misfiled_lines as m
    left join {{ ref('dim_team') }} as t
        on m.provider_team_id = t.team_sk
),

off_standings_items as (
    select
        'team_season_off_standings' as check_name,
        'none' as seed,
        r.fixture_sk,
        r.team_sk,
        cast(null as string) as correction,
        cast(null as int64) as provider_team_id
    from {{ ref('int_team_season_record') }} as r
    inner join {{ ref('int_team_season__metrics') }} as m
        on r.team_sk = m.team_sk and r.season_sk = m.season_sk
    where m.counts_withheld
),

no_longer_needed as (
    select
        'correction_no_longer_needed' as check_name,
        seed,
        cast(fixture_id as int64) as fixture_sk,
        cast(null as int64) as team_sk,
        correction,
        cast(null as int64) as provider_team_id,
        league_code,
        season_api_year
    from {{ ref('int_pipeline__corrections_no_longer_needed') }}
),

all_items as (
    select
        i.check_name,
        i.seed,
        i.fixture_sk,
        i.team_sk,
        i.correction,
        cast(null as int64) as provider_team_id,
        f.league_code,
        f.season_api_year
    from items as i
    inner join fixtures as f
        on i.fixture_sk = f.fixture_sk
    union all
    select
        m.check_name,
        m.seed,
        m.fixture_sk,
        m.team_sk,
        m.correction,
        m.provider_team_id,
        f.league_code,
        f.season_api_year
    from misfiled_items as m
    inner join fixtures as f
        on m.fixture_sk = f.fixture_sk
    union all
    select
        s.check_name,
        s.seed,
        s.fixture_sk,
        s.team_sk,
        s.correction,
        s.provider_team_id,
        f.league_code,
        f.season_api_year
    from off_standings_items as s
    inner join fixtures as f
        on s.fixture_sk = f.fixture_sk
    union all
    select
        check_name,
        seed,
        fixture_sk,
        team_sk,
        correction,
        provider_team_id,
        league_code,
        season_api_year
    from no_longer_needed
),

seasons as (
    select
        season_sk,
        league_code,
        season_api_year,
        season_is_current
    from {{ ref('dim_competition_season') }}
),

domestic_leagues as (
    select league_code
    from {{ ref('dim_league') }}
    where competition_type = 'domestic_league'
),

national_teams as (
    select team_sk
    from {{ ref('dim_team') }}
    where is_national_team
),

domestic_league_clubs as (
    select distinct m.team_sk
    from {{ ref('dim_team_competition_season_mapping') }} as m
    inner join domestic_leagues as d
        on m.league_code = d.league_code
    inner join seasons as s
        on m.season_sk = s.season_sk
    where s.season_is_current
)

select
    a.check_name,
    a.seed,
    a.correction,
    a.fixture_sk,
    a.team_sk,
    a.provider_team_id,
    a.league_code,
    a.season_api_year,
    f.fixture_date,
    concat(
        a.check_name, ' ', a.seed, ' ',
        coalesce(a.correction, cast(a.fixture_sk as string)),
        coalesce(concat(' ', cast(coalesce(a.provider_team_id, a.team_sk) as string)), '')
    ) as item_key,
    coalesce(s.season_is_current, false) as is_current_season,
    case
        when d.league_code is not null then 1
        when hn.team_sk is not null or an.team_sk is not null then 2
        when hc.team_sk is not null or ac.team_sk is not null then 3
    end as research_tier
from all_items as a
left join fixtures as f
    on a.fixture_sk = f.fixture_sk
left join seasons as s
    on a.league_code = s.league_code and a.season_api_year = s.season_api_year
left join domestic_leagues as d
    on a.league_code = d.league_code
left join national_teams as hn
    on f.home_team_sk = hn.team_sk
left join national_teams as an
    on f.away_team_sk = an.team_sk
left join domestic_league_clubs as hc
    on f.home_team_sk = hc.team_sk
left join domestic_league_clubs as ac
    on f.away_team_sk = ac.team_sk
