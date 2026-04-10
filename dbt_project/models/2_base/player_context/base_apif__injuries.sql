select * from {{ ref('stg_apif__injuries_d1') }}
union all
select * from {{ ref('stg_apif__injuries_e0') }}
union all
select * from {{ ref('stg_apif__injuries_i1') }}
union all
select * from {{ ref('stg_apif__injuries_sp1') }}
union all
select * from {{ ref('stg_apif__injuries_f1') }}
