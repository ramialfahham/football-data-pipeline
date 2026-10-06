# Review — docs/clean-core-docs

diff_sha256: 95469fd2692e587bab509727f93374cf479cfe5fd76609b5a2abeb996031d073

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- All files in scope_paths; no new mechanism, recurring cost, URL, slug, metric or label decision; the two pin tables lose exactly the six rewritten documents.
- Claims spot-checked against the repo: dim_coach, club_qualifying, fixture_slug, is_next_round, team_slug, slug_map, translit_latin, the copy gate in CI and the Stop hook, artifact_only and hash_exclude_paths.
- Section numbers and the parity anchors of working_agreement.md hold; decisions_reserved is not contradicted.
- Round 1 FAIL closed: the UI design brief now states the missing-value glyph as the en dash in all three places, matching format.ts and the other documents.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Pin rows removed in both tables match the tree: zero history markers and no sentence over its limit in the six documents.
- tests/test_governance_doc_parity.py: the three working_agreement anchors and the north_star anchor match once; the nine-path list and the three shared paths stay complete runs.
- Section anchors cited by hooks and agents still exist; no dependency, credential, workflow, build or hook change.
- Round 2 delta: two glyphs in the UI design brief; no word count, sentence boundary or history marker moves.

## escalations
(none)
