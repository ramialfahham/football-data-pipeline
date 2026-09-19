-- Every row of mart_competition_fixtures links both teams by the slug dim_team publishes, and the
-- fixture slug is composed of exactly those two slugs and the kick-off date. A team missing from
-- dim_team, a slug carried from anywhere but the dim, or a fixture slug built by another rule
-- fails here; the frontend links only what resolves.
--
-- Returns a row (= fails) per fixture whose team slugs or fixture slug do not resolve.
{{ config(store_failures = true) }}

with dim as (
    select
        team_sk,
        team_slug
    from {{ ref('dim_team') }}
),

served as (
    select
        fixture_sk,
        fixture_date,
        home_team_sk,
        away_team_sk,
        home_team_slug,
        away_team_slug,
        fixture_slug
    from {{ ref('mart_competition_fixtures') }}
)

select
    s.fixture_sk,
    s.home_team_sk,
    s.away_team_sk,
    s.home_team_slug,
    s.away_team_slug,
    s.fixture_slug,
    h.team_slug as expected_home_slug,
    a.team_slug as expected_away_slug
from served as s
left join dim as h
    on s.home_team_sk = h.team_sk
left join dim as a
    on s.away_team_sk = a.team_sk
where
    h.team_slug is null
    or a.team_slug is null
    or s.home_team_slug is distinct from h.team_slug
    or s.away_team_slug is distinct from a.team_slug
    or s.fixture_slug is distinct from concat(
        format_date('%Y-%m-%d', s.fixture_date), '-', h.team_slug, '-vs-', a.team_slug
    )
