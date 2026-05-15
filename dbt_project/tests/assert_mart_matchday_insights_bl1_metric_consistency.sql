{{
    config(
        tags=["dq", "mart", "form_metrics", "bl1"]
    )
}}

-- Form rate vs sum consistency on mart_matchday_insights_bl1 only.

{{ matchday_form_metric_consistency_failures(ref('mart_matchday_insights_bl1')) }}
