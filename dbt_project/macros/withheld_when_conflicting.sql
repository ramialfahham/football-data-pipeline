{#
  A value whose tied records hold two real values is blank until a correction row settles it:
  null where the records conflict and no correction row exists, the value otherwise.
#}
{% macro withheld_when_conflicting(has_conflict, has_correction, value) -%}
if(({{ has_conflict }}) and not ({{ has_correction }}), null, {{ value }})
{%- endmacro %}
