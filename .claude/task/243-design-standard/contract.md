# Task contract — design standard and visual-details decision right

objective: >
  Commit two texts copied word for word: the new docs/design/design_standard.md, and one
  paragraph "Visual details" in docs/working_agreement.md section 10 after the Agent-executable
  paragraph. Core document text approved in chat, 16 Nov 2026.
refs: "#243"

scope_paths:
  - docs/design/design_standard.md
  - docs/working_agreement.md

depends_on:
  - none: documentation only, no open MR's code is needed
shared_files:
  - none: no design baseline file is touched

decisions_taken: >
  Both texts are exact and unchanged; core document text approved in chat, 16 Nov 2026. No new
  mechanism and no recurring cost.

decisions_reserved:
  - none: both texts are CPO-approved word for word; a failing repo check is reported, never fixed by rewording

done_when:
  - docs/design/design_standard.md is byte-identical to the approved draft
  - the Visual details paragraph stands directly after the Agent-executable paragraph in working_agreement.md section 10
  - python scripts/ci_local.py --mr is green
  - full pytest is green

amendments: (none)
