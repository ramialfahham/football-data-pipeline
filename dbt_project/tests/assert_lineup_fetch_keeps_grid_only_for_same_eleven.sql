{#
  base_apif__lineups reads each team's latest fetch. When that fetch has no grid places, its starters
  take the grid places, and the sheet the formation, of the latest earlier fetch that has them, only
  if both name the same starting eleven; nothing else comes from the earlier fetch. Recomputed here
  from every stored fetch; returns the team sheets and starters that break this.
#}

with fetches as (
    select
        league_code,
        fixture_id,
        team_id,
        raw_ingested_at,
        formation,
        start_xi_json,
        (
            select countif(json_value(el, '$.player.grid') is not null) > 0
            from unnest(json_query_array(start_xi_json)) as el
        ) as has_grid,
        (
            select string_agg(id, ',' order by id)
            from unnest(json_query_array(start_xi_json)) as el,
                unnest([coalesce(json_value(el, '$.player.id'), '')]) as id
        ) as starting_eleven
    from {{ ref('stg_apif__lineups') }}
    where fixture_id is not null and team_id is not null
),

newest as (
    select *
    from fetches
    qualify row_number() over (
        partition by league_code, fixture_id, team_id order by raw_ingested_at desc
    ) = 1
),

lender_candidates as (
    select
        f.league_code,
        f.fixture_id,
        f.team_id,
        f.raw_ingested_at,
        f.formation,
        f.start_xi_json,
        farm_fingerprint(to_json_string(struct(f.formation, f.start_xi_json))) as content_hash
    from fetches as f
    inner join newest as n
        on f.league_code = n.league_code and f.fixture_id = n.fixture_id and f.team_id = n.team_id
    where not n.has_grid and f.has_grid and f.starting_eleven = n.starting_eleven
),

lender as (
    select
        f.league_code,
        f.fixture_id,
        f.team_id,
        f.formation,
        f.start_xi_json
    from lender_candidates as f
    qualify f.raw_ingested_at = max(f.raw_ingested_at) over (partition by f.league_code, f.fixture_id, f.team_id)
        and min(content_hash) over (partition by f.league_code, f.fixture_id, f.team_id, f.raw_ingested_at)
        = max(content_hash) over (partition by f.league_code, f.fixture_id, f.team_id, f.raw_ingested_at)
        and row_number() over (partition by f.league_code, f.fixture_id, f.team_id order by f.raw_ingested_at desc) = 1
),

lent_places as (
    select
        lender.league_code,
        lender.fixture_id,
        lender.team_id,
        safe_cast(json_value(el, '$.player.number') as int64) as shirt_number,
        json_value(el, '$.player.grid') as grid_position
    from lender, unnest(json_query_array(lender.start_xi_json)) as el
),

base_rows as (
    select *
    from {{ ref('base_apif__lineups') }}
    where lineup_state != 'researched'
),

wrong_fetch as (
    select
        b.league_code,
        b.fixture_id,
        b.team_id,
        b.player_id,
        'not read from the latest fetch' as problem
    from base_rows as b
    inner join newest as n
        on b.league_code = n.league_code and b.fixture_id = n.fixture_id and b.team_id = n.team_id
    where b.raw_ingested_at != n.raw_ingested_at
),

wrong_formation as (
    select distinct
        b.league_code,
        b.fixture_id,
        b.team_id,
        cast(null as int64) as player_id,
        'formation is neither the latest fetch formation nor, when it has none, the lender formation' as problem
    from base_rows as b
    inner join newest as n
        on b.league_code = n.league_code and b.fixture_id = n.fixture_id and b.team_id = n.team_id
    left join lender as l
        on b.league_code = l.league_code and b.fixture_id = l.fixture_id and b.team_id = l.team_id
    where b.team_formation is distinct from coalesce(n.formation, l.formation)
),

wrong_place as (
    select
        b.league_code,
        b.fixture_id,
        b.team_id,
        b.player_id,
        'starter grid place differs from the lender grid place' as problem
    from base_rows as b
    inner join newest as n
        on b.league_code = n.league_code and b.fixture_id = n.fixture_id and b.team_id = n.team_id
    left join lent_places as p
        on
            b.league_code = p.league_code
            and b.fixture_id = p.fixture_id
            and b.team_id = p.team_id
            and b.shirt_number = p.shirt_number
    where
        b.is_starter
        and not n.has_grid
        and b.grid_position is distinct from p.grid_position
)

select * from wrong_fetch
union all
select * from wrong_formation
union all
select * from wrong_place
