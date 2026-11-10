# Verification — Finnish player rows fit at 280px

Read from the built site (`npm run build` in site_v2 on this branch, sample data), every player row
on 548 Match pages and 34 Team pages per language, in Chromium at 280, 320, 360, 375, 700 and
1010px, and the Match pages also at 300, 310, 560, 600, 630 and 640px.

criteria_demonstrated:
  - **No row sticks out at 280px:** 0 of 1,879 Match-page and 0 of 999 Team-page player rows overflow their row at 280px in EN, DE and FI; the design check gives Match page 0 List row and 0 Player row misses and scroll 2184, main's baseline, where main's CI run counted 5, 5 and 2185.
  - **The narrow form under 280px:** every player row narrower than 280px (248px at 280 on Match and Team pages; on Match pages 268–278px at 300–310 and 243–279px in the two-column lists at 560–640) takes the grid areas "photo name name" / "photo pos stat": the name across the row, the position and the numbers on the second line, the numbers in the right-hand column; none of them sticks out.
  - **Unchanged at 280px and wider:** every row 280px or wider (288px and up at 320, 360, 375, 700 and 1010) keeps today's grid; 0 of 2,878 rows per language and width take the narrow form there.
