-- A published birth date under 13 years ago cannot be true.
select
    player_api_id,
    player_birth_date
from {{ ref('dim_player') }}
where player_birth_date > date_sub(current_date(), interval 13 year)
