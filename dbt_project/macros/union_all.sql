{% macro union_all(cte_names) %}
    {% for cte in cte_names %}
        select * from {{ cte }}
        {% if not loop.last %}union all{% endif %}
    {% endfor %}
{% endmacro %}
