# Review — fix/266-team-performance-registry

diff_sha256: 114a66199a42f5896eda7ffaffad86580040a26e8601a5036a6e1ff4b363df1b

rounds: 4
rounds_cap_override: approved in chat, 2026-11-07: one more round for the strip screenshot pins that CI measured for this change.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; the strip pins and manifest fall under tests/fixtures/chart_screenshots/*; the parked design-check change is absent from the diff.
- The scope addition is path-only and follows the objective: the strip heading margin and value position change what the strip pins render; no mechanism, cost, metric, naming or URL decision.
- The CSS moves the page to registry values already stated (Metric group heading 26px, Table name cell 600); no registry change; decisions_taken records the approval.
- The chart label placement only positions the two existing labels from values already in the payload; approved_design team #134 covers the only page changed.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: the placement reads only teamName, the served deserved_points_gap and the existing scatter dots; no field, label or string added; nulls still hide the section.
- Placement traced for both gap signs: beside where the name fits, otherwise name and difference stacked centred with the same x, dx 0 and anchor, difference at least 1.1em under the name, which `checkScatterLabels` accepts; the runtime `place()` takes its under path.
- Registry fidelity of the CSS: dpm names fall back to 600, 16px heading margin plus the row's 10px padding gives 26px, yoyt tracks change only below the 420px container.
- Rendered evidence names its tools (headless Chromium count script, Browser-pane geometry, design check on a build opened on Performance) and claims no screenshot.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The manifest says linux, lists the same 18 names as the folder, and every PNG hash matches it, so `pin_findings` and `screenshot_verdict` compare cleanly.
- Only the 6 strip pins and their manifest hashes changed; the scatter and comparison entries and files are untouched.
- The pins are the files the Linux validate:ui run wrote to `--artifacts`, the route the check prescribes; the strip images show the heading gap and the value at the row's top, 96px taller for 6 groups.
- PNGs are binary to git, so autocrlf cannot alter them; `.ui_paths` already triggers validate:ui on the pin folder.

## escalations
- question: the every-tab design check raises the Team page's split pin (47 → 56, the #249 hyphen class), which the rising-pin tests forbid; fix here, allow a one-time rise, or hold the check change back?
  CPO ANSWER: answered through the coordinating session, 2026-11-07: hold the check change back; it is parked on parked/266-every-tab-check and lands with #249.
