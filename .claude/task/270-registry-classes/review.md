# Review — fix/270-registry-classes-known

diff_sha256: 3cd08f378b2ef4b5e080a432e1f02f734eaa4d1ed5dacfb4814eacfa4ef4bde0

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path and the task folder are in scope_paths; no amendments.
- check_design_inventory.py and test_design_inventory.py are named in protected_override with a dated approval; the impact_map traces the guard, the blast radius and the registry's own gap pin.
- block_standard.md changes by the one approved line and carries no rationale or history.
- Every changed class pin falls and class-only entries are dropped; no other count moves; nothing reserved is decided.

## platform-reviewer
VERDICT: PASS
risks_checked:
- registry_classes reads the shape check_component_registry validates; a missing or malformed registry raises, so the check fails closed and never undercounts; PyYAML is already pinned for validate:ui.
- `registered` has one reader, COUNT_JS; check_page_css.py and the other counts are untouched.
- The new test fails without the change on both runs and exercises the listed and unlisted branches; its default-registry run relies on `crest` staying an unruled part.
- Removed baseline entries break no comparison or baseline test; the layout is unchanged and only class pins move, all downward.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The registry's open parts stay pinned by its own gap count, so the defect is counted once at its owner, not dropped.
- The check stays fail-closed on a bad registry.
- No new package, mechanism, run cadence or cost; the approval is named in protected_override and decisions_taken matches the diff.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- block_standard.md's sentence matches the code: every table row comes from a registry part, so "classes the component registry does not list" covers the table's classes too.
- The rest of the paragraph and the generated element table are unchanged and still accurate.
- No site_v2/src file changes; nothing a reader of the site sees changes.
