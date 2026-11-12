# Review — docs/readme-screenshots — 2026-11-12

diff_sha256: 6d31d57b95ebab72837fd0d39a8ba5e621c82131fa740f67cb609130bf061866

rounds: 14
rounds_cap_override: approved in chat, 2026-11-12; the 18 mock-based images are temporary until the Team, Players to watch and text-style pages are built, and no player photos are shown.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths: the task folder, the script, the test, the README and the 30 PNGs. No site_v2/src, dbt, ingestion, export or CI file is touched.
- Playwright 1.63.0 is already pinned in requirements-ui.txt, so there is no new library; dist/ is gitignored; no credential-shaped string; no recurring cost.
- The contract, the script docstring and the README line agree on build-first, --mock with hidden controls, photo stripping that exits on leftovers, three crops per page and approvals dated 2026-11-12.
- approved_design none holds: no page output changes.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Viewed all 30 images: club crests render in every crop, no player photo survives, no mock chrome, and each block lands on its named section.
- The 30 README image references match the 30 files and the regexes in tests/test_readme_screenshots.py; no unreferenced PNG.
- The script, a hand-run tool outside CI, requires an existing site_v2/dist and checks the 300 KB limit before every write.
- The sentence-length pin and the decision-history gate are unaffected by the README cells.

## escalations
(none)
