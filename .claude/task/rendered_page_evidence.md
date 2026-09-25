# Rendered page evidence — `feat/matches-page` (#160 part 2)

## 1. The measured design check on the built site

`npm run build` on the committed sample (2539 pages, exit 0), then `python
scripts/check_design_inventory.py --dist site_v2/dist` → `23 pages · 3 viewports · 3 languages
(pages per language: en 23, de 9, fi 23) · 165 renders · 0 failures · 27 warnings`, the warnings the
known 700px `.header-in` row, now also on the two new pages. Widths 375, 700, 1010px. The new built
rows "Matches page" (`en/matches/index.html`) and "Matches day page" (`en/matches/*/index.html`, the
first day, 2026-08-20) are measured in EN, DE and FI through the word table (`spiele`, `ottelut`),
expecting Page heading, Filter row, Filter button, Matchday picker, Picker title, Picker arrow,
Block heading, Competition group head and name, Fold, Match row kick-off (opening day) and Match row
score. Mutation on the built EN page (fold removed, heading 22px): 2 failures, restored → 0.

## 2. The dev server (`preview_start` v2), throwaway export of the same day's data

`/de/spiele/`: title "Fußball heute: alle Spiele, Donnerstag, 24. September", h1 "Spiele", crumb
Startseite › Spiele, picker title the long date, arrows to the neighbouring days; groups carry the
crest, name and chevron and link the competition page. Filter buttons (label clicks): Clubs hides the
two national-team groups (`display:none`), National teams + CONCACAF shows only CONCACAF Nations
League, All + All restores both. `/fi/ottelut/2026-09-20/`: 18 groups, 74 played rows with scores and
no links. `/en/matches/2026-08-20/`: no previous arrow; `/en/matches/2027-01-11/`: no next arrow.

## 3. Sent to the CPO

Self-contained snapshots of `dist/en/matches/index.html` and `dist/de/spiele/2026-09-20/index.html`
(stylesheet inlined). The design's render of record stays `design-mocks/renders/matches-hub_2026-
09-23_02.html`.
