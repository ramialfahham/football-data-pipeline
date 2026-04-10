select * from {{ ref('stg_fdorg__teams_bl1') }}
union all
select * from {{ ref('stg_fdorg__teams_pl') }}
union all
select * from {{ ref('stg_fdorg__teams_sa') }}
union all
select * from {{ ref('stg_fdorg__teams_pd') }}
union all
select * from {{ ref('stg_fdorg__teams_fl1') }}
