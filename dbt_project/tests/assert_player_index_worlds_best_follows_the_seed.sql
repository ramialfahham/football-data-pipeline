-- mart_player_index's World's best against player_award_results: the nominees with a Player page
-- of each award's latest edition, the Yashin Trophy ones in the GK list and the Ballon d'Or ones
-- who are not goalkeepers in their position's list, none missing and none extra; inside a list,
-- 1 to n by club_order, then placing. Returns every nominee that differs or is out of order, a
-- Ballon d'Or nominee with a page and no position, and a list with a gap.

with pages as (
    select distinct
        player_sk,
        position_group
    from {{ ref('mart_player_profile') }}
    where has_player_page and is_featured_season
),

seed_rows as (
    select
        award,
        edition_year,
        placing,
        player_api_id as player_sk
    from {{ ref('player_award_results') }}
),

latest as (
    select
        award,
        max(edition_year) as edition_year
    from seed_rows
    group by award
),

expected as (
    select
        s.player_sk,
        s.award,
        s.edition_year,
        s.placing,
        if(s.award = 'yashin_trophy', 'GK', p.position_group) as list
    from seed_rows as s
    inner join latest as l
        on s.award = l.award and s.edition_year = l.edition_year
    inner join pages as p
        on s.player_sk = p.player_sk
    where s.award = 'yashin_trophy' or p.position_group != 'GK'
),

served as (
    select
        player_sk,
        award,
        award_edition_year,
        award_placing,
        worlds_best_list,
        worlds_best_order,
        club_order
    from {{ ref('mart_player_index') }}
    where worlds_best_list is not null
),

pairs as (
    select
        *,
        lag(club_order) over by_order as prev_club_order,
        lag(award_placing) over by_order as prev_placing,
        lag(worlds_best_order) over by_order as prev_order
    from served
    window by_order as (partition by worlds_best_list order by worlds_best_order)
)

select
    coalesce(e.player_sk, s.player_sk) as player_sk,
    'differs from the seed' as failure
from expected as e
full outer join served as s
    on e.player_sk = s.player_sk
where
    e.player_sk is null
    or s.player_sk is null
    or e.award != s.award
    or e.edition_year != s.award_edition_year
    or e.placing is distinct from s.award_placing
    or e.list != s.worlds_best_list

union all

select
    player_sk,
    'placed after a nominee he should follow' as failure
from pairs
where
    (prev_order is not null and prev_club_order is null and club_order is not null)
    or prev_club_order > club_order
    or (
        prev_club_order is not distinct from club_order
        and (
            (prev_placing is null and award_placing is not null)
            or prev_placing > award_placing
        )
    )

union all

select
    s.player_sk,
    'a ballon_dor nominee with a page has no position' as failure
from seed_rows as s
inner join latest as l
    on s.award = l.award and s.edition_year = l.edition_year
inner join pages as p
    on s.player_sk = p.player_sk
where s.award = 'ballon_dor' and p.position_group is null

union all

select
    cast(null as int64) as player_sk,
    'worlds_best_order is not 1 to n' as failure
from served
group by worlds_best_list
having max(worlds_best_order) != count(*) or min(worlds_best_order) != 1
