# Rendered page evidence — the site build carries every played match

No markup, CSS or copy changes: the pages read the same data a different way. The rendered proof is
the text comparison in `.claude/task/acceptance_evidence.md`: all 2539 built pages equal main's. The
design check (`scripts/check_design_inventory.py --dist site_v2/dist`) on the branch build: 165
renders at 375, 700 and 1010px, 0 failures, 27 warnings, the same as main.
