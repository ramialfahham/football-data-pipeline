# Task contract — retire two obsolete scripts (#423, #424)

> Audit F14/F15: delete two dead scripts. Both verified unreferenced (no CI, no
> imports, no docs). Pure deletion. See docs/working_agreement.md §2/§4.

objective: >
  Retire two obsolete scripts flagged by the G4 audit:
  - #423 (F14): scripts/scaffold_domestic_league_staging.py — generates per-competition
    staging dirs, which the zero-file rule forbids; obsolete under unified raw tables.
  - #424 (F15): scripts/add_footer_i18n_keys.py — a one-time footer i18n migration,
    long complete; no __main__ guard, not idempotent. Retire it.
  Both confirmed unreferenced by CI, other scripts, and docs (grep, this session).
refs: #423 (F14), #424 (F15).

scope_paths:
  - scripts/scaffold_domestic_league_staging.py
  - scripts/add_footer_i18n_keys.py
  - .claude/active_work.md   # artifact-only: handover write-out at close

decisions_taken: >
  CPO-approved deletions (audit rulings 2026-06-12). Pure removal of dead code; no
  behavior change to any live path (both scripts are unreferenced).

decisions_reserved:
  - None. If a reviewer finds ANY live reference, STOP and escalate rather than delete.

done_when:
  - both script files are removed (git rm); grep shows zero remaining references to
    either script name anywhere except the audit doc + task artifacts.
  - validate-local offline gates green (the python-ci test suite does not import either).
  - reviewers: scope-auditor (always) + cto-reviewer (scripts/) — PASS.

amendments: (none)
