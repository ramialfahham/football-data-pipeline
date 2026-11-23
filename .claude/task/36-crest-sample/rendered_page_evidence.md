# Rendered page evidence — the chart legend label

Change: `site_v2/src/components/ui/ChartLegend.astro` puts each legend label in one `<span>` inside its `.chart-key`.
Measured on the dev server (`preview_start` name `v2`) from the accessibility tree and element geometry. The screenshot tool fails in this pane, so no image was taken. Widths are CSS pixels; a key is `[width, height]`.

## Player page, Rabiot-Provost (player 272), the legend of the comparison

The legend holds three keys: the player's name, the other players of the position, the median.

| Language | Viewport | Legend scrollWidth / clientWidth | Document scrollWidth | Name key | Other keys |
|---|---|---|---|---|---|
| de | 280 | 248 / 248 | 280 | 248 x 39 (two lines) | 209 x 20, 50 x 20 |
| en | 280 | 248 / 248 | 280 | 248 x 39 (two lines) | 162 x 20, 50 x 20 |
| fi | 280 | 248 / 248 | 280 | 248 x 39 (two lines) | 236 x 20, 61 x 20 |
| de | 375 | 343 / 343 | 375 | 343 x 39 (two lines) | 209 x 20, 50 x 20 |
| en | 375 | 343 / 343 | 375 | 343 x 39 (two lines) | 162 x 20, 50 x 20 |
| fi | 375 | 343 / 343 | 375 | 343 x 39 (two lines) | 236 x 20, 61 x 20 |
| de | 1010 | 928 / 928 | 995 | 406 x 20 (one line) | 209 x 20, 50 x 20 |
| en | 1010 | 928 / 928 | 995 | 358 x 20 (one line) | 162 x 20, 50 x 20 |
| fi | 1010 | 928 / 928 | 995 | 436 x 20 (one line) | 236 x 20, 61 x 20 |

- Before the change at 280 px in de, the name key was 265 wide in a 248 wide legend: the text, the kept-hyphen element "Rabiot-Provost," and the position name sat side by side as three flex items.
- After the change the name key is one flex item of the legend's width and wraps to two lines between words. No key is wider than its legend at any width.
- The kept-hyphen name stays in one piece: "Rabiot-Provost," is not split.
- The player team name does not appear in the legend of the Finnish page; the legend text is the player's name and the position names, which wrap between words.

## Team page, Manchester United FC, Performance tab (the plain-label legends)

The two legends of the tab are TeamDeserved (4 keys) and TeamLeagueStrips (3 keys).

| Language | Viewport | Legend scrollWidth / clientWidth | Keys | Mark position |
|---|---|---|---|---|
| en | 1010 | 928 / 928 | 126, 204, 152, 186 and 152, 186, 50, all 20 high | the mark at 0, the text after it |
| en | 280 | 248 / 248 | the same widths, all 20 high | the mark at 0 |
| fi | 280 | 248 / 248 | 121, 156, 152, 147 and 152, 147, 61, all 20 high | the text follows the mark |

- Every key on the Team page holds exactly the mark `<i>` and one `<span>`. The widths and the 20 px height are those of a one-line text, so a plain label renders as before.
- The document is no wider than the viewport on any measured page (280, 375, 1010).
