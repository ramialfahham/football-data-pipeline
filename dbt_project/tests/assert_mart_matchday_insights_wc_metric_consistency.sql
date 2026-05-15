{{
    config(
        tags=["dq", "mart", "form_metrics", "wc"]
    )
}}

-- Form rate vs sum consistency on mart_matchday_insights_wc only (independent of BL1 schema).

{{ matchday_form_metric_consistency_failures(ref('mart_matchday_insights_wc')) }}
