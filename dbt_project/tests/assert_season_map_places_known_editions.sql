{#
  Known placings a fan can check: which editions a league season holds and which it must not.
  Returns each case the windows get wrong.
#}
{{ config(store_failures = true, severity = 'error') }}

with cases as (
    select
        anchor_league,
        anchor_year,
        window_type,
        member_league,
        member_year,
        expected
    from unnest([
        struct(
            'BL1' as anchor_league, 2025 as anchor_year, 'this_season' as window_type,
            'UCL' as member_league, 2025 as member_year, true as expected
        ),
        ('BL1', 2025, 'this_season', 'UESC', 2025, true),
        ('BL1', 2025, 'this_season', 'CWC', 2025, false),
        ('BL1', 2024, 'this_season', 'CWC', 2025, true),
        ('BL1', 2026, 'last_season', 'DFBP', 2025, true),
        ('VL', 2026, 'this_season', 'UECL', 2026, true),
        ('VL', 2026, 'this_season', 'UECL', 2025, false),
        ('VL', 2026, 'last_season', 'UECL', 2025, true),
        ('LMX', 2025, 'this_season', 'CCCU', 2026, true),
        ('MLS', 2026, 'this_season', 'CCCU', 2026, true),
        ('KL1', 2025, 'this_season', 'AFCCL', 2025, true),
        ('KL1', 2026, 'this_season', 'AFCCL', 2025, false),
        ('J1', 2027, 'this_season', 'AFCCL', 2026, true),
        ('J1', 2027, 'last_season', 'J1', 2026, true)
    ])
),

seasons as (
    select
        season_sk,
        league_code,
        season_api_year
    from {{ ref('dim_competition_season') }}
),

found as (
    select
        c.*,
        w.season_sk is not null as is_member
    from cases as c
    left join seasons as a
        on c.anchor_league = a.league_code and c.anchor_year = a.season_api_year
    left join seasons as m
        on c.member_league = m.league_code and c.member_year = m.season_api_year
    left join {{ ref('int_competition_season__club_windows') }} as w
        on
            a.season_sk = w.anchor_season_sk
            and m.season_sk = w.season_sk
            and c.window_type = w.window_type
)

select *
from found
where is_member != expected
