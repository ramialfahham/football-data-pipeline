# Verification — the club Team page as approved, on the parts library

Read from this branch's dev server and, for "before", from main at de65e45a, with the same data;
the method and every difference are in `rendered_page_evidence.md`.

## Sizes (full export of 3,391 teams, prod data of 18 Nov 2026)

| | Before | After |
|---|---|---|
| Team payloads | 697,956,008 bytes | 722,800,591 bytes (+3.6%) |
| Team pages in `dist`, 10,173 pages | 484,670,309 bytes | 440,379,280 bytes (−9.1%) |
| BigQuery read by the team export | about 324 MiB | about 331 MiB |

## Data

- `mart_team_page_window_metrics` serves This season (3,131 clubs) and Compared with last season;
  it holds no national team, which is how a page tells a club from a national team.
- `mart_team_competition_benchmarks.round_stage_kind` is new: table where the competition-season is
  benchmarked over its table rounds (int_team_competition_phase__metrics), NULL otherwise. No
  existing column said it: checked int_round_names.round_stage_kind (per round),
  mart_team_competitions.reached_round_stage_kind (the team's latest round), mart_standings.table_kind
  (provider sections), int_team_season__table_state.phase (in or end of season).

criteria_demonstrated:
  - **This season against the whole of last season, all competitions:** the block reads `last_season` from mart_team_page_window_metrics (metric_value against metric_value_prev_season over every club competition); Bayern shows 15 matches against 54.
  - **From the first match, no minimum:** the block shows on 99 of 102 club pages, absent only where the club played no match last season; Cosenza with one match shows it.
  - **The explainer:** "This season (15 matches) against last season (54), across all competitions. Values are per match, so the number of matches doesn't tilt them. Early on, a few matches can swing the numbers; they settle as the matches add up." and the DE and FI texts of #250 note 4254003834, word for word.
  - **This season above the tabs:** 102 of 102 club pages, six cards, the note 4254003834 explainer listing the competitions in the served order, EN/DE/FI.
  - **Overview order and rows:** Competitions one line each (0 `.tc-extra`), Next matches before Recent matches, Recent matches and Results in `.rlist.pm`.
  - **Performance:** no tab explainer and no Standing on any club page; Deserved points opens with "Bundesliga 2026/27 only." / "Nur Bundesliga 2026/27." / "Vain Bundesliga 2026/27." on Bayern, the same form on all 102.
  - **Compared with other teams:** the league and each table-phase competition of the season as choices (16 clubs with two), a median on every strip row, 0 card rows, explainer "Ranked among all 18 teams of Bundesliga 2026/27." / "Ranked among all 36 teams of UEFA Champions League 2026/27."
  - **Compared with last season details:** 0 card rows; an empty trend where a season has no value; "1 match" / "1 Spiel" / "1 ottelu" on a one-match club; absent on the 3 club pages with no match last season.
  - **National team pages:** the same blocks, order, links and text; the strip plot only takes the part's standard form (median, no "better" marks).
  - **Player page:** 666 screenshots pixel-identical, the same links and text, on the shared parts.
  - **No break at 280–768px:** 0 sideways scroll and 0 element past the edge on every Team page, every tab, EN/DE/FI, at 280, 320, 360, 375, 700 and 768px; the design check is the `validate:ui` job.
