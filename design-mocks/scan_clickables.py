"""Inventory every clickable thing across the rendered mocks, and how each one signals it.

Before standardising interaction, know what exists. Read from the EMITTED html, so it is what a
reader meets rather than what a component intends.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
SYSTEM_CSS = Path(__file__).resolve().parent.parent / "site_v2/src/styles/system.css"

FILES = ["home_mock.html", "matches_next_mock.html", "matches_past_mock.html",
         "competition_hub_mock.html"]

A = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.S)


def attr(tag, name):
    m = re.search(r'%s="([^"]*)"' % name, tag)
    return m.group(1) if m else ""


def target_kind(href):
    if href in ("#", ""):
        return "placeholder"
    if href.endswith("_mock.html"):
        return "sibling page (mock)"
    p = [s for s in href.strip("/").split("/") if s]
    if len(p) == 1:
        return "locale root (home)"
    if p[1] == "teams":
        return "team"
    if p[1] == "matches":
        return "matches list"
    if len(p) >= 3 and p[2] == "matches":
        return "fixture"
    if len(p) == 2:
        return "competition"
    return "other: " + href


def main():
    css = re.sub(r"/\*.*?\*/", "", SYSTEM_CSS.read_text(encoding="utf-8"), flags=re.S)
    hover = {}
    for m in re.finditer(r"([^{}]*:hover[^{}]*)\{([^}]*)\}", css):
        hover[" ".join(m.group(1).split())] = " ".join(m.group(2).split())

    rows = defaultdict(lambda: {"count": 0, "targets": set(), "files": set()})
    for f in FILES:
        doc = (HERE / f).read_text(encoding="utf-8")
        body = doc.split('<div class="stage"', 1)[-1].split('<div class="legend"', 1)[0]
        for tag, inner in A.findall(body):
            cls = attr(tag, "class") or "(no class)"
            key = cls
            rows[key]["count"] += 1
            rows[key]["targets"].add(target_kind(attr(tag, "href")))
            rows[key]["files"].add(f.replace("_mock.html", ""))
            txt = re.sub(r"<[^>]+>", " ", inner)
            rows[key]["sample"] = " ".join(txt.split())[:38]

    print("CLICKABLE INVENTORY — what a reader can click, and where it goes\n")
    print("%-22s %5s  %-26s %s" % ("class", "n", "goes to", "seen on"))
    print("-" * 96)
    for cls, d in sorted(rows.items(), key=lambda kv: -kv[1]["count"]):
        print("%-22s %5d  %-26s %s" % (cls, d["count"], ", ".join(sorted(d["targets"])),
                                       ", ".join(sorted(d["files"]))))

    print("\n\nHOW EACH ONE SIGNALS IT IS CLICKABLE (hover rules that apply)\n")
    for sel, body in sorted(hover.items()):
        if any(k in sel for k in ("fxrow", "cnm", "linkchip", "lnk", "tab", "brow", "tm",
                                  "mainnav", "iconbtn", "flinks")):
            print("  %-34s %s" % (sel, body))


if __name__ == "__main__":
    main()
