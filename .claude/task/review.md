# Review — docs/166-metrics-display-one-window — 2026-10-17

diff_sha256: 6d71b124e35be24343a348893b274dcd5039e02615e9d3a0ebae9f80d4c74059

rounds: 1

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- One hunk: rule 3 is replaced by the approved text; numbering stays 1 to 5 and no other line changes.
- The built match page renders one form block per team with no switch, the block the export picks by the warehouse's is_form_window flag; the new rule states exactly that.
- The flag is tested to hold at most one window per side, and the section 3 to 4 reference resolves.
- No other rule in the file contradicts the new rule 3, and no document cites the removed rule.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; no code, site, dbt, export or protected file changes.
- The added text matches the approved words; only the line wrap differs.
- The locked-document change names its approval in decisions_taken; decisions_reserved none is honest.
- No decision history, rationale or chat quote in the document.

## escalations
- none
