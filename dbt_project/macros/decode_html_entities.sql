{#
  The provider sends some names HTML-escaped. The text is cut into entities and the runs between
  them, and each entity in the map becomes its character, so a double-escaped `&amp;apos;` becomes
  `&apos;` and nothing is decoded twice. An entity the map lacks stays as it is, for
  assert_names_carry_no_html_entity to find. The empty match at the end keeps an empty string empty.
#}
{%- macro decode_html_entities(text) -%}
(
    select string_agg(coalesce(entities.decoded, piece), '' order by piece_position)
    from unnest(regexp_extract_all({{ text }}, r'&#?\w+;|[^&]+|&|$')) as piece with offset as piece_position
    left join
        unnest([
            struct('&apos;' as entity, "'" as decoded),
            struct('&#39;', "'"),
            struct('&#x27;', "'"),
            struct('&quot;', '"'),
            struct('&amp;', '&'),
            struct('&lt;', '<'),
            struct('&gt;', '>')
        ]) as entities
        on piece = entities.entity
)
{%- endmacro %}
