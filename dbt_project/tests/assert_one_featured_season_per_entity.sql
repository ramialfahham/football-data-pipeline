{#
  #846 acceptance criterion 4: "If the rule ever breaks, a test catches it before a reader does.
  Every team and every player has exactly one opening season, never none and never two."

  `is_featured_season` marks the season an entity's page opens on. It is a row_number() = 1 over a
  partition, so it cannot produce two by construction — but it CAN produce none if the ordering
  expression ever sees only NULLs it cannot rank, or if a join drops the column's inputs. Both
  halves are asserted here because the criterion names both, and because a zero-featured entity is
  the silent failure: the page would fall back to nothing rather than to the wrong season.

  Covers both marts in one test: the rule is one rule, so a single failure surface keeps them from
  drifting apart, which is the whole point of #846.
#}
{{ config(store_failures = true) }}

with team_counts as (
    select
        'team' as entity_kind,
        cast(team_sk as string) as entity_id,
        countif(is_featured_season) as featured_seasons
    from {{ ref('mart_team_profile') }}
    group by team_sk
),

player_counts as (
    select
        'player' as entity_kind,
        cast(player_sk as string) as entity_id,
        countif(is_featured_season) as featured_seasons
    from {{ ref('mart_player_profile') }}
    group by player_sk
),

combined as (
    select
        entity_kind,
        entity_id,
        featured_seasons
    from team_counts
    union all
    select
        entity_kind,
        entity_id,
        featured_seasons
    from player_counts
)

select
    entity_kind,
    entity_id,
    featured_seasons
from combined
where featured_seasons != 1
