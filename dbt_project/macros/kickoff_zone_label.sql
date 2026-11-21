{#
  The label a kick-off prints beside its local time. BigQuery names a zone only by its offset
  (`UTC+2`), never `CEST`, so dim_timezone carries the conventional abbreviation for standard and
  daylight time where one exists. Daylight time is the offset at the kick-off being above the
  zone's lowest offset of that calendar year; a zone with no conventional abbreviation prints
  BigQuery's own `UTC+N`.

  The three offsets are columns the caller computes with utc_offset_minutes, so each stays a short
  expression the SQL linter can parse.
#}
{%- macro utc_offset_minutes(ts, zone) -%}
datetime_diff(datetime({{ ts }}, {{ zone }}), datetime({{ ts }}), minute)
{%- endmacro %}

{%- macro kickoff_zone_label(offset_now, offset_jan, offset_jul, ts, zone, label_standard, label_daylight) -%}
case
    when {{ offset_now }} > least({{ offset_jan }}, {{ offset_jul }})
        then coalesce({{ label_daylight }}, format_timestamp('%Z', {{ ts }}, {{ zone }}))
    else coalesce({{ label_standard }}, format_timestamp('%Z', {{ ts }}, {{ zone }}))
end
{%- endmacro %}
