# Review — fix/266-team-performance-registry

diff_sha256: 4179d04b29fede849f4a74cfe2ea8d0ac13fda099487b558167bf10be0c6fd4e

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path (system.css, TeamDeserved.astro, chartTheme.ts, task files) is in scope_paths; the parked design-check change is absent from the diff.
- The CSS moves the page to registry values already stated (Metric group heading 26px, Table name cell 600); no registry, wording, metric or URL change; decisions_taken records the approval.
- The chart label placement only positions the two existing labels from values already in the payload; named in objective, criteria and blast_radius; approved_design team #134 covers the only page changed.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: the placement reads only teamName, the served deserved_points_gap and the existing scatter dots; no field, label or string added; nulls still hide the section.
- Placement traced for both gap signs: beside where the name fits, otherwise name and difference stacked centred with the same x, dx 0 and anchor, difference at least 1.1em under the name, which `checkScatterLabels` accepts; the runtime `place()` takes its under path.
- Registry fidelity of the CSS: dpm names fall back to 600, 16px heading margin plus the row's 10px padding gives 26px, yoyt tracks change only below the 420px container.
- Rendered evidence names its tools (headless Chromium count script, Browser-pane geometry, design check on a build opened on Performance) and claims no screenshot.

## escalations
- question: the every-tab design check raises the Team page's split pin (47 → 56, the #249 hyphen class), which the rising-pin tests forbid; fix here, allow a one-time rise, or hold the check change back?
  CPO ANSWER: answered through the coordinating session, 2026-11-07: hold the check change back; it is parked on parked/266-every-tab-check and lands with #249.
