-- The team's line in a match, cleaned once and named in our own words: one row per team with a
-- statistics line and per team of every finished match, so the goal split and the card zeros the
-- events prove are cleaned here for a team-match with no line too. docs/metric_layer.md holds the
-- rules; the pivot of the long-format staging rows is business reshaping and lives here too.
with stat_lines as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_id,
        stat_type,
        stat_value_raw
    from {{ ref('stg_apif__fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

pivoted as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_id,
        max(case when stat_type = 'Shots on Goal' then safe_cast(stat_value_raw as int64) end)
            as shots_on_target,
        max(case when stat_type = 'Shots off Goal' then safe_cast(stat_value_raw as int64) end)
            as shots_off_target,
        max(case when stat_type = 'Total Shots' then safe_cast(stat_value_raw as int64) end)
            as shots,
        max(case when stat_type = 'Blocked Shots' then safe_cast(stat_value_raw as int64) end)
            as shots_blocked,
        max(case when stat_type = 'Shots insidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_inside_box,
        max(case when stat_type = 'Shots outsidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_outside_box,
        max(case when stat_type = 'Fouls' then safe_cast(stat_value_raw as int64) end)
            as fouls,
        max(case when stat_type = 'Corner Kicks' then safe_cast(stat_value_raw as int64) end)
            as corners,
        max(case when stat_type = 'Offsides' then safe_cast(stat_value_raw as int64) end)
            as offsides,
        max(case
            when stat_type = 'Ball Possession'
                then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)
        end) as possession_pct,
        max(case when stat_type = 'Yellow Cards' then safe_cast(stat_value_raw as int64) end)
            as cards_yellow,
        max(case when stat_type = 'Red Cards' then safe_cast(stat_value_raw as int64) end)
            as cards_red,
        max(case when stat_type = 'Goalkeeper Saves' then safe_cast(stat_value_raw as int64) end)
            as saves,
        max(case when stat_type = 'Total passes' then safe_cast(stat_value_raw as int64) end)
            as passes,
        max(case when stat_type = 'Passes accurate' then safe_cast(stat_value_raw as int64) end)
            as passes_accurate
    from stat_lines
    group by league_code, raw_ingested_at, fixture_id, team_id
),

-- Fixture participants (home/away team ids), used to evaluate the reattribute_if_cohabiting
-- override condition below. base_apif__fixtures_next grain is one row per fixture_id. Only
-- fixtures whose two participants are BOTH known are kept, so the IN / NOT IN participant checks
-- in the reattribute join never hit the NOT IN (value, NULL) -> UNKNOWN trap (a fixture with a
-- missing participant id is a separate defect; the override conservatively does not fire there).
fixture_participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        home_team_id is not null
        and away_team_id is not null
),

-- Hand-curated corrections for known provider team-id defects, from
-- seeds/fixture_team_id_overrides.csv. `alias` = unconditional duplicate-id replacement (one club
-- under two provider ids); `reattribute_if_cohabiting` = replace only when the correct id is a
-- fixture participant and the wrong id is not (a mis-attribution between two DISTINCT clubs, so a
-- club's own legitimate statistics are never touched).
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode
    from {{ ref('fixture_team_id_overrides') }}
),

-- Corrected BEFORE the dedup below, not after: the dedup key contains team_id and the model
-- carries a uniqueness test on (league_code, fixture_id, team_id). Remapping afterwards would emit
-- two rows for one (fixture, team) whenever the correct id already has one of its own; remapping
-- first lets the latest-ingest-wins rule resolve that collision.
corrected as (
    select
        pivoted.* except (team_id),
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            pivoted.team_id
        ) as team_id
    from pivoted
    left join overrides as alias_override
        on
            pivoted.team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on pivoted.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            pivoted.team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
),

delivered as (
    select *
    from corrected
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
),

fixtures as (
    select
        fixture_id,
        league_code,
        goals_home,
        goals_away,
        raw_ingested_at,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id,
        status_short in ('FT', 'AET', 'PEN', 'AWD', 'WO')
        and goals_home is not null and goals_away is not null
        and home_team_id is not null and away_team_id is not null as is_finished
    from {{ ref('base_apif__fixtures_next') }}
),

finished_teams as (
    select
        league_code,
        fixture_id,
        home_team_id as team_id
    from fixtures
    where is_finished
    union all
    select
        league_code,
        fixture_id,
        away_team_id
    from fixtures
    where is_finished
),

team_matches as (
    select
        d.* except (league_code, fixture_id, team_id, raw_ingested_at),
        d.raw_ingested_at as line_ingested_at,
        coalesce(
            d.shots_on_target, d.shots_off_target, d.shots, d.shots_blocked, d.shots_inside_box,
            d.shots_outside_box, d.fouls, d.corners, d.offsides, d.possession_pct, d.cards_yellow,
            d.cards_red, d.saves, d.passes, d.passes_accurate
        ) is not null as has_stat_line,
        coalesce(d.league_code, ft.league_code) as league_code,
        coalesce(d.fixture_id, ft.fixture_id) as fixture_id,
        coalesce(d.team_id, ft.team_id) as team_id
    from delivered as d
    full outer join finished_teams as ft
        on d.fixture_id = ft.fixture_id and d.team_id = ft.team_id
),

-- The provider files an own goal under the team it counts for, and a shoot-out kick is no goal.
-- A card event of no colour, and a video review of a card, count against a zero of either colour
-- they could be; an upgrade or a cancelled red counts as red.
events as (
    select
        fixture_id,
        team_id,
        event_type,
        event_detail,
        raw_ingested_at,
        event_comments is not distinct from 'Penalty Shootout' as is_shootout
    from {{ ref('base_apif__fixture_events') }}
),

-- The events prove a zero only where they cover more than the goals: a match with at least one
-- substitution or card, which every played match has.
match_events as (
    select
        fixture_id,
        logical_or(event_type in ('subst', 'Card')) as events_delivered,
        max(raw_ingested_at) as events_ingested_at
    from events
    group by fixture_id
),

team_events as (
    select
        fixture_id,
        team_id,
        countif(not is_shootout and event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty', 'Own Goal'))
            as goal_events,
        countif(not is_shootout and event_type = 'Goal' and event_detail = 'Penalty') as penalty_goal_events,
        countif(not is_shootout and event_type = 'Goal' and event_detail = 'Own Goal') as own_goal_events,
        countif(not is_shootout and event_type = 'Goal' and event_detail = 'Missed Penalty') as missed_penalty_events,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Red Card')
            or (event_type = 'Var' and event_detail = 'Card reviewed')
        ) as events_against_no_yellow,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Yellow Card')
            or (
                event_type = 'Var'
                and (
                    starts_with(event_detail, 'Card upgrade')
                    or event_detail in ('Red card cancelled', 'Card reviewed')
                )
            )
        ) as events_against_no_red
    from events
    where team_id is not null
    group by fixture_id, team_id
),

