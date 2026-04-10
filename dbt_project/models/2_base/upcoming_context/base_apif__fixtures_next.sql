select * from {{ ref('stg_apif__fixtures_next_d1') }}
union all
select * from {{ ref('stg_apif__fixtures_next_e0') }}
union all
select * from {{ ref('stg_apif__fixtures_next_i1') }}
union all
select * from {{ ref('stg_apif__fixtures_next_sp1') }}
union all
select * from {{ ref('stg_apif__fixtures_next_f1') }}
