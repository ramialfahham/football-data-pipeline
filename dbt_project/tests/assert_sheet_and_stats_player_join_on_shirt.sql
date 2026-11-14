{#
  In one match, a team-sheet player whose id has no stats line in it is the same team's stats-line
  player with his shirt number, when that player is on no sheet row of the match. Ids a hand
  override changed or a card or goal correction names are left as they are. Returns the pairs
  base_apif__lineups left apart, and the sheet players it joined away although their own id had a
  stats line.
#}

with sheet_rows as (
    select distinct
        league_code,
        fixture_id,
        team_id,
        player_id,
        shirt_number
    from {{ ref('base_apif__lineups') }}
    where lineup_state != 'researched' and player_id is not null
),

stat_rows as (
    select distinct
        league_code,
        fixture_id,
        team_id,
        player_id,
        shirt_number
    from {{ ref('base_apif__fixture_players') }}
    where player_id is not null
),

hand_overridden as (
    select wrong_player_api_id as player_id
    from {{ ref('player_id_overrides') }}
    union distinct
    select correct_player_api_id as player_id
    from {{ ref('player_id_overrides') }}
),

hand_corrected as (
    select cast(fixture_id as int64) as fixture_id, cast(player_id as int64) as player_id
    from {{ ref('fixture_card_corrections') }}
    union distinct
    select cast(fixture_id as int64), cast(player_id as int64)
    from {{ ref('fixture_goal_corrections') }}
    union distinct
    select cast(fixture_id as int64), cast(assist_player_id as int64)
    from {{ ref('fixture_goal_corrections') }}
),

read_fetches as (
    select distinct
        league_code,
        fixture_id,
        team_id,
        raw_ingested_at
    from {{ ref('base_apif__lineups') }}
    where lineup_state != 'researched'
),

left_apart as (
    select
        s.league_code,
        s.fixture_id,
        s.team_id,
        s.player_id,
        'sheet player and stats-line player of one shirt stay apart' as problem
    from sheet_rows as s
    inner join stat_rows as t
        on
            s.league_code = t.league_code
            and s.fixture_id = t.fixture_id
            and s.team_id = t.team_id
            and s.shirt_number = t.shirt_number
    left join stat_rows as own_line
        on
            s.league_code = own_line.league_code
            and s.fixture_id = own_line.fixture_id
            and s.player_id = own_line.player_id
    left join sheet_rows as named
        on
            t.league_code = named.league_code
            and t.fixture_id = named.fixture_id
            and t.player_id = named.player_id
    left join hand_overridden as h
        on s.player_id = h.player_id
    left join hand_corrected as hc
        on cast(s.fixture_id as int64) = hc.fixture_id and s.player_id = hc.player_id
    where
        own_line.player_id is null
        and named.player_id is null
        and h.player_id is null
        and hc.player_id is null
        and s.player_id != t.player_id
    qualify count(*) over (partition by s.league_code, s.fixture_id, s.team_id, s.shirt_number) = 1
),

-- the very fetch base read for each team sheet, so a sheet base dropped is never read here
latest_sheets as (
    select
        s.league_code,
        s.fixture_id,
        s.team_id,
        s.start_xi_json,
        s.substitutes_json
    from {{ ref('stg_apif__lineups') }} as s
    inner join read_fetches as r
        on
            s.league_code = r.league_code
            and s.fixture_id = r.fixture_id
            and s.team_id = r.team_id
            and s.raw_ingested_at = r.raw_ingested_at
),

provider_ids as (
    select distinct
        l.league_code,
        l.fixture_id,
        safe_cast(json_value(el, '$.player.id') as int64) as player_id
    from latest_sheets as l,
        unnest(array_concat(json_query_array(l.start_xi_json), json_query_array(l.substitutes_json))) as el
),

joined_away as (
    select
        p.league_code,
        p.fixture_id,
        cast(null as int64) as team_id,
        p.player_id,
        'a sheet id with its own stats line was joined away' as problem
    from provider_ids as p
    inner join stat_rows as t
        on p.league_code = t.league_code and p.fixture_id = t.fixture_id and p.player_id = t.player_id
    left join sheet_rows as kept
        on p.league_code = kept.league_code and p.fixture_id = kept.fixture_id and p.player_id = kept.player_id
    left join hand_overridden as h
        on p.player_id = h.player_id
    where kept.player_id is null and h.player_id is null
        and exists (
            select 1 from sheet_rows as any_row
            where any_row.league_code = p.league_code and any_row.fixture_id = p.fixture_id
        )
)

select * from left_apart
union all
select * from joined_away
