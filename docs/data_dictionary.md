# Data Dictionary and Definition Confidence

This document defines confidence levels for data definitions and records verified mappings.

## Confidence Levels

- `verified`: field meaning is explicitly confirmed by official source documentation.
- `inferred`: field meaning is derived from payload structure/naming and still needs source-doc confirmation.

## Verified Source Documents

- football-data.co.uk notes: https://www.football-data.co.uk/notes.txt

## Verified Canonical Mappings (football_data_co_uk)

The following canonical columns are currently verified against football-data.co.uk notes:

| canonical_column | source_column | verified_definition |
|---|---|---|
| `match_date` | `Date` | Match date |
| `home_team` | `HomeTeam` | Home team name |
| `away_team` | `AwayTeam` | Away team name |
| `full_time_home_goals` | `FTHG` | Full-time home team goals |
| `full_time_away_goals` | `FTAG` | Full-time away team goals |
| `full_time_result` | `FTR` | Full-time result (`H`, `D`, `A`) |

## Current Status by Source

- `football_data` (football-data.co.uk): key match/result columns are `verified`.
- `football_data_org`: top-level payload naming is currently `inferred`.
- `api_football`: top-level payload naming is currently `inferred`.

## Update Process

When a new source field is confirmed with official docs:

1. Add/update mapping in this document.
2. Update model/column descriptions in dbt YAML.
3. Add or tighten quality tests where applicable.
