# Review — feat/235-team-data — 2026-10-28

diff_sha256: b9d6a723c678b07171a4206319270ffb3047fe25a55136265062a544bf4a9402

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; both amendments name their authority; approved_design names the Team page, the only reader of the changed marts.
- The rank by direction and the upcoming date rule are quoted from the approved plan; the committed samples do not change here.
- No secret, no new dependency or run cadence; the export only selects and indexes.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every join keeps its grain; the last-season value is chosen as int_team_profile__yoy chooses it; the rank follows direction with shared ties.
- The season summary's runs moved unchanged into the shared intermediate; the descriptions and the layering row state what the models do.
- The two new tests fail in each direction; relationship and range tests cover the new columns.
- A shoot-out after a level score is neither a biggest win nor a heaviest defeat, which the two result tests pin.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The export tests pin the last-season value, the featured season's strip and the whole-table read on a sample run; each fails on revert.
- The generated metric map matches the catalogue and the YAML.
- No dependency, credential, workflow or hosting change; the strip adds about 15% to a team file, on the featured season only.

## escalations
(none)
