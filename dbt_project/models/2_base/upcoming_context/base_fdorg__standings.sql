select * from {{ ref('stg_fdorg__standings_bl1') }}
union all
select * from {{ ref('stg_fdorg__standings_pl') }}
union all
select * from {{ ref('stg_fdorg__standings_sa') }}
union all
select * from {{ ref('stg_fdorg__standings_pd') }}
union all
select * from {{ ref('stg_fdorg__standings_fl1') }}
