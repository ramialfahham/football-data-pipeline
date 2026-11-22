# Verification — a crest fills its spot, with no tile behind it

Read in the dev server (`preview_start` v2) on this branch, in the Browser pane, by computed style and
box geometry. Pages: `/en/teams/1-fc-koln/`, `/en/players/a-pavlovic-328033/` and
`/en/2-bundesliga/matches/2026-11-20-arminia-bielefeld-vs-1-fc-magdeburg/`. Widths 375px and 280px.
Dark is the page default; light is `data-theme="light"` on the body. Remote images do not load in the
pane, so the badge itself was not seen, only the `img` box and its spot.

criteria_demonstrated:
  - **Every `.crest`, `.crest.xs` and `.pphoto` has a transparent background and a 0px border, in light and dark, at 280px and 375px:** on the team page at 375px dark, 1 `.crest`, 78 `.crest.xs` and 28 `.pphoto`, 0 not bare; at 280px light on the team page, the player page and the match page, 0 spots with a background colour other than `rgba(0, 0, 0, 0)` or a border width other than 0; at 280px dark on the player page, 0; at 375px light on the match page (2 `.crest`, 19 `.crest.xs`, 12 `.pphoto`), 0.
  - **A crest image fills its spot:** on the team page at 375px dark, the 1 large crest (52px) and the 78 small ones (24px) each hold an `img` whose width and height equal the spot's within 0.6px; `object-fit: contain` (unchanged) keeps the badge whole.
  - **A spot with no image shows its initials with no fill behind them:** the 28 player spots on the team page and the 12 on the match page hold the initials in a `span`, with a transparent background and 0px borders; the player page's large crest (no image) does the same. Ink: `rgb(241, 243, 247)` on a crest in dark and `rgb(20, 20, 16)` in light; `rgb(119, 119, 110)` on a player spot in light.
  - **The registry records the rule on the crest and photo parts and names #340:** `docs/design/components.yml`, parts `crest`, `small` (component `crest`) and `photo` (component `player-row`) each carry the rule text and "#340"; `python scripts/check_component_registry.py` reports 0 failures and `python scripts/check_page_css.py` reports 0 findings.

Not covered: the measured design check does not assert the rule until #340 adds its row, so the
design baselines do not yet show the bare spot as a measured value.
