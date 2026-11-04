# Review — claude/feat-243-registry-de2b6b

diff_sha256: 1d6d1179b3cfd88105b372c18a87278f8ffb18b7c524aca15fdc0eae61279389

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2 FAIL closed: the contract's decisions_taken records the approval that the font covers every page, the Player page included, and that the competition stats page belongs to #129.
- `[player].astro` renders only Layout, a crumb and the heading, so the row changes do not reach it; only the font does.
- RecentMatch.astro and HeadToHead.astro are in scope_paths; the dot staying with the competition falls under the narrow-rows decision and components.yml's result-row rule.
- The pin exception in impact_map, decisions_taken, protected_override and amendments agree with the diff.
- Delta round: the rest of the branch was audited in rounds 1 and 2.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- With no competition, the row shows only the date, with no stray dot.
- The `.rmeta` markup matches components.yml's result-row rule and the generated row in block_standard.md.
- Only RecentMatch, HeadToHead and MatchGoals write `.rmeta`; the first two share one shape and MatchGoals is the goal row, ruled separately.
- Delta round: read from source; the built markup is in acceptance_evidence.md.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 2 FAIL closed: protected_override, the pin exception entry, decisions_taken and amendments state truthfully what the exception allows, that no test caps a listed count, and when it stops matching.
- validate:ui runs tests/test_design_inventory.py and test:python runs tests/ on every non-scheduled pipeline, as the record says.
- `_mains_baseline` uses HEAD^1 on main, so the first main pipeline still matches and later ones do not.
- All nine INTER_RISES values equal tests/fixtures/design_inventory/baseline.json; the comment above them is true.
- The no-break space and the Player page ruling need no further authority.
- The pin commit is not covered here: it takes its own delta against the nine counts.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The comment above INTER_RISES is accurate against `_unlisted`, `test_no_pin_rises_above_mains` and `di.rises`.
- Eleven script, test, hook and CI files in the patch match the staged blobs.
- The baseline is not re-pinned in this diff, so the nine exceptions are unexercised until CI's measurement lands.
