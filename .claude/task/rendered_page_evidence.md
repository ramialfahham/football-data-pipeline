# Rendered page evidence — #177 part 3: the Form comparison takes its rows from the catalogue

Read from the dev server (`npm run dev`) in the Browser pane. The page is a gitignored copy of a sample match whose
last-5 rows carry two real prod rows of `mart_team_momentum`, deleted after the check. For every Form comparison label
(name and second line): whether it leaves its column, and every mid-word line break.

| Page | Rows | 375px |
|---|---|---|
| /en/bundesliga/matches/<sample match>/ | 55 (35 last 5, 20 this season) | 0 overflow, 0 breaks, no sideways scroll |
| /de/bundesliga/spiele/<sample match>/ | 55 | 0 overflow, 0 breaks, no sideways scroll |
| /fi/bundesliga/ottelut/<sample match>/ | 55 | 0 overflow, 0 breaks, no sideways scroll |

Control: the same check at 230px flags 12 Finnish labels leaving their column (e.g. "Voitetut kaksinkamppailut",
"Viimeistelytehokkuus"), so it detects overflow when there is some. The longest new names ("Onnistuneet
harhautukset", "Ohi menneet laukaukset", "Erfolgreiche Dribblings") fit at 375px.
