-- A side of an upcoming fixture shows at most one form window (docs/metrics_context_model.md section 4).
-- Fail a side that flags both its form row and its season-record row, and a side that has played the
-- fixture's competition this season but does not flag its form row.
{{ config(store_failures = true, severity = 'error') }}

with form as (
    select
        upcoming_fixture_sk,
        team_sk,
        is_form_window
    from {{ ref('mart_team_momentum') }}
),

season as (
    select
        upcoming_fixture_sk,
        team_sk,
        window_type,
        is_form_window
    from {{ ref('mart_team_season_record') }}
)

select
    f.is_form_window as form_flag,
    s.is_form_window as season_flag,
    s.window_type,
    coalesce(f.upcoming_fixture_sk, s.upcoming_fixture_sk) as upcoming_fixture_sk,
    coalesce(f.team_sk, s.team_sk) as team_sk
from form as f
full outer join season as s
    on f.upcoming_fixture_sk = s.upcoming_fixture_sk and f.team_sk = s.team_sk
where
    (coalesce(f.is_form_window, false) and coalesce(s.is_form_window, false))
    or (s.window_type = 'season_to_date' and f.team_sk is not null and not f.is_form_window)