in_context as (
    select
        t.*,
        o.shots_on_target as opponent_shots_on_target,
        o.shots_off_target as opponent_shots_off_target,
        o.shots as opponent_shots,
        o.shots_blocked as opponent_shots_blocked,
        o.shots_inside_box as opponent_shots_inside_box,
        o.shots_outside_box as opponent_shots_outside_box,
        o.fouls as opponent_fouls,
        o.corners as opponent_corners,
        o.offsides as opponent_offsides,
        o.cards_yellow as opponent_cards_yellow,
        o.cards_red as opponent_cards_red,
        o.saves as opponent_saves,
        o.passes as opponent_passes,
        o.passes_accurate as opponent_passes_accurate,
        coalesce(f.is_finished, false) as is_finished,
        if(t.team_id = f.home_team_id, f.goals_home, f.goals_away) as goals_for,
        if(t.team_id = f.home_team_id, f.goals_away, f.goals_home) as goals_conceded,
        coalesce(me.events_delivered, false) as events_delivered,
        coalesce(te.goal_events, 0) as goal_events,
        coalesce(te.penalty_goal_events, 0) as penalty_goal_events,
        coalesce(te.own_goal_events, 0) as own_goal_events,
        coalesce(te.events_against_no_yellow, 0) as events_against_no_yellow,
        coalesce(te.events_against_no_red, 0) as events_against_no_red,
        coalesce(oe.penalty_goal_events, 0) as opponent_penalty_goal_events,
        coalesce(oe.own_goal_events, 0) as opponent_own_goal_events,
        coalesce(oe.missed_penalty_events, 0) as opponent_missed_penalty_events,
        greatest(
            coalesce(t.line_ingested_at, timestamp('1970-01-01')),
            coalesce(o.raw_ingested_at, timestamp('1970-01-01')),
            coalesce(me.events_ingested_at, timestamp('1970-01-01')),
            coalesce(f.raw_ingested_at, timestamp('1970-01-01'))
        ) as raw_ingested_at
    from team_matches as t
    left join fixtures as f
        on t.fixture_id = f.fixture_id
    left join delivered as o
        on
            t.fixture_id = o.fixture_id
            and o.team_id = if(t.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    left join match_events as me
        on t.fixture_id = me.fixture_id
    left join team_events as te
        on t.fixture_id = te.fixture_id and t.team_id = te.team_id
    left join team_events as oe
        on
            t.fixture_id = oe.fixture_id
            and oe.team_id = if(t.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
),

-- 1. The blank rule: a blank count is a zero where the other team's line, as delivered, has a value
-- for the stat; a card where the match's events were delivered and none of them stands against that
-- zero; saves where the opponent had no shot on target. Every other blank stays blank, possession
-- always: it is a share, not a count.
-- 2. The goal split: penalty and own goals are the team's goal events where the match's events
-- were delivered and they add up to its score, 0 where it scored none, blank otherwise.
filled as (
    select
        *,
        coalesce(shots_on_target, if(opponent_shots_on_target is not null, 0, null)) as shots_on_target_filled,
        coalesce(shots_off_target, if(opponent_shots_off_target is not null, 0, null)) as shots_off_target_filled,
        coalesce(shots, if(opponent_shots is not null, 0, null)) as shots_filled,
        coalesce(shots_blocked, if(opponent_shots_blocked is not null, 0, null)) as shots_blocked_filled,
        coalesce(shots_inside_box, if(opponent_shots_inside_box is not null, 0, null)) as shots_inside_box_filled,
        coalesce(shots_outside_box, if(opponent_shots_outside_box is not null, 0, null)) as shots_outside_box_filled,
        coalesce(fouls, if(opponent_fouls is not null, 0, null)) as fouls_filled,
        coalesce(corners, if(opponent_corners is not null, 0, null)) as corners_filled,
        coalesce(offsides, if(opponent_offsides is not null, 0, null)) as offsides_filled,
        coalesce(
            cards_yellow,
            if(opponent_cards_yellow is not null or (events_delivered and events_against_no_yellow = 0), 0, null)
        ) as cards_yellow_filled,
        coalesce(
            cards_red,
            if(opponent_cards_red is not null or (events_delivered and events_against_no_red = 0), 0, null)
        ) as cards_red_filled,
        coalesce(
            saves,
            if(
                opponent_saves is not null
                or coalesce(opponent_shots_on_target, if(shots_on_target is not null, 0, null)) = 0,
                0,
                null
            )
        ) as saves_filled,
        coalesce(passes, if(opponent_passes is not null, 0, null)) as passes_filled,
        coalesce(passes_accurate, if(opponent_passes_accurate is not null, 0, null)) as passes_accurate_filled,
        coalesce(opponent_shots_on_target, if(shots_on_target is not null, 0, null))
            as opponent_shots_on_target_filled,
        coalesce(opponent_shots, if(shots is not null, 0, null)) as opponent_shots_filled,
        case
            when not is_finished then null
            when goals_for = 0 then 0
            when events_delivered and goal_events = goals_for then penalty_goal_events
        end as goals_penalty,
        case
            when not is_finished then null
            when goals_for = 0 then 0
            when events_delivered and goal_events = goals_for then own_goal_events
        end as goals_own
    from in_context
),

-- 3. Against the results: shots on target are at least the open-play goals, and shots at least
-- both. The opponent's shots on target (plus the penalties it missed, which a
-- keeper can save) cap the saves only when that figure passes its own check: at least the
-- opponent's open-play goals, at most its shots. Only a gap of at most 2 is corrected; a larger
-- one leaves the stat blank.
against_results as (
    select
        *,
        case
            when shots_on_target_filled is null or goals_penalty is null or goals_own is null
                then shots_on_target_filled
            when goals_for - goals_penalty - goals_own <= shots_on_target_filled then shots_on_target_filled
            when goals_for - goals_penalty - goals_own - shots_on_target_filled <= 2
                then goals_for - goals_penalty - goals_own
        end as shots_on_target_clean,
        opponent_shots_on_target_filled is not null
        and opponent_shots_on_target_filled
        >= goals_conceded - opponent_penalty_goal_events - opponent_own_goal_events
        and (opponent_shots_filled is null or opponent_shots_on_target_filled <= opponent_shots_filled)
            as opponent_shots_on_target_verified,
        opponent_shots_on_target_filled + opponent_missed_penalty_events as saves_ceiling
    from filled
),

-- Shots are at least the shots on target and at least the open-play goals, each where known: a
-- shots figure is checked against the result even when the shots on target were left blank.
shots_floors as (
    select
        *,
        greatest(coalesce(shots_on_target_clean, 0), coalesce(goals_for - goals_penalty - goals_own, 0))
            as shots_floor
    from against_results
),

checked as (
    select
        *,
        case
            when shots_filled is null then shots_filled
            when shots_filled >= shots_floor then shots_filled
            when shots_floor - shots_filled <= 2 then shots_floor
        end as shots_clean,
        case
            when saves_filled is null or saves_ceiling is null or saves_filled <= saves_ceiling then saves_filled
            when not coalesce(opponent_shots_on_target_verified, false) then null
            when saves_filled - saves_ceiling <= 2 then saves_ceiling
        end as saves_clean,
        case
            when passes_accurate_filled is null or passes_filled is null then passes_accurate_filled
            when passes_accurate_filled <= passes_filled then passes_accurate_filled
            when passes_accurate_filled - passes_filled <= 2 then passes_filled
        end as passes_accurate_clean
    from shots_floors
),

-- 4. A part never above its whole, and a split of shots that does not add up to the total leaves
-- that split blank, apart from shots on target, which its own check vouches for. Where the inside
-- and outside the box exceed the total by exactly the own goals credited to the team, the provider
-- counted each own goal as a shot of the team's (its convention up to 2018): inside the box, where
-- an own goal is scored, loses them.
own_goals_in_split as (
    select
        *,
        coalesce(
            goals_own between 1 and 2
            and shots_inside_box_filled >= goals_own
            and shots_inside_box_filled + coalesce(shots_outside_box_filled, 0) - shots_clean = goals_own,
            false
        ) as own_goals_counted_as_shots
    from checked
),

against_whole as (
    select
        *,
        case
            when shots_inside_box_filled is null or shots_clean is null then shots_inside_box_filled
            when own_goals_counted_as_shots then shots_inside_box_filled - goals_own
            when shots_inside_box_filled <= shots_clean then shots_inside_box_filled
            when shots_inside_box_filled - shots_clean <= 2 then shots_clean
        end as shots_inside_box_limited
    from own_goals_in_split
),

splits as (
    select
        *,
        coalesce(shots_on_target_clean + shots_off_target_filled + shots_blocked_filled != shots_clean, false)
            as on_off_blocked_split_fails,
        coalesce(shots_inside_box_limited + shots_outside_box_filled != shots_clean, false)
            as inside_outside_split_fails
    from against_whole
),

cleaned as (
    select
        *,
        if(on_off_blocked_split_fails, null, shots_off_target_filled) as shots_off_target_clean,
        if(on_off_blocked_split_fails, null, shots_blocked_filled) as shots_blocked_clean,
        if(inside_outside_split_fails, null, shots_inside_box_limited) as shots_inside_box_clean,
        if(inside_outside_split_fails, null, shots_outside_box_filled) as shots_outside_box_clean
    from splits
)

select
    league_code,
    fixture_id,
    team_id,
    has_stat_line,
    shots_on_target_clean as shots_on_target,
    shots_off_target_clean as shots_off_target,
    shots_clean as shots,
    shots_blocked_clean as shots_blocked,
    shots_inside_box_clean as shots_inside_box,
    shots_outside_box_clean as shots_outside_box,
    fouls_filled as fouls,
    corners_filled as corners,
    offsides_filled as offsides,
    possession_pct,
    cards_yellow_filled as cards_yellow,
    cards_red_filled as cards_red,
    saves_clean as saves,
    passes_filled as passes,
    passes_accurate_clean as passes_accurate,
    goals_penalty,
    goals_own,
    raw_ingested_at,
    array(
        select correction
        from
            unnest([
                struct(
                    'shots_on_target' as stat,
                    shots_on_target as provider_value,
                    shots_on_target_clean as cleaned_value,
                    if(
                        shots_on_target_clean is distinct from shots_on_target_filled,
                        'raised_to_open_play_goals',
                        null
                    ) as rule
                ),
                struct(
                    'shots', shots, shots_clean,
                    case
                        when shots_clean is not distinct from shots_filled then null
                        when
                            coalesce(goals_for - goals_penalty - goals_own, 0) > coalesce(shots_on_target_clean, 0)
                            then 'raised_to_open_play_goals'
                        else 'raised_to_shots_on_target'
                    end
                ),
                struct(
                    'saves', saves, saves_clean,
                    case
                        when saves_clean is not distinct from saves_filled then null
                        when
                            coalesce(opponent_shots_on_target_verified, false)
                            then 'limited_to_opponent_shots_on_target'
                        else 'opponent_shots_on_target_unverified'
                    end
                ),
                struct(
                    'passes_accurate', passes_accurate, passes_accurate_clean,
                    if(passes_accurate_clean is distinct from passes_accurate_filled, 'limited_to_whole', null)
                ),
                struct(
                    'shots_inside_box', shots_inside_box, shots_inside_box_clean,
                    case
                        when shots_inside_box_clean is not distinct from shots_inside_box_filled then null
                        when inside_outside_split_fails then 'split_does_not_add_up'
                        when own_goals_counted_as_shots then 'own_goals_left_out'
                        else 'limited_to_whole'
                    end
                ),
                struct(
                    'shots_outside_box', shots_outside_box, shots_outside_box_clean,
                    if(
                        shots_outside_box_clean is distinct from shots_outside_box_filled,
                        'split_does_not_add_up',
                        null
                    )
                ),
                struct(
                    'shots_off_target', shots_off_target, shots_off_target_clean,
                    if(
                        shots_off_target_clean is distinct from shots_off_target_filled,
                        'split_does_not_add_up',
                        null
                    )
                ),
                struct(
                    'shots_blocked', shots_blocked, shots_blocked_clean,
                    if(shots_blocked_clean is distinct from shots_blocked_filled, 'split_does_not_add_up', null)
                )
            ]) as correction
        where correction.rule is not null
    ) as stat_corrections
from cleaned
