{% docs metric_catalogue %}
Every metric we compute, one row per metric and entity (a team or a player). A row holds what the
metric means (description) and how it is computed (base_relation, numerator_expr, denominator_expr,
computation_kind). It also holds the key of its name (label_i18n_key) and which way is better
(direction, interpretation). How it is shown is format, metric_group, metric_group_order,
metric_order and importance_tier. Every
model that computes a metric follows its row's formula. A row is window-free: which matches a
metric counts, and when its value is blank, are the rules below, never part of a row.

How every metric is computed:

- R1 A metric with a formula is that formula summed over the matches of its window: a ratio is a
  sum over a sum, never an average of match ratios.
- R2 A window chooses matches; it never makes a new metric.
- R3 A forfeit (AWD/WO) is a result awarded without the match being played. It counts in
  points_won, goals and goals_against and in the counts of matches, wins, draws and losses, as the
  league table counts it; every other metric counts played matches only. No player appears in a
  forfeit.
- R4 A metric is blank when any match it counts lacks an input; a player's metric also when its
  window holds a played team match with no player data at all.
- R5 A ratio over zero is blank.
- R6 Year-over-year exists for domestic league seasons only: a team's season through N matches
  against its previous season through its first N; a player's through N appearances against the
  previous season at the same club through its first N. It is blank when either side is.
- R7 Results the league publishes (the score, the league table) are taken as published, never
  computed; a count of results or a playing-time fact (appearances, minutes, starts) is a fact,
  not a catalogue metric.

A metric computed by a model (deserved points and its ranks, the contribution share, the league
position) is described on that model. A row that varies by window names its window in its
window_type column.
{% enddocs %}

{% docs ranking_rules %}
Who enters a ranking or a benchmark. A player enters a rate ranking from 270 minutes, the
finishing one also from 10 shots on target, and the pass-accuracy and finishing rankings are for
outfield players. A team enters a ranking from its first finished match. A ranking that lists the
most first leaves out a zero. A player enters a benchmark from 270 minutes in a position, the
finishing one also from 10 shots on target there; a benchmark compares players of one position
group, goalkeepers on saves and passing and outfield players on every benchmark metric but saves.
A team enters a benchmark from 3 finished matches.
{% enddocs %}

{% docs window_type__form %}
Which matches the window holds. `last_5`: the team's last five finished matches before the
fixture, across its club or its national-team competitions, for a club this season's only.
`tournament_to_date`: every finished match of the team in this tournament edition before the
fixture. `qualifiers`: before the team's first match of a tournament, every finished match of the
team in that tournament's qualifying competitions.
{% enddocs %}
