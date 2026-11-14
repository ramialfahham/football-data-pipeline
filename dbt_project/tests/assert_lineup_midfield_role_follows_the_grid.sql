{#
  Every line-up row's midfield_role is the one its grid line gives, recomputed here from the
  formation's digits: a starter's own line, a substitute's the line of the starter whose slot he took,
  followed back through every substitution. The common formations give the roles the rule was
  measured with. Returns the rows that disagree.
#}

with came_on as (
    select
        fixture_sk,
        team_sk,
        player_sk,
        replaced_player_sk
    from {{ ref('fct_fixture_lineup') }}
    where is_starter = false and replaced_player_sk is not null
),

starters as (
    select
        fixture_sk,
        team_sk,
        player_sk,
        player_sk as slot_player_sk
    from {{ ref('fct_fixture_lineup') }}
    where coalesce(is_starter, false)
),

hop_1 as (
    select
        c.fixture_sk,
        c.team_sk,
        c.player_sk,
        s.slot_player_sk
    from came_on as c
    inner join starters as s
        on c.fixture_sk = s.fixture_sk and c.team_sk = s.team_sk and c.replaced_player_sk = s.player_sk
),

hop_2 as (
    select
        c.fixture_sk,
        c.team_sk,
        c.player_sk,
        h.slot_player_sk
    from came_on as c
    inner join hop_1 as h
        on c.fixture_sk = h.fixture_sk and c.team_sk = h.team_sk and c.replaced_player_sk = h.player_sk
),

hop_3 as (
    select
        c.fixture_sk,
        c.team_sk,
        c.player_sk,
        h.slot_player_sk
    from came_on as c
    inner join hop_2 as h
        on c.fixture_sk = h.fixture_sk and c.team_sk = h.team_sk and c.replaced_player_sk = h.player_sk
),

hop_4 as (
    select
        c.fixture_sk,
        c.team_sk,
        c.player_sk,
        h.slot_player_sk
    from came_on as c
    inner join hop_3 as h
        on c.fixture_sk = h.fixture_sk and c.team_sk = h.team_sk and c.replaced_player_sk = h.player_sk
),

slots as (
    select * from starters
    union all
    select * from hop_1
    union all
    select * from hop_2
    union all
    select * from hop_3
    union all
    select * from hop_4
),

rows_with_lines as (
    select
        l.fixture_sk,
        l.team_sk,
        l.player_sk,
        l.team_formation,
        l.midfield_role,
        l.position_code = 'M' and s.slot_player_sk is not null as is_midfield_slot,
        safe_cast(regexp_extract(o.grid_position, r'^(\d+)(?::|$)') as int64) - 1 as line,
        regexp_extract_all(l.team_formation, r'\d+') as digits,
        regexp_contains(coalesce(l.team_formation, ''), r'^[1-9]\d*(-[1-9]\d*){2,}$') as is_formation
    from {{ ref('fct_fixture_lineup') }} as l
    left join slots as s
        on l.fixture_sk = s.fixture_sk and l.team_sk = s.team_sk and l.player_sk = s.player_sk
    left join {{ ref('fct_fixture_lineup') }} as o
        on s.fixture_sk = o.fixture_sk and s.team_sk = o.team_sk and s.slot_player_sk = o.player_sk
),

expected as (
    select
        *,
        case
            when not coalesce(is_midfield_slot, false) or not is_formation or line is null then null
            when line < 1 or line > array_length(digits) then null
            when line = 1 then 'DM'
            when line = array_length(digits) then 'AM'
            when array_length(digits) = 3 then 'CM'
            when line = 2 and cast(digits[offset(1)] as int64) <= 2 then 'DM'
            when line = 2 then 'CM'
            when line = array_length(digits) - 1 and cast(digits[offset(line - 1)] as int64) <= 3 then 'AM'
            else 'CM'
        end as expected_role
    from rows_with_lines
),

known_formations as (
    select *
    from unnest([
        struct('4-2-3-1' as team_formation, 2 as line, 'DM' as role),
        ('4-2-3-1', 3, 'AM'),
        ('4-4-2', 2, 'CM'),
        ('4-3-3', 2, 'CM'),
        ('3-5-2', 2, 'CM'),
        ('4-1-4-1', 2, 'DM'),
        ('4-1-4-1', 3, 'CM'),
        ('4-4-1-1', 2, 'CM'),
        ('4-4-1-1', 3, 'AM'),
        ('3-4-2-1', 2, 'CM'),
        ('3-4-2-1', 3, 'AM'),
        ('4-3-1-2', 2, 'CM'),
        ('4-3-1-2', 3, 'AM'),
        ('4-2-2-2', 2, 'DM'),
        ('4-2-2-2', 3, 'AM'),
        ('4-4-2', 1, 'DM'),
        ('4-4-2', 3, 'AM')
    ])
)

select
    e.fixture_sk,
    e.team_sk,
    e.player_sk,
    e.team_formation,
    e.line,
    e.midfield_role,
    e.expected_role,
    k.role as known_role
from expected as e
left join known_formations as k
    on e.team_formation = k.team_formation and e.line = k.line and e.is_midfield_slot
where
    e.midfield_role is distinct from e.expected_role
    or (k.role is not null and e.midfield_role is distinct from k.role)
