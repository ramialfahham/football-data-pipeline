# Review — feat/deploy-site-v2-firebase — 2026-07-24

diff_sha256: c05c7a6b0ec67bf858769bf9a96d636147159d81d42fdb8316701f0c038fb735

rounds: 5
rounds_cap_override: The CPO redirected scope mid-task (2026-07-24, "we work on the new website. Period."), after authorizing proceeding past the cap in the prior AskUserQuestion. Rounds 2-5 were the now-removed MVP-retirement doc detour, not new defects in the deploy job itself, which passed cto-reviewer every round. The final state is vendor-only, and both required reviewers PASS at this hash.

## scope-auditor
VERDICT: PASS
risks_checked:
- WIF/ADC credential chain for the Firebase hosting deploy: the workflow depends on firebase-tools accepting the Application Default Credentials the WIF step sets up. Checked that the contract flags this as verified-at-first-dispatch with a documented fallback (a firebasehosting.admin key raised to the CPO, never adopted silently), so the assumption is explicit and gated, not a silent decision.
- Base URL config alignment: the base flip /v2/ -> / affects every internal link and asset prefix. Checked that firebase.json (trailingSlash true, public dist, root serving) and astro.config.mjs (base /, trailingSlash always) are mutually consistent, the impact_map states the dist/ layout is unchanged, and the sample build is verified clean in de/en/fi.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard-path integrity (opus floor): the protected workflow file is byte-unchanged from the prior pass — workflow_dispatch-only (no schedule/workflow_run/push), minimal contents:read + id-token:write permissions, WIF secrets referenced by name, deploy-site-v2 concurrency group (not the prod-warehouse-write group, correct for a read-only export). The contract's protected_override quoting the CPO approval is intact.
- Governance scrubbing is a behavioral no-op: removing the MVP-retirement wording touched only prose (the doc vendor rows, the contract amendment, the astro.config comment). No CI check, hook, or workflow keys off the removed text; astro's actual config values (base /, i18n, output, trailingSlash) are byte-unchanged; the pre-existing MVP-stays-live constraint row is left untouched.

## escalations
(none)
