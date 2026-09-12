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
check("§0's order: next matches -> Top players -> Top teams -> browse",
      order == ["Next matches", "Top players", "Top teams", "Browse"], " -> ".join(order))
check("browse is LAST, so the follow-up inserts and never rearranges", order[-1] == "Browse")

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
check("12 fixtures, the fixed list §0 specifies", body.count('class="fxrow"') == 12,
      str(body.count('class="fxrow"')))
print("\nbrowse is FLAT (CPO 2026-08-10)")
check("no by-competition / by-country axes", 'class="colhead"' not in body
      and 'class="subhead"' not in body)
check("one chip row", body.count('class="linkrow"') == 1, str(body.count('class="linkrow"')))
check("12 chips, the registry's active competitions",
      body.count('class="linkchip"') == 12, str(body.count('class="linkchip"')))
# ⚠ anchors here by design direction; the SHIPPED component still emits <span> because the
# competition hub does not exist yet and an anchor would 404.
check("chips are anchors in this mock", body.count('<a class="linkchip"') == 12)

print("\nno regression on the block rules")
check("no column-header row anywhere", '<span class="bh v">' not in body)
check("crest on every board row and every fixture side",
      body.count('class="crest xs"') == 56 + 24, str(body.count('class="crest xs"')))
check("no external fetch", not re.search(r'(src|href)\s*=\s*"(https?:)?//', h))
check("no <script>", "<script" not in h.lower())

print("\nRESULT:", "ALL PASS" if ok else "FAILURES ABOVE")
