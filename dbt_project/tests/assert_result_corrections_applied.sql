-- Every hand correction of a result, from the three correction seeds, is applied, sourced and still
-- needed. One row per broken correction:
--   - not_applied: base has no such match or table row, or does not carry the official figures
--     and team.
--   - winner_not_valid: a winner is set where the score already decides, or names a team not in
--     the match.
--   - award_not_valid: an award without its kind or a kind without an award, a played or
--     abandoned award without the score on the pitch, or a score on the pitch on any other row.
--   - not_sourced: a source that is not https URLs separated by a space, an official one with
--     none, or match reports with fewer than two sites.
--   - does_not_add_up: a match's corrected goals do not add up to its score side by side (the
--     score on the pitch for a played or abandoned award), name a team not in the match, or sit
--     beside the row that says the match had no goal.
--   - no_longer_needed: the provider now carries the official result, or goals that add up, itself.
--     An award is always needed: the provider never says how it came about.

{{ config(store_failures = true) }}

with fixture_corrections as (
    select * from {{ ref('fixture_result_corrections') }}
),

fixtures as (
    select * from {{ ref('base_apif__fixtures_next') }}
),

table_corrections as (
    select * from {{ ref('standings_corrections') }}
),

standings as (
    select * from {{ ref('base_apif__standings') }}
),

goal_corrections as (
    select * from {{ ref('fixture_goal_corrections') }}
),

events as (
    select * from {{ ref('base_apif__fixture_events') }}
),

goal_counts as (
    select
        c.fixture_id,
        countif(c.goal_order > 0) as seed_goals,
        countif(c.goal_order = 0) > 0 and count(*) > 1 as no_goal_row_with_goals,
        countif(c.goal_order > 0 and c.team_id = f.home_team_id) as seed_home,
        countif(c.goal_order > 0 and c.team_id = f.away_team_id) as seed_away,
        any_value(if(f.award_kind in ('played', 'abandoned'), f.on_pitch_home, f.goals_home)) as score_home,
        any_value(if(f.award_kind in ('played', 'abandoned'), f.on_pitch_away, f.goals_away)) as score_away
    from goal_corrections as c
    left join fixtures as f
        on c.fixture_id = f.fixture_id
    group by c.fixture_id
),

event_counts as (
    select
        e.fixture_id,
        countif(e.is_goal and e.goal_correction_source is not null) as applied_goals,
        countif(e.is_goal and e.goal_correction_source is null) as provider_goals_counted,
        countif(e.is_provider_goal and e.team_id = f.home_team_id) as provider_home,
        countif(e.is_provider_goal and e.team_id = f.away_team_id) as provider_away
    from events as e
    inner join goal_counts as g
        on e.fixture_id = g.fixture_id
    inner join fixtures as f
        on e.fixture_id = f.fixture_id
    group by e.fixture_id
),

goal_checks as (
    select
        'fixture_goal_corrections' as seed,
        cast(g.fixture_id as string) as correction,
        case
            when
                coalesce(e.applied_goals, 0) != g.seed_goals
                or coalesce(e.provider_goals_counted, 0) != 0
                then 'not_applied'
            when
                g.no_goal_row_with_goals
                or g.seed_goals != g.seed_home + g.seed_away
                or g.seed_home is distinct from g.score_home
                or g.seed_away is distinct from g.score_away
                then 'does_not_add_up'
            when
                e.provider_home = g.score_home
                and e.provider_away = g.score_away
                then 'no_longer_needed'
        end as problem
    from goal_counts as g
    left join event_counts as e
        on g.fixture_id = e.fixture_id
),

