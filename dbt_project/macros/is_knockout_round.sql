{#
  Generic classifier: is a fixture's round_name a knockout-bracket round (as opposed
  to a round-robin / table phase)?

  Standings (league tables, group tables) are only meaningful for round-robin play.
  Knockout rounds are a bracket with no table, so league_rank is suppressed for them
  even when a finished group/league-phase table still exists for the season.

  Heuristic over the API round_name string (lower-cased). Covers the common shapes:
    - "Round of 16 / 32 / 64"      → knockout
    - "1/8-finals", "1/16 Finals"  → knockout
    - "8th Finals", "16th Finals"  → knockout
    - "Quarter-finals" / "Semi-finals" / "Final" / "3rd Place" → knockout
    - "Play-off(s)" / "Playoff"    → knockout (promotion/relegation/qualifying play-offs)
  Round-robin shapes are NOT matched (return false): "Regular Season - N",
  "Group A - N", "League Stage - N", "Apertura/Clausura - N", "Matchday N".

  This is a documented heuristic and may need per-competition tuning as new round_name
  formats appear (the regex is the single place to adjust). Returns false when
  round_name is null.
#}
{% macro is_knockout_round(round_name_expr) %}
    coalesce(
        regexp_contains(
            lower({{ round_name_expr }}),
            r'round of \d+|\d+/\d+[- ]?final|\d+(st|nd|rd|th) finals|quarter[- ]?final|semi[- ]?final|\bfinals?\b|3rd place|third place|play[- ]?off'
        ),
        false
    )
{% endmacro %}
