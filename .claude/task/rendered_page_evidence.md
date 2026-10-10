# Rendered page evidence — the Rankings tab's two blocks get their intro line

The change adds one existing element, the block explainer (`.bsub`), under each of the two block
names on the Rankings tab, and one CSS rule, `.bsub + .fxgroup { margin-top: 0; }`. In the branch
build that pair occurs only on the three Rankings tab pages (`grep` of the built HTML). The built
text is in `.claude/task/acceptance_evidence.md`.

Measured in the browser on the dev server, `getBoundingClientRect` per block:

| Page | Width | Block | name → intro | intro → first group head |
|---|---|---|---|---|
| en/bundesliga/stats | 375 | Team rankings, Player rankings | 14px | 8px |
| de/bundesliga/statistiken | 700 | Mannschafts-Ranglisten, Spieler-Ranglisten | 14px | 8px |
| fi/bundesliga/tilastot | 1010 | Joukkuerankingit, Pelaajarankingit | 14px | 8px |
| en/bundesliga (Deserved points table, approved) | 1010 | Deserved points table | 14px | 8px |

Without the rule the first group head sat 34px under the intro, its own margin.

The design check (`scripts/check_design_inventory.py --dist site_v2/dist`) on the branch build, with
the Rankings mock now carrying the two intros: 165 renders at 375, 700 and 1010px, 0 failures, 27
warnings. Main's build gives the same 0 failures and 27 warnings (the header row at 700px), so none
comes from this change.
