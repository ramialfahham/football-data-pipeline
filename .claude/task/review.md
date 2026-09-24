# Review — chore/claude-md-stale-facts — 2026-09-24

diff_sha256: 0a652fec5bf4ba995335b2c22ba8fc6baaf32d2b4bfe35c0c61042cf79b8087d

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Exactly three CLAUDE.md passages change and no other line; each new pointer is true: `FAST_GATES` holds six gates run with the repo's `.venv` when present, `.gitlab-ci.yml` has five stages, and the memory folder under `~/.claude/projects/` holds `MEMORY.md` while the old path and the two named files do not exist; only in-scope files; no new mechanism or cost; no credential-shaped string.

## escalations
(none)