fixture_checks as (
    select
        'fixture_result_corrections' as seed,
        cast(c.fixture_id as string) as correction,
        case
            when f.fixture_id is null then 'not_applied'
            when
                f.goals_home is distinct from c.goals_home
                or f.goals_away is distinct from c.goals_away
                or f.status_short is distinct from if(c.awarded, 'AWD', f.provider_status_short)
                or f.awarded_to_team_id is distinct from c.awarded_to_team_id
                then 'not_applied'
            when
                c.awarded_to_team_id is not null
                and (
                    not c.awarded
                    or c.goals_home != c.goals_away
                    or c.awarded_to_team_id not in (f.home_team_id, f.away_team_id)
                )
                then 'winner_not_valid'
            when
                c.awarded is distinct from (c.award_kind is not null)
                or (
                    c.award_kind in ('played', 'abandoned')
                    and (c.on_pitch_home is null or c.on_pitch_away is null)
                )
                or (
                    coalesce(c.award_kind, '') not in ('played', 'abandoned')
                    and (c.on_pitch_home is not null or c.on_pitch_away is not null)
                )
                then 'award_not_valid'
            when
                f.provider_goals_home = c.goals_home
                and f.provider_goals_away = c.goals_away
                and not c.awarded
                then 'no_longer_needed'
        end as problem
    from fixture_corrections as c
    left join fixtures as f
        on c.fixture_id = f.fixture_id
),

table_checks as (
    select
        'standings_corrections' as seed,
        concat(c.league_code, ' ', cast(c.season as string), ' ', cast(c.team_id as string), ' ', c.group_name)
            as correction,
        case
            when s.team_id is null then 'not_applied'
            when
                s.team_id != coalesce(c.official_team_id, c.team_id)
                or s.standing_rank is distinct from c.standing_rank
                or s.points is distinct from c.points
                or s.played_all is distinct from c.played
                or s.wins_all is distinct from c.wins
                or s.draws_all is distinct from c.draws
                or s.losses_all is distinct from c.losses
                or s.goals_for_all is distinct from c.goals_for
                or s.goals_against_all is distinct from c.goals_against
                or s.goals_diff is distinct from c.goals_for - c.goals_against
                then 'not_applied'
            when
                s.provider_standing_rank = c.standing_rank
                and s.provider_points = c.points
                and s.provider_played_all = c.played
                and s.provider_wins_all = c.wins
                and s.provider_draws_all = c.draws
                and s.provider_losses_all = c.losses
                and s.provider_goals_for_all = c.goals_for
                and s.provider_goals_against_all = c.goals_against
                and s.team_id = s.provider_team_id
                then 'no_longer_needed'
        end as problem
    from table_corrections as c
    left join standings as s
        on
            c.league_code = s.league_code
            and c.season = s.season
            and c.team_id = s.provider_team_id
            and c.group_name = s.group_name
),

sources as (
    select
        'fixture_result_corrections' as seed,
        cast(fixture_id as string) as correction,
        source_kind,
        source
    from fixture_corrections
    union all
    select
        'standings_corrections' as seed,
        concat(league_code, ' ', cast(season as string), ' ', cast(team_id as string), ' ', group_name)
            as correction,
        source_kind,
        source
    from table_corrections
    union all
    select
        'fixture_goal_corrections' as seed,
        concat(cast(fixture_id as string), ' ', cast(goal_order as string)) as correction,
        source_kind,
        source
    from goal_corrections
),

source_urls as (
    select
        s.seed,
        s.correction,
        s.source_kind,
        countif(u != '' and not regexp_contains(u, r'^https://[^/\s]+/\S*$')) as not_urls,
        count(distinct regexp_extract(u, r'^https://([^/\s]+)')) as sites
    from sources as s
    left join unnest(split(trim(coalesce(s.source, '')), ' ')) as u
        on true
    group by s.seed, s.correction, s.source_kind
),

source_checks as (
    select
        seed,
        correction,
        'not_sourced' as problem
    from source_urls
    where
        not_urls > 0
        or sites = 0
        or (source_kind = 'match_reports' and sites < 2)
        or source_kind is null
        or source_kind not in ('official', 'match_reports')
)

select
    seed,
    correction,
    problem
from fixture_checks
where problem is not null
union all
select
    seed,
    correction,
    problem
from table_checks
where problem is not null
union all
select
    seed,
    correction,
    problem
from goal_checks
where problem is not null
union all
select
    seed,
    correction,
    problem
from source_checks
