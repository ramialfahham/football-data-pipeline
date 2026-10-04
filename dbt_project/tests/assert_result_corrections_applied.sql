-- Every hand correction of a result, from the two correction seeds, is applied, sourced and still
-- needed. One row per broken correction:
--   - not_applied: base has no such match or table row, or does not carry the official figures.
--   - winner_not_valid: a winner is set where the score already decides, or names a team not in
--     the match.
--   - not_sourced: a source that is not https URLs separated by a space, an official one with
--     none, or match reports with fewer than two sites.
--   - no_longer_needed: the provider now carries the official result itself.

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
                f.provider_goals_home = c.goals_home
                and f.provider_goals_away = c.goals_away
                and (not c.awarded or f.provider_status_short in ('AWD', 'WO'))
                and c.awarded_to_team_id is null
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
                s.standing_rank is distinct from c.standing_rank
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
                then 'no_longer_needed'
        end as problem
    from table_corrections as c
    left join standings as s
        on
            c.league_code = s.league_code
            and c.season = s.season
            and c.team_id = s.team_id
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
from source_checks
