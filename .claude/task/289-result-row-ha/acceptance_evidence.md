# Verification — the Result row's two-line form

Read from the built site (`npm run build` in site_v2 on this branch, sample data) against main
0953e41c's build, every result row on 548 Match, 34 Team and 72 Player pages per language, in
Chromium at every width from 280 to 1010px in 10px steps, in EN, DE and FI.

criteria_demonstrated:
  - **Home or away starts line 2 in the two-line form:** in every two-line row (Match 101,487–118,973, Team 2,955–3,495, Player 12,828–13,849 row-measurements per language), home or away opens line 2 and is not on line 1: 0 failures in each language.
  - **Chip and score on the first line:** 0 rows with the chip or the score below the first line of the name, on every page, width and language.
  - **One-line form unchanged:** every row in the one-line form on both builds keeps main's positions within half a pixel: 0 moved.
  - **Match header without a line:** under 700px the stacked teams carry no border between them: main draws 1px solid under the first team at 375 and 560px, upcoming and played, EN, DE and FI, and the branch's built stylesheet has no border on `.mp .mast .team`.
  - **No row over two lines but by a wrap:** every row over two lines is one whose opponent's name or line 2 wraps between words or items; none sticks out of its row beyond the 12 row-measurements main also has.
