{#-
  Raw tables store the full API envelope (or batched wrapper) as one JSON column ``payload``.

  Expand ``$.response`` into an array of STRINGs suitable for ``json_value(..., '$.path')``:
  scalar JSON values use ``json_value``; objects/arrays use ``to_json_string`` so downstream
  can ``safe.parse_json`` / ``json_value`` as today.
-#}
{% macro apif_payload_response_json_strings(table_alias) %}
ifnull(
    (
        select array_agg(coalesce(json_value(resp_el, '$'), to_json_string(resp_el)))
        from unnest(ifnull(json_query_array({{ table_alias }}.payload, '$.response'), [])) as resp_el
    ),
    []
)
{% endmacro %}
