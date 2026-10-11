# Review — docs/naming-rule

diff_sha256: e406463e497e8b8d5a0f343f6c63ab3206090a548996eaee48cdd3ed328a35ad

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- The diff is the two rule lines in engineering_standards.md, the deleted content_architecture.md bullet and the contract, all in scope_paths; the rule text is in decisions_taken; no mart is renamed and the intermediate and staging lines are unchanged.
- The old rule text has no other copy in the repository; layering.md keeps the tests for fct_ and dim_, which the new line points to.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every core model is fct_ or dim_; every mart starts with one of the five entity words except the seven the contract lists, which matches an independent count of the 29 marts.
- No script, hook, test or CI gate reads the changed lines; check_layer_contract.py checks only the fct_ prefix, which the rule keeps.

## escalations
(none)
