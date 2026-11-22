{#
  Hand-written provider errors run through the rules that withhold them, and the cases our own
  data must keep. Each rule is the macro the models call: withheld_when_conflicting. Returns each
  case whose answer differs from the hand-worked one: a provider error that is not caught is a
  value that would be shown, and a correct value that is caught is one withheld for nothing.
#}
{{ config(store_failures = true, severity = 'error') }}

with bio_records as (
    select *
    from unnest([
        struct(
            'two real values and no correction' as case_name, true as has_conflict,
            false as has_correction, 'Japan' as provider_value, cast(null as string) as expected_value
        ),
        struct('two real values with a correction', true, true, 'Japan', 'Japan'),
        struct('one real value', false, false, 'Japan', 'Japan')
    ])
),

bio_cases as (
    select
        'conflicting_bio: ' || case_name as test_case,
        true as expected,
        expected_value is not distinct from
        {{ withheld_when_conflicting('has_conflict', 'has_correction', 'provider_value') }} as actual
    from bio_records
),

all_cases as (
    select
        test_case,
        expected,
        actual
    from bio_cases
)

select
    test_case,
    expected,
    actual
from all_cases
where expected is distinct from actual
