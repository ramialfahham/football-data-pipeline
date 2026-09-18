# Review — docs/readme-ci-badge — 2026-09-18

diff_sha256: d597b1ec85b0edcf85ef53fa8b15899d8ead97c815a501eac8c70d60fca5ac54

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- CPO authority for the §10 content decision (a badge is user-visible and permanent once published): `refs` quotes the dated chat, 2026-09-18, "yes, static badge", after the static-or-public choice was put to him.
- The badge's label (`CI` / `GitLab`) and link target (the repository page, not the pipelines page) match `decisions_taken`; the image is shields.io with a logo, the style of the row's other badges.
- README change is surgical: one line inserted, no deletion, nothing reordered.
- No credential or secret in the badge URL; README is not a protected or structural path, so no `impact_map` is owed; no new mechanism or recurring cost.
- `decisions_reserved` correctly empty: the CPO decided static over public pipelines; the form is the builder's and is stated in the MR head.

## escalations
(none)
