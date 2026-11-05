# Review — worktree-feat-design-check-scope

diff_sha256: 2603c88f351424087d7aec3335d32d952c5c1ed1279a6567ebd9a13846ba596d

rounds: 4

rounds_cap_override: the pin fill is data taken unchanged from CI's own artifact and the delta review found nothing; continue approved in chat, 2026-11-05.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths, including docs/wireframes/block_standard.md after the amendment; protected_override names the approval and its date.
- The second pin file is declared in decisions_taken; no new dependency, cadence or recurring cost; approved_design none holds, no page output changes.
- Doc-sync: block_standard.md now names both pin files and the two scopes, matching the CI branch and the script flags.
- The empty baseline_quick.json is a stated step: done_when requires the pins from a Linux run's counts.json, filled in the next commit.
- impact_map carries the grep -rl result (22 files), fires_on, on_failure and stops_being_enforced_if_wrong.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanism: a second pin file naming its own scope is declared and approved; one compare path, no new dependency.
- Fail closed: a test pins that baseline.json names no scope, that the quick file's scope equals the CI flags, and that the flags sit only inside the merge request branch; a scope drift never turns main into a narrower run.
- Ratchet: a quick pin cannot rise above main's copy of the file; the first fill is the one unratcheted step and gets a delta re-review against the first pipeline's counts.json.
- Cost: merge request build minutes fall; main and web runs are unchanged. No credentials, no permission widening.
- The approved trade is declared: a defect at 320, 360, 375 or 700 px or in Finnish, or a wrong full pin, shows on main after the merge.
- Delta round 4, the quick pin fill: the pins equal the first merge request pipeline's counts.json section by section (834 rendered lines, 274 coverage lines), none is padded, none exceeds the same key in baseline.json, and the scope keys and platform match the CI flags and runner. The fill makes the guard real; no mechanism, dependency or cost is added.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The only change in this lane is one sentence in docs/wireframes/block_standard.md; no wireframe block, metric row, tier, label or percentage changes, so nothing is bound to a field.
- The sentence matches the code: the quick flags appear only inside the merge request branch of .gitlab-ci.yml, and main and web runs read baseline.json at the default scope.
- The widths and languages it names match the doc's own list of widths and languages; it does not claim a merge request catches defects at the other widths or in Finnish.
- check_page_css.py reads only baseline.json's static section, so the quick file's missing static key breaks nothing.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-run and interruption safety: the check keeps no state outside a temp dir; a second run gives the same result.
- CI step ends in the python command, so its exit code is the job's; an empty-pin first run is red by design and uploads counts.json because artifacts are kept on failure.
- The changed full-run computation is covered end to end: a narrower scope against a baseline that names it compares, and against one that names none compares nothing.
- The merge request base lookup for the quick file returns None only when git says the file is missing, and fails closed on any other error.
- No requirements or package file changes; build:site-v2 and hosting config untouched.
