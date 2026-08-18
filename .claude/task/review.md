# Review — fix/74-nightly-image-tracks-main — 2026-08-18

diff_sha256: 437ed2f33c6b79aee3bfe9f0e7d08592099caf0e1d89dbdb1e9be89f94246eea

rounds: 3

> This is the review cycle for the KANIKO REDESIGN specifically. The original
> `--source .`/Cloud Build design went through its own 3 full rounds first (all
> reviewer verdicts and findings for that design are preserved in this branch's
> commit history via `.claude/task/escalations.log`), FAILed round 3 on a real
> project-Editor escalation path (verified live), and was replaced — at the
> CPO's explicit in-session choice — with an entirely different mechanism
> (build in the CI job with kaniko, no Cloud Build). That is a fresh design,
> not a patch, so it was reviewed as its own cycle from round 1. This file
> reflects only the kaniko cycle's 3 rounds, all summarized below.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: every changed file matches contract.md's scope_paths; the mid-task redesign (Cloud
  Build to kaniko) is recorded as a direct, in-session CPO choice presented with the finding
  and the alternative, not smuggled in as routine; the grant/revoke IAM history carries paired
  command evidence in escalations.log, read and cross-checked against the live .gitlab-ci.yml
  claims it rests on (WIF variables not Protected, Cloud Build default identity holds Editor)
  rather than trusted as narrative.
- Round 2: the scope_paths amendment (+Dockerfile) matches its stated content exactly (a header
  comment correction); the `.gcloudignore` rewrite, the dropped `:latest` tag, and the new
  resource_group/needs presence tests were all verified against the actual diff, not the
  contract's prose; no new §10-class decision, no new IAM action this round.
- Round 3: the `needs:` widening (+validate:secrets, +lint:python) is a reviewer-directed detail
  fix on an already-authorized CI gate, carries its own dated amendment naming round-2
  platform-reviewer as authority, and does not rise to a fresh CPO-class decision. Scope,
  authority and decision-rights hold across all three rounds.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1: traced the kaniko escalation surface end to end — `build:nightly-image` fires only
  on push-to-main (no feature-branch Dockerfile ever reaches it pre-merge), needs no Cloud
  Build submit right, and `roles/artifactregistry.writer` alone covers the push. Confirmed the
  self-actAs `iam.serviceAccountUser` grant is the correct one given the runtime SA is
  `github-actions-dbt` itself. Accepted the authority chain (CPO shown the finding and the two
  paths, chose the toolchain by name) and flagged kaniko's own upstream maintenance cadence as
  an honestly-unverified, accepted gap rather than asserting it either way.
- Round 2: verified the `.gcloudignore` model correction, the `:latest`-to-SHA-only tag fix and
  its corrected residual-risk description (the real hazard is `resource_group`'s unordered
  process mode, not an unread tag), and the doc sweep (Dockerfile, .dockerignore headers) all
  landed exactly as claimed against the real files. Four observations noted as non-blocking
  (README's accurate-in-context Cloud Build mention, .gitattributes' still-relevant fallback
  framing, impact_map's narrowly-optimistic blast_radius phrasing, google/cloud-sdk:slim as an
  unnamed second third-party image) — none escalated to a FAIL then or now.
- Round 3: confirmed all four `needs:` targets (validate:governance, validate:secrets,
  lint:python, test:python) carry unconditional `when: on_success` after the schedule guard
  with no `changes:`/`if:` clause that could make any absent on a push-to-main pipeline — the
  widening cannot make the pipeline unconstructible. Re-checked all four round-2 observations on
  the last round; none tips into a defect.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1: verified kaniko's Artifact Registry auth actually works via the same WIF
  external_account file the Python client libraries use (traced kaniko's own credential
  resolution chain, not asserted), the busybox/ash shell compatibility with `*gcp_auth`'s
  script, and `gcloud run jobs update --image=` preserving the job's other settings (service
  account, secrets, cpu/memory, timeout, retries) rather than resetting them.
- Round 2: independently confirmed all four round-1 findings fixed by re-deriving the model
  from source (kaniko reads `.dockerignore` only; `.gcloudignore` restores rather than narrows
  the manual-fallback exclusion set via `#!include:.gitignore`, verified against real
  `.gitignore` patterns including ones that were genuinely sitting in the tree). Found ONE new
  issue this round: `build:nightly-image`'s `needs:` omitted `validate:secrets` and
  `lint:python`, letting a failed secrets scan not block the image build — same failure class as
  the credential-leak defect this branch already found once.
- Round 3: verified the `needs:` widening by exact job name and rule inspection (all four gates
  unconditional on push-to-main, stage order holds, `data:build:main` correctly NOT added since
  its narrower path filter would make the pipeline unconstructible); confirmed the new test is
  non-vacuous by hand-checking it fails against the reverted two-gate list. Traced a genuine
  two-sided trade-off (the widened `needs:` decouples the image deploy from the `data` stage
  entirely, so a failing prod dbt build doesn't block it either) and concluded blocking on that
  would reintroduce #74 itself, not a defect. All four round-2 non-blocking observations
  re-examined on the last round; none escalated.

## escalations
(none)
