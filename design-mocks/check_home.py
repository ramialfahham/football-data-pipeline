"""Checks on the composed home-page mock: order, provenance and no-regression."""
import re
from pathlib import Path

h = Path(__file__).with_name("home_mock.html").read_text(encoding="utf-8")
all_css, body = h.split("</style>", 1)

ok = True


def check(name, cond, detail=""):
    global ok
    ok = ok and cond
    print(("  PASS " if cond else "  FAIL ") + name + (" -- " + detail if detail else ""))


print("composition")
order = re.findall(r'<span class="eyebrow">([^<]+)</span>', body)
check("the approved order: next matches -> Top players -> Top teams, nothing after",
      order == ["Next matches", "Top players", "Top teams"], " -> ".join(order))
check("no Browse block, no chip row", "Browse" not in body and 'class="linkrow"' not in body
      and 'class="linkchip"' not in body)

print("\nthe two designed blocks came from their own generators")
titles = re.findall(r'<span class="bt"><span class="en">([^<]+)</span>', body)
check("eight boards, players then teams",
      titles == ["Goals", "Assists", "Passes", "Key passes",
                 "Goals per match", "Shots on goal per match", "Passes per match",
                 "Duels per match"], " | ".join(titles))
check("56 board rows (8 boards x top 7)", body.count('<a class="brow"') == 56,
      str(body.count('<a class="brow"')))
check("every board still shows 7",
      {blk.count('<a class="brow"') for blk in body.split('<div class="board">')[1:]} == {7})

print("\nshipped modules mirrored, not approximated")
check("next matches uses .fxgroup/.gh/.fxrow", all(
    c in body for c in ('class="fxgroup"', 'class="gh"', 'class="fxrow"', 'class="sides"',
                        'class="when"')))
check("19 fixtures: the fixed list plus the Bundesliga's whole nine-match round",
      body.count('class="fxrow"') == 19, str(body.count('class="fxrow"')))

print("\nthe fold: 3 visible per competition, the rest inside <details> (#127)")
groups = body.split('<div class="fxgroup">')[1:]
outside = [g.split("<details", 1)[0].count('class="fxrow"') for g in groups]
check("no competition shows more than 3 rows outside the fold", max(outside) <= 3, str(outside))
folds = re.findall(r'<details class="fxmore"><summary><span class="lbl">Show all (\d+)</span>', body)
check("exactly one competition folds, and it is the nine-match round", folds == ["9"], str(folds))
bl1 = next(g for g in groups if "<details" in g)
check("the Bundesliga shows 3 rows, folds 6",
      bl1.split("<details", 1)[0].count('class="fxrow"') == 3
      and bl1.split("<details", 1)[1].count('class="fxrow"') == 6)
check("the fold needs no script: a native <details>/<summary>, chevron in the summary",
      '<details class="fxmore"><summary>' in body and body.count('</details>') == 1
      and 'class="chev"' in bl1.split("</summary>", 1)[0])

print("\nno regression on the block rules")
check("no column-header row anywhere", '<span class="bh v">' not in body)
check("crest on every board row and every fixture side",
      body.count('class="crest xs"') == 56 + 38, str(body.count('class="crest xs"')))
check("no external fetch", not re.search(r'(src|href)\s*=\s*"(https?:)?//', h))
check("no <script>", "<script" not in h.lower())

print("\nRESULT:", "ALL PASS" if ok else "FAILURES ABOVE")
