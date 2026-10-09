# Rendered page evidence — one order for every metric, from the catalogue

No markup or CSS changes; the evidence is the built pages' text, read by script from `astro build` of the committed
sample on this branch and on main. No screenshot.

| Page | Passing player boards, this branch | main |
|---|---|---|
| /en/bundesliga/stats/ | Passes · Pass accuracy · Key passes | Passes · Key passes · Pass accuracy |
| /de/bundesliga/statistiken/ | Pässe · Passquote · Schlüsselpässe | Pässe · Schlüsselpässe · Passquote |
| /fi/bundesliga/tilastot/ | Syötöt · Syöttötarkkuus · Avainsyötöt | Syötöt · Avainsyötöt · Syöttötarkkuus |

Every other board on these three pages, and every other page of the 2,539, reads as on main.
check_design_inventory.py reports 0 failures in 165 renders.
