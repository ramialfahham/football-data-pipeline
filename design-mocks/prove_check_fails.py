"""Negative control: the stacked-branch check must fail on broken CSS and pass on fixed CSS."""
import re

BROKEN = """@container (max-width: 480px) {
  .brow .ent { display: block; }
  .board .sub { margin-top: 1px; }
}"""

FIXED = """@container (max-width: 480px) {
  .brow .ent { display: block; }
  .board .nm,
  .board .sub { display: block; }
  .board .sub { margin-top: 1px; }
}"""


def blockifies_children(css):
    cq = next(m for m in re.finditer(r"@container \(max-width: (\d+)px\)\s*\{(.*?)\n\}", css, re.S)
              if ".brow .ent" in m.group(2))
    return re.search(r"\.board \.nm,\s*\n\s*\.board \.sub \{ display: block", cq.group(2)) is not None


broken = blockifies_children(BROKEN)
fixed = blockifies_children(FIXED)
print("check on the BROKEN css :", "PASS (bad -- check is vacuous)" if broken else "FAIL (good)")
print("check on the FIXED css  :", "PASS (good)" if fixed else "FAIL (bad)")
assert not broken, "the check does not catch the bug it exists for"
assert fixed, "the check rejects correct css"
print("\nthe check is real: red on the defect, green on the fix.")
