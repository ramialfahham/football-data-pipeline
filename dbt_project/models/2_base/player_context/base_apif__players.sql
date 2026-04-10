select * from {{ ref('stg_apif__players_d1') }}
union all
select * from {{ ref('stg_apif__players_e0') }}
union all
select * from {{ ref('stg_apif__players_i1') }}
union all
select * from {{ ref('stg_apif__players_sp1') }}
union all
select * from {{ ref('stg_apif__players_f1') }}
