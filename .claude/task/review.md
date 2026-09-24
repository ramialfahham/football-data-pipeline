# Review — fix/stop-gate-uses-venv — 2026-09-24

diff_sha256: aade84dd5b44341fb70e6185966adc22abaa78df99d347774dda73cbca43511c

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every touched file (`.claude/hooks/stop_gate.py`, `tests/test_governance_hooks.py`, `.claude/task/**`) is in `scope_paths`; `protected_override` quotes the dated #162 plan approval naming the function; `NEW MECHANISM: none` and `RECURRING COST: none` match the diff; no credential-shaped string; no doc describes the changed behaviour.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Authority: `protected_override` plus a real `impact_map` for the protected hook. The hook still fails open (`_gate_python` runs inside `main()`'s `try`; a raising `subprocess.run` skips the gate). Gate scripts, `FAST_GATES`, scope and stash checks are unchanged, so no gate can pass that should fail. `.venv` is gitignored, so the trust model is unchanged. Choosing the interpreter inside the hook rather than in `.claude/settings.json` keeps the hook startable before setup. No new mechanism, dependency, cost or permission.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `_gate_python` is stateless; an interrupted setup gives the same false failure as today and a rerun fixes it. `test_stop_gate_runs_gates_with_the_repo_venv` goes red on revert (the stub passes only inside the temp repo's `.venv`); `test_stop_gate_without_a_venv_runs_gates_with_its_own_python` pins the fallback and the interpreter in the message; `.gitignore` is committed before `.venv` is created so the scope check is not what the test hits; both venv layouts are exercised on Windows and CI Linux. Fails open locally; worktrees fall back as today; CI never runs the hook.
- Non-blocking observation (not taken): `.venv/Scripts/python.exe` is tried first on every OS, which would matter only for a Linux process on this Windows checkout (e.g. WSL); nothing here runs the hook that way.

## escalations
(none)
