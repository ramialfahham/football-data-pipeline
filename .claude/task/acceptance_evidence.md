# Verification — metric names on screen come only from the catalogue label

Checked locally on the branch: the six offline gates incl. check_copy_gate.py (1,122 strings, 201
metric labels) and check_description_hygiene.py; check-page-specs (10 pages OK); the site's node
tests (137 passed, 16 of them in check-metric-labels.test.mjs); pytest (1,606 passed, 2 skipped,
the decision-history pin at 719). A
local build of a copy of the branch on the committed sample (2,268 pages, audit-seo and
check-built-pages OK) and check_design_inventory.py on it (174 renders, 0 failures, 0 warnings).

criteria_demonstrated:
  - DeservedTable.astro takes its four heads from metricLabel and fills the block name and explainer through {deservedName}, {sotdName}, {sotdNameStart} and {sotName}; DeservedHero.astro fills the verdict, caption and x axis and takes the y axis from metricLabel; YearOverYear.astro takes Points, Goals and Goals against from metricLabel; the Rankings page's description fills {sotName}. compColBalance, compColDeserved, compColDiff, axPoints and the three yoy strings are gone.
  - The built Bundesliga Overview and Borussia Dortmund team pages read the approved wording in EN, DE and FI, e.g. heads "Differenz der Schüsse aufs Tor / pro Spiel · Verdiente Punkte · Punkte · Differenz zu den verdienten Punkten" and "Laukausero maalia kohti / ottelua kohden · Ansaitut pisteet · Pisteet · Ero ansaittuihin pisteisiin"; the FI tiles read "Laukaukset maalia kohti", "Vastustajan laukaukset maalia kohti", "Laukausero maalia kohti", the DE middle tile "Zugelassene Schüsse aufs Tor". No built page carries Balance, shot balance, Schussbilanz or laukaustase.
  - "no page string spells a catalogue metric name" parses the EN, DE and FI Dict blocks and fails on a multi-word name anywhere in a string (any case) or a string that is exactly a one-word name; four keys are listed as not the metric, each with its reason; its first two asserts prove the matcher finds a name. Run against main's strings.ts it fails, stopping at English with five strings that spell a name: axPlay, yoyGoalsFor, yoyGoalsAgainst, seoCompetitionStatsDesc and compDeservedExplainer.
  - The German verdict counts points through {gapPoints}, pointCountOne or pointCount picked by the gap as shown: across the built German team pages 6 read "holte 1 Punkt weniger/mehr" and none "1 Punkte"; "a verdict that counts points takes the singular for one point" fails on a sentence that puts a plural noun after {gap}.
  - "no two metrics of one entity share both name and second line" compares every catalogue metric with a label by entity, locale, name and metricSubline; it passes, comparing more than 150 names, and its first assert proves it finds a planted pair (goals and goals_per_match given the same second line). The name check reads every key of a Dict block, including several keys on one line.
