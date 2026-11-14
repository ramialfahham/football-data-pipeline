{#
  A player's match stat that the match's picked fetch leaves blank is the newest value of another
  fetch that gives him the same results. Returns one row per player-match and stat where
  base_apif__fixture_players shows something else, unless the cleaning changed that stat (a
  stat_corrections entry). Checked for the players whose results the events did not change; shots
  and shots on target only where the team's player total with the other fetches' values is no
  further from the team line than without.
#}
{{ config(store_failures = true, severity = 'error') }}

{%- set stats = {
    'shirt_number': 'shirt_number', 'position_code': 'position_code', 'offsides': 'offsides',
    'shots': 'shots_total', 'shots_on_target': 'shots_on', 'passes': 'passes_total',
    'passes_key': 'passes_key', 'tackles': 'tackles_total', 'blocks': 'tackles_blocks',
    'interceptions': 'tackles_interceptions', 'duels': 'duels_total', 'duels_won': 'duels_won',
    'dribbles': 'dribbles_attempts', 'dribbles_success': 'dribbles_success',
    'dribbles_against': 'dribbles_past', 'fouls': 'fouls_committed', 'fouls_against': 'fouls_drawn'
} %}
{%- set results = [
    'goals_total', 'goals_assists', 'cards_yellow', 'cards_red', 'minutes_played', 'goals_against', 'saves',
    'penalty_won', 'penalty_committed', 'penalty_scored', 'penalty_missed', 'penalty_saved'
] %}

with fetch_rows as (
    select
        stat_line.* replace (
            if(stat_line.position_code in ('G', 'D', 'M', 'F'), stat_line.position_code, null) as position_code
        ),
        {{ fixture_player_id(
            'stat_line.player_id', 'stat_line.fixture_id', 'stat_line.team_id', 'stat_line.shirt_number'
        ) }} as kept_player_id,
        logical_or(stat_line.goals_against is not null)
            over (partition by stat_line.league_code, stat_line.fixture_id, stat_line.raw_ingested_at)
            as fetch_is_complete
    from {{ ref('stg_apif__fixture_players') }} as stat_line
    where stat_line.fixture_id is not null and stat_line.team_id is not null
),

one_row_per_fetch as (
    select
        *,
        raw_ingested_at = coalesce(
            max(if(fetch_is_complete, raw_ingested_at, null)) over (partition by league_code, fixture_id),
            max(raw_ingested_at) over (partition by league_code, fixture_id)
        ) as is_picked
    from fetch_rows
    where kept_player_id is not null and kept_player_id != 0
    qualify row_number() over (
        partition by league_code, fixture_id, kept_player_id, raw_ingested_at
        order by
            (
                select countif(stat is not null)
                from unnest([
                    {%- for column in results + (stats.values() | list) %}
                    cast({{ column }} as string){{ ',' if not loop.last }}
                    {%- endfor %}
                ]) as stat
            ) desc,
            to_json_string(fetch_rows) asc
    ) = 1
),

picked as (
    select *
    from one_row_per_fetch
    where is_picked
),

donors as (
    select o.*
    from one_row_per_fetch as o
    inner join picked as p
        on o.league_code = p.league_code and o.fixture_id = p.fixture_id and o.kept_player_id = p.kept_player_id
    where
        not o.is_picked
        and coalesce(o.goals_total, 0) = coalesce(p.goals_total, 0)
        and coalesce(o.goals_assists, 0) = coalesce(p.goals_assists, 0)
        and coalesce(o.cards_yellow, 0) = coalesce(p.cards_yellow, 0)
        and coalesce(o.cards_red, 0) = coalesce(p.cards_red, 0)
        and coalesce(o.minutes_played, 0) = coalesce(p.minutes_played, 0)
        and coalesce(o.goals_against, 0) = coalesce(p.goals_against, 0)
        and coalesce(o.saves, 0) = coalesce(p.saves, 0)
        and coalesce(o.penalty_won, 0) = coalesce(p.penalty_won, 0)
        and coalesce(o.penalty_committed, 0) = coalesce(p.penalty_committed, 0)
        and coalesce(o.penalty_scored, 0) = coalesce(p.penalty_scored, 0)
        and coalesce(o.penalty_missed, 0) = coalesce(p.penalty_missed, 0)
        and coalesce(o.penalty_saved, 0) = coalesce(p.penalty_saved, 0)
),

donor_values as (
    select
        league_code,
        fixture_id,
        kept_player_id,
        {%- for column in stats.values() %}
        array_agg(cast({{ column }} as string) ignore nulls order by raw_ingested_at desc limit 1)[safe_offset(0)]
            as {{ column }},
        {%- endfor %}
        count(*) as donor_fetches
    from donors
    group by league_code, fixture_id, kept_player_id
),

expected as (
    select
        p.league_code,
        p.fixture_id,
        p.kept_player_id as player_id,
        stat.stat_name,
        stat.donated
    from picked as p
    inner join donor_values as d
        on p.league_code = d.league_code and p.fixture_id = d.fixture_id and p.kept_player_id = d.kept_player_id
    cross join
        unnest([
            {%- for name, column in stats.items() %}
            struct(
                '{{ name }}' as stat_name,
                cast(p.{{ column }} as string) as picked_value,
                d.{{ column }} as donated
            ){{ ',' if not loop.last }}
            {%- endfor %}
        ]) as stat
    where stat.picked_value is null and stat.donated is not null
),

held as (
    select
        b.league_code,
        b.fixture_id,
        b.team_id,
        b.player_id,
        b.stat_corrections,
        b.goals,
        b.assists,
        b.cards_yellow,
        b.cards_red,
        stat.stat_name,
        stat.stat_value
    from {{ ref('base_apif__fixture_players') }} as b
    cross join
        unnest([
            {%- for name in stats %}
            struct('{{ name }}' as stat_name, cast(b.{{ name }} as string) as stat_value){{ ',' if not loop.last }}
            {%- endfor %}
        ]) as stat
),

picked_shots as (
    select
        p.league_code,
        p.fixture_id,
        p.kept_player_id as player_id,
        shot.stat_name,
        shot.stat_value
    from picked as p
    cross join
        unnest([
            struct('shots' as stat_name, p.shots_total as stat_value),
            struct('shots_on_target', p.shots_on)
        ]) as shot
),

team_sums as (
    select
        h.fixture_id,
        h.team_id,
        h.stat_name,
        sum(coalesce(p.stat_value, safe_cast(e.donated as int64), 0)) as with_fills,
        sum(coalesce(p.stat_value, 0)) as without_fills
    from held as h
    left join picked_shots as p
        on
            h.league_code = p.league_code and h.fixture_id = p.fixture_id
            and h.player_id = p.player_id and h.stat_name = p.stat_name
    left join expected as e
        on
            h.league_code = e.league_code and h.fixture_id = e.fixture_id
            and h.player_id = e.player_id and h.stat_name = e.stat_name
    where h.stat_name in ('shots', 'shots_on_target')
    group by h.fixture_id, h.team_id, h.stat_name
),

team_lines as (
    select
        fixture_id,
        team_id,
        line.stat_name,
        line.stat_value
    from {{ ref('base_apif__fixture_statistics') }}
    cross join unnest([
        struct('shots' as stat_name, shots as stat_value),
        struct('shots_on_target', shots_on_target)
    ]) as line
)

select
    h.league_code,
    h.fixture_id,
    h.player_id,
    h.stat_name,
    e.donated,
    h.stat_value
from expected as e
inner join held as h
    on
        e.league_code = h.league_code and e.fixture_id = h.fixture_id
        and e.player_id = h.player_id and e.stat_name = h.stat_name
inner join picked as p
    on e.league_code = p.league_code and e.fixture_id = p.fixture_id and e.player_id = p.kept_player_id
left join team_sums as s
    on h.fixture_id = s.fixture_id and h.team_id = s.team_id and h.stat_name = s.stat_name
left join team_lines as t
    on h.fixture_id = t.fixture_id and h.team_id = t.team_id and h.stat_name = t.stat_name
where
    h.stat_value is distinct from e.donated
    and h.stat_name not in (select c.stat from unnest(h.stat_corrections) as c)
    and coalesce(h.goals, 0) = coalesce(p.goals_total, 0)
    and coalesce(h.assists, 0) = coalesce(p.goals_assists, 0)
    and coalesce(h.cards_yellow, 0) = coalesce(p.cards_yellow, 0)
    and coalesce(h.cards_red, 0) = coalesce(p.cards_red, 0)
    and (
        h.stat_name not in ('shots', 'shots_on_target')
        or coalesce(abs(s.with_fills - t.stat_value) <= abs(s.without_fills - t.stat_value), false)
    )
