# Review — claude/322-ci-local-long-paths — 2026-11-16

diff_sha256: d0c0cec3c59a017dda52c89ac0fdc51f4caa3f882834ae37643f4ffcf841286c

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged file is in scope_paths; depends_on and shared_files are present with reasons.
- No machine setting, new mechanism, dependency or recurring cost; the prefix is applied in-process only.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: long_path mangled UNC paths. Round 2: extended() maps a UNC path to the UNC form of the extended prefix, leaves an already-prefixed path alone, and a platform-neutral parametrized test pins the three branches.
- collect_needs returns the plain folder, so no extended prefix reaches the docker mount arguments.
- A live run of build:site-v2 and validate:ui from this deep worktree passed end to end.

## escalations
(none)
