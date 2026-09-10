"""Static checks on the generated mock. The preview renders it as a snapshot with no JS,
so geometry cannot be measured in the browser -- these are the checks makeable without a
live DOM.

Two scoping rules learned the hard way on the first run:
  * system.css is INLINED, so a check over the whole file also audits shipped code and
    reports its :checked toggles (#seg-w1, #tab-*) as mock defects. Scope to MOCK_CSS.
  * CSS comments must be stripped first, or the comment that DOCUMENTS the repeat(var())
    trap is itself matched as an instance of the trap.
"""
import re
from pathlib import Path

h = Path(__file__).with_name("top_players_mock.html").read_text(encoding="utf-8")
all_css, body = h.split("</style>", 1)

MARK = "MOCK HARNESS ONLY"
assert MARK in all_css, "cannot locate the mock CSS block"
mock_css_raw = all_css[all_css.index(MARK):]
def strip(s):
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)



mock_css = strip(mock_css_raw)

ok = True


def check(name, cond, detail=""):
    global ok
    ok = ok and cond
    print(("  PASS " if cond else "  FAIL ") + name + (" -- " + detail if detail else ""))


print("toggle wiring (mock's own toggles only)")
ids = re.findall(r'<input class="toggle" type="checkbox" id="([\w-]+)"', body)
check("three toggles are body-level siblings", sorted(ids) == ["t-fi", "t-light", "t-phone"], str(ids))
for sel in sorted(set(re.findall(r"#(t-[\w-]+):checked", mock_css))):
    check("#%s has a matching sibling input" % sel, sel in ids)
check("every mock toggle is actually used", all(any("#%s:checked" % i in mock_css for _ in [0]) for i in ids))
check("no leftover t-light-x", "t-light-x" not in h)
check("no <script> anywhere", "<script" not in h.lower())
check("no external fetch", not re.search(r'(src|href)\s*=\s*"(https?:)?//', h))

print("\ntrap 1 -- repeat(var(...)) is invalid CSS")
check("no repeat(var( in live declarations", "repeat(var(" not in mock_css.replace(" ", ""))
check("the trap is still documented in a comment", "repeat(var(--n)" in mock_css_raw)
tracks = re.findall(r"--cols:([^;]+);", mock_css)
check("one track list, written whole", len(tracks) == 1, "%d declared" % len(tracks))
check("exactly one fixed value track", tracks[0].count("var(--vw)") == 1, tracks[0].strip())

print("\ntrap 2 -- value columns are a fixed width")
check("every --vw is a length, not auto", all(re.fullmatch(r"\s*\d+px\s*", v) for v in re.findall(r"--vw:([^;]+);", mock_css)))
check("no auto track in any --cols", not any("auto" in t for t in tracks))

print("\ntrap 3 -- each board is its own container")
check(".board sets container-type", re.search(r"\.board\s*\{[^}]*container-type:\s*inline-size", mock_css) is not None)

print("\nentity cell: one line if it fits, stacked if not")
ent = re.search(r"\.brow \.ent\s*\{([^}]*)\}", mock_css).group(1)
check("nowrap, so no single row can wrap on its own", "flex-wrap: nowrap" in ent)
# select the entity-cell query by CONTENT: the first @container in the file is the --vw one
cq = next(m for m in re.finditer(r"@container \(max-width: (\d+)px\)\s*\{(.*?)\n\}", mock_css, re.S)
          if ".brow .ent" in m.group(2))
check("a CONTAINER query decides it, so the whole board switches at once", cq is not None)
check("the stacked branch blockifies .ent", ".brow .ent { display: block; }" in cq.group(2))
# ⚠ THE BUG THIS EXISTS FOR: .nm/.sub carry no display of their own (flex blockifies them in
# the inline branch), so a stacked branch that only sets .ent leaves two INLINE spans running
# together -- "Bayern MünchenBundesliga". Every other check passed on that CSS.
check("the stacked branch ALSO blockifies .nm and .sub",
      re.search(r"\.board \.nm,\s*\n\s*\.board \.sub \{ display: block", cq.group(2)) is not None)
check("neither child sets display outside the query, so flex governs inline",
      "display" not in re.search(r"\.board \.nm\s*\{([^}]*)\}", mock_css).group(1)
      and "display" not in re.search(r"\.board \.sub \{ min-width[^}]*\}", mock_css).group(0))
check("threshold clears the widest PLAYER row (name cell = board - 142px, widest needs ~331px)",
      int(cq.group(1)) >= 473, "%spx" % cq.group(1))
check("no media query decides the stack", "@media" not in mock_css)
check("name can shrink inside the flex row",
      "min-width: 0" in re.search(r"\.board \.nm\s*\{([^}]*)\}", mock_css).group(1))
