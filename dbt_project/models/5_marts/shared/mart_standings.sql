{#
  Generic standings mart — one approach for every competition that has standings.
  Serves two jobs:
    1. The competition's own table — league table (domestic_league, one section) or
       group tables (group stages of continental/world/qualifying, one section per
       group). Knockout/super/friendly competitions have no standings and are simply
       absent from fct_standings.
    2. A club's domestic-league standing as context on any club fixture — filter to
       competition_type = 'domestic_league' for one row per (club, season) = its
       home-league position.

  Every value is the league's official standings row (the provider's, except where corrected in
  base to the league's figures) — rank, points, W/D/L,
  goals scored and conceded, goal difference, form. The one computed value is the order of teams
  level on points: int_standings__official_rank puts them in the league's own tie-break order
  wherever our table equals the provider's. Nothing else is computed from fixtures: the official
  table carries deductions a recomputation cannot reproduce, so it is a fact from the source, like
  a match score. NO zones — the provider's zone annotation is
  carried verbatim in group_description and never interpreted.

  table_kind says what kind of table a section is (league, group, conference, split_round,
  ranking), resolved per league-season by int_standings__section_kinds from the section's name
  through the standings_table_kinds seed and from its teams, so that a
  page can render one table per group, drop the provider's cross-group ranking tables and head
  a split season's rounds — and never matches on a name itself. A name no seed pattern matches
  is the competition's own league table.

  league_code discriminates the competition and is not a BigQuery partition or cluster key;
  competition_type / entity_type come from dim_league. Lives in shared/
  because the output shape is uniform across competition types.

  Grain: (league_code, season_api_year, group_name, team_sk).
#}

with standings as (
    select * from {{ ref('int_standings__official_rank') }}
),

competitions as (
    select * from {{ ref('dim_league') }}
),

teams as (
    select
        team_sk,
        team_name,
        team_slug,
        team_logo_url
    from {{ ref('dim_team') }}
),

section_kinds as (
    select
        league_code,
        season_api_year,
        group_name,
        table_kind
    from {{ ref('int_standings__section_kinds') }}
)

select
    s.standing_sk,
    s.league_code,
    s.season_sk,
    s.season_api_year,
    s.group_name,
    reg.competition_type,
    reg.entity_type,
    s.team_sk,
    s.team_api_id,
    t.team_name,
    t.team_slug,
    t.team_logo_url,
    s.standing_rank,
    s.points,
    s.goals_scored,
    s.goals_conceded,
    s.goals_diff,
    s.form,
    s.played,
    s.wins,
    s.draws,
    s.losses,
    s.group_description,
    coalesce(k.table_kind, 'league') as table_kind
from standings as s
left join competitions as reg
    on s.league_code = reg.league_code
left join teams as t
    on s.team_sk = t.team_sk
left join section_kinds as k
    on
        s.league_code = k.league_code
        and s.season_api_year = k.season_api_year
        and s.group_name = k.group_name
