{#- The rows of each key that carry the newest ingest time of that key, counted, and whether they
    differ. Rows are "tied" when the provider's response held the same entity twice at one ingest
    time. They are identical when farm_fingerprint(to_json_string(row)) is equal for all of them, so
    one stands for the key and nothing is lost; a key whose tied rows differ has no value that can
    be picked, so its reader withholds it. The fingerprint covers the provider's content only: the
    caller names in ignore_columns every column we add per row (ingest time, an offset, a load id),
    so identical provider rows are never read as different. A tie in an older fetch does not
    withhold the key: the newer fetch replaces it, and a reader that still takes a value from an
    older fetch takes none when the rows tied there differ. The relation carries the key columns and
    raw_ingested_at. -#}
{% macro newest_fetch_ties(relation, key_columns, ignore_columns=[]) -%}
    select
        {{ key_columns | join(', ') }},
        raw_ingested_at,
        count(*) as tied_rows,
        min(row_hash) != max(row_hash) as rows_differ
    from (
        select
            *,
            farm_fingerprint(to_json_string(
                {%- if ignore_columns %}
                (select as struct source_row.* except ({{ ignore_columns | join(', ') }}))
                {%- else %}
                source_row
                {%- endif %}
            )) as row_hash,
            raw_ingested_at = max(raw_ingested_at) over (partition by {{ key_columns | join(', ') }})
                as in_newest_fetch
        from {{ relation }} as source_row
    )
    where in_newest_fetch
    group by {{ key_columns | join(', ') }}, raw_ingested_at
{%- endmacro %}