check("the BASE sub rule sets no display, so the inline branch stays flex",
      "display" not in re.search(r"\.board \.sub \{ min-width[^}]*\}", mock_css).group(0))

print("\nnames must never truncate")
nm = re.search(r"\.board \.nm\s*\{([^}]*)\}", mock_css).group(1)
for prop in ("white-space: normal", "overflow: visible", "text-overflow: clip"):
    check(prop, prop in nm)
check("the system.css ellipsis rule is present, so the override does real work",
      "text-overflow: ellipsis" in all_css[:all_css.index(MARK)])

print("\nthe board title is now the only label, so it must not truncate")
bt = re.search(r"\.bt\s*\{([^}]*)\}", mock_css).group(1)
check("no ellipsis on the title", "ellipsis" not in bt)
check("no nowrap on the title", "nowrap" not in bt)
check("no column-header rule left behind", ".bhead" not in mock_css)

print("\ncrest slot -- the CLUB logo, on player rows too (CPO 2026-08-10)")
check("every player row has a crest cell", body.count('class="crest xs"') == 28,
      str(body.count('class="crest xs"')))
check("the crest track is in the grid", "18px 24px minmax(0, 1fr)" in mock_css)
# ⚠ NOT the design system's text-initials fallback: in review that rendered "RMA / BAY / MCI",
# which on a player row merely restates the club already in the sub-line.
check("an inline placeholder, not text initials", body.count("<svg") == 28)
check("no external fetch, so nothing is hotlinked",
      not re.search(r'(src|href)\s*=\s*"(https?:)?//', h))

print("\ncontent")
check("system.css inlined verbatim", "MATCHDAY IQ" in all_css and len(all_css) > 30000, "%d chars" % len(all_css))
titles = re.findall(r'<span class="bt"><span class="en">([^<]+)</span>', body)
EXPECT = ["Goals", "Assists", "Passes", "Key passes"]
check("four boards in the CPO order", titles == EXPECT, " | ".join(titles))
check("no goalkeeper board", "faced" not in body and "conceded" not in body.lower())
check("titles are label_en verbatim, no sigil, no per-match",
      not any(t.startswith(("Ø", "%")) or "per match" in t for t in titles))
check("28 rows (4 boards x top 7)", body.count('<a class="brow"') == 28, str(body.count('<a class="brow"')))
per_board = [blk.count('<a class="brow"') for blk in body.split('<div class="board">')[1:]]
check("every board shows 7", per_board == [7] * 4, str(per_board))
check("scorer_points is gone as a board", "Goal contributions" not in body)
# all seven pool-1 leagues should appear somewhere, or the sample is not exercising the pool
# the player sub-line is "Club · League" -- #40 requires BOTH, so assert the shape too
subs = re.findall(r'<span class="sub">([^<]+)</span>', body)
check("every row carries club AND league", all("·" in s for s in subs), "%d rows" % len(subs))
leagues = {s.split("·")[-1].strip() for s in subs}
check("sample spans all seven pool-1 leagues", len(leagues) == 7, ", ".join(sorted(leagues)))
check("NO column-header row at all", '<span class="bh v">' not in body and "bhead" not in body)
vals_per_row = {blk.count('<span class="v">') for blk in body.split('<div class="board">')[1:]}
check("exactly one value per row on every board", vals_per_row == {7}, str(vals_per_row))
# the second column that left every #40 board, plus the combined metric itself
for gone in ("Goal contributions", "Pass accuracy", "Dribbles completed", "Successful dribbles",
             "Duels won", "Shots saved", "% "):
    check("dropped: %s" % gone, gone not in body)

# Every board leads with the metric that ranks it. The title is that metric's label_en
# minus its format sigil, so title + sigil must reconstruct the first column header exactly
# -- which proves the title still derives from the catalogue and was not hand-written.
for blk in body.split('<div class="board">')[1:]:
    title = re.search(r'<span class="bt"><span class="en">([^<]+)</span>', blk).group(1)
    vals = [float(v) for v in re.findall(r'<span class="v"><b>([\d.]+)</b></span>', blk)]
    check("'%s' ranks DESCENDING" % title, vals == sorted(vals, reverse=True), str(vals))
check("no per-count grid class left in the markup", 'class="bgrid c' not in body)
check("every board uses the single grid", body.count('<div class="bgrid">') == len(titles))
# The board title is the only translatable string left in the block.
fi_cells = len(re.findall(r'class="fi[^"]*" lang="fi"', body))
check("every board title has an FI twin", fi_cells == len(titles), "%d fi" % fi_cells)
check("every FI title is marked as a probe", len(re.findall(r'class="fi probe"', body)) == len(titles))
check("no mock annotation left", body.count('class="bnote"') == 0)

print("\nRESULT:", "ALL PASS" if ok else "FAILURES ABOVE")
