{#
    Persist standings history as SCD Type 2. The API only returns "current"
    standings; this snapshot captures the values we observe at each dbt
    snapshot run so we can reconstruct the table at any date going forward.

    Downstream ``fct_standings`` selects ``where dbt_valid_to is null`` for the
    current snapshot. Historical analysis queries this snapshot directly.
#}

{% snapshot snap_apif_d1_standings %}

{{
    config(
        unique_key='standing_key',
        strategy='check',
        check_cols=[
            'standing_rank',
            'points',
            'goals_diff',
            'form',
            'played_all',
            'wins_all',
            'draws_all',
            'losses_all'
        ],
        invalidate_hard_deletes=False
    )
}}

select
    {{ dbt_utils.generate_surrogate_key([
        'league_code', 'season', 'team_id', 'group_description'
    ]) }} as standing_key,
    league_code,
    league_api_id,
    league_name,
    season,
    team_id,
    team_name,
    group_description,
    standing_rank,
    points,
    goals_diff,
    form,
    played_all,
    wins_all,
    draws_all,
    losses_all,
    raw_ingested_at
from {{ ref('stg_apif__bl1_standings') }}

{% endsnapshot %}
