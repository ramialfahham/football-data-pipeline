{# BigQuery: profile `dataset` is dbt's target.schema. Layer names are the dataset ids. #}
{# Environment isolation: layer datasets (staging/core/intermediate/marts) are prefixed by  #}
{# the target name, so each environment writes its own copy. `prod` is the ONLY target that #}
{# writes the canonical bare datasets the site export reads — every other target (ci, dev,  #}
{# …) is auto-prefixed, so a non-prod build can never clobber prod. base + seeds carry no    #}
{# custom schema and ride target.schema (the profile `dataset`), which is already per-env.   #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set prefix = "" if target.name == "prod" else target.name ~ "_" -%}
    {%- if custom_schema_name is none or (custom_schema_name | trim) == "" -%}
        {{ target.schema }}
    {%- else -%}
        {{ prefix ~ (custom_schema_name | trim) }}
    {%- endif -%}
{%- endmacro %}
