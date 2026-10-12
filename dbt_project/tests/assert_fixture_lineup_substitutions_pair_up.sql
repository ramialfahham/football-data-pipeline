{#
  Every substitution in a confirmed or researched line-up of fct_fixture_lineup pairs two players
  of one match. Returns one row per broken line-up row:
  - starter_came_on: a starter with a minute on;
  - replaced_not_off: a substitute whose replaced player has no minute off, or a different one.
#}
{{ config(store_failures = true) }}

with lineups as (
    select * from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched')
)

select
    'starter_came_on' as problem,
    fixture_sk,
    team_sk,
    player_sk
from lineups
where is_starter and minute_on is not null

union all

select
    'replaced_not_off' as problem,
    came_on.fixture_sk,
    came_on.team_sk,
    came_on.player_sk
from lineups as came_on
left join lineups as went_off
    on
        came_on.fixture_sk = went_off.fixture_sk
        and came_on.replaced_player_sk = went_off.player_sk
where
    came_on.replaced_player_sk is not null
    and (
        went_off.minute_off is null
        or went_off.minute_off != came_on.minute_on
        or coalesce(went_off.minute_off_extra, 0) != coalesce(came_on.minute_on_extra, 0)
    )
