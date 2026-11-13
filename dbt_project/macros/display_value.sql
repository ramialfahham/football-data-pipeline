{#
  The value as a page shows it, given its catalogue format: a percentage to whole percent (kept as
  a share, 0.57 for 57%), a count as it is, any other number whole from 10 up and to one decimal
  below 10. Rounded half away from zero on the decimal value, so a rank and a page agree on it.
#}
{% macro display_value(value, format) -%}
    case
        when {{ format }} = 'percent' then cast(round(cast({{ value }} as numeric), 2) as float64)
        when {{ format }} = 'integer' then cast({{ value }} as float64)
        when abs(round(cast({{ value }} as numeric), 1)) >= 10
            then cast(round(cast({{ value }} as numeric), 0) as float64)
        else cast(round(cast({{ value }} as numeric), 1) as float64)
    end
{%- endmacro %}
