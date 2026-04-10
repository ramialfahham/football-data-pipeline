select * from {{ ref('stg_fdorg__matches_scheduled_bl1') }}
union all
select * from {{ ref('stg_fdorg__matches_scheduled_pl') }}
union all
select * from {{ ref('stg_fdorg__matches_scheduled_sa') }}
union all
select * from {{ ref('stg_fdorg__matches_scheduled_pd') }}
union all
select * from {{ ref('stg_fdorg__matches_scheduled_fl1') }}
