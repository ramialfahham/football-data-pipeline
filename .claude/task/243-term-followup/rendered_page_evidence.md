# Rendered page — the five-item menu and the singular save word

Read from the built site (`npm run build` in site_v2, sample data, 757 pages per language) on the
branch before main 7753c507 was merged; main changes nothing under `site_v2/` since the branch's
base, so the built output is the same.

| What | Where | Measured |
|---|---|---|
| Header menu, phone drawer, footer row | every built page, EN, DE and FI | five items in menu order; no Standings, Table, Tabelle or Sarjataulukko item. Which items link is unchanged by this branch: `menu.ts` gives Competitions, Matches and Teams an href |
| Goalkeeper row, one save | match pages, e.g. Al-Qadisiyah FC vs Al-Sadd | "1 save", "1 Parade", "1 torjunta" |
| Goalkeeper row, more saves | match pages, e.g. Bahia vs Flamengo | "36 saves", "36 Paraden", "36 torjuntaa" |
| Competition table section | the Bundesliga page | Table, Tabelle, Sarjataulukko |

Widths: the design check (`scripts/check_design_inventory.py --viewports 280,1010 --langs en,de`,
quick baseline) gives the same FAIL and COUNT lines as main at the branch's base, none added. The
menu loses one inert item, so no row gets wider. No screenshot: the Browser pane's screenshot fails
on this machine, so the evidence is the built HTML and the design check's measurements.
