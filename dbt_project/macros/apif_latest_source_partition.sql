{#-
  Read only the most recent snapshot row from an append-only raw reference table.

  WHY THIS MACRO EXISTS
  ---------------------
  Reference tables (fixtures, standings, teams, transfers, rounds, players, leagues)
  use append-only writes since issue #220. Each daily pipeline run appends one new
  complete snapshot row. BigQuery partitions the table by DATE(ingested_at).

  A staging model that reads the full table without a filter would see one row per
  day the pipeline has run, producing duplicate fixture_ids / team_ids / etc. and
  failing all uniqueness tests.

  This macro wraps a source() reference in a subquery that keeps only the row(s)
  from the most recent ingested_at value — i.e. yesterday's (or today's) run.

  USAGE — reference tables only
  ------------------------------
  Use this macro in the `src` CTE of every reference-table staging model:

      with src as (
          select *
          from {{ apif_latest_source_partition('api_football', 'raw_apif_fixtures_next') }}
      ),

  DO NOT use for fanout tables (lineups, fixture_events, fixture_statistics,
  fixture_players, predictions). Those tables accumulate rows across runs — each
  run adds only the newly fetched fixtures — so staging must union all partitions
  to see the complete dataset.
-#}
{% macro apif_latest_source_partition(source_name, table_name) -%}
(
    select *
    from {{ source(source_name, table_name) }}
    where ingested_at = (
        select max(ingested_at)
        from {{ source(source_name, table_name) }}
    )
)
{%- endmacro %}
