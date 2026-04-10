select * from {{ ref('stg_apif__lineups_d1') }}
union all
select * from {{ ref('stg_apif__lineups_e0') }}
union all
select * from {{ ref('stg_apif__lineups_i1') }}
union all
select * from {{ ref('stg_apif__lineups_sp1') }}
union all
select * from {{ ref('stg_apif__lineups_f1') }}
