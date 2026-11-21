{#
  Fixed kick-offs in known zones render the local time and label a reader expects, in winter and
  summer, across a date change, in the southern hemisphere and in a zone with no conventional
  abbreviation. Returns the cases that do not.
#}

with cases as (
    select
        kickoff_datetime,
        time_zone,
        expected_local,
        expected_label
    from unnest([
        struct(
            timestamp '2026-12-05 19:30:00' as kickoff_datetime,
            'Europe/Berlin' as time_zone,
            datetime '2026-12-05 20:30:00' as expected_local,
            'CET' as expected_label
        ),
        struct(timestamp '2026-07-05 18:00:00', 'Europe/Berlin', datetime '2026-07-05 20:00:00', 'CEST'),
        struct(timestamp '2026-12-05 19:30:00', 'Europe/London', datetime '2026-12-05 19:30:00', 'GMT'),
        struct(timestamp '2026-07-05 19:00:00', 'Europe/London', datetime '2026-07-05 20:00:00', 'BST'),
        struct(timestamp '2026-12-05 19:30:00', 'Europe/Dublin', datetime '2026-12-05 19:30:00', 'GMT'),
        struct(timestamp '2026-07-05 19:00:00', 'Europe/Dublin', datetime '2026-07-05 20:00:00', 'IST'),
        struct(timestamp '2026-07-05 00:00:00', 'America/New_York', datetime '2026-07-04 20:00:00', 'EDT'),
        struct(timestamp '2026-12-05 01:00:00', 'America/New_York', datetime '2026-12-04 20:00:00', 'EST'),
        struct(timestamp '2026-07-05 03:00:00', 'America/Phoenix', datetime '2026-07-04 20:00:00', 'MST'),
        struct(timestamp '2026-11-21 17:00:00', 'Asia/Riyadh', datetime '2026-11-21 20:00:00', 'AST'),
        struct(timestamp '2026-12-05 09:00:00', 'Australia/Sydney', datetime '2026-12-05 20:00:00', 'AEDT'),
        struct(timestamp '2026-07-05 10:00:00', 'Australia/Sydney', datetime '2026-07-05 20:00:00', 'AEST'),
        struct(timestamp '2026-12-05 19:30:00', 'Europe/Istanbul', datetime '2026-12-05 22:30:00', 'UTC+3'),
        struct(timestamp '2026-07-05 19:30:00', 'America/Sao_Paulo', datetime '2026-07-05 16:30:00', 'BRT'),
        struct(timestamp '2026-07-05 19:30:00', 'UTC', datetime '2026-07-05 19:30:00', 'UTC')
    ])
),

year_starts as (
    select
        *,
        timestamp(date_trunc(date(kickoff_datetime), year)) as year_start,
        timestamp(date_add(date_trunc(date(kickoff_datetime), year), interval 6 month)) as year_middle
    from cases
),

offsets as (
    select
        *,
        {{ utc_offset_minutes('kickoff_datetime', 'time_zone') }} as offset_now,
        {{ utc_offset_minutes('year_start', 'time_zone') }} as offset_january,
        {{ utc_offset_minutes('year_middle', 'time_zone') }} as offset_july
    from year_starts
),

labelled as (
    select
        offsets.*,
        datetime(offsets.kickoff_datetime, offsets.time_zone) as kickoff_local,
        {{ kickoff_zone_label(
            'offsets.offset_now',
            'offsets.offset_january',
            'offsets.offset_july',
            'offsets.kickoff_datetime',
            'offsets.time_zone',
            'zones.label_standard',
            'zones.label_daylight'
        ) }} as kickoff_zone_label
    from offsets
    left join {{ ref('dim_timezone') }} as zones
        on offsets.time_zone = zones.time_zone
)

select *
from labelled
where
    kickoff_local != expected_local
    or kickoff_zone_label != expected_label
