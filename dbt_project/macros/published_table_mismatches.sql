{#
  The teams whose rebuilt table differs from a table the provider published, among the teams that are
  not withheld. A team-season withheld against the standings (int_team_season__metrics) is left out.
  Every other team is a mismatch where its rebuilt points differ from its published points, or its
  rebuilt place differs from its published place.

  The places are compared within one published section (league_code, season_api_year, group_name,
  ingested_at). A team's place on a side is its rank on that side, less the number of withheld teams
  of the section ranked above it on that side. That is the rank itself when no team is withheld, so a
  place error is red next to a team with no rebuilt place or a place the league's rule does not fix.
  A withheld team's points cannot move the places of the others: they all move up by one on the side
  where the withheld team was ranked above them. A team with no published rank or no rebuilt rank, and
  a team whose place the league's rule does not fix, stays in the section and is left out of the place
  comparison.

  compared: a relation with league_code, season_api_year, group_name, ingested_at, team_sk,
      published_rank, rebuilt_rank, published_points, rebuilt_points, is_place_not_compared,
      is_comparable and is_withheld, one row per team of a published section.
  Returns a select with the section, the team, and the two places and the two points.
#}
{% macro published_table_mismatches(compared) -%}
    with section_teams as (
        select * from {{ compared }}
        where is_comparable
    ),

    place_counted as (
        select
            t.league_code,
            t.season_api_year,
            t.group_name,
            t.ingested_at,
            t.team_sk,
            t.published_rank,
            t.rebuilt_rank,
            t.published_points,
            t.rebuilt_points,
            t.is_place_not_compared,
            t.is_withheld,
            t.published_rank - countif(w.team_sk is not null and w.published_rank < t.published_rank) as published_place,
            t.rebuilt_rank - countif(w.team_sk is not null and w.rebuilt_rank < t.rebuilt_rank) as rebuilt_place
        from section_teams as t
        left join section_teams as w
            on
                t.league_code = w.league_code
                and t.season_api_year = w.season_api_year
                and t.group_name = w.group_name
                and t.ingested_at = w.ingested_at
                and w.is_withheld
        group by
            t.league_code,
            t.season_api_year,
            t.group_name,
            t.ingested_at,
            t.team_sk,
            t.published_rank,
            t.rebuilt_rank,
            t.published_points,
            t.rebuilt_points,
            t.is_place_not_compared,
            t.is_withheld
    )

    select
        league_code,
        season_api_year,
        group_name,
        ingested_at,
        team_sk,
        published_rank,
        rebuilt_rank,
        published_points,
        rebuilt_points
    from place_counted
    where
        not is_withheld
        and published_place != rebuilt_place
        and not is_place_not_compared
    union distinct
    select
        league_code,
        season_api_year,
        group_name,
        ingested_at,
        team_sk,
        published_rank,
        rebuilt_rank,
        published_points,
        rebuilt_points
    from section_teams
    where not is_withheld and rebuilt_points != published_points
{%- endmacro %}
