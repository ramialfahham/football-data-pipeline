-- Named editions carry the season label their organiser publishes. One row per edition whose label
-- differs from the answer key or that dim_competition_season does not hold.

with answer_key as (
    select * from unnest([
        struct('J1' as league_code, 2026 as season_api_year, '2026' as expected_label),
        struct('J1', 2027, '2026/27'),
        struct('CCCU', 2017, '2016/17'),
        struct('CCCU', 2018, '2018'),
        struct('CCCU', 2026, '2026'),
        struct('AFCCL', 2016, '2016'),
        struct('AFCCL', 2021, '2021'),
        struct('AFCCL', 2022, '2022'),
        struct('AFCCL', 2023, '2023/24'),
        struct('UESC', 2025, '2025'),
        struct('UCL', 2025, '2025/26'),
        struct('BL1', 2025, '2025/26'),
        struct('MLS', 2026, '2026'),
        struct('CWC', 2025, '2025'),
        struct('AFCON', 2023, '2023')
    ])
),

seasons as (
    select
        league_code,
        season_api_year,
        season_label
    from {{ ref('dim_competition_season') }}
)

select
    k.league_code,
    k.season_api_year,
    k.expected_label,
    s.season_label
from answer_key as k
left join seasons as s
    on k.league_code = s.league_code and k.season_api_year = s.season_api_year
where s.season_label is distinct from k.expected_label
