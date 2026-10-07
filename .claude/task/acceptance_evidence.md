# Acceptance evidence — #177 part 2: metric names without sigils, from one place

Read from `astro build` of the committed sample (2,538 pages; audit-seo and check-built-pages OK), scanned per label
element: the Form comparison row label (`.mlabel`), the team page rows (`.vs-name`), the board titles (`.bt`) and the
team hero tiles (`.hl`), in every built page of every locale.

criteria_demonstrated:
  - NO SIGIL IN ANY METRIC NAME. 0 label elements carry "Ø" or "%" across 2,539 built pages. The 12 "Ø" left in the
    HTML are player names (M. Ødegaard, S. Ørjasæter), not metric names. check-metric-labels.test.mjs now fails on
    any metric name with "Ø" or "%" in any locale.
  - THE SECOND LINE. Form comparison rows, EN: per-match averages read "Goals | per match" and so on; shares named
    by their count read "Duels won | percentage", "Shots inside box | percentage", "Saves | percentage"; shares with a
    word of their own ("Pass accuracy", "Goals per shot on target") and the count "Clean sheets" have none. DE reads
    "pro Spiel" / "in Prozent", FI "ottelua kohden" / "prosentteina", row for row. Team page: "Clean sheets |
    percentage", "Defensive actions | per match · 10 T · 6 I · 5 B". Boards: "Goals per match", "Duels won
    percentage", "Schüsse aufs Tor pro Spiel", "Maalit ottelua kohden"; count boards ("Goals", "Assists") plain. Hero
    tiles: "Schüsse aufs Tor | pro Spiel". No page shows a single match's values today. Layout at 375, 700 and
    1010px in German and Finnish: rendered_page_evidence.md.
  - THE APPROVED NAMES, ONLY IN strings.ts. Every name above is the approved list's (e.g. DE "Passquote", "Gehaltene
    Schüsse", "Schüsse aufs Tor"); no built page contains "Torschussdifferenz"; the German verdict reads "eine
    Differenz der Schüsse aufs Tor von 0,0 pro Spiel". Names live only in METRIC_LABELS_{EN,DE,FI}; the Home
    design-mock generators read them there and run (gen_top_teams, gen_top_players, gen_home, gen_home_with_rules,
    gen_competition_teams), and check_teams and check_players report ALL PASS. The three wireframes name metrics
    by key. A test fails when the site's per-match flags, its hero tiles or its share list disagree with the
    catalogue (per match = denominator count(*) and not a share).
  - NO label_en. The catalogue has 104 rows, every other field byte-identical to main (checked by parsing both);
    its seed column docs and the unique test on it are removed. dbt parse clean; pytest tests/: 1,460 passed;
    npm test: 112 passed; check_copy_gate: OK (132 metric labels).
